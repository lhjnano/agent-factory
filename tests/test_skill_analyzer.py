import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from agent_factory.core.skill_analyzer import (
    SkillAnalyzer,
    SkillCategory,
    SkillRecommendation
)


class TestSkillRecommendation:
    def test_recommendation_creation(self):
        rec = SkillRecommendation(
            skill_name="test-skill",
            confidence=0.9,
            reason="Test reason",
            category=SkillCategory.CORE
        )
        assert rec.skill_name == "test-skill"
        assert rec.confidence == 0.9
        assert rec.reason == "Test reason"
        assert rec.category == SkillCategory.CORE


class TestSkillCategory:
    def test_category_values(self):
        assert SkillCategory.CORE.value == "core"
        assert SkillCategory.SPECIALIZED.value == "specialized"
        assert SkillCategory.SUPPORT.value == "support"
        assert SkillCategory.QUALITY.value == "quality"


class TestSkillAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return SkillAnalyzer()
    
    @pytest.mark.asyncio
    async def test_analyze_work_problem_definition(self, analyzer):
        recommendations = await analyzer.analyze_work(
            work_name="Define Requirements",
            work_description="Define problem scope and business requirements",
            work_type="problem_definition",
            tags=["planning"],
            inputs={"stakeholders": ["team"]}
        )
        
        assert len(recommendations) > 0
        assert any(r.skill_name == "problem-definition-skill" for r in recommendations)
    
    @pytest.mark.asyncio
    async def test_analyze_work_data_collection(self, analyzer):
        recommendations = await analyzer.analyze_work(
            work_name="Collect Data",
            work_description="Gather and preprocess dataset for training",
            work_type="data_collection",
            tags=["data", "preprocessing"],
            inputs={"data_source": "api"}
        )
        
        assert len(recommendations) > 0
        assert any(r.skill_name == "data-collection-skill" for r in recommendations)
    
    @pytest.mark.asyncio
    async def test_analyze_work_with_keywords(self, analyzer):
        recommendations = await analyzer.analyze_work(
            work_name="Train Model",
            work_description="Train machine learning model with hyperparameter tuning",
            work_type="training_optimization",
            tags=["ml"],
            inputs={}
        )
        
        assert len(recommendations) > 0
        skill_names = [r.skill_name for r in recommendations]
        assert "training-optimization-skill" in skill_names
    
    @pytest.mark.asyncio
    async def test_analyze_work_with_tags(self, analyzer):
        recommendations = await analyzer.analyze_work(
            work_name="Build API",
            work_description="Create REST API endpoints",
            work_type="design_development",
            tags=["api", "web", "backend"],
            inputs={}
        )
        
        skill_names = [r.skill_name for r in recommendations]
        assert "design-development-skill" in skill_names
    
    @pytest.mark.asyncio
    async def test_analyze_work_sorts_by_confidence(self, analyzer):
        recommendations = await analyzer.analyze_work(
            work_name="Complex Task",
            work_description="Deploy model to production with monitoring and evaluation",
            work_type="deployment_monitoring",
            tags=["devops", "performance"],
            inputs={"environment": "production"}
        )
        
        confidences = [r.confidence for r in recommendations]
        assert confidences == sorted(confidences, reverse=True)
    
    @pytest.mark.asyncio
    async def test_analyze_work_limits_recommendations(self, analyzer):
        recommendations = await analyzer.analyze_work(
            work_name="Task",
            work_description="Complex task with many keywords: data, train, deploy, evaluate, monitor",
            work_type="coordinator",
            tags=["ml", "devops", "api", "testing", "performance"],
            inputs={}
        )
        
        assert len(recommendations) <= 10
    
    def test_assign_skills_to_raci(self, analyzer):
        recommendations = [
            SkillRecommendation("skill1", 0.9, "reason", SkillCategory.CORE),
            SkillRecommendation("skill2", 0.8, "reason", SkillCategory.SUPPORT),
            SkillRecommendation("skill3", 0.7, "reason", SkillCategory.QUALITY),
        ]
        
        raci_roles = {
            "responsible": "agent1",
            "accountable": "agent2",
            "consulted": "agent3",
            "informed": "agent4"
        }
        
        assignments = analyzer.assign_skills_to_raci(recommendations, raci_roles)
        
        assert "responsible" in assignments
        assert "accountable" in assignments
        assert "consulted" in assignments
        assert "informed" in assignments
        
        assert "agent1" in assignments["responsible"]["agent_id"]
        assert len(assignments["responsible"]["skills"]) > 0
    
    def test_get_work_type_skills(self, analyzer):
        skills = analyzer._get_work_type_skills("problem_definition")
        assert "problem-definition-skill" in skills
        
        skills = analyzer._get_work_type_skills("unknown_type")
        assert skills == []
    
    def test_analyze_text_keywords(self, analyzer):
        matches = analyzer._analyze_text("We need to train and optimize the model")
        
        assert "training-optimization-skill" in matches
        assert matches["training-optimization-skill"]["confidence"] > 0
    
    def test_analyze_tags(self, analyzer):
        matches = analyzer._analyze_tags(["ml", "api", "devops"])
        
        skill_names = list(matches.keys())
        assert any("training-optimization" in s for s in skill_names)
        assert any("design-development" in s for s in skill_names)
    
    def test_analyze_inputs(self, analyzer):
        matches = analyzer._analyze_inputs({
            "model": "gpt-4",
            "hyperparameters": {"lr": 0.001}
        })
        
        assert len(matches) > 0
    
    def test_get_skill_weight(self, analyzer):
        assert analyzer._get_skill_weight("skill", SkillCategory.CORE) == 1.0
        assert analyzer._get_skill_weight("skill", SkillCategory.SPECIALIZED) == 0.85
        assert analyzer._get_skill_weight("skill", SkillCategory.SUPPORT) == 0.7
        assert analyzer._get_skill_weight("skill", SkillCategory.QUALITY) == 0.75


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
