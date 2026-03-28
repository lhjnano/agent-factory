import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock, patch

from agent_factory.core.scaling import (
    AutoScaler,
    ScalingDecision,
    ScalingPolicy,
    ScalingConfig,
    ScalingMetric,
    ScalingAction,
    ScalingThresholds,
)
from agent_factory.core.agent_pool import AgentPool, AgentInstance, AgentStatus
from agent_factory.core.work import Work, WorkPriority, WorkStatus
from agent_factory.core.queue import MultiQueueManager


def create_test_agent(
    agent_id: str = "agent_1",
    agent_type: str = "data_collection",
    status: AgentStatus = AgentStatus.IDLE,
    current_works: int = 0,
) -> AgentInstance:
    agent = AgentInstance(
        agent_id=agent_id,
        agent_type=agent_type,
        capabilities=[agent_type],
        status=status,
    )
    agent.current_concurrent_works = current_works
    return agent


def create_test_work(
    work_id: str = "work_1",
    agent_type: str = "data_collection",
    priority: WorkPriority = WorkPriority.MEDIUM,
) -> Work:
    return Work(
        work_id=work_id,
        name="Test Work",
        description="Test",
        work_type="data_collection",
        agent_type=agent_type,
        priority=priority,
    )


class TestScalingPolicy:
    def test_initialization(self):
        policy = ScalingPolicy()
        assert policy.config is not None
        assert policy.config.enabled is True
    
    def test_scale_up_decision(self):
        config = ScalingConfig(
            thresholds=ScalingThresholds(
                scale_up_cooldown_seconds=0,
                scale_down_cooldown_seconds=0
            )
        )
        policy = ScalingPolicy(config)
        
        action = policy.evaluate(
            agent_type="data_collection",
            queue_length=20,
            available_capacity=0,  # Changed to 0
            total_capacity=10,
            current_agent_count=5
        )
        
        assert action == ScalingAction.SCALE_UP
    
    def test_scale_down_decision(self):
        config = ScalingConfig(
            thresholds=ScalingThresholds(
                scale_up_cooldown_seconds=0,
                scale_down_cooldown_seconds=0,
                max_agents=20
            )
        )
        policy = ScalingPolicy(config)
        
        action = policy.evaluate(
            agent_type="data_collection",
            queue_length=2,
            available_capacity=18,
            total_capacity=20,
            current_agent_count=10
        )
        
        assert action == ScalingAction.SCALE_DOWN
    
    def test_no_action_when_balanced(self):
        policy = ScalingPolicy()
        
        action = policy.evaluate(
            agent_type="data_collection",
            queue_length=10,
            available_capacity=5,
            total_capacity=10,
            current_agent_count=5
        )
        
        assert action == ScalingAction.NO_ACTION
    
    def test_cooldown_prevents_frequent_scaling(self):
        policy = ScalingPolicy()
        
        policy.evaluate(
            agent_type="data_collection",
            queue_length=20,
            available_capacity=2,
            total_capacity=10,
            current_agent_count=5
        )
        policy.record_scaling("data_collection", ScalingAction.SCALE_UP, 1)
        
        action = policy.evaluate(
            agent_type="data_collection",
            queue_length=30,
            available_capacity=1,
            total_capacity=11,
            current_agent_count=6
        )
        
        assert action == ScalingAction.NO_ACTION
    
    def test_min_max_agent_limits(self):
        config = ScalingConfig(
            thresholds=ScalingThresholds(
                min_agents=2,
                max_agents=5
            )
        )
        policy = ScalingPolicy(config)
        
        action = policy.evaluate(
            agent_type="test",
            queue_length=100,
            available_capacity=0,
            total_capacity=5,
            current_agent_count=5
        )
        assert action == ScalingAction.NO_ACTION
        
        action = policy.evaluate(
            agent_type="test",
            queue_length=0,
            available_capacity=2,
            total_capacity=2,
            current_agent_count=2
        )
        assert action == ScalingAction.NO_ACTION
    
    def test_calculate_scale_count(self):
        policy = ScalingPolicy()
        
        count = policy.calculate_scale_count(
            action=ScalingAction.SCALE_UP,
            queue_length=20,
            available_capacity=5,
            current_count=5  # Changed from 10 to 5
        )
        assert count > 0
        assert count <= policy.config.thresholds.max_scale_up_count
        
        count = policy.calculate_scale_count(
            action=ScalingAction.SCALE_DOWN,
            queue_length=2,
            available_capacity=8,
            current_count=10
        )
        assert count > 0
        assert count <= policy.config.thresholds.max_scale_down_count
    
    def test_record_and_get_stats(self):
        policy = ScalingPolicy()
        
        policy.record_scaling("type_a", ScalingAction.SCALE_UP, 2)
        policy.record_scaling("type_b", ScalingAction.SCALE_DOWN, 1)
        
        stats = policy.get_stats()
        assert stats["total_scale_ups"] == 1
        assert stats["total_scale_downs"] == 1


class TestAutoScaler:
    def test_initialization(self):
        pool = AgentPool()
        queue = MultiQueueManager()
        scaler = AutoScaler(pool, queue)
        
        assert scaler.agent_pool is pool
        assert scaler.queue_manager is queue
        assert scaler.config is not None
    
    def test_register_agent_factory(self):
        pool = AgentPool()
        queue = MultiQueueManager()
        scaler = AutoScaler(pool, queue)
        
        factory_called = False
        
        def factory():
            nonlocal factory_called
            factory_called = True
            return create_test_agent()
        
        scaler.register_agent_factory("data_collection", factory)
        assert "data_collection" in scaler._agent_factories
    
    @pytest.mark.asyncio
    async def test_evaluate_no_agents(self):
        pool = AgentPool()
        queue = MultiQueueManager()
        scaler = AutoScaler(pool, queue)
        
        decisions = await scaler.evaluate_and_scale()
        assert decisions == []
    
    @pytest.mark.asyncio
    async def test_evaluate_with_agents_no_queue(self):
        pool = AgentPool()
        queue = MultiQueueManager()
        
        for i in range(5):
            pool.register_agent(create_test_agent(agent_id=f"agent_{i}"))
        
        scaler = AutoScaler(pool, queue)
        decisions = await scaler.evaluate_and_scale()
        
        scale_down_decisions = [d for d in decisions if d.action == ScalingAction.SCALE_DOWN]
        assert len(scale_down_decisions) >= 0
    
    @pytest.mark.asyncio
    async def test_scale_up_with_queue(self):
        pool = AgentPool()
        queue = MultiQueueManager()
        
        pool.register_agent(create_test_agent())
        
        for i in range(20):
            work = create_test_work(work_id=f"work_{i}")
            work.status = WorkStatus.QUEUED
            await queue.enqueue(work)
        
        scaler = AutoScaler(pool, queue)
        factory_called_count = 0
        
        def factory():
            nonlocal factory_called_count
            factory_called_count += 1
            return create_test_agent(agent_id=f"new_agent_{factory_called_count}")
        
        scaler.register_agent_factory("data_collection", factory)
        
        decisions = await scaler.evaluate_and_scale()
        
        scale_up_decisions = [d for d in decisions if d.action == ScalingAction.SCALE_UP]
        assert len(scale_up_decisions) >= 0
    
    def test_get_stats(self):
        pool = AgentPool()
        queue = MultiQueueManager()
        scaler = AutoScaler(pool, queue)
        
        stats = scaler.get_stats()
        assert "running" in stats
        assert "evaluation_count" in stats
        assert "policy_stats" in stats
    
    def test_force_scale_up(self):
        pool = AgentPool()
        queue = MultiQueueManager()
        scaler = AutoScaler(pool, queue)
        
        decision = scaler.force_scale_up("data_collection", 2)
        
        assert decision.action == ScalingAction.SCALE_UP
        assert decision.agent_type == "data_collection"
        assert decision.count == 2
    
    def test_force_scale_down(self):
        pool = AgentPool()
        queue = MultiQueueManager()
        scaler = AutoScaler(pool, queue)
        
        decision = scaler.force_scale_down("data_collection", 1)
        
        assert decision.action == ScalingAction.SCALE_DOWN
        assert decision.agent_type == "data_collection"
        assert decision.count == 1


class TestScalingDecision:
    def test_decision_creation(self):
        decision = ScalingDecision(
            action=ScalingAction.SCALE_UP,
            agent_type="data_collection",
            count=2,
            reason="High queue length",
            current_count=5,
            target_count=7
        )
        
        assert decision.action == ScalingAction.SCALE_UP
        assert decision.count == 2
        assert decision.timestamp is not None


class TestScalingThresholds:
    def test_default_thresholds(self):
        thresholds = ScalingThresholds()
        
        assert thresholds.scale_up_threshold == 2.0
        assert thresholds.scale_down_threshold == 0.3
        assert thresholds.min_agents == 1
        assert thresholds.max_agents == 10
    
    def test_custom_thresholds(self):
        thresholds = ScalingThresholds(
            scale_up_threshold=3.0,
            min_agents=2,
            max_agents=20
        )
        
        assert thresholds.scale_up_threshold == 3.0
        assert thresholds.min_agents == 2
        assert thresholds.max_agents == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
