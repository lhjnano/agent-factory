import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from .. import expand_config_paths, AGENT_DIR, HOME_DIR


class AgentCoordinator:
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self._exit_stack = AsyncExitStack()
        self.agents: Dict[str, Any] = {}
        self.workflow_state: Dict[str, Any] = {}

    async def connect_servers(self):
        """sub-MCP 서버 연결 시도. 실패해도 서버 동작에 영향 없음."""
        try:
            config_path = AGENT_DIR / "coordinator" / "mcp_config.json"
            with open(config_path) as f:
                config = expand_config_paths(json.load(f))

            for name, server_config in config["mcpServers"].items():
                try:
                    params = StdioServerParameters(
                        command=server_config["command"],
                        args=server_config["args"],
                        env=server_config.get("env", {})
                    )
                    read, write = await self._exit_stack.enter_async_context(stdio_client(params))
                    session = await self._exit_stack.enter_async_context(ClientSession(read, write))
                    await session.initialize()
                    self.sessions[name] = session
                except Exception as e:
                    pass  # 개별 서버 연결 실패 무시
        except Exception:
            pass  # config 파일 없거나 전체 실패 무시

    async def initialize_agents(self):
        agent_dirs = [
            "problem_definition",
            "data_collection",
            "design_development",
            "training_optimization",
            "evaluation_validation",
            "deployment_monitoring"
        ]

        for agent_dir in agent_dirs:
            agent_path = AGENT_DIR / agent_dir
            if agent_path.exists():
                self.agents[agent_dir] = {
                    "path": str(agent_path),
                    "status": "ready",
                    "config": self._load_agent_config(agent_path)
                }

    def _load_agent_config(self, agent_path: Path) -> Dict:
        config_file = agent_path / "mcp_config.json"
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
        return {}

    # Keys each phase actually needs from the previous phase result.
    # Passing only these avoids propagating full result dicts as context.
    _ESSENTIAL_KEYS: Dict[str, list] = {
        "problem_definition":    ["objective", "model_type", "features", "target", "constraints"],
        "design_development":    ["architecture", "model_class", "hyperparameters", "input_shape"],
        "data_collection":       ["data_path", "schema", "row_count"],
        "training_optimization": ["model_path", "metrics"],
        "evaluation_validation": ["accuracy", "metrics", "model_path"],
    }

    def _extract_essentials(self, phase: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Return only the keys the next phase needs from a phase result."""
        keys = self._ESSENTIAL_KEYS.get(phase, [])
        if not keys:
            return result
        return {k: result[k] for k in keys if k in result}

    async def execute_workflow(self, user_request: str) -> Dict[str, Any]:
        workflow_result = {
            "request": user_request,
            "phases": [],
            "status": "in_progress",
            "errors": []
        }

        try:
            # problem_definition and data_collection are independent — run in parallel
            problem_def, data_result = await asyncio.gather(
                self._run_phase("problem_definition", {"requirements": user_request}),
                self._run_phase("data_collection", {"sources": [str(HOME_DIR / "data" / "raw_data.csv")]})
            )
            workflow_result["phases"].extend([problem_def, data_result])

            design_result = await self._run_phase(
                "design_development",
                {"problem_def": self._extract_essentials("problem_definition", problem_def.get("result", {}))}
            )
            workflow_result["phases"].append(design_result)

            training_result = await self._run_phase(
                "training_optimization",
                {"model_config": self._extract_essentials("design_development", design_result.get("result", {}))}
            )
            workflow_result["phases"].append(training_result)

            eval_result = await self._run_phase(
                "evaluation_validation",
                {"model": "trained_model"}
            )
            workflow_result["phases"].append(eval_result)

            deploy_result = await self._run_phase(
                "deployment_monitoring",
                {"model_path": str(HOME_DIR / "models" / "final_model.pt")}
            )
            workflow_result["phases"].append(deploy_result)

            workflow_result["status"] = "completed"

        except Exception as e:
            workflow_result["status"] = "failed"
            workflow_result["errors"].append(str(e))

        return workflow_result

    async def _run_phase(self, phase_name: str, inputs: Dict) -> Dict[str, Any]:
        result = {
            "phase": phase_name,
            "status": "completed",
            "result": {},
            "timestamp": None
        }

        print(f"[{phase_name}] Starting...")

        agent_module = __import__(
            f"agents.{phase_name}.agent",
            fromlist=[""]
        )

        agent = getattr(agent_module, f"{self._to_camel_case(phase_name)}Agent")()
        await agent.connect_servers()

        if phase_name == "problem_definition":
            result["result"] = await agent.define_problem(inputs.get("requirements", ""))
            result["result"].update(await agent.create_project_plan(result["result"]))
        elif phase_name == "data_collection":
            data = await agent.collect_data(inputs.get("sources", []))
            result["result"] = await agent.preprocess_data(data)
        elif phase_name == "design_development":
            architecture = await agent.design_architecture(inputs.get("problem_def", {}))
            await agent.generate_code(architecture)
            await agent.create_training_script(architecture)
            result["result"] = architecture
        elif phase_name == "training_optimization":
            result["result"] = {"status": "training_completed"}
        elif phase_name == "evaluation_validation":
            result["result"] = await agent.evaluate_model(None, None)
            result["result"].update(await agent.generate_report(result["result"]))
        elif phase_name == "deployment_monitoring":
            result["result"] = await agent.deploy_model(inputs.get("model_path", ""), {})

        await agent.close()
        print(f"[{phase_name}] Completed")

        return result

    def _to_camel_case(self, snake_str: str) -> str:
        components = snake_str.split('_')
        return ''.join(x.title() for x in components)

    async def monitor_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        memory_session = self.sessions.get("memory")
        if memory_session:
            status = await memory_session.call_tool(
                "memory_retrieve",
                arguments={"key": f"workflow_{workflow_id}"}
            )
            return json.loads(status) if status else {"status": "not_found"}
        return {"status": "not_found"}

    async def close(self):
        await self._exit_stack.aclose()


async def main():
    coordinator = AgentCoordinator()
    await coordinator.connect_servers()
    await coordinator.initialize_agents()

    print("Agent Coordinator Initialized")
    print(f"Loaded Agents: {list(coordinator.agents.keys())}")

    if len(sys.argv) > 1:
        user_request = " ".join(sys.argv[1:])
        print(f"\nExecuting workflow for: {user_request}")

        result = await coordinator.execute_workflow(user_request)

        filesystem_session = coordinator.sessions.get("filesystem")
        if filesystem_session:
            await filesystem_session.call_tool(
                "write_file",
                arguments={
                    "path": str(AGENT_DIR / f"workflow_result_{int(asyncio.get_event_loop().time())}.json"),
                    "content": json.dumps(result, indent=2, ensure_ascii=False)
                }
            )

        print(f"\nWorkflow Status: {result['status']}")
        if result['errors']:
            print(f"Errors: {result['errors']}")

    await coordinator.close()


if __name__ == "__main__":
    asyncio.run(main())
