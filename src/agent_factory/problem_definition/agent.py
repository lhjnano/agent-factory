import asyncio
import json
from pathlib import Path
from typing import Any, Dict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .. import expand_config_paths, AGENT_DIR, HOME_DIR


class ProblemDefinitionAgent:
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.tools: Dict[str, Any] = {}

    async def connect_servers(self):
        config_path = AGENT_DIR / "problem_definition" / "mcp_config.json"
        with open(config_path) as f:
            config = expand_config_paths(json.load(f))

        for name, server_config in config["mcpServers"].items():
            params = StdioServerParameters(
                command=server_config["command"],
                args=server_config["args"],
                env=server_config.get("env", {})
            )
            session = await stdio_client(params)
            await session.initialize()
            self.sessions[name] = session
            self.tools[name] = await session.list_tools()

    async def define_problem(self, user_requirements: str) -> Dict[str, Any]:
        context = {
            "requirements": user_requirements,
            "constraints": {},
            "success_metrics": []
        }

        result = {
            "problem_statement": "",
            "objectives": [],
            "constraints": [],
            "success_criteria": [],
            "stakeholders": []
        }

        memory_session = self.sessions.get("memory")
        if memory_session:
            await memory_session.call_tool(
                "memory_store",
                arguments={"key": "problem_definition", "value": json.dumps(result)}
            )

        return result

    async def create_project_plan(self, problem_def: Dict) -> Dict[str, Any]:
        phases = [
            {"name": "data_collection", "estimated_days": 3, "dependencies": []},
            {"name": "design_development", "estimated_days": 7, "dependencies": ["data_collection"]},
            {"name": "training_optimization", "estimated_days": 10, "dependencies": ["design_development"]},
            {"name": "evaluation_validation", "estimated_days": 5, "dependencies": ["training_optimization"]},
            {"name": "deployment_monitoring", "estimated_days": 3, "dependencies": ["evaluation_validation"]}
        ]

        return {"phases": phases, "timeline": sum(p["estimated_days"] for p in phases)}

    async def close(self):
        for session in self.sessions.values():
            await session.close()


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
