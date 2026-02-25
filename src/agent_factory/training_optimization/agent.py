import asyncio
import json
import torch
import numpy as np
from pathlib import Path
from typing import Any, Dict
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from .. import expand_config_paths, AGENT_DIR, HOME_DIR


class TrainingOptimizationAgent:
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.training_history = []

    async def connect_servers(self):
        config_path = AGENT_DIR / "training_optimization" / "mcp_config.json"
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

    async def train_model(self, model, train_data, val_data, config: Dict) -> Dict[str, Any]:
        optimizer = torch.optim.Adam(model.parameters(), lr=config["learning_rate"])
        epochs = config["epochs"]
        batch_size = config["batch_size"]

        training_log = {
            "epoch_losses": [],
            "val_losses": [],
            "best_val_loss": float("inf")
        }

        for epoch in range(epochs):
            model.train()
            epoch_loss = 0

            for batch in train_data:
                optimizer.zero_grad()
                outputs = model(batch[0])
                loss = torch.nn.functional.binary_cross_entropy_with_logits(
                    outputs.squeeze(), batch[1].float()
                )
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()

            val_loss = await self._validate(model, val_data)
            training_log["epoch_losses"].append(epoch_loss / len(train_data))
            training_log["val_losses"].append(val_loss)

            if val_loss < training_log["best_val_loss"]:
                training_log["best_val_loss"] = val_loss
                await self._save_checkpoint(model, epoch, val_loss)

        return training_log

    async def _validate(self, model, val_data) -> float:
        model.eval()
        total_loss = 0
        with torch.no_grad():
            for batch in val_data:
                outputs = model(batch[0])
                loss = torch.nn.functional.binary_cross_entropy_with_logits(
                    outputs.squeeze(), batch[1].float()
                )
                total_loss += loss.item()
        return total_loss / len(val_data)

    async def _save_checkpoint(self, model, epoch, loss):
        checkpoint = {
            "model_state_dict": model.state_dict(),
            "epoch": epoch,
            "loss": loss
        }

        filesystem_session = self.sessions.get("filesystem")
        if filesystem_session:
            await filesystem_session.call_tool(
                "write_file",
                arguments={
                    "path": str(HOME_DIR / "checkpoints" / f"checkpoint_epoch_{epoch}.pt"),
                    "content": str(checkpoint)
                }
            )

        postgres_session = self.sessions.get("postgres")
        if postgres_session:
            await postgres_session.call_tool(
                "postgres_query",
                arguments={
                    "query": """
                        INSERT INTO checkpoints (epoch, loss, timestamp)
                        VALUES ($1, $2, NOW())
                    """,
                    "params": [epoch, loss]
                }
            )

    async def optimize_hyperparameters(self, model, train_data, val_data) -> Dict[str, Any]:
        param_space = {
            "learning_rate": [0.001, 0.0005, 0.0001],
            "batch_size": [32, 64, 128],
            "hidden_size": [64, 128, 256]
        }

        best_config = None
        best_score = 0

        for lr in param_space["learning_rate"]:
            for bs in param_space["batch_size"]:
                config = {"learning_rate": lr, "batch_size": bs, "epochs": 50}
                result = await self.train_model(model, train_data, val_data, config)

                if result["best_val_loss"] < best_score or best_score == 0:
                    best_score = result["best_val_loss"]
                    best_config = config

        return {"best_config": best_config, "best_score": best_score}

    async def close(self):
        for session in self.sessions.values():
            await session.close()


async def main():
    agent = TrainingOptimizationAgent()
    await agent.connect_servers()

    print("Training optimization agent initialized")

    await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
