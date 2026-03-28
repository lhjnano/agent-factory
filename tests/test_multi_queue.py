import pytest
import asyncio
from datetime import datetime

from agent_factory.core.work import Work, WorkPriority, WorkStatus
from agent_factory.core.queue import (
    BaseQueue,
    PriorityQueue,
    PriorityLevel,
    TypeQueue,
    MultiQueueManager,
    QueueStrategy,
)


def create_test_work(
    work_id: str = "test_1",
    name: str = "Test Work",
    priority: WorkPriority = WorkPriority.MEDIUM,
    work_type: str = "data_collection",
    agent_type: str = "data_collection",
    dependencies: list = None
) -> Work:
    return Work(
        work_id=work_id,
        name=name,
        description="Test work description",
        work_type=work_type,
        agent_type=agent_type,
        priority=priority,
        dependencies=dependencies or [],
    )


class TestPriorityQueue:
    @pytest.mark.asyncio
    async def test_enqueue_dequeue(self):
        queue = PriorityQueue()
        work = create_test_work(priority=WorkPriority.HIGH)
        
        work_id = await queue.enqueue(work)
        assert work_id == work.work_id
        
        dequeued = await queue.dequeue([work.agent_type], set())
        assert dequeued is not None
        assert dequeued.work_id == work.work_id
    
    @pytest.mark.asyncio
    async def test_priority_order(self):
        queue = PriorityQueue()
        
        low_work = create_test_work(work_id="low", priority=WorkPriority.LOW)
        medium_work = create_test_work(work_id="medium", priority=WorkPriority.MEDIUM)
        high_work = create_test_work(work_id="high", priority=WorkPriority.HIGH)
        critical_work = create_test_work(work_id="critical", priority=WorkPriority.CRITICAL)
        
        await queue.enqueue(low_work)
        await queue.enqueue(medium_work)
        await queue.enqueue(high_work)
        await queue.enqueue(critical_work)
        
        first = await queue.dequeue([critical_work.agent_type], set())
        assert first.work_id == "critical"
        
        second = await queue.dequeue([high_work.agent_type], set())
        assert second.work_id == "high"
        
        third = await queue.dequeue([medium_work.agent_type], set())
        assert third.work_id == "medium"
        
        fourth = await queue.dequeue([low_work.agent_type], set())
        assert fourth.work_id == "low"
    
    @pytest.mark.asyncio
    async def test_get_pending_count(self):
        queue = PriorityQueue()
        
        assert await queue.get_pending_count() == 0
        
        work1 = create_test_work(work_id="w1")
        work2 = create_test_work(work_id="w2")
        
        await queue.enqueue(work1)
        await queue.enqueue(work2)
        
        assert await queue.get_pending_count() == 2
        
        await queue.dequeue([work1.agent_type], set())
        assert await queue.get_pending_count() == 1
    
    @pytest.mark.asyncio
    async def test_agent_capability_filter(self):
        queue = PriorityQueue()
        
        work1 = create_test_work(work_id="w1", agent_type="type_a")
        work2 = create_test_work(work_id="w2", agent_type="type_b")
        
        await queue.enqueue(work1)
        await queue.enqueue(work2)
        
        dequeued = await queue.dequeue(["type_a"], set())
        assert dequeued is not None
        assert dequeued.agent_type == "type_a"
        
        dequeued = await queue.dequeue(["type_c"], set())
        assert dequeued is None
    
    @pytest.mark.asyncio
    async def test_dependencies(self):
        queue = PriorityQueue()
        
        work1 = create_test_work(work_id="w1", agent_type="type_a")
        work2 = create_test_work(work_id="w2", agent_type="type_b", dependencies=["w1"])
        
        await queue.enqueue(work1)
        await queue.enqueue(work2)
        
        dequeued = await queue.dequeue(["type_b"], set())
        assert dequeued is None
        
        completed = {"w1"}
        dequeued = await queue.dequeue(["type_b"], completed)
        assert dequeued is not None
        assert dequeued.work_id == "w2"
    
    @pytest.mark.asyncio
    async def test_peek(self):
        queue = PriorityQueue()
        
        assert await queue.peek() is None
        
        work = create_test_work(priority=WorkPriority.HIGH)
        await queue.enqueue(work)
        
        peeked = await queue.peek()
        assert peeked is not None
        assert peeked.work_id == work.work_id
        
        assert await queue.get_pending_count() == 1
    
    @pytest.mark.asyncio
    async def test_remove(self):
        queue = PriorityQueue()
        
        work1 = create_test_work(work_id="w1")
        work2 = create_test_work(work_id="w2")
        
        await queue.enqueue(work1)
        await queue.enqueue(work2)
        
        assert await queue.remove("w1") is True
        assert await queue.get_pending_count() == 1
        
        assert await queue.remove("nonexistent") is False
    
    @pytest.mark.asyncio
    async def test_clear(self):
        queue = PriorityQueue()
        
        for i in range(5):
            await queue.enqueue(create_test_work(work_id=f"w{i}"))
        
        count = await queue.clear()
        assert count == 5
        assert await queue.get_pending_count() == 0
    
    @pytest.mark.asyncio
    async def test_get_count_by_priority(self):
        queue = PriorityQueue()
        
        await queue.enqueue(create_test_work(work_id="c1", priority=WorkPriority.CRITICAL))
        await queue.enqueue(create_test_work(work_id="c2", priority=WorkPriority.CRITICAL))
        await queue.enqueue(create_test_work(work_id="h1", priority=WorkPriority.HIGH))
        await queue.enqueue(create_test_work(work_id="m1", priority=WorkPriority.MEDIUM))
        await queue.enqueue(create_test_work(work_id="l1", priority=WorkPriority.LOW))
        await queue.enqueue(create_test_work(work_id="l2", priority=WorkPriority.LOW))
        
        counts = await queue.get_count_by_priority()
        assert counts[PriorityLevel.CRITICAL] == 2
        assert counts[PriorityLevel.HIGH] == 1
        assert counts[PriorityLevel.MEDIUM] == 1
        assert counts[PriorityLevel.LOW] == 2


class TestTypeQueue:
    @pytest.mark.asyncio
    async def test_enqueue_dequeue(self):
        queue = TypeQueue(work_type="data_collection")
        
        work = create_test_work(work_type="data_collection")
        work_id = await queue.enqueue(work)
        assert work_id == work.work_id
        
        dequeued = await queue.dequeue([work.agent_type], set())
        assert dequeued is not None
        assert dequeued.work_id == work.work_id
    
    @pytest.mark.asyncio
    async def test_max_size(self):
        from agent_factory.core.queue.type_queue import TypeQueueConfig
        
        queue = TypeQueue(
            work_type="data_collection",
            config=TypeQueueConfig(max_size=2)
        )
        
        work1 = create_test_work(work_id="w1")
        work2 = create_test_work(work_id="w2")
        work3 = create_test_work(work_id="w3")
        
        await queue.enqueue(work1)
        await queue.enqueue(work2)
        
        with pytest.raises(ValueError, match="is full"):
            await queue.enqueue(work3)
    
    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        queue = TypeQueue(work_type="data_collection")
        
        low = create_test_work(work_id="low", priority=WorkPriority.LOW, work_type="data_collection")
        high = create_test_work(work_id="high", priority=WorkPriority.HIGH, work_type="data_collection")
        
        await queue.enqueue(low)
        await queue.enqueue(high)
        
        first = await queue.dequeue(["data_collection"], set())
        assert first.work_id == "high"
        
        second = await queue.dequeue(["data_collection"], set())
        assert second.work_id == "low"
    
    @pytest.mark.asyncio
    async def test_utilization(self):
        from agent_factory.core.queue.type_queue import TypeQueueConfig
        
        config = TypeQueueConfig(max_size=10)
        queue = TypeQueue(work_type="test", config=config)
        
        assert queue.get_utilization() == 0.0
        
        for i in range(5):
            await queue.enqueue(create_test_work(work_id=f"w{i}"))
        
        assert queue.get_utilization() == 0.5


class TestMultiQueueManager:
    @pytest.mark.asyncio
    async def test_enqueue_dequeue_priority_first(self):
        manager = MultiQueueManager()
        
        work = create_test_work()
        work_id = await manager.enqueue(work)
        assert work_id == work.work_id
        
        dequeued = await manager.dequeue([work.agent_type], set())
        assert dequeued is not None
        assert dequeued.work_id == work.work_id
    
    @pytest.mark.asyncio
    async def test_strategy_priority_first(self):
        from agent_factory.core.queue.multi_queue import MultiQueueConfig
        
        manager = MultiQueueManager(config=MultiQueueConfig(
            strategy=QueueStrategy.PRIORITY_FIRST,
            enable_type_queues=True,
            priority_queue_weight=0.7,
            type_queue_weight=0.3,
            type_specific_work_types=['data_collection'],
            type_queue_max_size=100
        ))
        
        low = create_test_work(work_id="low", priority=WorkPriority.LOW, work_type="data_collection")
        high = create_test_work(work_id="high", priority=WorkPriority.HIGH, work_type="other")
        
        await manager.enqueue(low)
        await manager.enqueue(high)
        
        first = await manager.dequeue([low.agent_type, high.agent_type], set())
        assert first.work_id == "high"
    
    @pytest.mark.asyncio
    async def test_strategy_type_first(self):
        manager = MultiQueueManager(config=type('Config', (), {
            'strategy': QueueStrategy.TYPE_FIRST,
            'enable_type_queues': True,
            'priority_queue_weight': 0.7,
            'type_queue_weight': 0.3,
            'type_specific_work_types': ['data_collection'],
            'type_queue_max_size': 100
        })())
        
        work = create_test_work(work_type="data_collection")
        await manager.enqueue(work)
        
        dequeued = await manager.dequeue([work.agent_type], set())
        assert dequeued is not None
    
    @pytest.mark.asyncio
    async def test_get_queue_stats(self):
        manager = MultiQueueManager()
        
        for i in range(3):
            await manager.enqueue(create_test_work(
                work_id=f"w{i}",
                work_type="other_type",
                priority=WorkPriority.HIGH if i < 2 else WorkPriority.LOW
            ))
        
        stats = await manager.get_queue_stats()
        assert stats["strategy"] == "priority_first"
        assert stats["priority_queue"]["HIGH"] == 2
        assert stats["priority_queue"]["LOW"] == 1
        assert stats["total_pending"] == 3
    
    @pytest.mark.asyncio
    async def test_get_all_pending(self):
        manager = MultiQueueManager()
        
        work1 = create_test_work(work_id="w1")
        work2 = create_test_work(work_id="w2")
        
        await manager.enqueue(work1)
        await manager.enqueue(work2)
        
        pending = await manager.get_all_pending()
        assert len(pending) == 2
        assert work1.work_id in [w.work_id for w in pending]
        assert work2.work_id in [w.work_id for w in pending]
    
    @pytest.mark.asyncio
    async def test_remove_from_priority_queue(self):
        manager = MultiQueueManager()
        
        work = create_test_work()
        await manager.enqueue(work)
        
        assert await manager.remove(work.work_id) is True
        assert await manager.get_pending_count() == 0
    
    @pytest.mark.asyncio
    async def test_clear(self):
        manager = MultiQueueManager()
        
        for i in range(5):
            await manager.enqueue(create_test_work(work_id=f"w{i}"))
        
        count = await manager.clear()
        assert count == 5
        assert await manager.get_pending_count() == 0
    
    @pytest.mark.asyncio
    async def test_get_work(self):
        manager = MultiQueueManager()
        
        work = create_test_work(work_id="target")
        await manager.enqueue(work)
        
        found = await manager.get_work("target")
        assert found is not None
        assert found.work_id == "target"
        
        not_found = await manager.get_work("nonexistent")
        assert not_found is None
    
    @pytest.mark.asyncio
    async def test_set_strategy(self):
        manager = MultiQueueManager()
        
        manager.set_strategy(QueueStrategy.ROUND_ROBIN)
        assert manager.config.strategy == QueueStrategy.ROUND_ROBIN
        
        manager.set_strategy(QueueStrategy.BALANCED)
        assert manager.config.strategy == QueueStrategy.BALANCED
    
    @pytest.mark.asyncio
    async def test_get_type_queue(self):
        manager = MultiQueueManager()
        
        type_queue = manager.get_type_queue("data_collection")
        assert type_queue is not None
        assert type_queue.work_type == "data_collection"
        
        not_found = manager.get_type_queue("nonexistent_type")
        assert not_found is None
    
    @pytest.mark.asyncio
    async def test_round_robin_strategy(self):
        from agent_factory.core.queue.multi_queue import MultiQueueConfig
        
        manager = MultiQueueManager(config=MultiQueueConfig(
            strategy=QueueStrategy.ROUND_ROBIN,
            enable_type_queues=True,
            priority_queue_weight=0.5,
            type_queue_weight=0.5,
            type_specific_work_types=['data_collection'],
            type_queue_max_size=100
        ))
        
        work1 = create_test_work(work_id="w1", work_type="other")
        work2 = create_test_work(work_id="w2", work_type="data_collection")
        
        await manager.enqueue(work1)
        await manager.enqueue(work2)
        
        dequeued = await manager.dequeue([work1.agent_type, work2.agent_type], set())
        assert dequeued is not None


class TestBackwardCompatibility:
    @pytest.mark.asyncio
    async def test_work_queue_field_exists(self):
        work = create_test_work()
        assert hasattr(work, 'queue_preference')
        assert work.queue_preference == "auto"
    
    @pytest.mark.asyncio
    async def test_work_to_dict_includes_queue_preference(self):
        work = create_test_work()
        d = work.to_dict()
        assert 'queue_preference' in d
        assert d['queue_preference'] == "auto"
    
    @pytest.mark.asyncio
    async def test_base_queue_interface(self):
        from agent_factory.core.queue.base import BaseQueue
        
        assert hasattr(BaseQueue, 'enqueue')
        assert hasattr(BaseQueue, 'dequeue')
        assert hasattr(BaseQueue, 'peek')
        assert hasattr(BaseQueue, 'get_pending_count')
        assert hasattr(BaseQueue, 'get_all_pending')
        assert hasattr(BaseQueue, 'remove')
        assert hasattr(BaseQueue, 'clear')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
