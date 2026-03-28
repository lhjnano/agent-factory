from typing import TYPE_CHECKING, Optional, Dict, Any
from dataclasses import dataclass
import asyncio
import subprocess
import json
from pathlib import Path

from .base_worker import BaseWorker, WorkerType, WorkerResult, WorkerConfig

if TYPE_CHECKING:
    from ..work import Work
    from ..agent_pool import AgentInstance


@dataclass
class ExecutionWorkerConfig(WorkerConfig):
    default_timeout: float = 60.0
    max_output_size: int = 10000
    allowed_commands: list = None
    sandbox_enabled: bool = False
    working_directory: str = "/tmp"
    environment: Dict[str, str] = None
    
    def __post_init__(self):
        if self.allowed_commands is None:
            self.allowed_commands = ["python", "python3", "bash", "sh"]
        if self.environment is None:
            self.environment = {}


class ExecutionWorker(BaseWorker):
    def __init__(
        self,
        agent: "AgentInstance",
        config: Optional[ExecutionWorkerConfig] = None
    ):
        super().__init__(WorkerType.EXECUTION, agent, config or ExecutionWorkerConfig())
        self._execution_count: int = 0
        self._total_execution_time: float = 0.0
    
    async def execute(self, work: "Work") -> WorkerResult:
        from datetime import datetime
        
        started_at = datetime.now()
        
        try:
            if work.inputs.get("code"):
                result = await self._execute_code(work)
            elif work.inputs.get("command"):
                result = await self._execute_command(work)
            elif work.inputs.get("script_path"):
                result = await self._execute_script(work)
            else:
                result = await self._default_execution(work)
            
            self._execution_count += 1
            execution_time = (datetime.now() - started_at).total_seconds()
            self._total_execution_time += execution_time
            
            return WorkerResult(
                success=True,
                output=result,
                metrics={
                    "execution_time": execution_time,
                    "execution_count": self._execution_count
                },
                started_at=started_at,
                completed_at=datetime.now()
            )
            
        except asyncio.TimeoutError:
            return WorkerResult(
                success=False,
                error=f"Execution timed out after {self.config.default_timeout}s",
                started_at=started_at,
                completed_at=datetime.now()
            )
            
        except Exception as e:
            return WorkerResult(
                success=False,
                error=f"Execution failed: {str(e)}",
                started_at=started_at,
                completed_at=datetime.now()
            )
    
    async def _execute_code(self, work: "Work") -> Dict[str, Any]:
        code = work.inputs.get("code", "")
        language = work.inputs.get("language", "python")
        
        if language == "python":
            return await self._execute_python_code(code, work.inputs)
        elif language == "bash":
            return await self._execute_bash_code(code, work.inputs)
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    async def _execute_python_code(self, code: str, inputs: dict) -> Dict[str, Any]:
        temp_file = Path(self.config.working_directory) / f"exec_{inputs.get('work_id', 'temp')}.py"
        temp_file.write_text(code)
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "python3",
                str(temp_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.config.working_directory,
                env={**dict(__import__('os').environ), **self.config.environment}
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.config.default_timeout
            )
            
            return {
                "returncode": proc.returncode,
                "stdout": stdout.decode()[:self.config.max_output_size],
                "stderr": stderr.decode()[:self.config.max_output_size]
            }
            
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    async def _execute_bash_code(self, code: str, inputs: dict) -> Dict[str, Any]:
        proc = await asyncio.create_subprocess_shell(
            code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.config.working_directory
        )
        
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=self.config.default_timeout
        )
        
        return {
            "returncode": proc.returncode,
            "stdout": stdout.decode()[:self.config.max_output_size],
            "stderr": stderr.decode()[:self.config.max_output_size]
        }
    
    async def _execute_command(self, work: "Work") -> Dict[str, Any]:
        command = work.inputs.get("command", "")
        args = work.inputs.get("args", [])
        
        if not self._is_command_allowed(command):
            raise ValueError(f"Command not allowed: {command}")
        
        proc = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.config.working_directory
        )
        
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=self.config.default_timeout
        )
        
        return {
            "returncode": proc.returncode,
            "stdout": stdout.decode()[:self.config.max_output_size],
            "stderr": stderr.decode()[:self.config.max_output_size]
        }
    
    async def _execute_script(self, work: "Work") -> Dict[str, Any]:
        script_path = Path(work.inputs.get("script_path", ""))
        
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        proc = await asyncio.create_subprocess_exec(
            "bash" if script_path.suffix == ".sh" else "python3",
            str(script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.config.working_directory
        )
        
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=self.config.default_timeout
        )
        
        return {
            "returncode": proc.returncode,
            "stdout": stdout.decode()[:self.config.max_output_size],
            "stderr": stderr.decode()[:self.config.max_output_size]
        }
    
    async def _default_execution(self, work: "Work") -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {
            "work_id": work.work_id,
            "result": f"Executed: {work.name}"
        }
    
    def _is_command_allowed(self, command: str) -> bool:
        if not self.config.allowed_commands:
            return True
        
        cmd_name = Path(command).name
        return cmd_name in self.config.allowed_commands
    
    def get_execution_stats(self) -> dict:
        return {
            **self.get_stats(),
            "execution_count": self._execution_count,
            "total_execution_time": self._total_execution_time,
            "avg_execution_time": (
                self._total_execution_time / self._execution_count
                if self._execution_count > 0 else 0
            )
        }
