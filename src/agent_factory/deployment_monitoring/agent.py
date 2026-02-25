import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from .. import expand_config_paths, AGENT_DIR, HOME_DIR


class DeploymentMonitoringAgent:
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.deployment_status = {}

    async def connect_servers(self):
        config_path = AGENT_DIR / "deployment_monitoring" / "mcp_config.json"
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

    async def deploy_model(self, model_path: str, config: Dict) -> Dict[str, Any]:
        deployment_info = {
            "model_path": model_path,
            "version": config.get("version", "1.0.0"),
            "environment": config.get("environment", "production"),
            "endpoint": config.get("endpoint", "/api/predict"),
            "status": "deploying",
            "timestamp": time.time()
        }

        filesystem_session = self.sessions.get("filesystem")
        if filesystem_session:
            await filesystem_session.call_tool(
                "write_file",
                arguments={
                    "path": str(HOME_DIR / "deployments" / f"deployment_{deployment_info['version']}.json"),
                    "content": json.dumps(deployment_info, indent=2)
                }
            )

        self.deployment_status[deployment_info["version"]] = deployment_info

        postgres_session = self.sessions.get("postgres")
        if postgres_session:
            await postgres_session.call_tool(
                "postgres_query",
                arguments={
                    "query": """
                        INSERT INTO deployments (version, environment, endpoint, status, timestamp)
                        VALUES ($1, $2, $3, $4, NOW())
                    """,
                    "params": [
                        deployment_info["version"],
                        deployment_info["environment"],
                        deployment_info["endpoint"],
                        "deployed"
                    ]
                }
            )

        deployment_info["status"] = "deployed"
        return deployment_info

    async def monitor_performance(self, version: str) -> Dict[str, Any]:
        metrics = {
            "version": version,
            "request_count": 0,
            "avg_response_time": 0,
            "error_rate": 0,
            "cpu_usage": 0,
            "memory_usage": 0,
            "timestamp": time.time()
        }

        postgres_session = self.sessions.get("postgres")
        if postgres_session:
            result = await postgres_session.call_tool(
                "postgres_query",
                arguments={
                    "query": """
                        SELECT 
                            COUNT(*) as request_count,
                            AVG(response_time) as avg_response_time,
                            SUM(CASE WHEN error THEN 1 ELSE 0 END)::float / COUNT(*) as error_rate
                        FROM metrics
                        WHERE version = $1 AND timestamp > NOW() - INTERVAL '1 hour'
                    """,
                    "params": [version]
                }
            )
            metrics.update(result)

        filesystem_session = self.sessions.get("filesystem")
        if filesystem_session:
            await filesystem_session.call_tool(
                "write_file",
                arguments={
                    "path": str(HOME_DIR / "logs" / f"metrics_{version}_{int(time.time())}.json"),
                    "content": json.dumps(metrics, indent=2)
                }
            )

        return metrics

    async def check_health(self, endpoint: str) -> Dict[str, Any]:
        health_check = {
            "endpoint": endpoint,
            "status": "healthy",
            "last_check": time.time(),
            "response_time_ms": 0
        }

        fetch_session = self.sessions.get("fetch")
        if fetch_session:
            start_time = time.time()
            try:
                response = await fetch_session.call_tool(
                    "fetch",
                    arguments={"url": f"http://localhost:8000{endpoint}/health"}
                )
                health_check["response_time_ms"] = (time.time() - start_time) * 1000
            except Exception as e:
                health_check["status"] = "unhealthy"
                health_check["error"] = str(e)

        return health_check

    async def rollback_deployment(self, version: str) -> Dict[str, Any]:
        rollback_info = {
            "version": version,
            "action": "rollback",
            "timestamp": time.time(),
            "status": "completed"
        }

        postgres_session = self.sessions.get("postgres")
        if postgres_session:
            await postgres_session.call_tool(
                "postgres_query",
                arguments={
                    "query": """
                        UPDATE deployments
                        SET status = 'rolled_back', rolled_back_at = NOW()
                        WHERE version = $1
                    """,
                    "params": [version]
                }
            )

        return rollback_info

    async def alert_on_anomaly(self, metrics: Dict, thresholds: Dict) -> bool:
        alert_triggered = False

        if metrics["error_rate"] > thresholds.get("max_error_rate", 0.05):
            alert_triggered = True
        if metrics["avg_response_time"] > thresholds.get("max_response_time", 5000):
            alert_triggered = True

        if alert_triggered:
            filesystem_session = self.sessions.get("filesystem")
            if filesystem_session:
                await filesystem_session.call_tool(
                    "write_file",
                    arguments={
                        "path": str(HOME_DIR / "logs" / f"alert_{int(time.time())}.json"),
                        "content": json.dumps(metrics, indent=2)
                    }
                )

        return alert_triggered

    async def close(self):
        for session in self.sessions.values():
            await session.close()


async def main():
    agent = DeploymentMonitoringAgent()
    await agent.connect_servers()

    print("Deployment and monitoring agent initialized")

    await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
