import pytest
from datetime import datetime

from agent_factory.core.scheduler import (
    BaseScheduler,
    SchedulingStrategy,
    SJFScheduler,
    TokenAwareScheduler,
    DependencyAwareScheduler,
    CompositeScheduler,
    SchedulerConfig,
)
from agent_factory.core.work import Work, WorkPriority, WorkStatus
from agent_factory.core.agent_pool import AgentInstance, AgentStatus


def create_test_work(
    work_id: str = "test_1",
    name: str = "Test Work",
    priority: WorkPriority = WorkPriority.MEDIUM,
    work_type: str = "data_collection",
    agent_type: str = "data_collection",
    dependencies: list = None,
    estimated_duration_seconds: float = 60.0,
    estimated_tokens: int = 1000,
) -> Work:
    return Work(
        work_id=work_id,
        name=name,
        description="Test work description",
        work_type=work_type,
        agent_type=agent_type,
        priority=priority,
        dependencies=dependencies or [],
        estimated_duration_seconds=estimated_duration_seconds,
        estimated_tokens=estimated_tokens,
    )


def create_test_agent(
    agent_id: str = "agent_1",
    agent_type: str = "data_collection",
    capabilities: list = None,
    status: AgentStatus = AgentStatus.IDLE,
) -> AgentInstance:
    return AgentInstance(
        agent_id=agent_id,
        agent_type=agent_type,
        capabilities=capabilities or [agent_type],
        status=status,
    )


class TestSJFScheduler:
    def test_initialization(self):
        scheduler = SJFScheduler()
        assert scheduler.name == "sjf"
        assert scheduler.config is not None
    
    def test_select_no_works(self):
        scheduler = SJFScheduler()
        agents = [create_test_agent()]
        
        result = scheduler.select([], agents)
        assert result.work is None
        assert result.agent is None
    
    def test_select_no_agents(self):
        scheduler = SJFScheduler()
        works = [create_test_work()]
        
        result = scheduler.select(works, [])
        assert result.work is None
        assert result.agent is None
    
    def test_select_single_work(self):
        scheduler = SJFScheduler()
        works = [create_test_work(work_id="w1", estimated_duration_seconds=30.0)]
        agents = [create_test_agent()]
        
        result = scheduler.select(works, agents)
        assert result.work is not None
        assert result.work.work_id == "w1"
        assert result.agent is not None
    
    def test_select_shortest_first(self):
        scheduler = SJFScheduler()
        works = [
            create_test_work(work_id="w1", estimated_duration_seconds=120.0),
            create_test_work(work_id="w2", estimated_duration_seconds=30.0),
            create_test_work(work_id="w3", estimated_duration_seconds=60.0),
        ]
        agents = [create_test_agent()]
        
        result = scheduler.select(works, agents)
        assert result.work is not None
        assert result.work.work_id == "w2"
    
    def test_priority_influence(self):
        scheduler = SJFScheduler()
        works = [
            create_test_work(work_id="w1", estimated_duration_seconds=30.0, priority=WorkPriority.LOW),
            create_test_work(work_id="w2", estimated_duration_seconds=35.0, priority=WorkPriority.CRITICAL),
        ]
        agents = [create_test_agent()]
        
        result = scheduler.select(works, agents)
        assert result.work is not None
    
    def test_dependencies_blocking(self):
        scheduler = SJFScheduler()
        works = [
            create_test_work(work_id="w1", estimated_duration_seconds=30.0),
            create_test_work(work_id="w2", estimated_duration_seconds=10.0, dependencies=["w1"]),
        ]
        agents = [create_test_agent()]
        
        result = scheduler.select(works, agents, completed_work_ids=set())
        assert result.work is not None
        assert result.work.work_id == "w1"
        
        result = scheduler.select(works, agents, completed_work_ids={"w1"})
        assert result.work is not None
        assert result.work.work_id == "w2"
    
    def test_get_stats(self):
        scheduler = SJFScheduler()
        works = [create_test_work()]
        agents = [create_test_agent()]
        
        scheduler.select(works, agents)
        stats = scheduler.get_stats()
        
        assert stats["name"] == "sjf"
        assert stats["scheduling_count"] == 1
        assert stats["successful_schedules"] == 1


class TestTokenAwareScheduler:
    def test_initialization(self):
        scheduler = TokenAwareScheduler()
        assert scheduler.name == "token_aware"
        assert scheduler.config.token_budget == 1000000
    
    def test_select_within_budget(self):
        scheduler = TokenAwareScheduler()
        works = [create_test_work(work_id="w1", estimated_tokens=5000)]
        agents = [create_test_agent()]
        
        result = scheduler.select(works, agents)
        assert result.work is not None
        assert result.work.work_id == "w1"
    
    def test_budget_tracking(self):
        scheduler = TokenAwareScheduler()
        works = [create_test_work(work_id="w1", estimated_tokens=5000)]
        agents = [create_test_agent()]
        
        result = scheduler.select(works, agents)
        assert result.estimated_tokens == 5000
        
        stats = scheduler.get_token_stats()
        assert stats["reserved"] == 5000
        assert stats["remaining"] == scheduler.config.token_budget - 5000
    
    def test_budget_exhausted(self):
        scheduler = TokenAwareScheduler()
        works = [create_test_work(work_id="w1", estimated_tokens=2000000)]
        agents = [create_test_agent()]
        
        result = scheduler.select(works, agents)
        assert result.work is None
        assert "No affordable works" in result.reason
    
    def test_commit_tokens(self):
        scheduler = TokenAwareScheduler()
        works = [create_test_work(work_id="w1", estimated_tokens=5000)]
        agents = [create_test_agent()]
        
        result = scheduler.select(works, agents)
        reserved = result.estimated_tokens
        
        scheduler.commit_tokens(actual_tokens=4500, reserved_tokens=reserved)
        
        stats = scheduler.get_token_stats()
        assert stats["used"] == 4500
        assert stats["reserved"] == 0
    
    def test_reset_budget(self):
        scheduler = TokenAwareScheduler()
        works = [create_test_work(work_id="w1", estimated_tokens=5000)]
        agents = [create_test_agent()]
        
        scheduler.select(works, agents)
        scheduler.commit_tokens(5000, 5000)
        
        scheduler.reset_budget(new_budget=2000000)
        stats = scheduler.get_token_stats()
        assert stats["budget"] == 2000000
        assert stats["used"] == 0


class TestDependencyAwareScheduler:
    def test_initialization(self):
        scheduler = DependencyAwareScheduler()
        assert scheduler.name == "dependency_aware"
    
    def test_select_independent_work(self):
        scheduler = DependencyAwareScheduler()
        works = [create_test_work(work_id="w1")]
        agents = [create_test_agent()]
        
        result = scheduler.select(works, agents)
        assert result.work is not None
        assert result.work.work_id == "w1"
    
    def test_dependency_order(self):
        scheduler = DependencyAwareScheduler()
        works = [
            create_test_work(work_id="w1"),
            create_test_work(work_id="w2", dependencies=["w1"]),
            create_test_work(work_id="w3", dependencies=["w2"]),
        ]
        agents = [create_test_agent()]
        
        # First selection - w1 should be selected
        result = scheduler.select(works, agents, completed_work_ids=set())
        assert result.work.work_id == "w1"
        
        # Mark w1 as completed
        works[0].status = WorkStatus.COMPLETED
        
        # Second selection - w2 should be selected (w1 is COMPLETED)
        result = scheduler.select(works, agents, completed_work_ids={"w1"})
        assert result.work.work_id == "w2"
        
        # Mark w2 as completed
        works[1].status = WorkStatus.COMPLETED
        
        # Third selection - w3 should be selected
        result = scheduler.select(works, agents, completed_work_ids={"w1", "w2"})
        assert result.work.work_id == "w3"
    
    def test_critical_path_priority(self):
        scheduler = DependencyAwareScheduler()
        works = [
            create_test_work(work_id="w1"),
            create_test_work(work_id="w2"),
            create_test_work(work_id="w3", dependencies=["w1"]),
            create_test_work(work_id="w4", dependencies=["w3"]),
        ]
        agents = [create_test_agent()]
        
        result = scheduler.select(works, agents, completed_work_ids=set())
        assert result.work is not None
    
    def test_get_dependency_stats(self):
        scheduler = DependencyAwareScheduler()
        works = [
            create_test_work(work_id="w1"),
            create_test_work(work_id="w2", dependencies=["w1"]),
        ]
        agents = [create_test_agent()]
        
        scheduler.select(works, agents)
        stats = scheduler.get_dependency_stats()
        
        assert stats["total_works"] == 2
        assert stats["works_with_no_dependencies"] == 1
        assert stats["works_with_dependencies"] == 1


class TestCompositeScheduler:
    def test_initialization(self):
        scheduler = CompositeScheduler()
        assert scheduler.name == "composite"
        assert len(scheduler.config.strategies) == 3
    
    def test_select_with_default_config(self):
        scheduler = CompositeScheduler()
        works = [
            create_test_work(work_id="w1", estimated_duration_seconds=30.0),
            create_test_work(work_id="w2", estimated_duration_seconds=60.0),
        ]
        agents = [create_test_agent()]
        
        result = scheduler.select(works, agents)
        assert result.work is not None
        assert result.agent is not None
    
    def test_custom_config(self):
        config = SchedulerConfig(
            strategies=[SchedulingStrategy.SJF],
            weights={SchedulingStrategy.SJF: 1.0},
            token_budget=500000
        )
        scheduler = CompositeScheduler(config=config)
        
        assert len(scheduler.config.strategies) == 1
        assert SchedulingStrategy.SJF in scheduler._schedulers
    
    def test_weight_adjustment(self):
        scheduler = CompositeScheduler()
        
        scheduler.set_weight(SchedulingStrategy.SJF, 0.5)
        
        stats = scheduler.get_composite_stats()
        assert stats["weights"]["sjf"] == 0.5
    
    def test_get_composite_stats(self):
        scheduler = CompositeScheduler()
        works = [create_test_work()]
        agents = [create_test_agent()]
        
        scheduler.select(works, agents)
        stats = scheduler.get_composite_stats()
        
        assert "strategies" in stats
        assert "weights" in stats
        assert "schedulers" in stats


class TestBaseSchedulerInterface:
    def test_estimate_duration(self):
        scheduler = SJFScheduler()
        work = create_test_work(estimated_duration_seconds=120.0)
        
        duration = scheduler.estimate_duration(work)
        assert duration == 120.0
    
    def test_estimate_tokens(self):
        scheduler = TokenAwareScheduler()
        work = create_test_work(estimated_tokens=5000)
        
        tokens = scheduler.estimate_tokens(work)
        assert tokens == 5000
    
    def test_stats_tracking(self):
        scheduler = SJFScheduler()
        
        for i in range(5):
            work = create_test_work(work_id=f"w{i}")
            agent = create_test_agent()
            scheduler.select([work], [agent])
        
        stats = scheduler.get_stats()
        assert stats["scheduling_count"] == 5
        assert stats["success_rate"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
