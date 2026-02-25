import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from .. import expand_config_paths, AGENT_DIR, HOME_DIR

sys.path.insert(0, str(AGENT_DIR.parent))
from agent_factory.core import (
    Work, WorkStatus, WorkPriority, WorkResult, WorkQueue,
    AgentPool, AgentInstance, AgentStatus,
    TOCSupervisor, BottleneckAnalysis, BottleneckType, ThroughputMetrics
)


class TOCSupervisorAgent:
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.toc_supervisor = None
        self._agent_pool = None
        self._work_queue = None
        self._raci = None
    
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
    
    async def initialize_supervisor(self, agent_pool, work_queue, raci):
        self._agent_pool = agent_pool
        self._work_queue = work_queue
        self._raci = raci
        
        self.toc_supervisor = TOCSupervisor(
            agent_pool=agent_pool,
            work_queue=work_queue,
            raci=raci
        )
    
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
    print("Available commands: analyze, optimize, report, monitor")
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
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
    
    await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
