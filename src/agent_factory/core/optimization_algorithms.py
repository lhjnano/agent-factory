"""
TOC Supervisor Token Optimization Algorithms

알고리즘 정의서:
- Token Optimization Strategy
- Agent Scaling Policy
- Dynamic Allocation Rules
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


class TokenOptimizationStrategy(Enum):
    """토큰 최적화 전략"""
    CONSERVATIVE = "conservative"  # 보수적: 안정성 우선
    BALANCED = "balanced"  # 균형: 효율과 안정성 균형
    AGGRESSIVE = "aggressive"  # 공격적: 최대 효율 우선


class ScalingTrigger(Enum):
    """스케일링 트리거 조건"""
    UTILIZATION_THRESHOLD = "utilization_threshold"
    QUEUE_BACKLOG = "queue_backlog"
    SLA_VIOLATION = "sla_violation"
    TOKEN_EFFICIENCY = "token_efficiency"


@dataclass
class TokenOptimizationRule:
    """토큰 최적화 규칙"""
    name: str
    description: str
    work_types: List[str]
    target_efficiency: float
    max_tokens_per_work: int
    actions: List[str]


@dataclass
class ScalingPolicy:
    """스케일링 정책"""
    agent_type: str
    scale_up_threshold: float
    scale_down_threshold: float
    min_instances: int
    max_instances: int
    cooldown_seconds: int
    auto_scale: bool


@dataclass
class OptimizationRecommendation:
    """최적화 권장사항"""
    work_id: str
    agent_id: str
    action_type: str  # "token_optimization", "scale_up", "scale_down", "skill_refinement"
    priority: int  # 1-5, 1이 최우선
    description: str
    expected_benefit: str
    estimated_token_savings: int = 0
    implementation_effort: str = "low"  # low, medium, high


class TokenOptimizer:
    """
    토큰 최적화 엔진
    
    기능:
    1. Work별 토큰 사용 패턴 분석
    2. 효율 낮은 Work 타입 식별
    3. 프롬프트 최적화 권장
    4. Context 재사용 전략 제안
    """

    def __init__(self, strategy: TokenOptimizationStrategy = TokenOptimizationStrategy.BALANCED):
        self.strategy = strategy
        self._rules = self._initialize_rules()
        self._work_history: Dict[str, List[Dict[str, Any]]] = {}
        self._optimization_log: List[Dict[str, Any]] = []

    def _initialize_rules(self) -> Dict[str, TokenOptimizationRule]:
        """최적화 규칙 초기화"""
        return {
            "problem_definition": TokenOptimizationRule(
                name="문제 정의 최적화",
                description="명확하고 간결한 요구사항 정의",
                work_types=["problem_definition"],
                target_efficiency=0.85,
                max_tokens_per_work=2000,
                actions=[
                    "불필요한 설명 제거",
                    "구체적인 KPI 사용",
                    "템플릿 재사용"
                ]
            ),
            "data_collection": TokenOptimizationRule(
                name="데이터 수집 최적화",
                description="효율적인 데이터 수집 및 전처리",
                work_types=["data_collection"],
                target_efficiency=0.75,
                max_tokens_per_work=3000,
                actions=[
                    "데이터 샘플링 사용",
                    "단계별 전처리",
                    "캐싱 활용"
                ]
            ),
            "design_development": TokenOptimizationRule(
                name="설계 개발 최적화",
                description="간결한 설계와 효율적인 코드 생성",
                work_types=["design_development"],
                target_efficiency=0.75,
                max_tokens_per_work=2500,
                actions=[
                    "MVP부터 시작",
                    "코드 템플릿 사용",
                    "불필요한 주석 제거",
                    "컴포넌트 재사용"
                ]
            ),
            "training_optimization": TokenOptimizationRule(
                name="학습 최적화",
                description="효율적인 모델 학습",
                work_types=["training_optimization"],
                target_efficiency=0.70,
                max_tokens_per_work=6000,
                actions=[
                    "early stopping",
                    "하이퍼파라미터 공간 축소",
                    "검증 빈도 조정",
                    "체크포인트 최적화"
                ]
            ),
            "evaluation_validation": TokenOptimizationRule(
                name="평가 검증 최적화",
                description="필요한 평가만 수행",
                work_types=["evaluation_validation"],
                target_efficiency=0.80,
                max_tokens_per_work=2000,
                actions=[
                    "핵심 메트릭 집중",
                    "중복 테스트 제거",
                    "자동화된 보고서"
                ]
            ),
            "deployment_monitoring": TokenOptimizationRule(
                name="배포 모니터링 최적화",
                description="간결한 배포와 효율적 모니터링",
                work_types=["deployment_monitoring"],
                target_efficiency=0.75,
                max_tokens_per_work=3000,
                actions=[
                    "IaC 사용",
                    "CD 파이프라인 재사용",
                    "알림 규칙 간소화"
                ]
            )
        }

    def analyze_work_token_efficiency(self, work_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        단일 Work의 토큰 효율 분석
        
        Returns:
            {
                "work_id": str,
                "work_type": str,
                "estimated_tokens": int,
                "actual_tokens": int,
                "efficiency": float,
                "status": "efficient" | "inefficient" | "critical",
                "recommendations": List[str]
            }
        """
        estimated = work_data.get("estimated_tokens", 1000)
        actual = work_data.get("actual_tokens", 0)
        work_type = work_data.get("work_type", "")

        efficiency = (estimated / actual * 100) if actual > 0 else 100

        # 규칙 기반 상태 결정
        rule = self._rules.get(work_type)
        if not rule:
            target_eff = 0.75
            max_tokens = 4000
        else:
            target_eff = rule.target_efficiency
            max_tokens = rule.max_tokens_per_work

        if efficiency < target_eff * 0.5:
            status = "critical"
        elif efficiency < target_eff:
            status = "inefficient"
        else:
            status = "efficient"

        # 권장사항 생성
        recommendations = []

        if status in ["inefficient", "critical"]:
            if rule:
                recommendations.extend(rule.actions)

            # 추가 권장사항
            if actual > max_tokens:
                recommendations.append(f"토큰 사용량이 상한({max_tokens:,}) 초과")

            # Context 관련 권장사항
            if efficiency < 50:
                recommendations.append("Context 재사용 고려")
                recommendations.append("프롬프트 간소화")

        return {
            "work_id": work_data.get("work_id"),
            "work_type": work_type,
            "estimated_tokens": estimated,
            "actual_tokens": actual,
            "efficiency": efficiency,
            "status": status,
            "rule_target": target_eff,
            "max_allowed": max_tokens,
            "recommendations": recommendations,
            "token_waste": max(0, actual - estimated)
        }

    def generate_prompt_optimization(self, work_type: str) -> Dict[str, Any]:
        """
        프롬프트 최적화 권장사항 생성
        
        Returns:
            {
                "work_type": str,
                "prompt_optimizations": List[str],
                "context_savings": List[str],
                "expected_token_reduction": int
            }
        """
        optimizations = {
            "problem_definition": {
                "prompt_optimizations": [
                    "불필요한 배경 정보 제거",
                    "구체적인 질문 사용",
                    "단계별 안내 제공"
                ],
                "context_savings": [
                    "이전 work의 결과 요약만 사용",
                    "공통 가이드라인 템플릿화"
                ],
                "expected_token_reduction": 30  # %
            },
            "data_collection": {
                "prompt_optimizations": [
                    "데이터 샘플 크기 명시",
                    "처리 단계 명확화",
                    "필요한 필드만 요청"
                ],
                "context_savings": [
                    "데이터 스키마만 context에 포함",
                    "이미 처리된 결과 재사용"
                ],
                "expected_token_reduction": 40
            },
            "design_development": {
                "prompt_optimizations": [
                    "기존 코드 먼저 검토",
                    "변경 범위 명시",
                    "템플릿 패턴 사용"
                ],
                "context_savings": [
                    "관련 코드 파일만 포함",
                    "이전 설계 문서 요약",
                    "API 문서 링크로 대체"
                ],
                "expected_token_reduction": 35
            },
            "training_optimization": {
                "prompt_optimizations": [
                    "하이퍼파라미터 제한",
                    "데이터셋 크기 지정",
                    "early stopping 조건"
                ],
                "context_savings": [
                    "모델 아키텍처 요약",
                    "이전 체크포인트 정보",
                    "훈련 로그 필요 부분만"
                ],
                "expected_token_reduction": 25
            },
            "evaluation_validation": {
                "prompt_optimizations": [
                    "평가 메트릭 명시",
                    "테스트 케이스 예시 제공",
                    "보고서 템플릿 사용"
                ],
                "context_savings": [
                    "모델 결과 요약",
                    "평가 기준만 포함",
                    "테스트 데이터 경로로 대체"
                ],
                "expected_token_reduction": 45
            },
            "deployment_monitoring": {
                "prompt_optimizations": [
                    "배포 단계 명시",
                    "모니터링 지표 제한",
                    "롤백 절차 간소화"
                ],
                "context_savings": [
                    "IaC 템플릿 사용",
                    "배포 기록 요약",
                    "구성 변수 파일로 대체"
                ],
                "expected_token_reduction": 30
            }
        }

        return optimizations.get(work_type, {})

    def get_token_budget_recommendation(self, total_budget: int, usage_history: List[int]) -> Dict[str, Any]:
        """
        토큰 예산 권장사항 생성
        
        Args:
            total_budget: 총 토큰 예산
            usage_history: 최근 사용량 기록 (token per day)
        
        Returns:
            {
                "current_budget": int,
                "recommended_allocation": Dict[str, int],
                "daily_usage_trend": str,
                "warning_threshold": float,
                "projected_usage": int
            }
        """
        if not usage_history:
            return {
                "current_budget": total_budget,
                "recommended_allocation": {},
                "daily_usage_trend": "unknown",
                "warning_threshold": 0.8,
                "projected_usage": 0
            }

        # 사용량 추세 분석
        avg_daily = sum(usage_history) / len(usage_history)
        trend = "stable"
        if len(usage_history) >= 3:
            recent = sum(usage_history[-3:]) / 3
            older = sum(usage_history[:-3]) / len(usage_history[:-3]) if len(usage_history) > 3 else avg_daily
            if recent > older * 1.1:
                trend = "increasing"
            elif recent < older * 0.9:
                trend = "decreasing"

        # Work 타입별 할당 권장 (예시)
        recommended_allocation = {
            "problem_definition": int(total_budget * 0.15),
            "data_collection": int(total_budget * 0.25),
            "design_development": int(total_budget * 0.25),
            "training_optimization": int(total_budget * 0.20),
            "evaluation_validation": int(total_budget * 0.10),
            "deployment_monitoring": int(total_budget * 0.05)
        }

        # 예상 사용량
        projected_usage = int(avg_daily * 30)  # 30일 예상

        return {
            "current_budget": total_budget,
            "recommended_allocation": recommended_allocation,
            "daily_usage_trend": trend,
            "warning_threshold": 0.8,
            "projected_usage": projected_usage,
            "budget_status": "warning" if avg_daily > total_budget / 30 * 0.8 else "ok"
        }


class AgentScalingManager:
    """
    에이전트 스케일링 관리자
    
    기능:
    1. 에이전트 풀 모니터링
    2. 스케일링 정책 관리
    3. 자동 스케일링 추천
    4. 비용 최적화 제안
    """

    def __init__(self):
        self._policies: Dict[str, ScalingPolicy] = {}
        self._scaling_history: List[Dict[str, Any]] = []
        self._cooldowns: Dict[str, datetime] = {}
        self._initialize_default_policies()

    def _initialize_default_policies(self):
        """기본 스케일링 정책 초기화"""
        self._policies = {
            "problem_definition": ScalingPolicy(
                agent_type="problem_definition",
                scale_up_threshold=0.75,
                scale_down_threshold=0.25,
                min_instances=1,
                max_instances=5,
                cooldown_seconds=300,  # 5분
                auto_scale=True
            ),
            "data_collection": ScalingPolicy(
                agent_type="data_collection",
                scale_up_threshold=0.80,
                scale_down_threshold=0.20,
                min_instances=1,
                max_instances=5,
                cooldown_seconds=300,
                auto_scale=True
            ),
            "design_development": ScalingPolicy(
                agent_type="design_development",
                scale_up_threshold=0.85,
                scale_down_threshold=0.30,
                min_instances=2,
                max_instances=10,
                cooldown_seconds=180,  # 3분
                auto_scale=True
            ),
            "training_optimization": ScalingPolicy(
                agent_type="training_optimization",
                scale_up_threshold=0.90,
                scale_down_threshold=0.35,
                min_instances=1,
                max_instances=5,
                cooldown_seconds=600,  # 10분
                auto_scale=True
            ),
            "evaluation_validation": ScalingPolicy(
                agent_type="evaluation_validation",
                scale_up_threshold=0.80,
                scale_down_threshold=0.30,
                min_instances=1,
                max_instances=3,
                cooldown_seconds=180,
                auto_scale=True
            ),
            "deployment_monitoring": ScalingPolicy(
                agent_type="deployment_monitoring",
                scale_up_threshold=0.75,
                scale_down_threshold=0.20,
                min_instances=1,
                max_instances=3,
                cooldown_seconds=300,
                auto_scale=True
            )
        }

    def update_policy(self, agent_type: str, policy: ScalingPolicy):
        """스케일링 정책 업데이트"""
        self._policies[agent_type] = policy

    def get_scaling_recommendation(
        self,
        agent_type: str,
        current_utilization: float,
        current_instances: int,
        queue_size: int = 0
    ) -> Optional[OptimizationRecommendation]:
        """
        스케일링 권장사항 생성
        
        Args:
            agent_type: 에이전트 타입
            current_utilization: 현재 활용률 (0-1)
            current_instances: 현재 인스턴스 수
            queue_size: 대기 중인 work 수
        
        Returns:
            OptimizationRecommendation 또는 None
        """
        policy = self._policies.get(agent_type)
        if not policy or not policy.auto_scale:
            return None

        # 쿨다운 확인
        if agent_type in self._cooldowns:
            if datetime.now() < self._cooldowns[agent_type]:
                return None  # 쿨다운 중
            else:
                del self._cooldowns[agent_type]

        # 스케일업 결정
        if current_utilization > policy.scale_up_threshold or queue_size > 5:
            if current_instances < policy.max_instances:
                scale_to = min(current_instances + 1, policy.max_instances)

                # 쿨다운 설정
                self._cooldowns[agent_type] = datetime.now() + timedelta(seconds=policy.cooldown_seconds)

                return OptimizationRecommendation(
                    work_id="system",
                    agent_id=agent_type,
                    action_type="scale_up",
                    priority=1,  # 최우선
                    description=f"활용률 {current_utilization*100:.1f}%가 임계치 {policy.scale_up_threshold*100:.0f}% 초과",
                    expected_benefit=f"{current_instances} -> {scale_to} 인스턴스",
                    implementation_effort="low"
                )

        # 스케일다운 결정
        elif current_utilization < policy.scale_down_threshold and queue_size == 0:
            if current_instances > policy.min_instances:
                scale_to = max(current_instances - 1, policy.min_instances)

                # 쿨다운 설정
                self._cooldowns[agent_type] = datetime.now() + timedelta(seconds=policy.cooldown_seconds)

                return OptimizationRecommendation(
                    work_id="system",
                    agent_id=agent_type,
                    action_type="scale_down",
                    priority=3,  # 중간 우선순위
                    description=f"활용률 {current_utilization*100:.1f}%가 임계치 {policy.scale_down_threshold*100:.0f}% 미만",
                    expected_benefit=f"{current_instances} -> {scale_to} 인스턴스 (비용 절감)",
                    implementation_effort="low"
                )

        return None

    def get_cost_optimization_recommendations(
        self,
        utilization_by_type: Dict[str, float],
        instance_count_by_type: Dict[str, int]
    ) -> List[OptimizationRecommendation]:
        """
        비용 최적화 권장사항 생성
        
        Returns:
            List[OptimizationRecommendation]
        """
        recommendations = []

        # 과소활용 에이전트 감지
        for agent_type, util in utilization_by_type.items():
            policy = self._policies.get(agent_type)
            if policy and util < policy.scale_down_threshold:
                recommendations.append(OptimizationRecommendation(
                    work_id="system",
                    agent_id=agent_type,
                    action_type="scale_down",
                    priority=4,
                    description=f"{agent_type} 활용률 {util*100:.1f}% - 감축 가능",
                    expected_benefit="비용 절감",
                    implementation_effort="low"
                ))

        # 불균형 부하 감지
        util_values = list(utilization_by_type.values())
        if len(util_values) > 1:
            avg_util = sum(util_values) / len(util_values)
            std_util = (sum((u - avg_util) ** 2 for u in util_values) / len(util_values)) ** 0.5

            if std_util > 0.2:  # 표준편차가 20% 이상
                overloaded = [k for k, v in utilization_by_type.items() if v > avg_util + std_util]
                underloaded = [k for k, v in utilization_by_type.items() if v < avg_util - std_util]

                if overloaded and underloaded:
                    recommendations.append(OptimizationRecommendation(
                        work_id="system",
                        agent_id="workload_rebalance",
                        action_type="rebalance",
                        priority=2,
                        description=f"불균형 부하 - {overloaded} 과부하, {underloaded} 과소활용",
                        expected_benefit="전체 효율 향상",
                        implementation_effort="medium"
                    ))

        return recommendations


class OptimizationOrchestrator:
    """
    최적화 오케스트레이터
    
    토큰 최적화와 스케일링을 통합 관리
    """

    def __init__(self, strategy: TokenOptimizationStrategy = TokenOptimizationStrategy.BALANCED):
        self.token_optimizer = TokenOptimizer(strategy)
        self.scaling_manager = AgentScalingManager()
        self._active_recommendations: List[OptimizationRecommendation] = []

    def analyze_and_optimize(
        self,
        work_data_list: List[Dict[str, Any]],
        agent_pool_status: Dict[str, Any],
        token_budget: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        전체 시스템 분석 및 최적화 권장사항 생성
        
        Args:
            work_data_list: Work 데이터 리스트
            agent_pool_status: 에이전트 풀 상태
            token_budget: 총 토큰 예산
        
        Returns:
            {
                "timestamp": str,
                "token_analysis": Dict,
                "scaling_analysis": Dict,
                "recommendations": List[OptimizationRecommendation],
                "priority_actions": List[str]
            }
        """
        # 1. 토큰 효율 분석
        token_analysis = {
            "by_work": [],
            "inefficient_works": [],
            "critical_works": [],
            "total_waste": 0,
            "potential_savings": 0
        }

        for work_data in work_data_list:
            analysis = self.token_optimizer.analyze_work_token_efficiency(work_data)
            token_analysis["by_work"].append(analysis)

            if analysis["status"] == "inefficient":
                token_analysis["inefficient_works"].append(analysis)
            elif analysis["status"] == "critical":
                token_analysis["critical_works"].append(analysis)

            token_analysis["total_waste"] += analysis["token_waste"]

        # 잠재 절감액 계산
        for work in token_analysis["inefficient_works"]:
            token_analysis["potential_savings"] += int(work["token_waste"] * 0.5)
        for work in token_analysis["critical_works"]:
            token_analysis["potential_savings"] += int(work["token_waste"] * 0.8)

        # 2. 스케일링 분석
        scaling_analysis = {
            "recommendations": [],
            "by_agent_type": {}
        }

        for agent_type, pool_data in agent_pool_status.get("by_type", {}).items():
            util = pool_data.get("utilization", 0)
            queue_size = pool_data.get("queue_size", 0)
            instances = pool_data.get("instance_count", 1)

            rec = self.scaling_manager.get_scaling_recommendation(
                agent_type=agent_type,
                current_utilization=util,
                current_instances=instances,
                queue_size=queue_size
            )

            if rec:
                scaling_analysis["by_agent_type"][agent_type] = rec
                scaling_analysis["recommendations"].append(rec)

        # 비용 최적화 추가
        util_by_type = {}
        instances_by_type = {}
        for agent_type, pool_data in agent_pool_status.get("by_type", {}).items():
            util_by_type[agent_type] = pool_data.get("utilization", 0)
            instances_by_type[agent_type] = pool_data.get("instance_count", 1)

        cost_recs = self.scaling_manager.get_cost_optimization_recommendations(
            utilization_by_type=util_by_type,
            instance_count_by_type=instances_by_type
        )
        scaling_analysis["recommendations"].extend(cost_recs)

        # 3. 우선순위 정렬
        all_recommendations = scaling_analysis["recommendations"]

        # 토큰 최적화 권장사항 추가
        if token_analysis["critical_works"]:
            for work in token_analysis["critical_works"][:3]:  # 상위 3개만
                all_recommendations.append(OptimizationRecommendation(
                    work_id=work["work_id"],
                    agent_id=work.get("agent_id", "unknown"),
                    action_type="token_optimization",
                    priority=1,
                    description=f"토큰 효율 {work['efficiency']:.1f}% - 긴급 최적화 필요",
                    expected_benefit=f"{work['token_waste']:,} 토큰 절감",
                    estimated_token_savings=int(work['token_waste'] * 0.7),
                    implementation_effort="medium"
                ))

        # 우선순위 정렬
        all_recommendations.sort(key=lambda x: x.priority)

        # 4. 우선 조치사항
        priority_actions = []
        critical_count = len(token_analysis["critical_works"])
        if critical_count > 0:
            priority_actions.append(f"긴급: {critical_count}개 Work 토큰 최적화 필요")

        scale_up_count = sum(1 for r in all_recommendations if r.action_type == "scale_up")
        if scale_up_count > 0:
            priority_actions.append(f"중요: {scale_up_count}개 에이전트 스케일업 필요")

        return {
            "timestamp": datetime.now().isoformat(),
            "token_analysis": token_analysis,
            "scaling_analysis": scaling_analysis,
            "recommendations": all_recommendations,
            "priority_actions": priority_actions,
            "summary": {
                "total_waste": token_analysis["total_waste"],
                "potential_savings": token_analysis["potential_savings"],
                "scaling_actions": len(scaling_analysis["recommendations"]),
                "critical_works": critical_count
            }
        }
