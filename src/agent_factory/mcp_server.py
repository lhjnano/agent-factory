import asyncio
import json
from pathlib import Path
from typing import Any, Dict
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from pathlib import Path

def _import_agents():
    """agent 클래스들을 지연 import - torch/numpy 등 미설치 패키지 있어도 서버 기동 가능"""
    from .problem_definition.agent import ProblemDefinitionAgent
    from .data_collection.agent import DataCollectionAgent
    from .design_development.agent import DesignDevelopmentAgent
    from .training_optimization.agent import TrainingOptimizationAgent
    from .evaluation_validation.agent import EvaluationValidationAgent
    from .deployment_monitoring.agent import DeploymentMonitoringAgent
    return (ProblemDefinitionAgent, DataCollectionAgent, DesignDevelopmentAgent,
            TrainingOptimizationAgent, EvaluationValidationAgent, DeploymentMonitoringAgent)

from .core.skill_manager import SkillManager
from .core.skill_analyzer import SkillAnalyzer

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
            description=(
                "Execute a multi-agent workflow. work_type을 지정하거나 생략하면 자동 감지. "
                "지원 타입: ml_development, software_development, test_generation, "
                "data_analysis, code_review, api_testing, deployment, ci_cd"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_request": {
                        "type": "string",
                        "description": "작업 설명 또는 요구사항"
                    },
                    "work_type": {
                        "type": "string",
                        "description": "파이프라인 유형 (생략 시 자동 감지)",
                        "enum": [
                            "ml_development", "software_development",
                            "test_generation", "data_analysis",
                            "code_review", "api_testing",
                            "deployment", "ci_cd"
                        ]
                    },
                    "stages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "실행할 단계 직접 지정 (생략 시 work_type 기본값 사용)"
                    },
                    "context": {
                        "type": "object",
                        "description": "단계 간 공유할 초기 컨텍스트"
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
        (ProblemDefinitionAgent, DataCollectionAgent, DesignDevelopmentAgent,
         TrainingOptimizationAgent, EvaluationValidationAgent, DeploymentMonitoringAgent) = _import_agents()

        if name == "execute_workflow":
            result = await _execute_workflow(
                user_request=arguments.get("user_request", ""),
                work_type=arguments.get("work_type"),
                stages=arguments.get("stages"),
                context=arguments.get("context", {}),
            )
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
            agent = DataCollectionAgent()
            await agent.connect_servers()
            import pandas as pd
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

        elif name == "assign_skills_to_work":
            skill_manager = SkillManager(repo_root=Path.cwd())
            result = skill_manager.assign_skills_to_work(
                work_id=arguments.get("work_id", ""),
                consultant_agent_id=arguments.get("consultant_agent_id")
            ) if hasattr(skill_manager, "assign_skills_to_work") else {"status": "not_supported"}
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "get_work_skills":
            skill_manager = SkillManager(repo_root=Path.cwd())
            result = skill_manager.get_work_skills(
                work_id=arguments.get("work_id", "")
            ) if hasattr(skill_manager, "get_work_skills") else {"status": "not_supported"}
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

# ---------------------------------------------------------------------------
# 파이프라인 레지스트리
# 각 work_type별 실행할 stage 순서 정의
# ---------------------------------------------------------------------------
PIPELINE_REGISTRY: Dict[str, list] = {
    "ml_development": [
        "problem_definition",
        "data_collection",
        "design_development",
        "training_optimization",
        "evaluation_validation",
        "deployment_monitoring",
    ],
    "software_development": [
        "problem_definition",
        "design_development",
        "evaluation_validation",
    ],
    "test_generation": [
        "problem_definition",
        "design_development",
        "evaluation_validation",
    ],
    "data_analysis": [
        "problem_definition",
        "data_collection",
        "evaluation_validation",
    ],
    "code_review": [
        "problem_definition",
        "evaluation_validation",
    ],
    "api_testing": [
        "problem_definition",
        "design_development",
        "evaluation_validation",
        "deployment_monitoring",
    ],
    "deployment": [
        "problem_definition",
        "deployment_monitoring",
    ],
    "ci_cd": [
        "problem_definition",
        "design_development",
        "evaluation_validation",
        "deployment_monitoring",
    ],
}

# work_type 자동 감지용 키워드 맵
_WORK_TYPE_KEYWORDS: Dict[str, list] = {
    # 구체적인 것 먼저 — 순서가 우선순위
    "ml_development":       ["train", "model", "ml ", "machine learning", "학습", "모델", "신경망", "neural"],
    "api_testing":          ["api 테스트", "api test", "rest api", "api", "endpoint", "엔드포인트"],
    "ci_cd":                ["ci/cd", "ci cd", "pipeline", "파이프라인", "jenkins", "gitlab-ci", "gitlab ci", "gitlab"],
    "deployment":           ["deploy", "배포", "release", "릴리스", "rollout"],
    "code_review":          ["review", "검토", "코드리뷰", "refactor", "리팩"],
    "data_analysis":        ["data analys", "데이터 분석", "statistics", "통계"],
    "test_generation":      ["test", "테스트", "spec", "coverage", "커버리지", "assert"],
    "data_analysis":        ["data", "데이터", "analys", "분석"],
    "software_development": [],   # fallback
}

def _detect_work_type(user_request: str) -> str:
    lower = user_request.lower()
    for wtype, keywords in _WORK_TYPE_KEYWORDS.items():
        if keywords and any(kw in lower for kw in keywords):
            return wtype
    return "software_development"


async def _run_stage(stage: str, ctx: Dict[str, Any], agents_tuple) -> Dict[str, Any]:
    """단일 stage 실행 — 결과를 ctx에 누적해 다음 stage에 전달"""
    (ProblemDefinitionAgent, DataCollectionAgent, DesignDevelopmentAgent,
     TrainingOptimizationAgent, EvaluationValidationAgent, DeploymentMonitoringAgent) = agents_tuple

    if stage == "problem_definition":
        agent = ProblemDefinitionAgent()
        await agent.connect_servers()
        problem_def = await agent.define_problem(ctx.get("user_request", ""))
        plan = await agent.create_project_plan(problem_def)
        await agent.close()
        ctx["problem_def"] = problem_def
        ctx["plan"] = plan
        return {"problem_def": problem_def, "plan": plan}

    elif stage == "data_collection":
        agent = DataCollectionAgent()
        await agent.connect_servers()
        sources = ctx.get("sources", [])
        data = await agent.collect_data(sources)
        stats = await agent.preprocess_data(data)
        await agent.close()
        ctx["data_stats"] = stats
        return {"stats": stats}

    elif stage == "design_development":
        agent = DesignDevelopmentAgent()
        await agent.connect_servers()
        architecture = await agent.design_architecture(ctx.get("problem_def", {}))
        code = await agent.generate_code(architecture)
        await agent.close()
        ctx["architecture"] = architecture
        ctx["code"] = code
        return {"architecture": architecture}

    elif stage == "training_optimization":
        agent = TrainingOptimizationAgent()
        await agent.connect_servers()
        config = {
            "epochs": ctx.get("epochs", 100),
            "learning_rate": ctx.get("learning_rate", 0.001),
            "batch_size": ctx.get("batch_size", 32),
        }
        result = {"status": "process_configured", "config": config}
        await agent.close()
        ctx["training_config"] = config
        return result

    elif stage == "evaluation_validation":
        agent = EvaluationValidationAgent()
        await agent.connect_servers()
        metrics = await agent.evaluate_model(None, None)
        report = await agent.generate_report(metrics)
        await agent.close()
        ctx["metrics"] = metrics
        return {"metrics": metrics, "report": report}

    elif stage == "deployment_monitoring":
        agent = DeploymentMonitoringAgent()
        await agent.connect_servers()
        result = await agent.deploy_model(
            ctx.get("artifact_path", ""),
            ctx.get("deploy_config", {})
        )
        await agent.close()
        ctx["deployment"] = result
        return result

    else:
        return {"skipped": f"unknown stage: {stage}"}


async def _execute_workflow(
    user_request: str,
    work_type: str = None,
    stages: list = None,
    context: Dict[str, Any] = None,
) -> Dict[str, Any]:
    agents_tuple = _import_agents()

    # work_type 결정
    detected_type = work_type or _detect_work_type(user_request)

    # 실행할 stage 결정
    pipeline_stages = stages or PIPELINE_REGISTRY.get(detected_type, PIPELINE_REGISTRY["software_development"])

    # 컨텍스트 초기화 (이전 단계 출력 → 다음 단계 입력)
    ctx: Dict[str, Any] = {"user_request": user_request}
    if context:
        ctx.update(context)

    workflow_result = {
        "request": user_request,
        "work_type": detected_type,
        "pipeline": pipeline_stages,
        "phases": [],
        "context": {},
        "status": "in_progress",
    }

    for stage in pipeline_stages:
        try:
            stage_result = await _run_stage(stage, ctx, agents_tuple)
            workflow_result["phases"].append({
                "stage": stage,
                "status": "completed",
                "result": stage_result,
            })
        except Exception as e:
            workflow_result["phases"].append({
                "stage": stage,
                "status": "failed",
                "error": str(e),
            })
            workflow_result["status"] = "failed"
            workflow_result["error"] = f"stage '{stage}' failed: {e}"
            break

    if workflow_result["status"] != "failed":
        workflow_result["status"] = "completed"

    # 최종 컨텍스트 (단계 간 전달된 데이터) 포함
    workflow_result["context"] = {k: v for k, v in ctx.items() if k != "user_request"}

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
