import pytest
from datetime import datetime
import asyncio

from agent_factory.core.retry import (
    RetryPolicy,
    RetryStrategy,
    RetryManager,
    TimeoutStrategy,
)


class TestRetryPolicy:
    def test_default_policy(self):
        policy = RetryPolicy()
        
        assert policy.max_retries == 3
        assert policy.strategy == RetryStrategy.EXPONENTIAL
        assert policy.base_delay == 1.0
    
    def test_exponential_backoff(self):
        policy = RetryPolicy(strategy=RetryStrategy.EXPONENTIAL)
        
        assert policy.get_delay(1) == 1.0
        assert policy.get_delay(2) == 2.0
        assert policy.get_delay(3) == 4.0
        assert policy.get_delay(4) == 8.0
    
    def test_linear_backoff(self):
        policy = RetryPolicy(strategy=RetryStrategy.LINEAR)
        
        assert policy.get_delay(1) == 1.0
        assert policy.get_delay(2) == 2.0
        assert policy.get_delay(3) == 3.0
    
    def test_constant_backoff(self):
        policy = RetryPolicy(strategy=RetryStrategy.CONSTANT)
        
        assert policy.get_delay(1) == 1.0
        assert policy.get_delay(2) == 1.0
        assert policy.get_delay(3) == 1.0
    
    def test_max_delay(self):
        policy = RetryPolicy(
            strategy=RetryStrategy.EXPONENTIAL,
            max_delay=10.0
        )
        
        assert policy.get_delay(10) <= 10.0
    
    def test_should_retry(self):
        policy = RetryPolicy()
        
        assert policy.should_retry(Exception("timeout error")) is True
        assert policy.should_retry(Exception("rate_limit exceeded")) is True
        assert policy.should_retry(Exception("connection_error")) is True
        assert policy.should_retry(Exception("unknown error")) is False
    
    def test_custom_retry_errors(self):
        policy = RetryPolicy(
            retry_on_errors=["custom_error", "another_error"]
        )
        
        assert policy.should_retry(Exception("custom_error")) is True
        assert policy.should_retry(Exception("another_error")) is True
        assert policy.should_retry(Exception("timeout")) is False
    
    def test_to_dict(self):
        policy = RetryPolicy(max_retries=5)
        d = policy.to_dict()
        
        assert d["max_retries"] == 5
        assert "strategy" in d


class TestRetryManager:
    def test_initialization(self):
        manager = RetryManager()
        
        assert manager.default_policy is not None
    
    def test_custom_default_policy(self):
        policy = RetryPolicy(max_retries=5)
        manager = RetryManager(default_policy=policy)
        
        assert manager.default_policy.max_retries == 5
    
    def test_record_retry(self):
        manager = RetryManager()
        
        manager.record_retry("work_1", Exception("test error"))
        
        assert manager.get_retry_count("work_1") == 1
    
    def test_multiple_retries(self):
        manager = RetryManager()
        
        for i in range(3):
            manager.record_retry("work_1", Exception(f"error {i}"))
        
        assert manager.get_retry_count("work_1") == 3
    
    def test_can_retry(self):
        manager = RetryManager()
        
        assert manager.can_retry("work_1") is True
        
        for i in range(3):
            manager.record_retry("work_1", Exception("error"))
        
        assert manager.can_retry("work_1") is False
    
    def test_get_next_delay(self):
        manager = RetryManager()
        
        delay1 = manager.get_next_delay("work_1")
        assert delay1 == 1.0
        
        manager.record_retry("work_1", Exception("error"))
        delay2 = manager.get_next_delay("work_1")
        assert delay2 == 2.0
    
    def test_get_stats(self):
        manager = RetryManager()
        
        manager.record_retry("work_1", Exception("error"))
        manager.record_retry("work_2", Exception("error"))
        
        stats = manager.get_stats()
        
        assert stats["total_retries"] == 2
        assert stats["unique_works"] == 2


class TestTimeoutStrategy:
    def test_initialization(self):
        strategy = TimeoutStrategy()
        
        assert strategy.default_timeout == 300.0
    
    def test_custom_default_timeout(self):
        strategy = TimeoutStrategy(default_timeout=60.0)
        
        assert strategy.default_timeout == 60.0
    
    def test_set_and_get_timeout(self):
        strategy = TimeoutStrategy()
        
        strategy.set_timeout("work_1", 120.0)
        
        assert strategy.get_timeout("work_1") == 120.0
    
    def test_get_default_for_unknown_work(self):
        strategy = TimeoutStrategy(default_timeout=60.0)
        
        assert strategy.get_timeout("unknown_work") == 60.0
    
    def test_clear_timeout(self):
        strategy = TimeoutStrategy()
        
        strategy.set_timeout("work_1", 120.0)
        strategy.clear_timeout("work_1")
        
        assert strategy.get_timeout("work_1") == 300.0
    
    def test_get_stats(self):
        strategy = TimeoutStrategy()
        
        strategy.set_timeout("work_1", 60.0)
        strategy.set_timeout("work_2", 120.0)
        
        stats = strategy.get_stats()
        
        assert stats["active_timeouts"] == 2
        assert "timeout_history" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
