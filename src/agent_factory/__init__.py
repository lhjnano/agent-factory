import os
from pathlib import Path

AGENT_DIR = Path(__file__).parent
HOME_DIR = Path("/var/lib/agent-factory")

def expand_config_paths(config):
    """JSON config에서 환경변수를 확장합니다."""
    import copy
    config = copy.deepcopy(config)
    
    def expand_value(obj):
        if isinstance(obj, str):
            expanded = os.path.expandvars(obj)
            expanded = expanded.replace("${AGENT_DIR}", str(AGENT_DIR))
            expanded = expanded.replace("${HOME}", str(HOME_DIR))
            return expanded
        elif isinstance(obj, list):
            return [expand_value(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: expand_value(v) for k, v in obj.items()}
        return obj
    
    return expand_value(config)

def __getattr__(name: str):
    """Lazy import to avoid mcp dependency errors during testing."""
    _lazy_imports = {
        "ProblemDefinitionAgent": ".problem_definition",
        "DataCollectionAgent": ".data_collection",
        "DesignDevelopmentAgent": ".design_development",
        "TrainingOptimizationAgent": ".training_optimization",
        "EvaluationValidationAgent": ".evaluation_validation",
        "DeploymentMonitoringAgent": ".deployment_monitoring",
        "AgentCoordinator": ".coordinator",
    }
    if name in _lazy_imports:
        import importlib
        module = importlib.import_module(_lazy_imports[name], __package__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

from .core import (
    Work, WorkStatus, WorkPriority, WorkResult, WorkQueue, WorkPlan, PlanStatus,
    RACI, RACIRole, RACIMatrix,
    DocumentationManager, DocumentTemplate, DocumentType, Document,
    AgentPool, AgentInstance, AgentStatus,
    TOCSupervisor, BottleneckAnalysis, BottleneckType, ThroughputMetrics,
    MultiAgentOrchestrator, WorkflowConfig, WorkflowResult
)

__all__ = [
    "ProblemDefinitionAgent",
    "DataCollectionAgent",
    "DesignDevelopmentAgent",
    "TrainingOptimizationAgent",
    "EvaluationValidationAgent",
    "DeploymentMonitoringAgent",
    "AgentCoordinator",
    "expand_config_paths",
    "AGENT_DIR",
    "HOME_DIR",
    "Work", "WorkStatus", "WorkPriority", "WorkResult", "WorkQueue", "WorkPlan", "PlanStatus",
    "RACI", "RACIRole", "RACIMatrix",
    "DocumentationManager", "DocumentTemplate", "DocumentType", "Document",
    "AgentPool", "AgentInstance", "AgentStatus",
    "TOCSupervisor", "BottleneckAnalysis", "BottleneckType", "ThroughputMetrics",
    "MultiAgentOrchestrator", "WorkflowConfig", "WorkflowResult",
]

__version__ = "1.0.0"
