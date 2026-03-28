import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from agent_factory.core.skill_manager import (
    SkillManager,
    SkillVersion,
    SkillCache
)


class TestSkillCache:
    def test_cache_creation(self):
        cache = SkillCache(
            content="test content",
            cached_at=datetime.now(),
            ttl_seconds=3600
        )
        assert cache.content == "test content"
        assert cache.hits == 0
        assert not cache.is_expired()

    
    def test_cache_expiration(self):
        cache = SkillCache(
            content="test content",
            cached_at=datetime.now() - timedelta(seconds=3700),
            ttl_seconds=3600
        )
        assert cache.is_expired()
    
    def test_cache_not_expired(self):
        cache = SkillCache(
            content="test content",
            cached_at=datetime.now() - timedelta(seconds=1800),
            ttl_seconds=3600
        )
        assert not cache.is_expired()
    
    def test_cache_hits_increment(self):
        cache = SkillCache(
            content="test content",
            cached_at=datetime.now(),
            ttl_seconds=3600
        )
        cache.hits += 1
        cache.hits += 1
        assert cache.hits == 2


class TestSkillVersion:
    def test_version_creation(self):
        version = SkillVersion(
            version="v20240101120000_abc123",
            content="skill content",
            created_at=datetime.now(),
            changelog="Initial version"
        )
        assert version.version == "v20240101120000_abc123"
        assert version.content == "skill content"
        assert version.changelog == "Initial version"
    
    def test_version_without_changelog(self):
        version = SkillVersion(
            version="v1",
            content="content",
            created_at=datetime.now()
        )
        assert version.changelog == ""


class TestSkillManagerCaching:
    @pytest.fixture
    def temp_skill_dir(self, tmp_path):
        skill_dir = tmp_path / ".agent" / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("---\nname: test-skill\n---\n# Test Skill\n\nThis is test content.")
        return tmp_path
    
    @pytest.fixture
    def skill_manager(self, temp_skill_dir):
        return SkillManager(repo_root=temp_skill_dir)
    
    def test_cache_enabled_by_default(self, skill_manager):
        assert skill_manager._cache_enabled is True
        assert skill_manager._cache_ttl == 3600
    
    def test_enable_cache(self, skill_manager):
        skill_manager.enable_cache(ttl_seconds=7200)
        assert skill_manager._cache_enabled is True
        assert skill_manager._cache_ttl == 7200
    
    def test_disable_cache(self, skill_manager):
        skill_manager.disable_cache()
        assert skill_manager._cache_enabled is False
    
    @pytest.mark.asyncio
    async def test_load_skill_caches_content(self, skill_manager):
        content = await skill_manager.load_skill("test-skill")
        assert content is not None
        assert "test-skill" in skill_manager._cache
        assert skill_manager._cache["test-skill"].content == content
    
    @pytest.mark.asyncio
    async def test_cache_hit_increments_hits(self, skill_manager):
        await skill_manager.load_skill("test-skill")
        assert skill_manager._cache["test-skill"].hits == 1
        
        await skill_manager.load_skill("test-skill")
        assert skill_manager._cache["test-skill"].hits == 2
    
    @pytest.mark.asyncio
    async def test_expired_cache_reloads(self, skill_manager):
        await skill_manager.load_skill("test-skill")
        
        skill_manager._cache["test-skill"].cached_at = datetime.now() - timedelta(seconds=4000)
        assert skill_manager._cache["test-skill"].is_expired()
        
        await skill_manager.load_skill("test-skill")
        assert skill_manager._cache["test-skill"].hits == 1
    
    def test_clear_cache_specific_skill(self, skill_manager):
        skill_manager._cache["skill1"] = SkillCache("content1", datetime.now())
        skill_manager._cache["skill2"] = SkillCache("content2", datetime.now())
        
        skill_manager.clear_cache("skill1")
        
        assert "skill1" not in skill_manager._cache
        assert "skill2" in skill_manager._cache
    
    def test_clear_cache_all(self, skill_manager):
        skill_manager._cache["skill1"] = SkillCache("content1", datetime.now())
        skill_manager._cache["skill2"] = SkillCache("content2", datetime.now())
        
        skill_manager.clear_cache()
        
        assert len(skill_manager._cache) == 0
    
    def test_get_cache_stats(self, skill_manager):
        skill_manager._cache["skill1"] = SkillCache("content1", datetime.now(), hits=5)
        skill_manager._cache["skill2"] = SkillCache(
            "content2", 
            datetime.now() - timedelta(seconds=4000), 
            hits=3
        )
        
        stats = skill_manager.get_cache_stats()
        
        assert stats["enabled"] is True
        assert stats["cached_skills"] == 2
        assert stats["total_hits"] == 8
        assert stats["expired_entries"] == 1


class TestSkillManagerVersioning:
    @pytest.fixture
    def skill_manager(self):
        return SkillManager()
    
    def test_create_version(self, skill_manager):
        content = "skill content"
        version = skill_manager.create_version("test-skill", content, "Initial version")
        
        assert version.startswith("v")
        assert "test-skill" in skill_manager._versions
        assert len(skill_manager._versions["test-skill"]) == 1
        assert skill_manager._current_version["test-skill"] == version
    
    def test_multiple_versions(self, skill_manager):
        v1 = skill_manager.create_version("skill", "content1", "v1")
        v2 = skill_manager.create_version("skill", "content2", "v2")
        
        assert len(skill_manager._versions["skill"]) == 2
        assert skill_manager._current_version["skill"] == v2
    
    def test_get_skill_version(self, skill_manager):
        content = "original content"
        version = skill_manager.create_version("skill", content)
        
        retrieved = skill_manager.get_skill_version("skill", version)
        assert retrieved == content
    
    def test_get_skill_version_nonexistent(self, skill_manager):
        retrieved = skill_manager.get_skill_version("skill", "nonexistent")
        assert retrieved is None
    
    def test_get_current_version(self, skill_manager):
        v1 = skill_manager.create_version("skill", "content1")
        v2 = skill_manager.create_version("skill", "content2")
        
        assert skill_manager.get_current_version("skill") == v2
    
    def test_list_versions(self, skill_manager):
        v1 = skill_manager.create_version("skill", "c1", "first")
        v2 = skill_manager.create_version("skill", "c2", "second")
        
        versions = skill_manager.list_versions("skill")
        
        assert len(versions) == 2
        assert versions[0]["version"] == v1
        assert versions[0]["changelog"] == "first"
        assert versions[0]["is_current"] is False
        assert versions[1]["is_current"] is True
    
    def test_rollback_version(self, skill_manager):
        v1 = skill_manager.create_version("skill", "content1")
        v2 = skill_manager.create_version("skill", "content2")
        
        result = skill_manager.rollback_version("skill", v1)
        
        assert result is True
        assert skill_manager._current_version["skill"] == v1
        assert skill_manager._skills["skill"] == "content1"
    
    def test_rollback_nonexistent_version(self, skill_manager):
        skill_manager.create_version("skill", "content")
        result = skill_manager.rollback_version("skill", "nonexistent")
        assert result is False
    
    def test_get_version_diff(self, skill_manager):
        v1 = skill_manager.create_version("skill", "short")
        v2 = skill_manager.create_version("skill", "much longer content here")
        
        diff = skill_manager.get_version_diff("skill", v1, v2)
        
        assert diff["version1"] == v1
        assert diff["version2"] == v2
        assert diff["size_diff"] > 0
    
    def test_get_versioning_stats(self, skill_manager):
        skill_manager.create_version("skill1", "c1")
        skill_manager.create_version("skill1", "c2")
        skill_manager.create_version("skill2", "c3")
        
        stats = skill_manager.get_versioning_stats()
        
        assert stats["total_skills_with_versions"] == 2
        assert stats["total_versions"] == 3
        assert stats["version_details"]["skill1"] == 2
        assert stats["version_details"]["skill2"] == 1


class TestSkillManagerEffectiveness:
    @pytest.fixture
    def skill_manager(self):
        return SkillManager()
    
    def test_record_skill_usage(self, skill_manager):
        skill_manager.record_skill_usage("test-skill", True, 1000, 5.0)
        
        assert "test-skill" in skill_manager._skill_effectiveness
        data = skill_manager._skill_effectiveness["test-skill"]
        assert data["usage_count"] == 1
        assert data["success_count"] == 1
        assert data["total_tokens"] == 1000
        assert data["total_duration"] == 5.0
    
    def test_multiple_usage_records(self, skill_manager):
        skill_manager.record_skill_usage("skill", True, 1000, 5.0)
        skill_manager.record_skill_usage("skill", False, 2000, 10.0)
        skill_manager.record_skill_usage("skill", True, 1500, 7.5)
        
        data = skill_manager._skill_effectiveness["skill"]
        assert data["usage_count"] == 3
        assert data["success_count"] == 2
        assert data["total_tokens"] == 4500
        assert data["total_duration"] == 22.5
    
    def test_get_skill_effectiveness(self, skill_manager):
        skill_manager.record_skill_usage("skill", True, 1000, 5.0)
        skill_manager.record_skill_usage("skill", True, 2000, 10.0)
        
        metrics = skill_manager.get_skill_effectiveness("skill")
        
        assert metrics["usage_count"] == 2
        assert metrics["success_rate"] == 1.0
        assert metrics["avg_tokens"] == 1500.0
        assert metrics["avg_duration"] == 7.5
        assert 0 <= metrics["efficiency_score"] <= 1
    
    def test_get_skill_effectiveness_nonexistent(self, skill_manager):
        metrics = skill_manager.get_skill_effectiveness("nonexistent")
        assert metrics is None
    
    def test_efficiency_score_calculation(self, skill_manager):
        for _ in range(10):
            skill_manager.record_skill_usage("high-perf", True, 500, 30.0)
        
        metrics = skill_manager.get_skill_effectiveness("high-perf")
        assert metrics["efficiency_score"] > 0.7
    
    def test_get_all_skill_effectiveness(self, skill_manager):
        skill_manager.record_skill_usage("skill1", True, 1000, 5.0)
        skill_manager.record_skill_usage("skill2", False, 2000, 10.0)
        
        all_metrics = skill_manager.get_all_skill_effectiveness()
        
        assert "skill1" in all_metrics
        assert "skill2" in all_metrics
    
    def test_get_skill_recommendations(self, skill_manager):
        for _ in range(5):
            skill_manager.record_skill_usage("good-skill", True, 1000, 60.0)
        
        for _ in range(5):
            skill_manager.record_skill_usage("bad-skill", False, 4000, 300.0)
        
        skill_manager._skills["unused-skill"] = "content"
        
        recommendations = skill_manager.get_skill_recommendations()
        
        assert len(recommendations) >= 2
        
        good_rec = next((r for r in recommendations if r["skill"] == "good-skill"), None)
        assert good_rec is not None
        assert good_rec["action"] in ["maintain", "monitor"]
        
        unused_rec = next((r for r in recommendations if r["skill"] == "unused-skill"), None)
        assert unused_rec is not None
        assert unused_rec["action"] == "evaluate"
    
    def test_reset_skill_effectiveness(self, skill_manager):
        skill_manager.record_skill_usage("skill", True, 1000, 5.0)
        
        skill_manager.reset_skill_effectiveness()
        
        assert len(skill_manager._skill_effectiveness) == 0


class TestSkillManagerLoading:
    @pytest.fixture
    def temp_skill_dir(self, tmp_path):
        skill_dir = tmp_path / ".agent" / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("---\nname: test-skill\n---\n# Test Skill\n\nThis is test content.")
        return tmp_path
    
    @pytest.fixture
    def skill_manager(self, temp_skill_dir):
        return SkillManager(repo_root=temp_skill_dir)
    
    @pytest.mark.asyncio
    async def test_load_skill_from_file(self, skill_manager):
        content = await skill_manager.load_skill("test-skill")
        assert content is not None
        assert "Test Skill" in content
    
    @pytest.mark.asyncio
    async def test_load_nonexistent_skill(self, skill_manager):
        content = await skill_manager.load_skill("nonexistent")
        assert content is None
    
    @pytest.mark.asyncio
    async def test_load_all_skills(self, skill_manager, temp_skill_dir):
        skill_dir2 = temp_skill_dir / ".agent" / "skills" / "another-skill"
        skill_dir2.mkdir(parents=True)
        (skill_dir2 / "SKILL.md").write_text("# Another Skill")
        
        skills = await skill_manager.load_all_skills(["test-skill", "another-skill"])
        
        assert "test-skill" in skills
        assert "another-skill" in skills
    
    @pytest.mark.asyncio
    async def test_get_skill_content(self, skill_manager):
        content = await skill_manager.get_skill_content("test-skill")
        assert content is not None
        assert "test-skill" in skill_manager._skills
    
    @pytest.mark.asyncio
    async def test_inject_skills(self, skill_manager):
        injected = await skill_manager.inject_skills(["test-skill"])
        assert "Available Skills" in injected
        assert "test-skill" in injected
    
    def test_extract_skill_body(self, skill_manager):
        full_content = "---\nname: test\n---\nActual body content"
        body = skill_manager._extract_skill_body(full_content)
        assert body == "Actual body content"
        assert "---" not in body
    
    def test_extract_skill_body_no_frontmatter(self, skill_manager):
        content = "Just content without frontmatter"
        body = skill_manager._extract_skill_body(content)
        assert body == content


class TestSkillManagerWorkMatching:
    @pytest.fixture
    def skill_manager(self):
        return SkillManager()
    
    @pytest.mark.asyncio
    async def test_match_skills_to_problem_definition(self, skill_manager):
        skills = await skill_manager.match_skills_to_work("problem_definition")
        assert "problem-definition-skill" in skills
    
    @pytest.mark.asyncio
    async def test_match_skills_to_data_collection(self, skill_manager):
        skills = await skill_manager.match_skills_to_work("data_collection")
        assert "data-collection-skill" in skills
    
    @pytest.mark.asyncio
    async def test_match_skills_to_unknown_type(self, skill_manager):
        skills = await skill_manager.match_skills_to_work("unknown_type")
        assert skills == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
