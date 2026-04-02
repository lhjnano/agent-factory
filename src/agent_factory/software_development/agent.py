from __future__ import annotations

import json
import re
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, Dict

from .. import AGENT_DIR


class SoftwareDevelopmentAgent:
    """software_development work_type 전용 에이전트.

    sw_analysis → sw_design → sw_validation 세 단계로 구성된다.
    ML 파이프라인과 완전히 분리되어 신경망 아키텍처를 생성하지 않는다.
    """

    def __init__(self):
        self._exit_stack = AsyncExitStack()

    async def connect_servers(self):
        pass  # sub-MCP 서버 연결 필요 시 확장

    # ── Stage 1: sw_analysis ────────────────────────────────────────────────

    async def analyze_requirements(self, user_request: str) -> Dict[str, Any]:
        """user_request를 파싱해 소프트웨어 요구사항 구조체로 변환한다."""
        # 출력 포맷 힌트 줄 제거
        lines = [
            l.strip() for l in user_request.split("\n")
            if l.strip() and not l.strip().startswith("[출력")
        ]

        summary = lines[0] if lines else user_request[:200]

        # 파일/모듈 생성 관련 컴포넌트 추출
        component_keywords = (
            "create", "add", "implement", "build", "generate", "write",
            "생성", "추가", "구현", "작성", "만들", "개발",
        )
        components = [
            l.lstrip("-*•0123456789. ")
            for l in lines[1:]
            if any(kw in l.lower() for kw in component_keywords)
        ][:15]

        # 파일 경로 패턴 추출 (예: watchdog/collectors/*.py)
        file_patterns = re.findall(r"[\w/]+\.py\b|[\w/]+/[\w*]+", user_request)[:10]

        # 수정 대상 파일 vs 신규 파일 분류
        modify_keywords = ("수정", "변경", "fix", "update", "modify", "refactor")
        create_keywords = ("생성", "추가", "create", "add", "new", "신규")

        task_type = "mixed"
        lower = user_request.lower()
        if any(kw in lower for kw in create_keywords) and not any(kw in lower for kw in modify_keywords):
            task_type = "create"
        elif any(kw in lower for kw in modify_keywords) and not any(kw in lower for kw in create_keywords):
            task_type = "modify"

        return {
            "summary": summary,
            "task_type": task_type,
            "components": components,
            "file_patterns": file_patterns,
            "total_lines": len(lines),
        }

    # ── Stage 2: sw_design ──────────────────────────────────────────────────

    async def design_software_architecture(self, analysis: Dict) -> Dict[str, Any]:
        """분석 결과를 바탕으로 소프트웨어 아키텍처를 설계한다."""
        components = analysis.get("components", [])
        task_type = analysis.get("task_type", "mixed")

        # 컴포넌트를 레이어별로 분류
        layers: Dict[str, list] = {
            "collector": [],
            "storage": [],
            "api": [],
            "config": [],
            "other": [],
        }
        layer_keywords = {
            "collector": ("collector", "수집", "monitor", "모니터"),
            "storage":   ("storage", "db", "model", "database", "저장"),
            "api":       ("router", "api", "endpoint", "route"),
            "config":    ("config", "setting", "env", "설정"),
        }
        for comp in components:
            placed = False
            for layer, keywords in layer_keywords.items():
                if any(kw in comp.lower() for kw in keywords):
                    layers[layer].append(comp)
                    placed = True
                    break
            if not placed:
                layers["other"].append(comp)

        # 의존성 방향 정의
        dependency_order = ["config", "storage", "collector", "api", "other"]

        return {
            "type": "software",
            "task_type": task_type,
            "layers": {k: v for k, v in layers.items() if v},
            "dependency_order": [l for l in dependency_order if layers.get(l)],
            "component_count": len(components),
            "summary": analysis.get("summary", ""),
        }

    # ── Stage 3: sw_validation ──────────────────────────────────────────────

    async def validate_design(
        self,
        design: Dict,
        analysis: Dict,
    ) -> Dict[str, Any]:
        """설계 결과를 검토하고 문제점 및 권장사항을 반환한다."""
        issues = []
        recommendations = []

        if not design.get("layers"):
            issues.append("컴포넌트 분류 실패 — 요구사항을 구체적으로 명시하세요.")

        if design.get("component_count", 0) == 0:
            issues.append("식별된 컴포넌트가 없습니다.")

        task_type = design.get("task_type", "mixed")
        if task_type == "create":
            recommendations.append("기존 패턴(collectors/, storage/, api/routers/)을 참조해 일관성 유지")
            recommendations.append("새 DB 테이블은 db.py의 init_db에 DDL 추가 필요")
        elif task_type == "modify":
            recommendations.append("수정 전 기존 파일을 반드시 Read로 읽어 패턴 파악")
            recommendations.append("import 변경 여부 확인")

        recommendations.append("에러 발생 시 WARNING 로그 + 빈 결과 반환 패턴 유지")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations,
            "layers_identified": list(design.get("layers", {}).keys()),
            "component_count": design.get("component_count", 0),
        }

    # ── Stage 4: sw_implementation ──────────────────────────────────────────

    async def implement_code(self, files_to_write: list[Dict[str, Any]]) -> Dict[str, Any]:
        """context의 files_to_write 목록을 실제 파일로 저장하거나 패치한다.

        files_to_write 지원 형식:

        1) 전체 파일 쓰기 (기존):
           {"path": "/path/to/file.py", "content": "...전체 코드..."}

        2) 문자열 치환 패치 (신규):
           {"path": "/path/to/file.py", "patches": [
               {"old": "교체할 문자열", "new": "새 문자열"},
               ...
           ]}

        3) 단일 패치 (신규, patches 배열 없이 단축형):
           {"path": "/path/to/file.py", "patch": {"old": "교체할 문자열", "new": "새 문자열"}}

        반환:
          {"files_written": [...], "files_patched": [...], "files_failed": [...], "total": n}
        """
        written = []
        patched = []
        failed = []

        for item in files_to_write:
            fpath = item.get("path", "").strip()
            if not fpath:
                failed.append({"path": fpath, "reason": "path missing"})
                continue

            content = item.get("content", "")
            patches = item.get("patches") or (
                [item["patch"]] if item.get("patch") else []
            )

            # ── 전체 파일 쓰기 ────────────────────────────────────────────────
            if content and not patches:
                try:
                    p = Path(fpath)
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(content, encoding="utf-8")
                    written.append(fpath)
                except Exception as e:
                    failed.append({"path": fpath, "reason": str(e)})
                continue

            # ── 패치 (문자열 치환) ────────────────────────────────────────────
            if patches:
                try:
                    p = Path(fpath)
                    if not p.exists():
                        failed.append({"path": fpath, "reason": "file not found for patching"})
                        continue
                    text = p.read_text(encoding="utf-8")
                    patch_log = []
                    for op in patches:
                        old = op.get("old", "")
                        new = op.get("new", "")
                        if old not in text:
                            failed.append({
                                "path": fpath,
                                "reason": f"patch old_string not found: {old[:60]!r}",
                            })
                            text = None
                            break
                        text = text.replace(old, new, 1)
                        patch_log.append({"old": old[:40], "new": new[:40]})
                    if text is not None:
                        p.write_text(text, encoding="utf-8")
                        patched.append({"path": fpath, "patches_applied": patch_log})
                except Exception as e:
                    failed.append({"path": fpath, "reason": str(e)})
                continue

            failed.append({"path": fpath, "reason": "path or content missing"})

        return {
            "files_written": written,
            "files_patched": patched,
            "files_failed": failed,
            "total": len(files_to_write),
        }

    async def close(self):
        await self._exit_stack.aclose()
