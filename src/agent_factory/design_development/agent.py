import asyncio
import json
from pathlib import Path
from typing import Any, Dict
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from .. import expand_config_paths, AGENT_DIR, HOME_DIR


class DesignDevelopmentAgent:
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}

    async def connect_servers(self):
        config_path = AGENT_DIR / "design_development" / "mcp_config.json"
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

    async def design_architecture(self, problem_def: Dict) -> Dict[str, Any]:
        architecture = {
            "model_type": "neural_network",
            "input_features": problem_def.get("input_features", []),
            "output_size": problem_def.get("output_size", 1),
            "hidden_layers": [
                {"size": 128, "activation": "relu", "dropout": 0.2},
                {"size": 64, "activation": "relu", "dropout": 0.3},
                {"size": 32, "activation": "relu", "dropout": 0.4}
            ],
            "optimizer": "adam",
            "learning_rate": 0.001
        }

        return architecture

    async def generate_code(self, architecture: Dict) -> str:
        code_template = """
import torch
import torch.nn as nn

class {model_name}(nn.Module):
    def __init__(self, input_size):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_size, {first_layer_size}),
            nn.ReLU(),
            nn.Dropout({first_dropout}),
            nn.Linear({first_layer_size}, {second_layer_size}),
            nn.ReLU(),
            nn.Dropout({second_dropout}),
            nn.Linear({second_layer_size}, {third_layer_size}),
            nn.ReLU(),
            nn.Dropout({third_dropout}),
            nn.Linear({third_layer_size}, {output_size})
        )

    def forward(self, x):
        return self.layers(x)
        """.format(
            model_name="CustomModel",
            first_layer_size=architecture["hidden_layers"][0]["size"],
            first_dropout=architecture["hidden_layers"][0]["dropout"],
            second_layer_size=architecture["hidden_layers"][1]["size"],
            second_dropout=architecture["hidden_layers"][1]["dropout"],
            third_layer_size=architecture["hidden_layers"][2]["size"],
            third_dropout=architecture["hidden_layers"][2]["dropout"],
            output_size=architecture["output_size"]
        )

        filesystem_session = self.sessions.get("filesystem")
        if filesystem_session:
            await filesystem_session.call_tool(
                "write_file",
                arguments={
                    "path": str(HOME_DIR / "src" / "model.py"),
                    "content": code_template.strip()
                }
            )

        return code_template

    async def create_training_script(self, architecture: Dict) -> str:
        script = """
import torch
from torch.utils.data import DataLoader
from model import CustomModel

def train_model(model, train_loader, val_loader, epochs=100):
    optimizer = torch.optim.{optimizer}(model.parameters(), lr={learning_rate})
    criterion = nn.{loss_fn}()

    for epoch in range(epochs):
        model.train()
        for batch in train_loader:
            optimizer.zero_grad()
            outputs = model(batch[0])
            loss = criterion(outputs, batch[1])
            loss.backward()
            optimizer.step()

    return model
        """.format(
            optimizer=architecture["optimizer"],
            learning_rate=architecture["learning_rate"],
            loss_fn="BCEWithLogitsLoss" if architecture["output_size"] == 1 else "CrossEntropyLoss"
        )

        filesystem_session = self.sessions.get("filesystem")
        if filesystem_session:
            await filesystem_session.call_tool(
                "write_file",
                arguments={
                    "path": str(HOME_DIR / "src" / "train.py"),
                    "content": script.strip()
                }
            )

        return script

    async def commit_changes(self, message: str):
        git_session = self.sessions.get("git")
        if git_session:
            await git_session.call_tool(
                "git_commit",
                arguments={"message": message}
            )

    async def close(self):
        for session in self.sessions.values():
            await session.close()


async def main():
    agent = DesignDevelopmentAgent()
    await agent.connect_servers()

    problem = {"input_features": 10, "output_size": 1}
    architecture = await agent.design_architecture(problem)
    model_code = await agent.generate_code(architecture)
    train_code = await agent.create_training_script(architecture)

    await agent.commit_changes("Add model architecture and training script")

    print("Architecture:", json.dumps(architecture, indent=2, ensure_ascii=False))

    await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
