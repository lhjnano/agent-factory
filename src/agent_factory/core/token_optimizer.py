"""
TokenOptimizer — agent-factory 토큰 절감 자동화 모듈

적용 전략:
  1. Context compression   — ctx dict가 임계치 초과 시 파일로 내려쓰고 경로만 전달
  2. Output format hint    — stage/work 별 출력 포맷 제약 자동 주입
  3. Stage bundling        — 의존성 없는 독립 stage를 asyncio.gather로 병렬 실행
  4. Dedup context         — 동일 키 중복 출력 제거 후 최신 값만 유지
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ctx 값을 파일로 내려쓰는 임계 문자 수 (≈ 5000 tokens)
# sw_implementation의 files_to_write는 압축하지 않고 메모리에서 직접 처리
_COMPRESS_THRESHOLD = 20000
_SHARED_DIR = Path("/tmp/agent_factory/shared")


# ---------------------------------------------------------------------------
# 1. Context compression
# ---------------------------------------------------------------------------

def compress_context(ctx: Dict[str, Any], workflow_id: str = "default") -> Dict[str, Any]:
    """
    ctx에서 _COMPRESS_THRESHOLD 를 넘는 값을 파일로 기록하고 경로 참조로 교체한다.

    반환 dict는 원본 ctx를 수정하지 않고 새 dict로 반환.
    파일 참조 형식: {"_file": "/tmp/agent_factory/shared/{workflow_id}/{key}.json"}
    """
    out: Dict[str, Any] = {}
    shared_dir = _SHARED_DIR / workflow_id
    shared_dir.mkdir(parents=True, exist_ok=True)

    for key, value in ctx.items():
        serialized = _serialize(value)
        if len(serialized) > _COMPRESS_THRESHOLD:
            file_path = shared_dir / f"{_safe_key(key)}.json"
            file_path.write_text(serialized, encoding="utf-8")
            out[key] = {"_file": str(file_path), "_summary": serialized[:200] + "..."}
        else:
            out[key] = value

    return out


def decompress_context(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """compress_context 역변환 — 에이전트가 실제 값이 필요할 때 호출."""
    out: Dict[str, Any] = {}
    for key, value in ctx.items():
        if isinstance(value, dict) and "_file" in value:
            try:
                out[key] = json.loads(Path(value["_file"]).read_text(encoding="utf-8"))
            except Exception:
                out[key] = value  # 파일 없으면 ref 그대로
        else:
            out[key] = value
    return out


def build_context_summary(ctx: Dict[str, Any]) -> str:
    """에이전트 프롬프트에 삽입할 컨텍스트 요약 (파일 참조 포함)."""
    lines = []
    for key, value in ctx.items():
        if isinstance(value, dict) and "_file" in value:
            lines.append(f"- {key}: [파일 참조: {value['_file']}]  요약={value.get('_summary','')[:100]}")
        else:
            v_str = _serialize(value)
            if len(v_str) > 200:
                lines.append(f"- {key}: {v_str[:200]}...")
            else:
                lines.append(f"- {key}: {v_str}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 2. Output format hint
# ---------------------------------------------------------------------------

OUTPUT_FORMAT_HINTS: Dict[str, str] = {
    "paths_only":    "응답 형식: 생성된 파일 경로 목록만. 설명/요약 불필요.",
    "brief":         "응답 형식: 핵심 결과만 3줄 이내. 코드 스니펫/전체 파일 내용 불필요.",
    "key_facts":     "응답 형식: 결정 사항과 변경된 파일 경로만. 상세 설명 불필요.",
    "full":          "",   # 제약 없음
}

# stage → 기본 output_format 매핑
_STAGE_DEFAULT_FORMAT: Dict[str, str] = {
    "problem_definition":   "brief",
    "data_collection":      "brief",
    "design_development":   "key_facts",
    "training_optimization":"brief",
    "evaluation_validation":"brief",
    "deployment_monitoring":"brief",
}


def get_output_format_hint(stage: str, override: str | None = None) -> str:
    fmt = override or _STAGE_DEFAULT_FORMAT.get(stage, "brief")
    return OUTPUT_FORMAT_HINTS.get(fmt, "")


def inject_output_format(user_request: str, stage: str, override: str | None = None) -> str:
    """user_request 끝에 출력 포맷 힌트를 추가한다."""
    hint = get_output_format_hint(stage, override)
    if hint:
        return f"{user_request}\n\n[출력 제약] {hint}"
    return user_request


# ---------------------------------------------------------------------------
# 3. Stage bundling — 의존성 없는 독립 stage 그룹으로 분리
# ---------------------------------------------------------------------------

def build_execution_plan(stages: List[str], dependencies: Dict[str, List[str]] | None = None) -> List[List[str]]:
    """
    stages 를 순서를 지키면서 병렬 실행 가능한 그룹으로 분리.

    dependencies: {"stage_b": ["stage_a"]} 형태 — stage_b는 stage_a 완료 후 실행.
    의존성이 없으면 stages를 단일 그룹으로 묶어 병렬 실행 가능하게 반환.

    반환: [[병렬그룹1], [병렬그룹2], ...]
    """
    if not dependencies:
        # 의존성 정보 없으면 전부 순차 (안전)
        return [[s] for s in stages]

    completed: set[str] = set()
    remaining = list(stages)
    plan: List[List[str]] = []

    while remaining:
        # 현재 완료된 것들을 기준으로 실행 가능한 stage 추출
        runnable = [
            s for s in remaining
            if all(dep in completed for dep in dependencies.get(s, []))
        ]
        if not runnable:
            # 순환 의존성 방지 — 나머지 순차 추가
            plan.append(remaining[:])
            break
        plan.append(runnable)
        for s in runnable:
            remaining.remove(s)
            completed.add(s)

    return plan


# ---------------------------------------------------------------------------
# 4. Dedup / prune context
# ---------------------------------------------------------------------------

def prune_context(ctx: Dict[str, Any], keep_keys: List[str] | None = None) -> Dict[str, Any]:
    """
    다음 stage에 전달할 ctx를 정리한다.
      - keep_keys 지정 시 해당 키만 유지
      - 지정 없으면 '_summary', '_file' 참조 외 큰 값 제거
    """
    if keep_keys is not None:
        return {k: v for k, v in ctx.items() if k in keep_keys}

    out: Dict[str, Any] = {}
    for k, v in ctx.items():
        if isinstance(v, dict) and "_file" in v:
            out[k] = v  # 파일 참조는 유지 (이미 압축됨)
        elif len(_serialize(v)) <= _COMPRESS_THRESHOLD:
            out[k] = v  # 작은 값 유지
        # 크고 파일 참조도 아닌 값은 제거 (compress_context 이후엔 이 케이스 없어야 함)
    return out


# ---------------------------------------------------------------------------
# 5. Stats tracking
# ---------------------------------------------------------------------------

class TokenSavingsTracker:
    """워크플로우 실행 동안 절감 통계를 누적."""

    def __init__(self):
        self._original_chars = 0
        self._compressed_chars = 0
        self._files_written: List[str] = []
        self._format_hints_applied: List[str] = []

    def record_compression(self, original_size: int, compressed_size: int, file_path: str):
        self._original_chars += original_size
        self._compressed_chars += compressed_size
        self._files_written.append(file_path)

    def record_format_hint(self, stage: str, fmt: str):
        self._format_hints_applied.append(f"{stage}:{fmt}")

    @property
    def savings_chars(self) -> int:
        return self._original_chars - self._compressed_chars

    @property
    def savings_pct(self) -> float:
        if self._original_chars == 0:
            return 0.0
        return self.savings_chars / self._original_chars * 100

    def summary(self) -> Dict[str, Any]:
        return {
            "original_chars": self._original_chars,
            "compressed_chars": self._compressed_chars,
            "savings_chars": self.savings_chars,
            "savings_pct": round(self.savings_pct, 1),
            "files_written": self._files_written,
            "format_hints_applied": self._format_hints_applied,
        }


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _serialize(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)


def _safe_key(key: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in key)[:64]
