from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import re
import hashlib
import json


@dataclass
class SkillVersion:
    version: str
    content: str
    created_at: datetime
    changelog: str = ""


@dataclass
class SkillCache:
    content: str
    cached_at: datetime
    ttl_seconds: int = 3600
    hits: int = 0
    
    def is_expired(self) -> bool:
        return (datetime.now() - self.cached_at).total_seconds() > self.ttl_seconds


class SkillManager:
    """
    Manages agent skills - loading, assigning, caching, versioning, and effectiveness tracking.
    Skills are defined in SKILL.md files under .agent/skills/ or .claude/skills/.
    """

    def __init__(self, repo_root: Optional[Path] = None):
        self._skills: Dict[str, str] = {}
        self._skill_effectiveness: Dict[str, Dict[str, float]] = {}
        self._repo_root = repo_root or Path.cwd()
        self._lock = asyncio.Lock()
        
        # Caching
        self._cache: Dict[str, SkillCache] = {}
        self._cache_enabled: bool = True
        self._cache_ttl: int = 3600
        
        # Versioning
        self._versions: Dict[str, List[SkillVersion]] = {}
        self._current_version: Dict[str, str] = {}

    async def load_skill(self, skill_name: str) -> Optional[str]:
        """
        Load a skill from SKILL.md file.
        Searches in order: .agent/skills/, .claude/skills/
        Uses cache if available and not expired.
        """
        # Check cache first
        if self._cache_enabled and skill_name in self._cache:
            cache_entry = self._cache[skill_name]
            if not cache_entry.is_expired():
                cache_entry.hits += 1
                self._skills[skill_name] = cache_entry.content
                return cache_entry.content
        
        async with self._lock:
            if skill_name in self._skills:
                return self._skills[skill_name]

            search_paths = [
                self._repo_root / ".agent" / "skills" / skill_name / "SKILL.md",
                Path.home() / ".agent" / "skills" / skill_name / "SKILL.md",
                self._repo_root / ".claude" / "skills" / skill_name / "SKILL.md",
                Path.home() / ".claude" / "skills" / skill_name / "SKILL.md",
            ]

            for path in search_paths:
                if path.exists():
                    try:
                        content = path.read_text(encoding="utf-8")
                        self._skills[skill_name] = content
                        
                        # Cache the skill
                        if self._cache_enabled:
                            self._cache[skill_name] = SkillCache(
                                content=content,
                                cached_at=datetime.now(),
                                ttl_seconds=self._cache_ttl,
                                hits=1
                            )
                        
                        return content
                    except Exception as e:
                        print(f"Failed to load skill {skill_name} from {path}: {e}")
                        continue

            return None

    async def load_all_skills(self, skill_names: List[str]) -> Dict[str, str]:
        """Load multiple skills at once."""
        skills = {}
        for skill_name in skill_names:
            content = await self.load_skill(skill_name)
            if content:
                skills[skill_name] = content
        return skills

    async def get_skill_content(self, skill_name: str) -> Optional[str]:
        """Get the content of a skill, loading if necessary."""
        if skill_name not in self._skills:
            await self.load_skill(skill_name)
        return self._skills.get(skill_name)

    async def inject_skills(self, skill_names: List[str]) -> str:
        """
        Inject multiple skills into a formatted system prompt.
        Returns formatted skill content for agent consumption.
        """
        skills_content = []
        for skill_name in skill_names:
            content = await self.get_skill_content(skill_name)
            if content:
                # Extract the main skill content (after frontmatter)
                skill_body = self._extract_skill_body(content)
                skills_content.append(f"### {skill_name}\n\n{skill_body}")

        if not skills_content:
            return ""

        return "## Available Skills\n\n" + "\n\n".join(skills_content)

    def _extract_skill_body(self, skill_content: str) -> str:
        """
        Extract skill body content by removing YAML frontmatter.
        """
        # Split by triple dashes
        parts = skill_content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
        return skill_content.strip()

    def record_skill_usage(self, skill_name: str, success: bool, tokens_used: int, duration_seconds: float):
        """Record skill usage for effectiveness tracking."""
        if skill_name not in self._skill_effectiveness:
            self._skill_effectiveness[skill_name] = {
                "usage_count": 0,
                "success_count": 0,
                "total_tokens": 0,
                "total_duration": 0.0
            }

        self._skill_effectiveness[skill_name]["usage_count"] += 1
        if success:
            self._skill_effectiveness[skill_name]["success_count"] += 1
        self._skill_effectiveness[skill_name]["total_tokens"] += tokens_used
        self._skill_effectiveness[skill_name]["total_duration"] += duration_seconds

    def get_skill_effectiveness(self, skill_name: str) -> Optional[Dict[str, float]]:
        """Get effectiveness metrics for a skill."""
        if skill_name not in self._skill_effectiveness:
            return None

        data = self._skill_effectiveness[skill_name]
        usage_count = data["usage_count"]

        if usage_count == 0:
            return None

        return {
            "usage_count": usage_count,
            "success_rate": data["success_count"] / usage_count,
            "avg_tokens": data["total_tokens"] / usage_count,
            "avg_duration": data["total_duration"] / usage_count,
            "efficiency_score": self._calculate_efficiency_score(skill_name)
        }

    def _calculate_efficiency_score(self, skill_name: str) -> float:
        """
        Calculate a composite efficiency score for a skill.
        Score combines success rate, token efficiency, and duration efficiency.
        Returns a value between 0 and 1.
        """
        if skill_name not in self._skill_effectiveness:
            return 0.0

        data = self._skill_effectiveness[skill_name]
        usage_count = data["usage_count"]

        if usage_count == 0:
            return 0.0

        # Base score from success rate (weight: 0.5)
        success_rate = data["success_count"] / usage_count

        # Token efficiency: lower is better, invert (weight: 0.3)
        avg_tokens = data["total_tokens"] / usage_count
        token_efficiency = max(0, 1 - min(1, avg_tokens / 5000))  # Normalize against 5000 tokens

        # Duration efficiency: lower is better, invert (weight: 0.2)
        avg_duration = data["total_duration"] / usage_count
        duration_efficiency = max(0, 1 - min(1, avg_duration / 600))  # Normalize against 10 minutes

        # Weighted composite score
        efficiency_score = (
            success_rate * 0.5 +
            token_efficiency * 0.3 +
            duration_efficiency * 0.2
        )

        return efficiency_score

    def get_all_skill_effectiveness(self) -> Dict[str, Dict[str, float]]:
        """Get effectiveness metrics for all skills."""
        result = {}
        for skill_name in self._skill_effectiveness:
            metrics = self.get_skill_effectiveness(skill_name)
            if metrics:
                result[skill_name] = metrics
        return result

    def get_skill_recommendations(self) -> List[Dict[str, str]]:
        """
        Generate recommendations for skill optimization.
        Returns list of recommendations with skill names and actions.
        """
        recommendations = []
        effectiveness = self.get_all_skill_effectiveness()

        for skill_name, metrics in effectiveness.items():
            score = metrics.get("efficiency_score", 0)

            if score > 0.9:
                recommendations.append({
                    "skill": skill_name,
                    "action": "maintain",
                    "reason": f"High efficiency score ({score:.2f}), keep current usage"
                })
            elif score > 0.7:
                recommendations.append({
                    "skill": skill_name,
                    "action": "monitor",
                    "reason": f"Good efficiency score ({score:.2f}), continue monitoring"
                })
            elif score > 0.5:
                recommendations.append({
                    "skill": skill_name,
                    "action": "optimize",
                    "reason": f"Moderate efficiency score ({score:.2f}), consider optimization"
                })
            else:
                recommendations.append({
                    "skill": skill_name,
                    "action": "refine",
                    "reason": f"Low efficiency score ({score:.2f}), skill refinement needed"
                })

        # Check for underutilized skills
        loaded_skills = set(self._skills.keys())
        used_skills = set(effectiveness.keys())
        unused_skills = loaded_skills - used_skills

        for skill_name in unused_skills:
            recommendations.append({
                "skill": skill_name,
                "action": "evaluate",
                "reason": "Skill loaded but never used, consider if it's needed"
            })

        return recommendations

    async def match_skills_to_work(self, work_type: str) -> List[str]:
        """
        Recommend skills based on work type.
        This is a simple mapping; can be enhanced with ML-based matching.
        """
        work_type_to_skills = {
            "problem_definition": ["problem-definition-skill", "toc-supervisor-skill"],
            "data_collection": ["data-collection-skill"],
            "design_development": ["design-development-skill", "toc-supervisor-skill"],
            "training_optimization": ["training-optimization-skill"],
            "evaluation_validation": ["evaluation-validation-skill"],
            "deployment_monitoring": ["deployment-monitoring-skill", "toc-supervisor-skill"],
            "coordinator": ["toc-supervisor-skill"]
        }

        return work_type_to_skills.get(work_type, [])

    def reset_skill_effectiveness(self):
        """Reset all skill effectiveness metrics."""
        self._skill_effectiveness.clear()
    
    # ==================== Caching Methods ====================
    
    def enable_cache(self, ttl_seconds: int = 3600):
        """Enable skill caching with specified TTL."""
        self._cache_enabled = True
        self._cache_ttl = ttl_seconds
    
    def disable_cache(self):
        """Disable skill caching."""
        self._cache_enabled = False
    
    def clear_cache(self, skill_name: Optional[str] = None):
        """Clear cache for specific skill or all skills."""
        if skill_name:
            self._cache.pop(skill_name, None)
        else:
            self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_hits = sum(c.hits for c in self._cache.values())
        expired_count = sum(1 for c in self._cache.values() if c.is_expired())
        
        return {
            "enabled": self._cache_enabled,
            "ttl_seconds": self._cache_ttl,
            "cached_skills": len(self._cache),
            "total_hits": total_hits,
            "expired_entries": expired_count,
            "cache_details": {
                name: {
                    "hits": cache.hits,
                    "age_seconds": (datetime.now() - cache.cached_at).total_seconds(),
                    "expired": cache.is_expired()
                }
                for name, cache in self._cache.items()
            }
        }
    
    # ==================== Versioning Methods ====================
    
    def create_version(self, skill_name: str, content: str, changelog: str = "") -> str:
        """
        Create a new version of a skill.
        Returns the version identifier.
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
        version = f"v{datetime.now().strftime('%Y%m%d%H%M%S')}_{content_hash}"
        
        version_entry = SkillVersion(
            version=version,
            content=content,
            created_at=datetime.now(),
            changelog=changelog
        )
        
        if skill_name not in self._versions:
            self._versions[skill_name] = []
        
        self._versions[skill_name].append(version_entry)
        self._current_version[skill_name] = version
        
        return version
    
    def get_skill_version(self, skill_name: str, version: str) -> Optional[str]:
        """Get a specific version of a skill."""
        if skill_name not in self._versions:
            return None
        
        for v in self._versions[skill_name]:
            if v.version == version:
                return v.content
        
        return None
    
    def get_current_version(self, skill_name: str) -> Optional[str]:
        """Get the current version identifier for a skill."""
        return self._current_version.get(skill_name)
    
    def list_versions(self, skill_name: str) -> List[Dict[str, Any]]:
        """List all versions of a skill."""
        if skill_name not in self._versions:
            return []
        
        return [
            {
                "version": v.version,
                "created_at": v.created_at.isoformat(),
                "changelog": v.changelog,
                "is_current": v.version == self._current_version.get(skill_name)
            }
            for v in self._versions[skill_name]
        ]
    
    def rollback_version(self, skill_name: str, version: str) -> bool:
        """Rollback to a specific version."""
        if skill_name not in self._versions:
            return False
        
        for v in self._versions[skill_name]:
            if v.version == version:
                self._current_version[skill_name] = version
                self._skills[skill_name] = v.content
                
                # Update cache
                if self._cache_enabled:
                    self._cache[skill_name] = SkillCache(
                        content=v.content,
                        cached_at=datetime.now(),
                        ttl_seconds=self._cache_ttl
                    )
                
                return True
        
        return False
    
    def get_version_diff(self, skill_name: str, version1: str, version2: str) -> Optional[Dict[str, Any]]:
        """Get the difference between two versions."""
        content1 = self.get_skill_version(skill_name, version1)
        content2 = self.get_skill_version(skill_name, version2)
        
        if content1 is None or content2 is None:
            return None
        
        return {
            "version1": version1,
            "version2": version2,
            "size_diff": len(content2) - len(content1),
            "line_diff": content2.count('\n') - content1.count('\n')
        }
    
    def get_versioning_stats(self) -> Dict[str, Any]:
        """Get versioning statistics."""
        total_versions = sum(len(v) for v in self._versions.values())
        
        return {
            "total_skills_with_versions": len(self._versions),
            "total_versions": total_versions,
            "average_versions_per_skill": total_versions / len(self._versions) if self._versions else 0,
            "version_details": {
                name: len(versions)
                for name, versions in self._versions.items()
            }
        }
