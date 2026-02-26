import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class SkillCategory(Enum):
    """Categories of skills for better matching."""
    CORE = "core"
    SPECIALIZED = "specialized"
    SUPPORT = "support"
    QUALITY = "quality"


@dataclass
class SkillRecommendation:
    skill_name: str
    confidence: float
    reason: str
    category: SkillCategory


class SkillAnalyzer:
    """
    Analyzes work requirements and recommends appropriate skills.
    Uses keyword matching and rule-based analysis to determine skill needs.
    """

    def __init__(self):
        self._skill_patterns = self._initialize_patterns()
        self._work_type_mappings = self._initialize_work_type_mappings()

    def _initialize_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize keyword patterns for each skill."""
        return {
            "problem-definition-skill": [
                {
                    "keywords": ["define problem", "requirements", "scope", "objectives", "kpi"],
                    "category": SkillCategory.CORE,
                    "weight": 1.0
                },
                {
                    "keywords": ["business need", "stakeholder", "success criteria", "constraint"],
                    "category": SkillCategory.CORE,
                    "weight": 0.8
                }
            ],
            "data-collection-skill": [
                {
                    "keywords": ["data", "dataset", "collect", "gather", "ingest", "scrape"],
                    "category": SkillCategory.CORE,
                    "weight": 1.0
                },
                {
                    "keywords": ["preprocess", "clean", "transform", "validate", "quality"],
                    "category": SkillCategory.SUPPORT,
                    "weight": 0.9
                }
            ],
            "design-development-skill": [
                {
                    "keywords": ["architecture", "design", "develop", "implement", "code"],
                    "category": SkillCategory.CORE,
                    "weight": 1.0
                },
                {
                    "keywords": ["api", "database", "component", "system", "framework"],
                    "category": SkillCategory.CORE,
                    "weight": 0.9
                },
                {
                    "keywords": ["docker", "kubernetes", "deployment", "ci/cd", "devops"],
                    "category": SkillCategory.SUPPORT,
                    "weight": 0.7
                }
            ],
            "training-optimization-skill": [
                {
                    "keywords": ["train", "optimize", "hyperparameter", "tune", "learning rate"],
                    "category": SkillCategory.CORE,
                    "weight": 1.0
                },
                {
                    "keywords": ["model", "performance", "accuracy", "loss", "epoch"],
                    "category": SkillCategory.SUPPORT,
                    "weight": 0.8
                }
            ],
            "evaluation-validation-skill": [
                {
                    "keywords": ["evaluate", "test", "validate", "metric", "benchmark"],
                    "category": SkillCategory.CORE,
                    "weight": 1.0
                },
                {
                    "keywords": ["accuracy", "precision", "recall", "f1", "cross-validation"],
                    "category": SkillCategory.QUALITY,
                    "weight": 0.9
                }
            ],
            "deployment-monitoring-skill": [
                {
                    "keywords": ["deploy", "monitor", "production", "serving", "api"],
                    "category": SkillCategory.CORE,
                    "weight": 1.0
                },
                {
                    "keywords": ["alert", "drift", "latency", "throughput", "uptime"],
                    "category": SkillCategory.SUPPORT,
                    "weight": 0.85
                }
            ],
            "toc-supervisor-skill": [
                {
                    "keywords": ["orchestrate", "coordinate", "manage", "supervise", "optimize"],
                    "category": SkillCategory.CORE,
                    "weight": 1.0
                },
                {
                    "keywords": ["bottleneck", "throughput", "constraint", "resource"],
                    "category": SkillCategory.SUPPORT,
                    "weight": 0.8
                }
            ]
        }

    def _initialize_work_type_mappings(self) -> Dict[str, List[str]]:
        """Initialize default skill mappings for each work type."""
        return {
            "problem_definition": ["problem-definition-skill", "toc-supervisor-skill"],
            "data_collection": ["data-collection-skill"],
            "design_development": ["design-development-skill", "toc-supervisor-skill"],
            "training_optimization": ["training-optimization-skill"],
            "evaluation_validation": ["evaluation-validation-skill"],
            "deployment_monitoring": ["deployment-monitoring-skill", "toc-supervisor-skill"],
            "coordinator": ["toc-supervisor-skill"],
            "web_development": ["design-development-skill"],
            "mobile_development": ["design-development-skill"],
            "data_science": ["data-collection-skill", "training-optimization-skill"],
            "machine_learning": ["training-optimization-skill", "evaluation-validation-skill"],
            "devops": ["deployment-monitoring-skill", "design-development-skill"],
            "security": ["evaluation-validation-skill", "design-development-skill"],
            "ui_design": ["design-development-skill"],
            "api_development": ["design-development-skill"],
            "database_design": ["design-development-skill"],
            "testing": ["evaluation-validation-skill"],
            "documentation": ["problem-definition-skill"],
            "performance": ["toc-supervisor-skill", "evaluation-validation-skill"]
        }

    async def analyze_work(self, work_name: str, work_description: str,
                          work_type: str, tags: List[str],
                          inputs: Dict[str, Any]) -> List[SkillRecommendation]:
        """
        Analyze work and recommend appropriate skills.

        Args:
            work_name: Name of the work
            work_description: Detailed description of the work
            work_type: Type of work (problem_definition, data_collection, etc.)
            tags: List of tags associated with the work
            inputs: Input parameters and requirements

        Returns:
            List of SkillRecommendation objects sorted by confidence
        """
        recommendations = []

        # 1. Start with work type-based recommendations
        base_skills = self._get_work_type_skills(work_type)
        for skill_name in base_skills:
            confidence = self._get_skill_weight(skill_name, SkillCategory.CORE)
            recommendations.append(SkillRecommendation(
                skill_name=skill_name,
                confidence=confidence,
                reason=f"Based on work type '{work_type}'",
                category=SkillCategory.CORE
            ))

        # 2. Analyze work description for keyword matches
        desc_matches = self._analyze_text(work_description)
        for skill_name, match_data in desc_matches.items():
            if not any(r.skill_name == skill_name for r in recommendations):
                recommendations.append(SkillRecommendation(
                    skill_name=skill_name,
                    confidence=match_data["confidence"],
                    reason=match_data["reason"],
                    category=match_data["category"]
                ))
            else:
                # Update confidence if higher
                for rec in recommendations:
                    if rec.skill_name == skill_name and match_data["confidence"] > rec.confidence:
                        rec.confidence = match_data["confidence"]
                        rec.reason = match_data["reason"]
                        rec.category = match_data["category"]

        # 3. Analyze tags
        tag_matches = self._analyze_tags(tags)
        for skill_name, match_data in tag_matches.items():
            if not any(r.skill_name == skill_name for r in recommendations):
                recommendations.append(SkillRecommendation(
                    skill_name=skill_name,
                    confidence=match_data["confidence"] * 0.8,  # Tags have lower weight
                    reason=f"Based on tag: {match_data['tag']}",
                    category=match_data["category"]
                ))

        # 4. Analyze inputs/requirements
        input_matches = self._analyze_inputs(inputs)
        for skill_name, match_data in input_matches.items():
            if not any(r.skill_name == skill_name for r in recommendations):
                recommendations.append(SkillRecommendation(
                    skill_name=skill_name,
                    confidence=match_data["confidence"] * 0.7,  # Inputs have lowest weight
                    reason=match_data["reason"],
                    category=match_data["category"]
                ))

        # Sort by confidence
        recommendations.sort(key=lambda x: x.confidence, reverse=True)

        # Limit to top recommendations
        return recommendations[:10]

    def _get_work_type_skills(self, work_type: str) -> List[str]:
        """Get default skills for a given work type."""
        return self._work_type_mappings.get(work_type, [])

    def _analyze_text(self, text: str) -> Dict[str, Dict[str, Any]]:
        """Analyze text for keyword matches."""
        matches = {}
        text_lower = text.lower()

        for skill_name, patterns in self._skill_patterns.items():
            best_match = None
            best_weight = 0.0

            for pattern in patterns:
                for keyword in pattern["keywords"]:
                    if keyword.lower() in text_lower:
                        weight = pattern["weight"]
                        if weight > best_weight:
                            best_weight = weight
                            best_match = {
                                "confidence": weight,
                                "reason": f"Keyword match: '{keyword}'",
                                "category": pattern["category"]
                            }

            if best_match:
                matches[skill_name] = best_match

        return matches

    def _analyze_tags(self, tags: List[str]) -> Dict[str, Dict[str, Any]]:
        """Analyze tags for skill relevance."""
        matches = {}

        tag_to_skills = {
            "ml": ["training-optimization-skill", "evaluation-validation-skill"],
            "ai": ["training-optimization-skill", "design-development-skill"],
            "web": ["design-development-skill", "deployment-monitoring-skill"],
            "api": ["design-development-skill", "deployment-monitoring-skill"],
            "data": ["data-collection-skill"],
            "database": ["design-development-skill"],
            "devops": ["deployment-monitoring-skill"],
            "security": ["evaluation-validation-skill", "design-development-skill"],
            "testing": ["evaluation-validation-skill"],
            "performance": ["toc-supervisor-skill", "evaluation-validation-skill"],
            "orchestration": ["toc-supervisor-skill"]
        }

        for tag in tags:
            tag_lower = tag.lower()
            for key, skills in tag_to_skills.items():
                if key in tag_lower:
                    for skill_name in skills:
                        if skill_name not in matches:
                            matches[skill_name] = {
                                "confidence": 0.7,
                                "reason": f"Tag match: '{tag}'",
                                "category": SkillCategory.SUPPORT,
                                "tag": tag
                            }

        return matches

    def _analyze_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Analyze input parameters for skill requirements."""
        matches = {}

        input_keywords = {
            "problem_definition-skill": ["requirements", "stakeholders", "business_case"],
            "data_collection-skill": ["data_source", "dataset", "file_path"],
            "design_development-skill": ["architecture", "framework", "tech_stack"],
            "training_optimization-skill": ["model", "hyperparameters", "epochs"],
            "evaluation_validation-skill": ["test_set", "metrics", "validation"],
            "deployment_monitoring-skill": ["environment", "endpoint", "scaling"],
            "toc-supervisor-skill": ["workflow", "orchestration", "optimization"]
        }

        inputs_text = str(inputs).lower()

        for skill_name, keywords in input_keywords.items():
            for keyword in keywords:
                if keyword.lower() in inputs_text:
                    if skill_name not in matches:
                        matches[skill_name] = {
                            "confidence": 0.6,
                            "reason": f"Input parameter: '{keyword}'",
                            "category": SkillCategory.SUPPORT
                        }

        return matches

    def _get_skill_weight(self, skill_name: str, category: SkillCategory) -> float:
        """Get weight for a skill based on category."""
        if category == SkillCategory.CORE:
            return 1.0
        elif category == SkillCategory.SPECIALIZED:
            return 0.85
        elif category == SkillCategory.SUPPORT:
            return 0.7
        elif category == SkillCategory.QUALITY:
            return 0.75
        return 0.5

    def assign_skills_to_raci(self, recommendations: List[SkillRecommendation],
                             raci_roles: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """
        Assign skills to RACI roles based on role requirements.

        Args:
            recommendations: List of recommended skills
            raci_roles: Dictionary of RACI roles {role_type: agent_id}

        Returns:
            Dictionary mapping RACI roles to assigned skills
        """
        assignments = {}

        # Define which roles get which categories of skills
        role_skill_preferences = {
            "responsible": [SkillCategory.CORE, SkillCategory.SPECIALIZED],
            "accountable": [SkillCategory.CORE, SkillCategory.QUALITY],
            "consulted": [SkillCategory.SUPPORT, SkillCategory.SPECIALIZED, SkillCategory.QUALITY],
            "informed": [SkillCategory.SUPPORT]
        }

        # Assign skills to each role
        for role, agent_id in raci_roles.items():
            preferred_categories = role_skill_preferences.get(role, [SkillCategory.SUPPORT])

            # Filter recommendations by category
            role_skills = [
                rec.skill_name for rec in recommendations
                if rec.category in preferred_categories and rec.confidence > 0.5
            ]

            assignments[role] = {
                "agent_id": agent_id,
                "skills": role_skills,
                "rationale": f"Assigned skills matching {role} role preferences"
            }

        return assignments
