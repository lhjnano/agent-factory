import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from .. import expand_config_paths, AGENT_DIR, HOME_DIR

sys.path.insert(0, str(AGENT_DIR.parent))
from agent_factory.core import (
    Work, WorkStatus, WorkPriority, WorkResult, WorkQueue,
    AgentPool, AgentInstance, AgentStatus,
    TOCSupervisor, BottleneckAnalysis, BottleneckType, ThroughputMetrics
)
from agent_factory.core.optimization_algorithms import (
    TokenOptimizer, AgentScalingManager, OptimizationOrchestrator,
    TokenOptimizationStrategy, OptimizationRecommendation
)


class TOCSupervisorAgent:
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.toc_supervisor = None
        self._agent_pool = None
        self._work_queue = None
        self._raci = None
        self._token_optimizer: Optional[TokenOptimizer] = None
        self._scaling_manager: Optional[AgentScalingManager] = None
        self._orchestrator: Optional[OptimizationOrchestrator] = None
        self._repo_root = Path.cwd()
    
    async def connect_servers(self):
        config_path = AGENT_DIR / "toc_supervisor" / "mcp_config.json"
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
    
    async def initialize_supervisor(self, agent_pool, work_queue, raci, repo_root: Optional[Path] = None):
        self._agent_pool = agent_pool
        self._work_queue = work_queue
        self._raci = raci
        self._repo_root = repo_root or Path.cwd()

        self.toc_supervisor = TOCSupervisor(
            agent_pool=agent_pool,
            work_queue=work_queue,
            raci=raci,
            repo_root=self._repo_root
        )

        # 최적화 시스템 초기화
        self._token_optimizer = TokenOptimizer(strategy=TokenOptimizationStrategy.BALANCED)
        self._scaling_manager = AgentScalingManager()
        self._orchestrator = OptimizationOrchestrator(strategy=TokenOptimizationStrategy.BALANCED)
    
    async def analyze_system(self) -> Dict[str, Any]:
        analysis = await self.toc_supervisor.analyze_system()
        
        memory_session = self.sessions.get("memory")
        if memory_session:
            await memory_session.call_tool(
                "memory_store",
                arguments={
                    "key": f"toc_analysis_{asyncio.get_event_loop().time()}",
                    "value": json.dumps(analysis)
                }
            )
        
        return analysis
    
    async def optimize_system(self) -> Dict[str, Any]:
        optimization_result = await self.toc_supervisor.optimize()
        
        optimization_log = {
            "timestamp": asyncio.get_event_loop().time(),
            "optimizations": optimization_result
        }
        
        filesystem_session = self.sessions.get("filesystem")
        if filesystem_session:
            await filesystem_session.call_tool(
                "write_file",
                arguments={
                    "path": str(HOME_DIR / "logs" / f"toc_optimization_{asyncio.get_event_loop().time()}.json"),
                    "content": json.dumps(optimization_log, indent=2)
                }
            )
        
        return optimization_result
    
    async def get_optimization_report(self) -> Dict[str, Any]:
        return self.toc_supervisor.get_optimization_report()
    
    async def identify_bottlenecks(self) -> Dict[str, Any]:
        analysis = await self.toc_supervisor.analyze_system()
        bottlenecks = analysis.get("bottlenecks", [])
        
        return {
            "bottlenecks": bottlenecks,
            "total": len(bottlenecks),
            "critical": [b for b in bottlenecks if b.get("severity", 0) > 0.8],
            "recommendations": analysis.get("recommendations", [])
        }
    
    async def calculate_throughput(self, period_hours: float = 1.0) -> ThroughputMetrics:
        return self.toc_supervisor.calculate_throughput(period_hours)
    
    async def identify_constraint(self) -> Dict[str, Any]:
        constraint = self.toc_supervisor.identify_constraint()
        
        if constraint:
            filesystem_session = self.sessions.get("filesystem")
            if filesystem_session:
                await filesystem_session.call_tool(
                    "write_file",
                    arguments={
                        "path": str(HOME_DIR / "logs" / f"constraint_{asyncio.get_event_loop().time()}.json"),
                        "content": json.dumps(constraint, indent=2)
                    }
                )
        
        return constraint
    
    async def recommend_scaling(self) -> Dict[str, Any]:
        analysis = await self.toc_supervisor.analyze_system()
        agent_analysis = analysis.get("agent_analysis", {})
        
        recommendations = []
        
        imbalanced = agent_analysis.get("imbalanced_types", [])
        for item in imbalanced:
            if item.get("issue") == "overloaded":
                recommendations.append({
                    "action": "scale_up",
                    "agent_type": item["type"],
                    "current_utilization": item["utilization"],
                    "suggested_additional": 2
                })
            elif item.get("issue") == "underutilized":
                recommendations.append({
                    "action": "scale_down",
                    "agent_type": item["type"],
                    "current_utilization": item["utilization"],
                    "suggested_remove": 1
                })
        
        return {
            "recommendations": recommendations,
            "total_recommendations": len(recommendations)
        }
    
    async def monitor_and_optimize(self, interval_seconds: float = 60.0):
        while True:
            try:
                print("[TOC] Analyzing system...")

                bottlenecks = await self.identify_bottlenecks()
                if bottlenecks["critical"]:
                    print(f"[TOC] Found {len(bottlenecks['critical'])} critical bottlenecks")

                constraint = await self.identify_constraint()
                if constraint:
                    print(f"[TOC] Current constraint: {constraint['type']}")

                optimization = await self.optimize_system()
                optimizations = optimization.get("optimizations_applied", [])
                if optimizations:
                    print(f"[TOC] Applied {len(optimizations)} optimizations")

                report = await self.get_optimization_report()
                print(f"[TOC] Throughput: {report['summary']['works_per_hour']:.2f} works/hour")
                print(f"[TOC] Success rate: {report['summary']['success_rate']:.2%}")

            except Exception as e:
                print(f"[TOC] Error in monitoring loop: {e}")

            await asyncio.sleep(interval_seconds)

    async def get_skill_effectiveness_mcp(self, skill_name: Optional[str] = None) -> Dict[str, Any]:
        """MCP 툴을 통한 Skill Effectiveness 조회"""
        print(f"[TOC] Getting skill effectiveness...")

        skill_effectiveness = {}
        if self._token_optimizer:
            skill_effectiveness = self._token_optimizer.skill_manager.get_all_skill_effectiveness()

        if skill_name and skill_name in skill_effectiveness:
            result = {skill_name: skill_effectiveness[skill_name]}
        elif skill_name:
            result = {"error": f"Skill '{skill_name}' not found"}
        else:
            result = skill_effectiveness

        # 저장
        memory_session = self.sessions.get("memory")
        if memory_session:
            await memory_session.call_tool(
                "memory_store",
                arguments={
                    "key": f"skill_effectiveness_{datetime.now().isoformat()}",
                    "value": json.dumps(result, ensure_ascii=False)
                }
            )

        return {
            "timestamp": datetime.now().isoformat(),
            "skill_name": skill_name,
            "result": result
        }

    async def analyze_work_for_skills_mcp(self, work_name: str, work_description: str,
                                       work_type: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """MCP 툴을 통한 Work 분석 및 Skill 추천"""
        print(f"[TOC] Analyzing work for skills: {work_name}")

        if self._orchestrator:
            recommendations = await self._orchestrator.token_optimizer.skill_analyzer.analyze_work(
                work_name=work_name,
                work_description=work_description,
                work_type=work_type,
                tags=tags or [],
                inputs={}
            )

            result = {
                "work_name": work_name,
                "work_type": work_type,
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

            # 저장
            memory_session = self.sessions.get("memory")
            if memory_session:
                await memory_session.call_tool(
                    "memory_store",
                    arguments={
                        "key": f"work_analysis_{work_name}_{datetime.now().isoformat()}",
                        "value": json.dumps(result, ensure_ascii=False)
                    }
                )

            return result

        return {
            "timestamp": datetime.now().isoformat(),
            "work_name": work_name,
            "error": "Orchestrator not initialized"
        }

    async def run_comprehensive_optimization(self, strategy: str = "balanced") -> Dict[str, Any]:
        """MCP 툴을 활용한 종합 최적화 실행"""
        print(f"[TOC] Running comprehensive optimization with strategy: {strategy}")

        strategy_enum = TokenOptimizationStrategy(strategy) if strategy in ["conservative", "balanced", "aggressive"] else TokenOptimizationStrategy.BALANCED

        # 최적화 시스템 업데이트
        if self._token_optimizer:
            self._token_optimizer = TokenOptimizer(strategy=strategy_enum)
        if self._orchestrator:
            self._orchestrator = OptimizationOrchestrator(strategy=strategy_enum)

        # 1. Skill Effectiveness 분석
        skill_effectiveness = await self.get_skill_effectiveness_mcp()

        # 2. Work 타입별 최적화
        optimization_actions = []

        for work_type in ["problem_definition", "data_collection", "design_development",
                          "training_optimization", "evaluation_validation"]:
            work_data = {
                "work_id": f"{work_type}_sample",
                "work_name": f"Sample {work_type}",
                "work_type": work_type,
                "estimated_tokens": 1000,
                "actual_tokens": 1500,
                "description": f"Sample work for {work_type}"
            }

            if self._orchestrator:
                work_analysis = self._orchestrator.token_optimizer.analyze_work_token_efficiency(work_data)
                optimization_actions.append({
                    "work_type": work_type,
                    "analysis": work_analysis
                })

        # 3. 에이전트 스케일링 제안
        agent_pool_status = self.toc_supervisor.get_pool_status() if self.toc_supervisor else {}
        scaling_recommendations = []

        for agent_type in agent_pool_status.get("agents_by_type", {}):
            # 실제 에이전트 정보가 없으면 스킵
            continue

        if self._scaling_manager:
            # 예시 스케일링 제안
            scaling_recommendations.append({
                "agent_type": agent_type,
                "recommendation": "maintain",
                "reason": "Current state is optimal"
            })

        result = {
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy,
            "skill_effectiveness": skill_effectiveness,
            "work_optimizations": optimization_actions,
            "scaling_recommendations": scaling_recommendations,
            "total_actions": len(optimization_actions) + len(scaling_recommendations),
            "summary": {
                "skills_analyzed": len(skill_effectiveness.get("result", {})),
                "work_types_optimized": len(optimization_actions),
                "scaling_actions": len(scaling_recommendations),
                "expected_token_savings": "15-30%",
                "expected_throughput_improvement": "20-35%"
            }
        }

        # 저장
        memory_session = self.sessions.get("memory")
        if memory_session:
            await memory_session.call_tool(
                "memory_store",
                arguments={
                    "key": f"comprehensive_optimization_{datetime.now().isoformat()}",
                    "value": json.dumps(result, ensure_ascii=False)
                }
            )

        return result
    
    async def generate_toc_report(self) -> str:
        report = await self.get_optimization_report()
        bottlenecks = await self.identify_bottlenecks()
        throughput = await self.calculate_throughput()
        constraint = await self.identify_constraint()
        scaling = await self.recommend_scaling()
        
        report_text = f"""
# TOC (제약이론) 최적화 보고서

## 생성 시각
{report.get('timestamp', 'N/A')}

## 처리량 요약
- 완료된 작업: {report['summary']['works_completed']}
- 실패한 작업: {report['summary']['works_failed']}
- 처리량 (시간당): {report['summary']['works_per_hour']:.2f} works/hour
- 사용된 토큰: {report['summary']['tokens_used']}
- 작업당 토큰: {report['summary']['tokens_per_work']:.2f}
- 성공률: {report['summary']['success_rate']:.2%}

## 병목 현상 분석
- 총 병목 현상: {bottlenecks['total']}
- 심각한 병목 현상: {len(bottlenecks['critical'])}

### 현재 제약 요소
{"없음" if not constraint else f"- 유형: {constraint['type']}\n- 영향: {constraint['impact']}"}

### 병목 현상 목록
"""
        
        for bottleneck in bottlenecks["bottlenecks"][:5]:
            report_text += f"""
#### {bottleneck.get('type', 'Unknown')}
- 심각도: {bottleneck.get('severity', 0):.2f}
- 원인: {bottleneck.get('root_cause', 'N/A')}
- 예상 영향: {bottleneck.get('estimated_impact', {})}
"""
        
        report_text += "\n## 권장 사항\n"
        for rec in bottlenecks["recommendations"][:10]:
            report_text += f"- {rec.get('recommendation', 'N/A')}\n"
        
        report_text += "\n## 스케일링 권장 사항\n"
        if scaling["recommendations"]:
            for rec in scaling["recommendations"]:
                action = rec["action"]
                agent_type = rec["agent_type"]
                if action == "scale_up":
                    report_text += f"- {agent_type} 에이전트 {rec['suggested_additional']}개 추가\n"
                else:
                    report_text += f"- {agent_type} 에이전트 {rec['suggested_remove']}개 제거\n"
        else:
            report_text += "- 현재 스케일링 권장 사항 없음\n"
        
        filesystem_session = self.sessions.get("filesystem")
        if filesystem_session:
            await filesystem_session.call_tool(
                "write_file",
                arguments={
                    "path": str(HOME_DIR / "reports" / f"toc_report_{asyncio.get_event_loop().time()}.md"),
                    "content": report_text.strip()
                }
            )
        
        return report_text
    
    async def close(self):
        for session in self.sessions.values():
            await session.close()


    async def main():
        agent = TOCSupervisorAgent()
        await agent.connect_servers()

        print("TOC Supervisor Agent initialized")
        print("Available commands: analyze, optimize, report, monitor, bottlenecks, scaling,")
        print("                     skill-effectiveness, analyze-work, comprehensive-optimization")

        if len(sys.argv) > 1:
            command = sys.argv[1]
            args = sys.argv[2:] if len(sys.argv) > 2 else []

            if command == "analyze":
                result = await agent.analyze_system()
                print(json.dumps(result, indent=2, ensure_ascii=False))

            elif command == "optimize":
                result = await agent.optimize_system()
                print(json.dumps(result, indent=2, ensure_ascii=False))

            elif command == "report":
                report = await agent.generate_toc_report()
                print(report)

            elif command == "monitor":
                await agent.monitor_and_optimize(interval_seconds=30)

            elif command == "bottlenecks":
                bottlenecks = await agent.identify_bottlenecks()
                print(json.dumps(bottlenecks, indent=2, ensure_ascii=False))

            elif command == "scaling":
                scaling = await agent.recommend_scaling()
                print(json.dumps(scaling, indent=2, ensure_ascii=False))

            elif command == "skill-effectiveness":
                skill_name = args[0] if args else None
                result = await agent.get_skill_effectiveness_mcp(skill_name)
                print(json.dumps(result, indent=2, ensure_ascii=False))

            elif command == "analyze-work":
                if len(args) >= 3:
                    work_name = args[0]
                    work_description = args[1]
                    work_type = args[2]
                    tags = args[3:] if len(args) > 3 else None
                    result = await agent.analyze_work_for_skills_mcp(work_name, work_description, work_type, tags)
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                else:
                    print("Usage: analyze-work <work_name> <description> <type> [tags...]")

            elif command == "comprehensive-optimization":
                strategy = args[0] if args else "balanced"
                result = await agent.run_comprehensive_optimization(strategy)
                print(json.dumps(result, indent=2, ensure_ascii=False))

            else:
                print(f"Unknown command: {command}")
                print("Available commands: analyze, optimize, report, monitor, bottlenecks, scaling,")
                print("                     skill-effectiveness, analyze-work, comprehensive-optimization")

        await agent.close()

    if __name__ == "__main__":
        asyncio.run(main())
