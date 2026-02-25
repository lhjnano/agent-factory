import asyncio
import json
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from .. import expand_config_paths, AGENT_DIR, HOME_DIR


class DataCollectionAgent:
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}

    async def connect_servers(self):
        config_path = AGENT_DIR / "data_collection" / "mcp_config.json"
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

    async def collect_data(self, sources: List[str]) -> pd.DataFrame:
        collected_data = []

        for source in sources:
            if source.startswith("http"):
                fetch_session = self.sessions.get("fetch")
                if fetch_session:
                    response = await fetch_session.call_tool(
                        "fetch",
                        arguments={"url": source}
                    )
                    collected_data.append(response)
            elif source.endswith((".csv", ".json", ".parquet")):
                filesystem_session = self.sessions.get("filesystem")
                if filesystem_session:
                    response = await filesystem_session.call_tool(
                        "read_file",
                        arguments={"path": source}
                    )
                    collected_data.append(response)

        return pd.DataFrame(collected_data)

    async def preprocess_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        stats = {
            "original_rows": len(df),
            "original_columns": len(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "data_types": df.dtypes.astype(str).to_dict()
        }

        df_clean = df.dropna()
        stats["cleaned_rows"] = len(df_clean)
        stats["rows_removed"] = len(df) - len(df_clean)

        filesystem_session = self.sessions.get("filesystem")
        if filesystem_session:
            await filesystem_session.call_tool(
                "write_file",
                arguments={
                    "path": str(HOME_DIR / "data" / "processed_data.csv"),
                    "content": df_clean.to_csv(index=False)
                }
            )

        memory_session = self.sessions.get("memory")
        if memory_session:
            await memory_session.call_tool(
                "memory_store",
                arguments={"key": "data_stats", "value": json.dumps(stats)}
            )

        return stats

    async def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        quality_report = {
            "completeness": (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100,
            "uniqueness": df.duplicated().sum(),
            "consistency": df.nunique().to_dict()
        }

        return quality_report

    async def close(self):
        for session in self.sessions.values():
            await session.close()


async def main():
    agent = DataCollectionAgent()
    await agent.connect_servers()

    data = await agent.collect_data([str(HOME_DIR / "data" / "raw_data.csv")])
    if not data.empty:
        stats = await agent.preprocess_data(data)
        quality = await agent.validate_data_quality(data)

        print("Data Stats:", json.dumps(stats, indent=2, ensure_ascii=False))
        print("Quality Report:", json.dumps(quality, indent=2, ensure_ascii=False))

    await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
