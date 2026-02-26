import asyncio
import json
from pathlib import Path
from typing import Any, Dict
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from .problem_definition.agent import ProblemDefinitionAgent
from .data_collection.agent import DataCollectionAgent
from .design_development.agent import DesignDevelopmentAgent
from .training_optimization.agent import TrainingOptimizationAgent
from .evaluation_validation.agent import EvaluationValidationAgent
from .deployment_monitoring.agent import DeploymentMonitoringAgent
from .core.skill_manager import SkillManager
from .core.skill_analyzer import SkillAnalyzer
from pathlib import Path

AGENT_DIR = Path(__file__).parent
HOME_DIR = Path("/var/lib/agent-factory")

app = Server("multi-agent-development-system")

@app.list_resources()
async def list_resources():
    return [
        {
            "uri": f"file://{AGENT_DIR}/workflows",
            "name": "Agent Workflows",
            "description": "Stored workflow executions and results",
            "mimeType": "application/json"
        }
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    if uri.startswith(f"file://{AGENT_DIR}/workflows"):
        path = uri.replace("file://", "")
        if Path(path).exists():
            with open(path) as f:
                return f.read()
    raise FileNotFoundError(f"Resource not found: {uri}")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="execute_workflow",
            description="Execute complete development workflow from problem definition to deployment",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_request": {
                        "type": "string",
                        "description": "User's problem statement or requirements"
                    }
                },
                "required": ["user_request"]
            }
        ),
        Tool(
            name="define_problem",
            description="Define problem scope and create project plan with phases and timeline",
            inputSchema={
                "type": "object",
                "properties": {
                    "requirements": {
                        "type": "string",
                        "description": "Project requirements and objectives"
                    }
                },
                "required": ["requirements"]
            }
        ),
        Tool(
            name="define_problem",
            description="Define the ML problem and create project plan",
            inputSchema={
                "type": "object",
                "properties": {
                    "requirements": {
                        "type": "string",
                        "description": "Project requirements and objectives"
                    }
                },
                "required": ["requirements"]
            }
        ),
        Tool(
            name="collect_data",
            description="Collect data from various sources",
            inputSchema={
                "type": "object",
                "properties": {
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of data sources (file paths or URLs)"
                    }
                },
                "required": ["sources"]
            }
        ),
        Tool(
            name="preprocess_data",
            description="Preprocess collected data",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_path": {
                        "type": "string",
                        "description": "Path to the raw data file"
                    }
                },
                "required": ["data_path"]
            }
        ),
        Tool(
            name="design_architecture",
            description="Design system architecture based on problem definition",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem_def": {
                        "type": "object",
                        "description": "Problem definition with input/output specifications"
                    }
                },
                "required": ["problem_def"]
            }
        ),
        Tool(
            name="generate_implementation",
            description="Generate code implementation including core logic and scripts",
            inputSchema={
                "type": "object",
                "properties": {
                    "architecture": {
                        "type": "object",
                        "description": "System architecture configuration"
                    }
                },
                "required": ["architecture"]
            }
        ),
        Tool(
            name="optimize_process",
            description="Run process with configuration and optimization",
            inputSchema={
                "type": "object",
                "properties": {
                    "config": {
                        "type": "object",
                        "description": "Process configuration (epochs, iterations, parameters)"
                    }
                },
                "required": ["config"]
            }
        ),
        Tool(
            name="evaluate_results",
            description="Evaluate performance and generate detailed report",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_path": {
                        "type": "string",
                        "description": "Path to process output or results"
                    },
                    "test_data_path": {
                        "type": "string",
                        "description": "Path to test data (if applicable)"
                    }
                },
                "required": ["output_path"]
            }
        ),
        Tool(
            name="deploy_system",
            description="Deploy system to production environment",
            inputSchema={
                "type": "object",
                "properties": {
                    "artifact_path": {
                        "type": "string",
                        "description": "Path to deployable artifact or file"
                    },
                    "config": {
                        "type": "object",
                        "description": "Deployment configuration (version, environment, endpoint)"
                    }
                },
                "required": ["artifact_path"]
            }
        ),
        Tool(
            name="monitor_system",
            description="Monitor deployed system performance and metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "version": {
                        "type": "string",
                        "description": "System version to monitor"
                    }
                },
                "required": ["version"]
            }
        ),
        Tool(
            name="assign_skills_to_work",
            description="Analyze work and dynamically assign appropriate skills based on RACI roles",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_id": {
                        "type": "string",
                        "description": "Work ID to assign skills to"
                    },
                    "consultant_agent_id": {
                        "type": "string",
                        "description": "Agent ID of the consultant making the assignment (optional)"
                    }
                },
                "required": ["work_id"]
            }
        ),
        Tool(
            name="get_work_skills",
            description="Get skill assignments and content for a specific work",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_id": {
                        "type": "string",
                        "description": "Work ID to get skills for"
                    }
                },
                "required": ["work_id"]
            }
        ),
        Tool(
            name="get_skill_effectiveness",
            description="Get skill effectiveness metrics for all skills or a specific skill",
            inputSchema={
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": "Specific skill name (optional, returns all if not provided)"
                    }
                }
            }
        ),
        Tool(
            name="analyze_work_for_skills",
            description="Analyze a work and recommend appropriate skills",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_name": {
                        "type": "string",
                        "description": "Name of the work"
                    },
                    "work_description": {
                        "type": "string",
                        "description": "Detailed description of the work"
                    },
                    "work_type": {
                        "type": "string",
                        "description": "Type of work (e.g., problem_definition, data_collection)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tags associated with the work"
                    }
                },
                "required": ["work_name", "work_description", "work_type"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent | ImageContent | EmbeddedResource]:
    try:
        if name == "execute_workflow":
            result = await _execute_workflow(arguments.get("user_request", ""))
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "define_problem":
            agent = ProblemDefinitionAgent()
            await agent.connect_servers()
            problem_def = await agent.define_problem(arguments.get("requirements", ""))
            plan = await agent.create_project_plan(problem_def)
            await agent.close()
            result = {"problem_definition": problem_def, "project_plan": plan}
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "collect_data":
            agent = DataCollectionAgent()
            await agent.connect_servers()
            data = await agent.collect_data(arguments.get("sources", []))
            stats = await agent.preprocess_data(data)
            await agent.close()
            return [TextContent(type="text", text=json.dumps(stats, indent=2, ensure_ascii=False))]
        
        elif name == "preprocess_data":
            import pandas as pd
            agent = DataCollectionAgent()
            await agent.connect_servers()
            df = pd.read_csv(arguments.get("data_path", ""))
            result = await agent.preprocess_data(df)
            quality = await agent.validate_data_quality(df)
            await agent.close()
            result["quality_report"] = quality
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "design_architecture":
            agent = DesignDevelopmentAgent()
            await agent.connect_servers()
            result = await agent.design_architecture(arguments.get("problem_def", {}))
            await agent.close()
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "generate_implementation":
            agent = DesignDevelopmentAgent()
            await agent.connect_servers()
            code = await agent.generate_code(arguments.get("architecture", {}))
            train_script = await agent.create_training_script(arguments.get("architecture", {}))
            await agent.close()
            result = {"implementation_code": code, "script": train_script}
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "optimize_process":
            agent = TrainingOptimizationAgent()
            await agent.connect_servers()
            config = arguments.get("config", {})
            config.setdefault("epochs", 100)
            config.setdefault("learning_rate", 0.001)
            config.setdefault("batch_size", 32)
            result = {"status": "process_configured", "config": config}
            await agent.close()
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "evaluate_results":
            agent = EvaluationValidationAgent()
            await agent.connect_servers()
            metrics = await agent.evaluate_model(None, None)
            report = await agent.generate_report(metrics)
            await agent.close()
            result = {"metrics": metrics, "report": report}
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "deploy_system":
            agent = DeploymentMonitoringAgent()
            await agent.connect_servers()
            result = await agent.deploy_model(
                arguments.get("artifact_path", ""),
                arguments.get("config", {})
            )
            await agent.close()
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "monitor_system":
            agent = DeploymentMonitoringAgent()
            await agent.connect_servers()
            result = await agent.monitor_performance(arguments.get("version", "1.0.0"))
            await agent.close()
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "analyze_work_for_skills":
            skill_analyzer = SkillAnalyzer()
            recommendations = await skill_analyzer.analyze_work(
                work_name=arguments.get("work_name", ""),
                work_description=arguments.get("work_description", ""),
                work_type=arguments.get("work_type", ""),
                tags=arguments.get("tags", []),
                inputs={}
            )
            result = {
                "recommendations": [
                    {
                        "skill_name": rec.skill_name,
                        "confidence": rec.confidence,
                        "reason": rec.reason,
                        "category": rec.category.value
                    }
                    for rec in recommendations
                ]
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "get_skill_effectiveness":
            skill_manager = SkillManager(repo_root=Path.cwd())
            skill_name = arguments.get("skill_name")

            if skill_name:
                result = skill_manager.get_skill_effectiveness(skill_name)
                if not result:
                    result = {"error": f"Skill '{skill_name}' not found or has no metrics"}
            else:
                result = skill_manager.get_all_skill_effectiveness()
                recommendations = skill_manager.get_skill_recommendations()
                result_dict = {"skill_effectiveness": result, "recommendations": recommendations}
                result = result_dict

            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]

async def _execute_workflow(user_request: str) -> Dict[str, Any]:
    workflow_result = {
        "request": user_request,
        "phases": [],
        "status": "in_progress"
    }

    try:
        phase1 = ProblemDefinitionAgent()
        await phase1.connect_servers()
        problem_def = await phase1.define_problem(user_request)
        plan = await phase1.create_project_plan(problem_def)
        await phase1.close()
        workflow_result["phases"].append({"phase": "problem_definition", "status": "completed", "result": {"problem_def": problem_def, "plan": plan}})

        phase2 = DesignDevelopmentAgent()
        await phase2.connect_servers()
        architecture = await phase2.design_architecture(problem_def)
        code = await phase2.generate_code(architecture)
        train_script = await phase2.create_training_script(architecture)
        await phase2.close()
        workflow_result["phases"].append({"phase": "design_development", "status": "completed", "result": {"architecture": architecture}})

        workflow_result["status"] = "completed"
    except Exception as e:
        workflow_result["status"] = "failed"
        workflow_result["error"] = str(e)

    return workflow_result

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
