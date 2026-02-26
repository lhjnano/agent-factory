#!/usr/bin/env python3
"""TOC Supervisor Final Report Generator"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from agent_factory.core import (
    Work, WorkStatus, WorkPriority, WorkResult,
    AgentPool, AgentInstance, WorkQueue,
    RACI, TOCSupervisor, SkillManager
)

class MockWork(Work):
    def __init__(self, work_id, name, work_type, status=WorkStatus.COMPLETED,
                 estimated_tokens=1000, actual_tokens=1200, duration_seconds=300,
                 required_skills=None):
        super().__init__(
            work_id=work_id,
            name=name,
            description=f"Description for {name}",
            work_type=work_type,
            agent_type=work_type,
            status=status,
            estimated_tokens=estimated_tokens,
            actual_tokens=actual_tokens,
            timeout_seconds=300.0,
            required_skills=required_skills or []
        )
        self._duration_seconds = duration_seconds

    @property
    def duration_seconds(self):
        return self._duration_seconds

async def generate_toc_final_report():
    print("=" * 80)
    print("TOC SUPERVISOR 최종 분석 보고서")
    print("=" * 80)
    print(f"\n생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"버전: agent-factory-v2.0 (Skill 시스템 포함)")

    agent_pool = AgentPool()
    skill_manager = SkillManager(repo_root=Path.cwd() / ".agent")

    for i in range(5):
        agent = AgentInstance(
            agent_id=f"agent_{i+1}",
            agent_type=["problem_definition", "data_collection", "design_development",
                     "training_optimization", "evaluation_validation"][i],
            capabilities=[f"capability_{j}" for j in range(3)],
            completed_works=10 + i * 2,
            failed_works=i,
            total_tokens_used=5000 + i * 1000,
            total_work_time_seconds=1800 + i * 300
        )
        agent.skills = ["toc-supervisor-skill"]
        agent_pool.register_agent(agent)

    works = [
        MockWork("work_001", "Define Problem", "problem_definition",
                 actual_tokens=1200, duration_seconds=300,
                 required_skills=["problem-definition-skill"]),
        MockWork("work_002", "Collect Data", "data_collection",
                 actual_tokens=2500, duration_seconds=600,
                 required_skills=["data-collection-skill"]),
        MockWork("work_003", "Design Architecture", "design_development",
                 actual_tokens=2000, duration_seconds=500,
                 required_skills=["design-development-skill"]),
    ]

    for work in works:
        for skill_name in work.required_skills:
            skill_manager.record_skill_usage(
                skill_name=skill_name,
                success=0.95,
                tokens_used=work.actual_tokens // len(work.required_skills) if work.required_skills else work.actual_tokens,
                duration_seconds=work.duration_seconds
            )

    raci = RACI()
    work_queue = WorkQueue()
    toc = TOCSupervisor(agent_pool=agent_pool, work_queue=work_queue, raci=raci)

    analysis = await toc.generate_final_analysis(works)

    print("\n" + "=" * 80)
    print("✅ 보고서 생성 완료")
    print("=" * 80)
    print("\n📊 핵심 요약:")
    work_summary = analysis["work_summary"]
    print(f"  • Work 성공률: {work_summary['success_rate']*100:.1f}%")

    skill_analysis = analysis["skill_effectiveness_analysis"]
    print(f"  • Skill 추천사항: {len(skill_analysis.get('skill_recommendations', []))}개")

    print("\n📁 보고서 저장: ~/toc_final_report.json")
    with open(Path.home() / "toc_final_report.json", "w") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    asyncio.run(generate_toc_final_report())
