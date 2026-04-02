import asyncio
import json
import re
from contextlib import AsyncExitStack
from typing import Any, Dict

from .. import expand_config_paths, AGENT_DIR, HOME_DIR


class ProblemDefinitionAgent:
    def __init__(self):
        self.sessions: Dict[str, Any] = {}
        self._exit_stack = AsyncExitStack()
        self.tools: Dict[str, Any] = {}

    async def connect_servers(self):
        """sub-MCP 서버 연결 시도. 실패해도 서버 동작에 영향 없음."""
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            config_path = AGENT_DIR / "problem_definition" / "mcp_config.json"
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
                    session = await self._exit_stack.enter_async_context(
                        ClientSession(read, write)
                    )
                    await session.initialize()
                    self.sessions[name] = session
                except Exception:
                    pass
        except Exception:
            pass

    async def define_problem(self, user_requirements: str) -> Dict[str, Any]:
        """user_requirements 텍스트를 파싱해 구조화된 문제 정의를 반환한다."""
        # 출력 포맷 힌트 줄 제거
        raw_lines = [
            l.strip() for l in user_requirements.split("\n")
            if l.strip() and not l.strip().startswith("[출력")
        ]

        # 첫 번째 유의미한 줄을 problem_statement로 사용
        problem_statement = raw_lines[0] if raw_lines else user_requirements[:300]

        # 목표 추출: 액션 키워드가 포함된 줄 또는 bullet point
        action_keywords = (
            "create", "add", "implement", "build", "fix", "update", "generate",
            "생성", "추가", "구현", "수정", "변경", "개발", "만들", "작성",
        )
        objectives = []
        for line in raw_lines[1:]:
            clean = line.lstrip("-*•#0123456789. ")
            if not clean:
                continue
            if (
                any(kw in clean.lower() for kw in action_keywords)
                or line.startswith(("-", "*", "•"))
            ):
                objectives.append(clean[:150])
        objectives = objectives[:10]

        # 제약 조건 추출: 금지/필수/주의 키워드
        constraint_keywords = (
            "must", "should not", "avoid", "never", "only", "반드시", "금지", "주의",
        )
        constraints = [
            line.lstrip("-*•#0123456789. ")[:150]
            for line in raw_lines
            if any(kw in line.lower() for kw in constraint_keywords)
        ][:5]

        # 파일 경로 패턴 → success_criteria
        file_patterns = re.findall(r"[\w/]+\.py\b", user_requirements)
        success_criteria = [f"파일 생성/수정: {p}" for p in file_patterns[:5]]

        result = {
            "problem_statement": problem_statement,
            "objectives": objectives,
            "constraints": constraints,
            "success_criteria": success_criteria,
            "stakeholders": [],
        }

        memory_session = self.sessions.get("memory")
        if memory_session:
            try:
                await memory_session.call_tool(
                    "memory_store",
                    arguments={"key": "problem_definition", "value": json.dumps(result)},
                )
            except Exception:
                pass

        return result

    async def create_project_plan(self, problem_def: Dict) -> Dict[str, Any]:
        """문제 정의를 바탕으로 소프트웨어 개발 단계를 반환한다."""
        objectives = problem_def.get("objectives", [])
        n = len(objectives)

        phases = [
            {"name": "analysis",        "estimated_days": 1, "dependencies": []},
            {"name": "design",           "estimated_days": max(1, n // 3), "dependencies": ["analysis"]},
            {"name": "implementation",   "estimated_days": max(2, n),      "dependencies": ["design"]},
            {"name": "testing",          "estimated_days": max(1, n // 2), "dependencies": ["implementation"]},
            {"name": "review",           "estimated_days": 1,              "dependencies": ["testing"]},
        ]

        return {
            "phases": phases,
            "timeline": sum(p["estimated_days"] for p in phases),
        }

    async def close(self):
        await self._exit_stack.aclose()


async def main():
    agent = ProblemDefinitionAgent()
    await agent.connect_servers()

    problem = await agent.define_problem("고객 이탈 예측 모델 개발")
    plan = await agent.create_project_plan(problem)

    print("Problem Definition:", json.dumps(problem, indent=2, ensure_ascii=False))
    print("Project Plan:", json.dumps(plan, indent=2, ensure_ascii=False))

    await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
