import asyncio
import json
from pathlib import Path
from typing import Any, Dict
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from .core.token_optimizer import (
    compress_context,
    inject_output_format,
    build_execution_plan,
    prune_context,
    TokenSavingsTracker,
)

_AGENTS_CACHE = None  # 최초 1회만 import

def _import_agents():
    """agent 클래스들을 지연 import (캐시) - torch/numpy 등 미설치 패키지 있어도 서버 기동 가능"""
    global _AGENTS_CACHE
    if _AGENTS_CACHE is not None:
        return _AGENTS_CACHE
    from .problem_definition.agent import ProblemDefinitionAgent
    from .data_collection.agent import DataCollectionAgent
    from .design_development.agent import DesignDevelopmentAgent
    from .training_optimization.agent import TrainingOptimizationAgent
    from .evaluation_validation.agent import EvaluationValidationAgent
    from .deployment_monitoring.agent import DeploymentMonitoringAgent
    _AGENTS_CACHE = (ProblemDefinitionAgent, DataCollectionAgent, DesignDevelopmentAgent,
                     TrainingOptimizationAgent, EvaluationValidationAgent, DeploymentMonitoringAgent)
    return _AGENTS_CACHE

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
                        "items": {
                            "type": "string",
                            "enum": [
                                "problem_definition", "data_collection",
                                "design_development", "training_optimization",
                                "evaluation_validation", "deployment_monitoring",
                                "sw_analysis", "sw_design", "sw_implementation", "sw_validation",
                            ]
                        },
                        "description": (
                            "실행할 단계 직접 지정 (생략 시 work_type 기본값 사용). "
                            "ML: problem_definition/data_collection/design_development/"
                            "training_optimization/evaluation_validation/deployment_monitoring. "
                            "SW: sw_analysis/sw_design/sw_implementation/sw_validation. "
                            "sw_implementation: context의 files_to_write를 실제 파일로 저장/패치. "
                            "전체 쓰기: {path, content}. "
                            "패치(문자열 치환): {path, patches:[{old,new},...]} 또는 {path, patch:{old,new}}."
                        )
                    },
                    "context": {
                        "type": "object",
                        "description": "단계 간 공유할 초기 컨텍스트"
                    },
                    "output_format": {
                        "type": "string",
                        "description": "에이전트 출력 포맷 제약. brief(기본): 3줄 요약 / paths_only: 파일 경로만 / key_facts: 결정사항+경로만 / full: 제약 없음",
                        "enum": ["brief", "paths_only", "key_facts", "full"]
                    },
                    "stage_dependencies": {
                        "type": "object",
                        "description": "stage 의존성 맵 (지정 시 독립 stage 병렬 실행). 예: {\"design_development\": [\"problem_definition\"]}"
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
                output_format=arguments.get("output_format"),
                stage_dependencies=arguments.get("stage_dependencies"),
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
        "sw_analysis",
        "sw_design",
        "sw_implementation",
        "sw_validation",
    ],
    "test_generation": [
        "sw_analysis",
        "sw_design",
        "sw_validation",
    ],
    "data_analysis": [
        "problem_definition",
        "data_collection",
        "evaluation_validation",
    ],
    "code_review": [
        "sw_analysis",
        "sw_validation",
    ],
    "api_testing": [
        "sw_analysis",
        "sw_design",
        "sw_validation",
    ],
    "deployment": [
        "problem_definition",
        "deployment_monitoring",
    ],
    "ci_cd": [
        "sw_analysis",
        "sw_design",
        "sw_validation",
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


async def _run_stage(
    stage: str,
    ctx: Dict[str, Any],
    agents_tuple,
    output_format: str | None = None,
    tracker: TokenSavingsTracker | None = None,
) -> Dict[str, Any]:
    """단일 stage 실행 — 결과를 ctx에 누적해 다음 stage에 전달.

    output_format: "brief" | "paths_only" | "key_facts" | "full" | None(기본값 사용)
    """
    from .core.token_optimizer import inject_output_format, get_output_format_hint
    from .software_development import SoftwareDevelopmentAgent
    (ProblemDefinitionAgent, DataCollectionAgent, DesignDevelopmentAgent,
     TrainingOptimizationAgent, EvaluationValidationAgent, DeploymentMonitoringAgent) = agents_tuple

    # output_format 힌트를 user_request 에 주입
    user_request = inject_output_format(ctx.get("user_request", ""), stage, output_format)
    if tracker:
        fmt = output_format or "brief"
        tracker.record_format_hint(stage, fmt)

    if stage == "problem_definition":
        agent = ProblemDefinitionAgent()
        await agent.connect_servers()
        problem_def = await agent.define_problem(user_request)
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

    elif stage == "sw_analysis":
        agent = SoftwareDevelopmentAgent()
        await agent.connect_servers()
        analysis = await agent.analyze_requirements(user_request)
        await agent.close()
        ctx["sw_analysis"] = analysis
        return {"analysis": analysis}

    elif stage == "sw_design":
        agent = SoftwareDevelopmentAgent()
        await agent.connect_servers()
        design = await agent.design_software_architecture(ctx.get("sw_analysis", {}))
        await agent.close()
        ctx["sw_design"] = design
        return {"design": design}

    elif stage == "sw_implementation":
        from .core.token_optimizer import decompress_context
        agent = SoftwareDevelopmentAgent()
        await agent.connect_servers()
        # compress_context가 files_to_write를 파일 참조로 교체했을 수 있으므로 반드시 복원
        actual_ctx = decompress_context(ctx)
        files_to_write = actual_ctx.get("files_to_write", [])
        result = await agent.implement_code(files_to_write)
        await agent.close()
        ctx["sw_implementation"] = result
        return result

    elif stage == "sw_validation":
        agent = SoftwareDevelopmentAgent()
        await agent.connect_servers()
        validation = await agent.validate_design(
            ctx.get("sw_design", {}),
            ctx.get("sw_analysis", {}),
        )
        await agent.close()
        ctx["sw_validation"] = validation
        return {"validation": validation}

    else:
        supported = [
            "problem_definition", "data_collection", "design_development",
            "training_optimization", "evaluation_validation", "deployment_monitoring",
            "sw_analysis", "sw_design", "sw_validation",
        ]
        raise ValueError(
            f"Unsupported stage: '{stage}'. Supported stages: {supported}"
        )


async def _execute_workflow(
    user_request: str,
    work_type: str = None,
    stages: list = None,
    context: Dict[str, Any] = None,
    output_format: str | None = None,
    stage_dependencies: Dict[str, list] | None = None,
) -> Dict[str, Any]:
    """
    토큰 절감 전략 자동 적용:
      1. stage 간 ctx 압축 (임계치 초과 시 파일 참조로 교체)
      2. 각 stage에 output_format 힌트 주입
      3. 의존성 없는 독립 stage 병렬 실행
    """
    agents_tuple = _import_agents()
    tracker = TokenSavingsTracker()
    workflow_id = f"wf_{id(tracker)}"

    # work_type 결정
    detected_type = work_type or _detect_work_type(user_request)

    # 실행할 stage 결정
    pipeline_stages = stages or PIPELINE_REGISTRY.get(detected_type, PIPELINE_REGISTRY["software_development"])

    # 병렬 실행 계획 수립
    execution_plan = build_execution_plan(pipeline_stages, stage_dependencies)

    # 컨텍스트 초기화
    ctx: Dict[str, Any] = {"user_request": user_request}
    if context:
        ctx.update(context)

    workflow_result = {
        "request": user_request,
        "work_type": detected_type,
        "pipeline": pipeline_stages,
        "execution_plan": execution_plan,
        "phases": [],
        "context": {},
        "status": "in_progress",
        "token_savings": {},
    }

    failed = False
    for stage_group in execution_plan:
        # stage_group 실행 전에 ctx 압축
        ctx = compress_context(ctx, workflow_id=workflow_id)

        if len(stage_group) == 1:
            # 단일 stage — 순차 실행
            stage = stage_group[0]
            try:
                stage_result = await _run_stage(stage, ctx, agents_tuple, output_format, tracker)
                workflow_result["phases"].append({"stage": stage, "status": "completed", "result": stage_result})
            except Exception as e:
                workflow_result["phases"].append({"stage": stage, "status": "failed", "error": str(e)})
                workflow_result["status"] = "failed"
                workflow_result["error"] = f"stage '{stage}' failed: {e}"
                failed = True
                break
        else:
            # 독립 stage 그룹 — 병렬 실행
            # 각 stage는 동일한 ctx 스냅샷을 받고, 결과를 별도로 수집
            async def _run_one(s: str, ctx_snapshot: Dict[str, Any]) -> tuple[str, Any, Exception | None]:
                try:
                    r = await _run_stage(s, ctx_snapshot, agents_tuple, output_format, tracker)
                    return s, r, None
                except Exception as exc:
                    return s, None, exc

            ctx_snapshot = dict(ctx)
            results = await asyncio.gather(*[_run_one(s, ctx_snapshot) for s in stage_group])

            group_failed = False
            for s, r, err in results:
                if err:
                    workflow_result["phases"].append({"stage": s, "status": "failed", "error": str(err)})
                    workflow_result["status"] = "failed"
                    workflow_result["error"] = f"stage '{s}' failed: {err}"
                    group_failed = True
                else:
                    workflow_result["phases"].append({"stage": s, "status": "completed", "result": r})
                    # 병렬 결과를 ctx에 병합
                    for k, v in ctx_snapshot.items():
                        if k not in ctx:
                            ctx[k] = v

            if group_failed:
                failed = True
                break

    if not failed:
        workflow_result["status"] = "completed"

    # 최종 컨텍스트 (파일 참조는 경로만 포함)
    workflow_result["context"] = {
        k: (v["_file"] if isinstance(v, dict) and "_file" in v else v)
        for k, v in ctx.items()
        if k != "user_request"
    }
    workflow_result["token_savings"] = tracker.summary()

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
