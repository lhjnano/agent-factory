from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass
import asyncio

from .base_worker import BaseWorker, WorkerType, WorkerResult, WorkerConfig

if TYPE_CHECKING:
    from ..work import Work
    from ..agent_pool import AgentInstance


@dataclass
class LLMWorkerConfig(WorkerConfig):
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_delay: float = 0.1
    enable_streaming: bool = False
    max_tokens_per_request: int = 4000


class LLMWorker(BaseWorker):
    def __init__(
        self,
        agent: "AgentInstance",
        config: Optional[LLMWorkerConfig] = None
    ):
        super().__init__(WorkerType.LLM, agent, config or LLMWorkerConfig())
        self._rate_limit_counter: int = 0
        self._last_rate_limit: Optional[float] = None
    
    async def execute(self, work: "Work") -> WorkerResult:
        from datetime import datetime
        
        started_at = datetime.now()
        
        await self._apply_rate_limiting()
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.config.max_retries:
            try:
                result = await self._call_llm(work)
                
                return WorkerResult(
                    success=True,
                    output=result,
                    metrics={
                        "tokens_used": work.estimated_tokens,
                        "retry_count": retry_count
                    },
                    started_at=started_at,
                    completed_at=datetime.now()
                )
                
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                
                if self._is_rate_limit_error(e):
                    await self._handle_rate_limit()
                else:
                    await asyncio.sleep(self.config.retry_delay * retry_count)
        
        return WorkerResult(
            success=False,
            error=f"LLM call failed after {retry_count} retries: {last_error}",
            started_at=started_at,
            completed_at=datetime.now()
        )
    
    async def _call_llm(self, work: "Work") -> any:
        if hasattr(work, 'execute_func') and work.execute_func:
            return await work.execute_func(work.inputs)
        
        await asyncio.sleep(0.1)
        
        return {
            "work_id": work.work_id,
            "type": work.work_type,
            "result": f"LLM processed: {work.name}"
        }
    
    async def _apply_rate_limiting(self):
        if self._last_rate_limit:
            elapsed = asyncio.get_event_loop().time() - self._last_rate_limit
            if elapsed < self.config.rate_limit_delay:
                await asyncio.sleep(self.config.rate_limit_delay - elapsed)
    
    def _is_rate_limit_error(self, error: Exception) -> bool:
        error_str = str(error).lower()
        return "rate limit" in error_str or "429" in error_str
    
    async def _handle_rate_limit(self):
        self._rate_limit_counter += 1
        self._last_rate_limit = asyncio.get_event_loop().time()
        
        backoff = min(2 ** self._rate_limit_counter, 60)
        await asyncio.sleep(backoff)
    
    def get_llm_stats(self) -> dict:
        return {
            **self.get_stats(),
            "rate_limit_counter": self._rate_limit_counter,
            "last_rate_limit": self._last_rate_limit
        }
