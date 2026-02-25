from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from .work import Work, WorkStatus, WorkPriority, WorkQueue, PlanStatus
from .agent_pool import AgentPool, AgentStatus, AgentInstance
from .raci import RACI, RACIRole


class BottleneckType(Enum):
    AGENT_CAPACITY = "agent_capacity"
    WORK_DEPENDENCY = "work_dependency"
    TOKEN_LIMIT = "token_limit"
    TIMEOUT = "timeout"
    QUEUE_OVERFLOW = "queue_overflow"
    IMBALANCED_LOAD = "imbalanced_load"


@dataclass
class BottleneckAnalysis:
    bottleneck_id: str
    bottleneck_type: BottleneckType
    severity: float
    affected_works: List[str]
    affected_agents: List[str]
    root_cause: str
    recommendations: List[str]
    estimated_impact: Dict[str, float]
    detected_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolution_applied: Optional[str] = None


@dataclass
class ThroughputMetrics:
    period_start: datetime
    period_end: datetime
    works_completed: int
    works_failed: int
    total_tokens_used: int
    total_duration_seconds: float
    works_per_hour: float
    tokens_per_work: float
    average_work_duration: float
    by_agent_type: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    by_work_type: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class TOCSupervisor:
    def __init__(self, agent_pool: AgentPool, work_queue: WorkQueue, raci: RACI):
        self._agent_pool = agent_pool
        self._work_queue = work_queue
        self._raci = raci
        
        self._bottlenecks: List[BottleneckAnalysis] = []
        self._throughput_history: List[ThroughputMetrics] = []
        self._optimization_log: List[Dict[str, Any]] = []
        self._completed_works: List[Dict[str, Any]] = []
        self._work_agent_history: Dict[str, List[Dict[str, Any]]] = {}
        
        self._config = {
            "bottleneck_threshold": 0.7,
            "scaling_threshold": 0.85,
            "rebalance_threshold": 0.3,
            "max_queue_size": 100,
            "token_budget_per_hour": 1000000,
            "target_utilization": 0.75,
        }
        
        self._baseline_metrics = None
        
        self._memory_storage: Optional[Any] = None
        self._filesystem_storage: Optional[Any] = None
        self._storage_path = None
    
    async def analyze_system(self) -> Dict[str, Any]:
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "agent_analysis": await self._analyze_agents(),
            "work_analysis": await self._analyze_works(),
            "bottlenecks": [],
            "recommendations": []
        }
        
        bottlenecks = await self._detect_bottlenecks()
        analysis["bottlenecks"] = [self._bottleneck_to_dict(b) for b in bottlenecks]
        
        recommendations = self._generate_recommendations(bottlenecks)
        analysis["recommendations"] = recommendations
        
        self._bottlenecks.extend(bottlenecks)
        
        return analysis
    
    async def _analyze_agents(self) -> Dict[str, Any]:
        pool_status = self._agent_pool.get_pool_status()
        
        analysis = {
            "total_capacity": 0,
            "available_capacity": 0,
            "utilization_by_type": {},
            "imbalanced_types": [],
            "overloaded_agents": [],
            "underutilized_agents": []
        }
        
        agent_types = set()
        for agent in self._agent_pool._agents.values():
            agent_types.add(agent.agent_type)
        
        for agent_type in agent_types:
            capacity = self._agent_pool.get_capacity(agent_type)
            available = self._agent_pool.get_available_capacity(agent_type)
            utilization = 1 - (available / capacity) if capacity > 0 else 0
            
            analysis["total_capacity"] += capacity
            analysis["available_capacity"] += available
            analysis["utilization_by_type"][agent_type] = {
                "capacity": capacity,
                "available": available,
                "utilization": utilization
            }
            
            if utilization > self._config["scaling_threshold"]:
                analysis["imbalanced_types"].append({
                    "type": agent_type,
                    "issue": "overloaded",
                    "utilization": utilization
                })
            elif utilization < self._config["rebalance_threshold"]:
                analysis["imbalanced_types"].append({
                    "type": agent_type,
                    "issue": "underutilized",
                    "utilization": utilization
                })
        
        for agent in self._agent_pool._agents.values():
            if agent.utilization >= 1.0 and agent.status == AgentStatus.BUSY:
                analysis["overloaded_agents"].append(agent.agent_id)
            elif agent.utilization == 0 and agent.status == AgentStatus.IDLE:
                analysis["underutilized_agents"].append(agent.agent_id)
        
        return analysis
    
    async def _analyze_works(self) -> Dict[str, Any]:
        pending_count = await self._work_queue.get_pending_count()
        blocked_works = await self._work_queue.get_blocked_works()
        
        analysis = {
            "pending_works": pending_count,
            "blocked_works": len(blocked_works),
            "dependency_chains": self._analyze_dependency_chains(blocked_works),
            "priority_distribution": {},
            "estimated_completion_time": 0
        }
        
        for work in blocked_works:
            priority = work.priority.name
            analysis["priority_distribution"][priority] = \
                analysis["priority_distribution"].get(priority, 0) + 1
        
        available_capacity = sum(
            self._agent_pool.get_available_capacity(at)
            for at in self._agent_pool._type_index.keys()
        )
        if available_capacity > 0 and pending_count > 0:
            analysis["estimated_completion_time"] = pending_count / available_capacity * 60
        
        return analysis
    
    def _analyze_dependency_chains(self, blocked_works: List[Work]) -> Dict[str, Any]:
        chains = {
            "max_depth": 0,
            "critical_path": [],
            "circular_dependencies": []
        }
        
        work_map = {w.work_id: w for w in blocked_works}
        
        def get_depth(work_id: str, visited: set) -> int:
            if work_id in visited:
                chains["circular_dependencies"].append(work_id)
                return 0
            visited.add(work_id)
            
            work = work_map.get(work_id)
            if not work:
                return 0
            
            if not work.dependencies:
                return 1
            
            max_dep_depth = 0
            for dep_id in work.dependencies:
                dep_depth = get_depth(dep_id, visited.copy())
                max_dep_depth = max(max_dep_depth, dep_depth)
            
            return max_dep_depth + 1
        
        for work in blocked_works:
            depth = get_depth(work.work_id, set())
            chains["max_depth"] = max(chains["max_depth"], depth)
        
        return chains
    
    async def _detect_bottlenecks(self) -> List[BottleneckAnalysis]:
        bottlenecks = []
        timestamp = datetime.now()
        
        pool_status = self._agent_pool.get_pool_status()
        
        for agent_type, agents in self._agent_pool._type_index.items():
            available = self._agent_pool.get_available_capacity(agent_type)
            capacity = self._agent_pool.get_capacity(agent_type)
            
            if capacity > 0 and available == 0:
                pending = await self._work_queue.get_pending_count()
                if pending > 0:
                    bottleneck = BottleneckAnalysis(
                        bottleneck_id=f"capacity_{agent_type}_{timestamp.timestamp()}",
                        bottleneck_type=BottleneckType.AGENT_CAPACITY,
                        severity=1.0,
                        affected_works=[],
                        affected_agents=agents,
                        root_cause=f"No available capacity for agent type: {agent_type}",
                        recommendations=[
                            f"Scale up {agent_type} agents",
                            "Redistribute work to other agent types",
                            "Optimize agent processing time"
                        ],
                        estimated_impact={
                            "throughput_reduction": 0.5,
                            "delay_minutes": pending * 5
                        }
                    )
                    bottlenecks.append(bottleneck)
        
        blocked_works = await self._work_queue.get_blocked_works()
        if blocked_works:
            dependency_groups: Dict[str, List[str]] = {}
            for work in blocked_works:
                for dep in work.dependencies:
                    if dep not in dependency_groups:
                        dependency_groups[dep] = []
                    dependency_groups[dep].append(work.work_id)
            
            for blocking_work, blocked in dependency_groups.items():
                if len(blocked) > 3:
                    bottleneck = BottleneckAnalysis(
                        bottleneck_id=f"dependency_{blocking_work}_{timestamp.timestamp()}",
                        bottleneck_type=BottleneckType.WORK_DEPENDENCY,
                        severity=len(blocked) / 10,
                        affected_works=blocked,
                        affected_agents=[],
                        root_cause=f"Work {blocking_work} is blocking {len(blocked)} other works",
                        recommendations=[
                            f"Prioritize completion of work {blocking_work}",
                            "Consider parallelizing dependent works",
                            "Review dependency chain for optimization"
                        ],
                        estimated_impact={
                            "throughput_reduction": len(blocked) * 0.1,
                            "delay_minutes": len(blocked) * 3
                        }
                    )
                    bottlenecks.append(bottleneck)
        
        total_tokens = pool_status.get("total_tokens_used", 0)
        if total_tokens > self._config["token_budget_per_hour"] * 0.8:
            bottleneck = BottleneckAnalysis(
                bottleneck_id=f"token_limit_{timestamp.timestamp()}",
                bottleneck_type=BottleneckType.TOKEN_LIMIT,
                severity=0.8,
                affected_works=[],
                affected_agents=list(self._agent_pool._agents.keys()),
                root_cause="Token usage approaching budget limit",
                recommendations=[
                    "Optimize prompts to reduce token usage",
                    "Implement token caching",
                    "Consider cheaper models for simple tasks"
                ],
                estimated_impact={
                    "throughput_reduction": 0.3,
                    "cost_increase": 0.5
                }
            )
            bottlenecks.append(bottleneck)
        
        if pool_status.get("utilization_rate", 0) < self._config["rebalance_threshold"]:
            bottleneck = BottleneckAnalysis(
                bottleneck_id=f"imbalanced_{timestamp.timestamp()}",
                bottleneck_type=BottleneckType.IMBALANCED_LOAD,
                severity=0.5,
                affected_works=[],
                affected_agents=[],
                root_cause="System utilization is low, resources may be wasted",
                recommendations=[
                    "Scale down idle agents",
                    "Consolidate agent types",
                    "Increase work queue size"
                ],
                estimated_impact={
                    "efficiency_loss": 0.3,
                    "cost_waste": 0.2
                }
            )
            bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    def _generate_recommendations(self, bottlenecks: List[BottleneckAnalysis]) -> List[Dict[str, Any]]:
        recommendations = []
        
        for bottleneck in bottlenecks:
            for rec in bottleneck.recommendations:
                recommendations.append({
                    "bottleneck_id": bottleneck.bottleneck_id,
                    "type": bottleneck.bottleneck_type.value,
                    "severity": bottleneck.severity,
                    "recommendation": rec,
                    "estimated_impact": bottleneck.estimated_impact
                })
        
        recommendations.sort(key=lambda r: r["severity"], reverse=True)
        
        return recommendations
    
    async def optimize(self) -> Dict[str, Any]:
        analysis = await self.analyze_system()
        optimizations_applied = []
        
        for bottleneck in self._bottlenecks[-5:]:
            if bottleneck.resolved_at:
                continue
            
            if bottleneck.bottleneck_type == BottleneckType.AGENT_CAPACITY:
                optimization = await self._optimize_capacity(bottleneck)
                if optimization:
                    optimizations_applied.append(optimization)
                    bottleneck.resolution_applied = optimization["action"]
                    bottleneck.resolved_at = datetime.now()
            
            elif bottleneck.bottleneck_type == BottleneckType.WORK_DEPENDENCY:
                optimization = await self._optimize_dependencies(bottleneck)
                if optimization:
                    optimizations_applied.append(optimization)
                    bottleneck.resolution_applied = optimization["action"]
                    bottleneck.resolved_at = datetime.now()
            
            elif bottleneck.bottleneck_type == BottleneckType.IMBALANCED_LOAD:
                optimization = await self._optimize_load_balance(bottleneck)
                if optimization:
                    optimizations_applied.append(optimization)
                    bottleneck.resolution_applied = optimization["action"]
                    bottleneck.resolved_at = datetime.now()
        
        self._optimization_log.extend(optimizations_applied)
        
        return {
            "analysis": analysis,
            "optimizations_applied": optimizations_applied,
            "total_optimizations": len(self._optimization_log)
        }
    
    async def _optimize_capacity(self, bottleneck: BottleneckAnalysis) -> Optional[Dict[str, Any]]:
        affected_agents = bottleneck.affected_agents
        if not affected_agents:
            return None
        
        agent = self._agent_pool.get_agent(affected_agents[0])
        if not agent:
            return None
        
        return {
            "type": "capacity_optimization",
            "action": f"suggested_scale_up_{agent.agent_type}",
            "details": {
                "agent_type": agent.agent_type,
                "current_capacity": self._agent_pool.get_capacity(agent.agent_type),
                "recommended_additional": 2,
                "reason": bottleneck.root_cause
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _optimize_dependencies(self, bottleneck: BottleneckAnalysis) -> Optional[Dict[str, Any]]:
        affected_works = bottleneck.affected_works
        if not affected_works:
            return None
        
        return {
            "type": "dependency_optimization",
            "action": "prioritize_blocking_work",
            "details": {
                "blocking_works": list(set(
                    dep for work_id in affected_works
                    for dep in self._work_queue._queue
                    if hasattr(dep, 'work_id') and dep.work_id in affected_works
                )),
                "blocked_count": len(affected_works),
                "recommended_priority": "CRITICAL"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _optimize_load_balance(self, bottleneck: BottleneckAnalysis) -> Optional[Dict[str, Any]]:
        utilization = self._agent_pool.get_pool_status().get("utilization_rate", 0)
        
        return {
            "type": "load_balance_optimization",
            "action": "rebalance_agent_allocation",
            "details": {
                "current_utilization": utilization,
                "target_utilization": self._config["target_utilization"],
                "recommendation": "Scale down idle agents or increase work intake"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def calculate_throughput(self, period_hours: float = 1.0) -> ThroughputMetrics:
        now = datetime.now()
        period_start = now - timedelta(hours=period_hours)
        
        completed_works = 0
        failed_works = 0
        total_tokens = 0
        total_duration = 0.0
        
        by_agent_type: Dict[str, Dict[str, Any]] = {}
        by_work_type: Dict[str, Dict[str, Any]] = {}
        
        for agent in self._agent_pool._agents.values():
            completed_works += agent.completed_works
            failed_works += agent.failed_works
            total_tokens += agent.total_tokens_used
            total_duration += agent.total_work_time_seconds
            
            if agent.agent_type not in by_agent_type:
                by_agent_type[agent.agent_type] = {
                    "completed": 0,
                    "failed": 0,
                    "tokens": 0,
                    "duration": 0.0
                }
            by_agent_type[agent.agent_type]["completed"] += agent.completed_works
            by_agent_type[agent.agent_type]["failed"] += agent.failed_works
            by_agent_type[agent.agent_type]["tokens"] += agent.total_tokens_used
            by_agent_type[agent.agent_type]["duration"] += agent.total_work_time_seconds
        
        works_per_hour = (completed_works + failed_works) / period_hours if period_hours > 0 else 0
        tokens_per_work = total_tokens / completed_works if completed_works > 0 else 0
        avg_duration = total_duration / (completed_works + failed_works) if (completed_works + failed_works) > 0 else 0
        
        metrics = ThroughputMetrics(
            period_start=period_start,
            period_end=now,
            works_completed=completed_works,
            works_failed=failed_works,
            total_tokens_used=total_tokens,
            total_duration_seconds=total_duration,
            works_per_hour=works_per_hour,
            tokens_per_work=tokens_per_work,
            average_work_duration=avg_duration,
            by_agent_type=by_agent_type,
            by_work_type=by_work_type
        )
        
        self._throughput_history.append(metrics)
        
        return metrics
    
    def identify_constraint(self) -> Optional[Dict[str, Any]]:
        if not self._throughput_history:
            return None
        
        recent = self._throughput_history[-1]
        
        constraints = []
        
        for agent_type, stats in recent.by_agent_type.items():
            if stats["completed"] == 0 and stats["failed"] == 0:
                continue
            
            avg_duration = stats["duration"] / (stats["completed"] + stats["failed"])
            if avg_duration > recent.average_work_duration * 1.5:
                constraints.append({
                    "type": "slow_agent",
                    "agent_type": agent_type,
                    "avg_duration": avg_duration,
                    "baseline": recent.average_work_duration,
                    "impact": "high"
                })
        
        pool_status = self._agent_pool.get_pool_status()
        for agent_type, type_status in pool_status.get("agents_by_type", {}).items():
            available = self._agent_pool.get_available_capacity(agent_type)
            if available == 0:
                constraints.append({
                    "type": "capacity_limit",
                    "agent_type": agent_type,
                    "available_capacity": 0,
                    "impact": "critical"
                })
        
        if constraints:
            return max(constraints, key=lambda c: 1 if c["impact"] == "critical" else 0.5)
        
        return None
    
    def get_optimization_report(self) -> Dict[str, Any]:
        throughput = self.calculate_throughput() if not self._throughput_history else self._throughput_history[-1]
        constraint = self.identify_constraint()
        
        return {
            "summary": {
                "works_completed": throughput.works_completed,
                "works_failed": throughput.works_failed,
                "works_per_hour": throughput.works_per_hour,
                "tokens_used": throughput.total_tokens_used,
                "tokens_per_work": throughput.tokens_per_work,
                "success_rate": throughput.works_completed / (throughput.works_completed + throughput.works_failed)
                    if (throughput.works_completed + throughput.works_failed) > 0 else 1.0
            },
            "current_constraint": constraint,
            "bottlenecks_detected": len(self._bottlenecks),
            "bottlenecks_resolved": sum(1 for b in self._bottlenecks if b.resolved_at),
            "optimizations_applied": len(self._optimization_log),
            "recommendations": [
                rec for rec in self._generate_recommendations(self._bottlenecks[-5:])
            ]
        }
    
    def record_work_completion(self, work: Work, result):
        completion_data = {
            "work_id": work.work_id,
            "work_type": work.work_type,
            "agent_id": work.assigned_agent,
            "priority": work.priority.value,
            "estimated_tokens": work.estimated_tokens,
            "actual_tokens": work.actual_tokens,
            "estimated_duration": work.estimated_duration_seconds,
            "actual_duration": work.actual_duration_seconds,
            "status": result.status.value,
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "had_plan": work.plan is not None,
            "plan_status": work.plan.status.value if work.plan else None
        }
        self._completed_works.append(completion_data)
        
        self._track_work_agent_activity(work, result)
    
    def _track_work_agent_activity(self, work: Work, result):
        if work.assigned_agent is None:
            return
        
        if work.work_id not in self._work_agent_history:
            self._work_agent_history[work.work_id] = []
        
        agent = self._agent_pool.get_agent(work.assigned_agent)
        agent_type = agent.agent_type if agent else "unknown"
        
        self._work_agent_history[work.work_id].append({
            "agent_id": work.assigned_agent,
            "agent_type": agent_type,
            "work_type": work.work_type,
            "tokens_used": work.actual_tokens,
            "duration_seconds": work.actual_duration_seconds,
            "status": result.status.value,
            "started_at": work.started_at.isoformat() if work.started_at else None,
            "completed_at": work.completed_at.isoformat() if work.completed_at else None
        })
    
    def get_work_agent_statistics(self, work_id: Optional[str] = None) -> Dict[str, Any]:
        if work_id is not None:
            return self._get_single_work_statistics(work_id)
        else:
            return self._get_all_work_statistics()
    
    def _get_single_work_statistics(self, work_id: str) -> Dict[str, Any]:
        if work_id not in self._work_agent_history:
            return {
                "work_id": work_id,
                "status": "not_found",
                "message": f"Work {work_id} has no agent activity recorded"
            }
        
        activities = self._work_agent_history[work_id]
        
        total_tokens = sum(a["tokens_used"] for a in activities)
        total_duration = sum(a["duration_seconds"] for a in activities)
        
        agent_summary: Dict[str, Dict[str, Any]] = {}
        for activity in activities:
            agent_id = activity["agent_id"]
            if agent_id not in agent_summary:
                agent_summary[agent_id] = {
                    "agent_type": activity["agent_type"],
                    "work_count": 0,
                    "total_tokens": 0,
                    "total_duration": 0,
                    "activities": []
                }
            agent_summary[agent_id]["work_count"] += 1
            agent_summary[agent_id]["total_tokens"] += activity["tokens_used"]
            agent_summary[agent_id]["total_duration"] += activity["duration_seconds"]
            agent_summary[agent_id]["activities"].append(activity)
        
        return {
            "work_id": work_id,
            "total_activities": len(activities),
            "total_tokens": total_tokens,
            "total_duration_seconds": total_duration,
            "agents": agent_summary
        }

    def _get_all_work_statistics(self) -> Dict[str, Any]:
        work_stats: Dict[str, Dict[str, Any]] = {}
        
        for work_id, activities in self._work_agent_history.items():
            total_tokens = sum(a["tokens_used"] for a in activities)
            total_duration = sum(a["duration_seconds"] for a in activities)
            
            agent_types: Dict[str, int] = {}
            for activity in activities:
                agent_type = activity["agent_type"]
                agent_types[agent_type] = agent_types.get(agent_type, 0) + 1
            
            work_stats[work_id] = {
                "work_type": activities[0]["work_type"] if activities else "unknown",
                "total_activities": len(activities),
                "total_tokens": total_tokens,
                "total_duration_seconds": total_duration,
                "agent_types": agent_types
            }
        
        agent_type_stats: Dict[str, Dict[str, Any]] = {}
        for work_id, activities in self._work_agent_history.items():
            work_type = activities[0]["work_type"] if activities else "unknown"
            
            for activity in activities:
                agent_type = activity["agent_type"]
                if agent_type not in agent_type_stats:
                    agent_type_stats[agent_type] = {
                        "total_works": 0,
                        "total_tokens": 0,
                        "total_duration": 0,
                        "work_types": {}
                    }
                agent_type_stats[agent_type]["total_works"] += 1
                agent_type_stats[agent_type]["total_tokens"] += activity["tokens_used"]
                agent_type_stats[agent_type]["total_duration"] += activity["duration_seconds"]
                
                if work_type not in agent_type_stats[agent_type]["work_types"]:
                    agent_type_stats[agent_type]["work_types"][work_type] = 0
                agent_type_stats[agent_type]["work_types"][work_type] += 1
        
        return {
            "summary": {
                "total_works": len(work_stats),
                "total_activities": sum(len(activities) for activities in self._work_agent_history.values()),
                "total_tokens": sum(ws["total_tokens"] for ws in work_stats.values()),
                "total_duration": sum(ws["total_duration_seconds"] for ws in work_stats.values())
            },
            "by_work": work_stats,
            "by_agent_type": agent_type_stats
        }
    
    def format_work_agent_report(self, work_id: Optional[str] = None) -> str:
        stats = self.get_work_agent_statistics(work_id)
        
        if work_id is not None:
            return self._format_single_work_report(work_id, stats)
        else:
            return self._format_all_works_report(stats)
    
    def _format_single_work_report(self, work_id: str, stats: Dict[str, Any]) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append(f"Work-Agent 통계 보고서: {work_id}")
        lines.append("=" * 80)
        lines.append("")
        
        if stats.get("status") == "not_found":
            lines.append(f"⚠ {stats['message']}")
            lines.append("")
            lines.append("=" * 80)
            return "\n".join(lines)
        
        lines.append("## 요약")
        lines.append(f"  총 활동 수: {stats['total_activities']}")
        lines.append(f"  총 토큰 사용: {stats['total_tokens']:,}")
        lines.append(f"  총 작업 시간: {stats['total_duration_seconds']:.2f}초")
        lines.append("")
        
        lines.append("## 에이전트별 통계")
        for agent_id, agent_data in stats["agents"].items():
            lines.append(f"\n### {agent_id} ({agent_data['agent_type']})")
            lines.append(f"  작업 수: {agent_data['work_count']}")
            lines.append(f"  토큰 사용: {agent_data['total_tokens']:,}")
            lines.append(f"  작업 시간: {agent_data['total_duration']:.2f}초")
            lines.append(f"  평균 토큰/작업: {agent_data['total_tokens'] / agent_data['work_count'] if agent_data['work_count'] > 0 else 0:.0f}")
            lines.append(f"  평균 시간/작업: {agent_data['total_duration'] / agent_data['work_count'] if agent_data['work_count'] > 0 else 0:.2f}초")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def _format_all_works_report(self, stats: Dict[str, Any]) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append("전체 Work-Agent 통계 보고서")
        lines.append("=" * 80)
        lines.append("")
        
        summary = stats["summary"]
        lines.append("## 전체 요약")
        lines.append(f"  총 Work 수: {summary['total_works']}")
        lines.append(f"  총 활동 수: {summary['total_activities']}")
        lines.append(f"  총 토큰 사용: {summary['total_tokens']:,}")
        lines.append(f"  총 작업 시간: {summary['total_duration']:.2f}초")
        lines.append("")
        
        lines.append("## Work별 통계")
        for work_id, work_data in stats["by_work"].items():
            lines.append(f"\n### {work_id} ({work_data['work_type']})")
            lines.append(f"  활동 수: {work_data['total_activities']}")
            lines.append(f"  토큰: {work_data['total_tokens']:,}")
            lines.append(f"  시간: {work_data['total_duration_seconds']:.2f}초")
            lines.append(f"  에이전트 타입: {', '.join(f'{k}: {v}' for k, v in work_data['agent_types'].items())}")
        
        lines.append("\n## 에이전트 타입별 통계")
        for agent_type, type_data in stats["by_agent_type"].items():
            lines.append(f"\n### {agent_type}")
            lines.append(f"  총 Work 수: {type_data['total_works']}")
            lines.append(f"  토큰 사용: {type_data['total_tokens']:,}")
            lines.append(f"  작업 시간: {type_data['total_duration']:.2f}초")
            lines.append(f"  Work 타입:")
            for work_type, count in type_data["work_types"].items():
                lines.append(f"    - {work_type}: {count}")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    async def generate_final_analysis(self, all_works: List[Work]) -> Dict[str, Any]:
        completed = [w for w in all_works if w.status == WorkStatus.COMPLETED]
        failed = [w for w in all_works if w.status == WorkStatus.FAILED]
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "work_summary": {
                "total": len(all_works),
                "completed": len(completed),
                "failed": len(failed),
                "success_rate": len(completed) / len(all_works) if all_works else 1.0
            },
            "token_analysis": await self._analyze_token_efficiency(completed),
            "agent_analysis": await self._analyze_agent_efficiency(),
            "bottleneck_analysis": await self._detect_final_bottlenecks(),
            "plan_approval_analysis": await self._analyze_plan_approvals(completed),
            "recommendations": []
        }
        
        recommendations = self._generate_final_recommendations(analysis)
        analysis["recommendations"] = recommendations
        
        return analysis
    
    async def _analyze_token_efficiency(self, completed_works: List[Work]) -> Dict[str, Any]:
        if not completed_works:
            return {"status": "no_data"}
        
        total_estimated = sum(w.estimated_tokens for w in completed_works)
        total_actual = sum(w.actual_tokens for w in completed_works)
        efficiency = (total_estimated / total_actual * 100) if total_actual > 0 else 100
        
        by_type: Dict[str, Dict[str, Any]] = {}
        for work in completed_works:
            if work.work_type not in by_type:
                by_type[work.work_type] = {
                    "count": 0,
                    "estimated": 0,
                    "actual": 0,
                    "efficiency": 0
                }
            by_type[work.work_type]["count"] += 1
            by_type[work.work_type]["estimated"] += work.estimated_tokens
            by_type[work.work_type]["actual"] += work.actual_tokens
        
        for work_type, data in by_type.items():
            data["efficiency"] = (data["estimated"] / data["actual"] * 100) if data["actual"] > 0 else 100
        
        inefficiencies = []
        for work_type, data in by_type.items():
            if data["efficiency"] < 80:
                inefficiencies.append({
                    "work_type": work_type,
                    "efficiency": data["efficiency"],
                    "waste": data["actual"] - data["estimated"]
                })
        
        return {
            "total_estimated": total_estimated,
            "total_actual": total_actual,
            "overall_efficiency": efficiency,
            "by_type": by_type,
            "inefficiencies": inefficiencies,
            "potential_savings": total_actual - total_estimated if total_actual > total_estimated else 0
        }
    
    async def _analyze_agent_efficiency(self) -> Dict[str, Any]:
        agents = self._agent_pool._agents
        
        analysis = {
            "by_agent": {},
            "by_type": {},
            "underperforming": [],
            "overperforming": []
        }
        
        for agent_id, agent in agents.items():
            if agent.completed_works + agent.failed_works == 0:
                continue
            
            avg_tokens = agent.total_tokens_used / agent.completed_works if agent.completed_works > 0 else 0
            avg_duration = agent.total_work_time_seconds / (agent.completed_works + agent.failed_works)
            success_rate = agent.success_rate
            
            analysis["by_agent"][agent_id] = {
                "completed": agent.completed_works,
                "failed": agent.failed_works,
                "success_rate": success_rate,
                "avg_tokens": avg_tokens,
                "avg_duration": avg_duration,
                "utilization": agent.utilization
            }
        
        for agent in agents.values():
            if agent.agent_type not in analysis["by_type"]:
                analysis["by_type"][agent.agent_type] = {
                    "agents": 0,
                    "total_completed": 0,
                    "total_failed": 0,
                    "total_tokens": 0,
                    "total_duration": 0
                }
            agent_type = agent.agent_type
            analysis["by_type"][agent_type]["agents"] += 1
            analysis["by_type"][agent_type]["total_completed"] += agent.completed_works
            analysis["by_type"][agent_type]["total_failed"] += agent.failed_works
            analysis["by_type"][agent_type]["total_tokens"] += agent.total_tokens_used
            analysis["by_type"][agent_type]["total_duration"] += agent.total_work_time_seconds
        
        for agent_type, data in analysis["by_type"].items():
            total = data["total_completed"] + data["total_failed"]
            data["success_rate"] = data["total_completed"] / total if total > 0 else 1.0
            data["avg_tokens"] = data["total_tokens"] / data["total_completed"] if data["total_completed"] > 0 else 0
            data["avg_duration"] = data["total_duration"] / total if total > 0 else 0
        
        return analysis
    
    async def _detect_final_bottlenecks(self) -> List[Dict[str, Any]]:
        bottlenecks = []
        pool_status = self._agent_pool.get_pool_status()
        
        analyzed_types = set()
        
        for agent_id, agent in self._agent_pool._agents.items():
            agent_type = agent.agent_type
            if agent_type in analyzed_types:
                continue
            analyzed_types.add(agent_type)
            
            agents_of_type = self._agent_pool.get_agents_by_type(agent_type)
            capacity = self._agent_pool.get_capacity(agent_type)
            if capacity == 0:
                continue
            
            total_completed = sum(a.completed_works for a in agents_of_type)
            agent_count = len(agents_of_type)
            works_per_agent = total_completed / agent_count if agent_count > 0 else 0
            
            if works_per_agent < 2 and total_completed > 0:
                bottlenecks.append({
                    "type": "agent_underutilization",
                    "agent_type": agent_type,
                    "severity": "medium",
                    "description": f"{agent_type} 에이전트가 너무 많습니다. {agent_count}개 에이전트가 평균 {works_per_agent:.1f}개의 작업만 완료했습니다.",
                    "recommendation": f"{agent_type} 에이전트를 {max(1, agent_count // 2)}개로 줄이세요."
                })
            
            if works_per_agent > 10:
                bottlenecks.append({
                    "type": "agent_overload",
                    "agent_type": agent_type,
                    "severity": "high",
                    "description": f"{agent_type} 에이전트가 과부하 상태입니다. 에이전트당 {works_per_agent:.1f}개의 작업을 처리했습니다.",
                    "recommendation": f"{agent_type} 에이전트를 추가로 배치하세요."
                })
        
        return bottlenecks
    
    async def _analyze_plan_approvals(self, completed_works: List[Work]) -> Dict[str, Any]:
        with_plan = [w for w in completed_works if w.plan is not None]
        approved = [w for w in with_plan if w.plan is not None and w.plan.status == PlanStatus.APPROVED]
        
        return {
            "total_with_plan": len(with_plan),
            "approved": len(approved),
            "approval_rate": len(approved) / len(with_plan) if with_plan else 1.0,
            "benefits": [
                "계획 승인이 있을 때 더 명확한 실행 방향",
                "예상 결과와 실제 결과 비교 가능",
                "초기 리스크 식별 및 감소"
            ]
        }
    
    def _generate_final_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        recommendations = []
        
        token_analysis = analysis.get("token_analysis", {})
        if token_analysis.get("overall_efficiency", 100) < 85:
            recommendations.append({
                "priority": "high",
                "category": "token_optimization",
                "title": "Token 사용 효율 개선",
                "description": f"전체 token 효율이 {token_analysis['overall_efficiency']:.1f}%로 목표치(90%) 미달입니다.",
                "actions": [
                    "프롬프트를 더 간결하게 작성",
                    "반복되는 작업에서 context 재사용",
                    "불필요한 정보 출력 제거",
                    "작업 분해를 통해 단일 작업당 token 사용량 감소"
                ],
                "expected_benefit": f"약 {token_analysis.get('potential_savings', 0):.0f} 토큰 절감 가능"
            })
        
        for ineff in token_analysis.get("inefficiencies", []):
            recommendations.append({
                "priority": "medium",
                "category": "work_type_optimization",
                "title": f"{ineff['work_type']} 작업 토큰 최적화",
                "description": f"{ineff['work_type']} 작업의 효율이 {ineff['efficiency']:.1f%}로 낮습니다.",
                "actions": [
                    f"{ineff['work_type']} 작업 핸들러 프롬프트 최적화",
                    "불필요한 중간 단계 제거",
                    "결과 출력 형식 간소화"
                ],
                "expected_benefit": f"약 {ineff['waste']:.0f} 토큰 절감"
            })
        
        bottleneck_analysis = analysis.get("bottleneck_analysis", [])
        for bottleneck in bottleneck_analysis:
            recommendations.append({
                "priority": bottleneck["severity"],
                "category": bottleneck["type"],
                "title": f"{bottleneck['agent_type']} 병목 해결",
                "description": bottleneck["description"],
                "actions": [bottleneck["recommendation"]],
                "expected_benefit": "에이전트 활용도 및 처리량 개선"
            })
        
        agent_analysis = analysis.get("agent_analysis", {})
        for agent_id, data in agent_analysis.get("by_agent", {}).items():
            if data["success_rate"] < 0.8 and (data["completed"] + data["failed"]) >= 3:
                recommendations.append({
                    "priority": "medium",
                    "category": "agent_performance",
                    "title": f"{agent_id} 성능 개선",
                    "description": f"{agent_id}의 성공률이 {data['success_rate']:.1%}로 낮습니다.",
                    "actions": [
                        "에이전트 핸들러 로그 확인",
                        "실패 원인 분석 및 수정",
                        "retry 로직 개선"
                    ],
                    "expected_benefit": "작업 성공률 향상, 재시작 비용 감소"
                })
        
        plan_analysis = analysis.get("plan_approval_analysis", {})
        if plan_analysis.get("approval_rate", 1.0) < 0.5 and plan_analysis.get("total_with_plan", 0) > 0:
            recommendations.append({
                "priority": "low",
                "category": "process_improvement",
                "title": "계획 승인 프로세스 개선",
                "description": f"계획 승인률이 {plan_analysis['approval_rate']:.1%}로 낮습니다.",
                "actions": [
                    "RESPONSIBLE 에이전트에 더 상세한 계획 가이드 제공",
                    "계획 템플릿 표준화",
                    "ACCOUNTABLE 에이전트 승인 기준 명확화"
                ],
                "expected_benefit": "계획 품질 향상, 재계획 시간 감소"
            })
        
        recommendations.sort(key=lambda r: {
            "high": 0,
            "medium": 1,
            "low": 2
        }.get(r["priority"], 3))
        
        return recommendations
    
    def format_final_report(self, analysis: Dict[str, Any]) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append("TOC 최종 분석 보고서")
        lines.append("=" * 80)
        lines.append("")
        
        work_summary = analysis["work_summary"]
        lines.append("## 작업 요약")
        lines.append(f"  전체 작업: {work_summary['total']}")
        lines.append(f"  완료: {work_summary['completed']}")
        lines.append(f"  실패: {work_summary['failed']}")
        lines.append(f"  성공률: {work_summary['success_rate']:.1%}")
        lines.append("")
        
        token_analysis = analysis["token_analysis"]
        if token_analysis.get("status") != "no_data":
            lines.append("## Token 효율 분석")
            lines.append(f"  예상 토큰: {token_analysis['total_estimated']:,}")
            lines.append(f"  실제 토큰: {token_analysis['total_actual']:,}")
            lines.append(f"  효율: {token_analysis['overall_efficiency']:.1f}%")
            
            if token_analysis.get("potential_savings", 0) > 0:
                lines.append(f"  절감 가능 토큰: {token_analysis['potential_savings']:,} ({token_analysis['potential_savings'] / token_analysis['total_actual'] * 100:.1f}%)")
            lines.append("")
            
            if token_analysis.get("inefficiencies"):
                lines.append("### 효율이 낮은 작업 타입:")
                for ineff in token_analysis["inefficiencies"]:
                    lines.append(f"  - {ineff['work_type']}: {ineff['efficiency']:.1f}% ({ineff['waste']:,} 토큰 낭비)")
                lines.append("")
        
        bottleneck_analysis = analysis["bottleneck_analysis"]
        if bottleneck_analysis:
            lines.append("## 병목 현상 분석")
            for bn in bottleneck_analysis:
                lines.append(f"  [{bn['severity'].upper()}] {bn['agent_type']}")
                lines.append(f"    {bn['description']}")
                lines.append(f"    제안: {bn['recommendation']}")
            lines.append("")
        
        recommendations = analysis["recommendations"]
        if recommendations:
            lines.append("## 개선 제안")
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"  {i}. [{rec['priority'].upper()}] {rec['title']}")
                lines.append(f"     {rec['description']}")
                lines.append(f"     예상 효과: {rec['expected_benefit']}")
                lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    async def save_final_analysis(self, analysis: Dict[str, Any]):
        await self._save_all_data()
        
        final_report = {
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "report": self.format_final_report(analysis)
        }
        
        await self._save_to_filesystem(f"toc_final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", final_report)
    
    async def generate_improved_recommendations(self, completed_works: List[Work]) -> List[Dict[str, Any]]:
        comparison = await self.compare_with_baselines()
        
        recommendations = []
        
        if comparison.get("status") == "success":
            baseline_comparison = comparison
            
            for improvement in baseline_comparison.get("improvements", []):
                recommendations.append({
                    "priority": "high",
                    "category": "trend_improvement",
                    "title": f"{improvement['metric']} 개선됨",
                    "description": f"기준 대비 {improvement['change_pct']:.1f}% 개선",
                    "actions": [
                        "현재 방식 유지",
                        "개선 요인 추가 분석",
                        "유사 작업에 적용"
                    ],
                    "expected_benefit": f"{improvement['metric']} 개선 유지"
                })
            
            for degradation in baseline_comparison.get("degradations", []):
                recommendations.append({
                    "priority": "high",
                    "category": "trend_degradation",
                    "title": f"{degradation['metric']} 저하",
                    "description": f"기준 대비 {degradation['change_pct']:.1f}% 저하",
                    "actions": [
                        "저하 원인 분석",
                        "이전 설정으로 롤백 검토",
                        "문제 해결 후 재최적화"
                    ],
                    "expected_benefit": f"{degradation['metric']} 원래 수준 복원"
                })
        
        analysis = await self.generate_final_analysis(completed_works)
        for rec in analysis.get("recommendations", []):
            recommendations.append(rec)
        
        return recommendations
    
    def _bottleneck_to_dict(self, bottleneck: BottleneckAnalysis) -> Dict[str, Any]:
        return {
            "bottleneck_id": bottleneck.bottleneck_id,
            "type": bottleneck.bottleneck_type.value,
            "severity": bottleneck.severity,
            "root_cause": bottleneck.root_cause,
            "recommendations": bottleneck.recommendations,
            "estimated_impact": bottleneck.estimated_impact,
            "resolved": bottleneck.resolved_at is not None,
            "resolution": bottleneck.resolution_applied
        }
    
    def update_config(self, config: Dict[str, Any]):
        self._config.update(config)
    
    def get_config(self) -> Dict[str, Any]:
        return self._config.copy()
    
    def set_mcp_sessions(self, memory_session=None, filesystem_session=None):
        self._memory_storage = memory_session
        self._filesystem_storage = filesystem_session
    
    def set_storage_path(self, path: str):
        self._storage_path = path
    
    async def _save_to_memory(self, key: str, data: Dict[str, Any]):
        if self._memory_storage is None:
            return
        
        try:
            await self._memory_storage.call_tool(
                "memory_store",
                arguments={
                    "key": key,
                    "value": data
                }
            )
        except Exception as e:
            print(f"Warning: Failed to save to memory: {e}")
    
    async def _load_from_memory(self, key: str) -> Optional[Dict[str, Any]]:
        if self._memory_storage is None:
            return None
        
        try:
            result = await self._memory_storage.call_tool(
                "memory_retrieve",
                arguments={"key": key}
            )
            if result and result.strip():
                import json
                return json.loads(result)
        except Exception as e:
            print(f"Warning: Failed to load from memory: {e}")
        
        return None
    
    async def _save_to_filesystem(self, filename: str, data: Dict[str, Any]):
        if self._filesystem_storage is None:
            return
        
        import json
        
        try:
            from pathlib import Path
            
            if self._storage_path:
                save_path = Path(self._storage_path) / filename
            else:
                save_path = Path.home() / ".agents_toc" / filename
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            await self._filesystem_storage.call_tool(
                "write_file",
                arguments={
                    "path": str(save_path),
                    "content": json.dumps(data, indent=2, ensure_ascii=False)
                }
            )
        except Exception as e:
            print(f"Warning: Failed to save to filesystem: {e}")
    
    async def _save_baselines(self):
        metrics = self.calculate_throughput()
        
        baselines = {
            "updated_at": datetime.now().isoformat(),
            "throughput": {
                "works_per_hour": metrics.works_per_hour,
                "tokens_per_work": metrics.tokens_per_work,
                "average_work_duration": metrics.average_work_duration,
                "success_rate": metrics.works_completed / (metrics.works_completed + metrics.works_failed)
                    if (metrics.works_completed + metrics.works_failed) > 0 else 1.0
            },
            "by_agent_type": metrics.by_agent_type,
            "by_work_type": metrics.by_work_type
        }
        
        await self._save_to_memory("toc_baselines", baselines)
        await self._save_to_filesystem("toc_baselines.json", baselines)
        
        self._baseline_metrics = baselines
    
    async def _save_bottleneck_history(self):
        history = {
            "updated_at": datetime.now().isoformat(),
            "total_bottlenecks": len(self._bottlenecks),
            "active_bottlenecks": len([b for b in self._bottlenecks if not b.resolved_at]),
            "resolved_bottlenecks": len([b for b in self._bottlenecks if b.resolved_at]),
            "bottlenecks": [
                {
                    "bottleneck_id": b.bottleneck_id,
                    "type": b.bottleneck_type.value,
                    "severity": b.severity,
                    "root_cause": b.root_cause,
                    "detected_at": b.detected_at.isoformat() if b.detected_at else None,
                    "resolved_at": b.resolved_at.isoformat() if b.resolved_at else None,
                    "resolution": b.resolution_applied
                }
                for b in self._bottlenecks[-50:]
            ]
        }
        
        await self._save_to_memory("toc_bottleneck_history", history)
        await self._save_to_filesystem("toc_bottleneck_history.json", history)
    
    async def _save_optimization_log(self):
        log = {
            "updated_at": datetime.now().isoformat(),
            "total_optimizations": len(self._optimization_log),
            "recent_optimizations": self._optimization_log[-20:]
        }
        
        await self._save_to_memory("toc_optimization_log", log)
        await self._save_to_filesystem("toc_optimization_log.json", log)
    
    async def _save_work_history(self):
        history = {
            "updated_at": datetime.now().isoformat(),
            "total_completed": len(self._completed_works),
            "recent_works": self._completed_works[-100:]
        }
        
        await self._save_to_memory("toc_work_history", history)
        await self._save_to_filesystem("toc_work_history.json", history)
    
    async def _save_all_data(self):
        await asyncio.gather(
            self._save_baselines(),
            self._save_bottleneck_history(),
            self._save_optimization_log(),
            self._save_work_history()
        )
    
    async def load_saved_data(self):
        baselines = await self._load_from_memory("toc_baselines")
        if baselines:
            self._baseline_metrics = baselines
        
        print(f"Loaded baselines from memory: {baselines is not None}")
    
    async def compare_with_baselines(self) -> Dict[str, Any]:
        if self._baseline_metrics is None:
            return {"status": "no_baselines"}
        
        current_metrics = self.calculate_throughput()
        
        comparison = {
            "status": "success",
            "updated_at": datetime.now().isoformat(),
            "improvements": [],
            "degradations": [],
            "stable": []
        }
        
        baseline_tp = self._baseline_metrics.get("throughput", {})
        current_tp = {
            "works_per_hour": current_metrics.works_per_hour,
            "tokens_per_work": current_metrics.tokens_per_work,
            "average_work_duration": current_metrics.average_work_duration,
            "success_rate": current_metrics.works_completed / (current_metrics.works_completed + current_metrics.works_failed)
                if (current_metrics.works_completed + current_metrics.works_failed) > 0 else 1.0
        }
        
        metrics_to_compare = [
            ("works_per_hour", "works_per_hour", "high", "Works per Hour"),
            ("tokens_per_work", "tokens_per_work", "low", "Tokens per Work"),
            ("average_work_duration", "average_work_duration", "low", "Average Duration"),
            ("success_rate", "success_rate", "high", "Success Rate")
        ]
        
        for current_key, baseline_key, direction, name in metrics_to_compare:
            current_value = current_tp.get(current_key)
            baseline_value = baseline_tp.get(baseline_key)
            
            if current_value is None or baseline_value is None or baseline_value == 0:
                continue
            
            change_pct = ((current_value - baseline_value) / baseline_value) * 100
            
            if direction == "high" and change_pct > 5:
                comparison["improvements"].append({
                    "metric": name,
                    "baseline": baseline_value,
                    "current": current_value,
                    "change_pct": change_pct
                })
            elif direction == "low" and change_pct < -5:
                comparison["improvements"].append({
                    "metric": name,
                    "baseline": baseline_value,
                    "current": current_value,
                    "change_pct": change_pct
                })
            elif direction == "high" and change_pct < -5:
                comparison["degradations"].append({
                    "metric": name,
                    "baseline": baseline_value,
                    "current": current_value,
                    "change_pct": change_pct
                })
            elif direction == "low" and change_pct > 5:
                comparison["degradations"].append({
                    "metric": name,
                    "baseline": baseline_value,
                    "current": current_value,
                    "change_pct": change_pct
                })
            elif abs(change_pct) < 5:
                comparison["stable"].append({
                    "metric": name,
                    "baseline": baseline_value,
                    "current": current_value,
                    "change_pct": change_pct
                })
        
        return comparison
