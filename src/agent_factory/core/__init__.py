from .work import Work, WorkStatus, WorkPriority, WorkResult, WorkQueue, WorkPlan, PlanStatus
from .raci import RACI, RACIRole, RACIMatrix
from .documentation import DocumentationManager, DocumentTemplate, DocumentType, Document
from .agent_pool import AgentPool, AgentInstance, AgentStatus
from .toc_supervisor import TOCSupervisor, BottleneckAnalysis, BottleneckType, ThroughputMetrics
from .orchestrator import MultiAgentOrchestrator, WorkflowConfig, WorkflowResult
from .context import WorkContext, WorkflowContext
from .context_manager import ContextManager
from .skill_manager import SkillManager
from .skill_analyzer import SkillAnalyzer, SkillCategory, SkillRecommendation

__all__ = [
    "Work", "WorkStatus", "WorkPriority", "WorkResult", "WorkQueue", "WorkPlan", "PlanStatus",
    "RACI", "RACIRole", "RACIMatrix",
    "DocumentationManager", "DocumentTemplate", "DocumentType", "Document",
    "AgentPool", "AgentInstance", "AgentStatus",
    "TOCSupervisor", "BottleneckAnalysis", "BottleneckType", "ThroughputMetrics",
    "MultiAgentOrchestrator", "WorkflowConfig", "WorkflowResult",
    "WorkContext", "WorkflowContext", "ContextManager",
    "SkillManager", "SkillAnalyzer", "SkillCategory", "SkillRecommendation",
]

# Work-Agent 통계 기능 추가
TOCSupervisor.get_work_agent_statistics.__doc__ = """
    Work별 Agent 작업 통계를 반환합니다.

    Args:
        work_id: 특정 Work의 ID (None인 경우 전체 통계 반환)

    Returns:
        Dict[str, Any]: 통계 데이터
    """

TOCSupervisor.format_work_agent_report.__doc__ = """
    Work-Agent 통계 보고서를 형식화된 문자열로 반환합니다.

    Args:
        work_id: 특정 Work의 ID (None인 경우 전체 보고서)

    Returns:
        str: 형식화된 보고서
    """
