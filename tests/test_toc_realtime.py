import pytest
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, AsyncMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_factory.core.toc_supervisor import (
    TOCSupervisor,
    BottleneckAnalysis,
    BottleneckType,
    ThroughputMetrics
)


class TestTOCSupervisorBasics:
    @pytest.fixture
    def toc_supervisor(self):
        agent_pool = Mock()
        work_queue = Mock()
        raci = Mock()
        
        agent_pool._agents = {}
        agent_pool._type_index = {}
        agent_pool.get_pool_status.return_value = {"utilization_rate": 0.5}
        agent_pool.get_capacity.return_value = 10
        agent_pool.get_available_capacity.return_value = 5
        
        return TOCSupervisor(agent_pool, work_queue, raci)
    
    def test_init(self, toc_supervisor):
        assert toc_supervisor._config is not None
        assert toc_supervisor._config["bottleneck_threshold"] == 0.7
        assert len(toc_supervisor._bottlenecks) == 0
        assert len(toc_supervisor._throughput_history) == 0
    
    @pytest.mark.asyncio
    async def test_analyze_system(self, toc_supervisor):
        work_queue_mock = AsyncMock()
        work_queue_mock.get_pending_count.return_value = 5
        work_queue_mock.get_blocked_works.return_value = []
        toc_supervisor._work_queue = work_queue_mock
        
        analysis = await toc_supervisor.analyze_system()
        
        assert analysis["timestamp"] is not None
        assert "agent_analysis" in analysis
        assert "work_analysis" in analysis
        assert "bottlenecks" in analysis
        assert "recommendations" in analysis


class TestBottleneckDetection:
    @pytest.fixture
    def toc_supervisor(self):
        agent_pool = Mock()
        work_queue = Mock()
        raci = Mock()
        
        agent_pool._agents = {"agent1": Mock()}
        agent_pool._type_index = {"type1": ["agent1"]}
        agent_pool.get_pool_status.return_value = {}
        agent_pool.get_capacity.return_value = 1
        agent_pool.get_available_capacity.return_value = 0
        
        work_queue_mock = AsyncMock()
        work_queue_mock.get_pending_count.return_value = 10
        work_queue_mock.get_blocked_works.return_value = []
        
        supervisor = TOCSupervisor(agent_pool, work_queue, raci)
        supervisor._work_queue = work_queue_mock
        
        return supervisor
    
    @pytest.mark.asyncio
    async def test_detect_agent_capacity_bottleneck(self, toc_supervisor):
        bottlenecks = await toc_supervisor._detect_bottlenecks()
        
        capacity_bottlenecks = [b for b in bottlenecks if b.bottleneck_type == BottleneckType.AGENT_CAPACITY]
        assert len(capacity_bottlenecks) > 0
        assert capacity_bottlenecks[0].severity > 0.8
    
    @pytest.mark.asyncio
    async def test_detect_token_limit_bottleneck(self, toc_supervisor):
        toc_supervisor._agent_pool.get_pool_status.return_value = {
            "utilization_rate": 0.9,
            "total_tokens_used": 900000,
        }
        
        bottlenecks = await toc_supervisor._detect_bottlenecks()
        
        token_bottlenecks = [b for b in bottlenecks if b.bottleneck_type == BottleneckType.TOKEN_LIMIT]
        assert len(token_bottlenecks) > 0


class TestThroughputCalculation:
    @pytest.fixture
    def toc_supervisor(self):
        agent_pool = Mock()
        work_queue = Mock()
        raci = Mock()
        
        agent1 = Mock()
        agent1.completed_works = 10
        agent1.failed_works = 2
        agent1.total_tokens_used = 1000
        agent1.total_work_time_seconds = 600
        agent1.agent_type = "test"
        
        agent_pool._agents = {"agent1": agent1}
        agent_pool._type_index = {"test": ["agent1"]}
        agent_pool.get_pool_status.return_value = {}
        
        return TOCSupervisor(agent_pool, work_queue, raci)
    
    def test_calculate_throughput(self, toc_supervisor):
        metrics = toc_supervisor.calculate_throughput()
        
        assert metrics is not None
        assert metrics.works_completed == 10
        assert metrics.works_failed == 2
        assert metrics.total_tokens_used == 1000
        assert metrics.total_duration_seconds == 600
        assert metrics.works_per_hour > 0
        assert len(toc_supervisor._throughput_history) == 1
    
    def test_identify_constraint_no_data(self, toc_supervisor):
        constraint = toc_supervisor.identify_constraint()
        assert constraint is None
    
    def test_identify_constraint_with_data(self, toc_supervisor):
        toc_supervisor._throughput_history.append(
            ThroughputMetrics(
                period_start=datetime.now(),
                period_end=datetime.now(),
                works_completed=10,
                works_failed=0,
                total_tokens_used=1000,
                total_duration_seconds=60,
                works_per_hour=10,
                tokens_per_work=100,
                average_work_duration=6,
                by_agent_type={
                    "test": {
                        "completed": 10,
                        "failed": 0,
                        "tokens": 1000,
                        "duration": 100
                    }
                },
                by_work_type={}
            )
        )
        
        toc_supervisor._agent_pool.get_pool_status.return_value = {
            "agents_by_type": {"test": {"available": 0}}
        }
        
        constraint = toc_supervisor.identify_constraint()
        assert constraint is not None


class TestOptimization:
    @pytest.fixture
    def toc_supervisor(self):
        agent_pool = Mock()
        work_queue = Mock()
        raci = Mock()
        
        agent_pool._agents = {}
        agent_pool._type_index = {}
        agent_pool.get_pool_status.return_value = {}
        
        work_queue_mock = AsyncMock()
        work_queue_mock.get_pending_count.return_value = 5
        work_queue_mock.get_blocked_works.return_value = []
        
        supervisor = TOCSupervisor(agent_pool, work_queue, raci)
        supervisor._work_queue = work_queue_mock
        
        return supervisor
    
    @pytest.mark.asyncio
    async def test_optimize_capacity(self, toc_supervisor):
        agent = Mock()
        agent.agent_type = "test_type"
        toc_supervisor._agent_pool.get_agent = Mock(return_value=agent)
        toc_supervisor._agent_pool.get_capacity = Mock(return_value=5)
        
        bottleneck = BottleneckAnalysis(
            bottleneck_id="test",
            bottleneck_type=BottleneckType.AGENT_CAPACITY,
            severity=0.9,
            affected_works=[],
            affected_agents=["agent1"],
            root_cause="Test",
            recommendations=[],
            estimated_impact={},
            detected_at=datetime.now()
        )
        
        result = await toc_supervisor._optimize_capacity(bottleneck)
        
        assert result is not None
        assert result["type"] == "capacity_optimization"
        assert "scale_up" in result["action"]
    
    @pytest.mark.asyncio
    async def test_optimize_with_bottleneck(self, toc_supervisor):
        toc_supervisor._bottlenecks = [
            BottleneckAnalysis(
                bottleneck_id="b1",
                bottleneck_type=BottleneckType.AGENT_CAPACITY,
                severity=0.8,
                affected_works=[],
                affected_agents=["agent1"],
                root_cause="Test",
                recommendations=[],
                estimated_impact={},
                detected_at=datetime.now()
            )
        ]
        
        toc_supervisor._optimize_capacity = AsyncMock(return_value={
            "type": "test",
            "action": "test_action"
        })
        toc_supervisor._optimize_dependencies = AsyncMock(return_value=None)
        
        result = await toc_supervisor.optimize()
        
        assert "analysis" in result
        assert "optimizations_applied" in result
        assert "total_optimizations" in result


class TestStatistics:
    @pytest.fixture
    def toc_supervisor(self):
        agent_pool = Mock()
        work_queue = Mock()
        raci = Mock()
        agent_pool._agents = {}
        agent_pool._type_index = {}
        
        return TOCSupervisor(agent_pool, work_queue, raci)
    
    def test_get_work_agent_statistics_all_works(self, toc_supervisor):
        toc_supervisor._work_agent_history = {
            "work1": [{
                "agent_id": "agent1",
                "agent_type": "type1",
                "work_type": "type1",
                "tokens_used": 100,
                "duration_seconds": 5,
                "status": "completed"
            }]
        }
        
        stats = toc_supervisor.get_work_agent_statistics()
        
        assert stats is not None
        assert "summary" in stats
        assert "by_work" in stats
        assert "by_agent_type" in stats
    
    def test_get_optimization_report(self, toc_supervisor):
        toc_supervisor.calculate_throughput = Mock(return_value=Mock(
            works_completed=10,
            works_failed=2,
            works_per_hour=5,
            total_tokens_used=1000,
            tokens_per_work=100,
            by_agent_type={},
            by_work_type={}
        ))
        toc_supervisor.identify_constraint = Mock(return_value=None)
        toc_supervisor._bottlenecks = []
        toc_supervisor._optimization_log = []
        
        report = toc_supervisor.get_optimization_report()
        
        assert report is not None
        assert "summary" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
