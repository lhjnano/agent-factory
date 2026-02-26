# Context Management System 구현

## 개요

`~/source/agent-factory` 프로젝트에서 work 별 context 관리 부족 문제를 해결하기 위해 다음 기능을 구현했습니다.

## 문제점 분석

### 이전 문제

1. **Work 간 Context 공유 부족**
   - dependencies는 work_id만 참조하고, outputs를 직접 가져오는 메커니즘 없음
   - `orchestrator.py:168`에서 `inputs={"problem_def": work1.work_id}` 처럼 work_id만 전달

2. **Context 누적 불가**
   - Work가 진행될수록 context가 누적되는 구조가 없음
   - 이전 work의 결과들이 다음 work에 전달되지 않거나 수동으로 관리

3. **영속성 부족**
   - Context는 in-memory로만 관리되고 MCP storage 활용하지 않음

4. **Workflow 수준의 Context 없음**
   - 개별 work의 context만 존재하고, workflow 전체를 아우르는 context 부족

## 구현 내용

### 1. WorkContext (`src/agent_factory/core/context.py`)

개별 work의 context를 관리하는 클래스

```python
@dataclass
class WorkContext:
    work_id: str
    work_type: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    accumulated_context: Dict[str, Any]  # 누적되는 context
    metadata: Dict[str, Any]  # dependencies 등
```

**주요 기능:**
- `update_outputs()`: work의 결과를 업데이트
- `add_to_context()`: context에 데이터 추가
- `extend_context()`: context 병합

### 2. WorkflowContext (`src/agent_factory/core/context.py`)

Workflow 전체의 context를 관리하는 클래스

```python
@dataclass
class WorkflowContext:
    workflow_id: str
    name: str
    description: str
    work_contexts: Dict[str, WorkContext]  # 모든 work의 context
    global_context: Dict[str, Any]  # 전역 context
    dependency_chain: List[str]
```

**주요 기능:**
- `add_work_context()`: work context 추가
- `resolve_dependencies()`: dependencies의 outputs를 해결
- `get_full_context_for_work()`: work 실행에 필요한 전체 context 반환
- `merge_work_outputs_to_global()`: work 결과를 global context에 병합

### 3. ContextManager (`src/agent_factory/core/context_manager.py`)

Context를 통합 관리하고 영속성을 지원

```python
class ContextManager:
    def __init__(self):
        self._workflow_contexts: Dict[str, WorkflowContext] = {}
        self._memory_storage = None
        self._filesystem_storage = None
```

**주요 기능:**
- `create_workflow_context()`: workflow context 생성
- `create_work_context()`: work context 생성 및 dependencies 해결
- `update_work_outputs()`: work 결과 업데이트 및 global context로 전파
- `get_full_context_for_work()`: work 실행에 필요한 context 반환
- `save_workflow_context()`: context를 MCP storage에 저장
- `load_workflow_context()`: MCP storage에서 context 로드

### 4. Orchestrator 통합 (`src/agent_factory/core/orchestrator.py`)

MultiAgentOrchestrator에 ContextManager 통합

**변경 사항:**
- `self.context_manager = ContextManager()` 추가
- `set_mcp_sessions()`에서 context_manager에도 MCP sessions 전달
- `_execute_work()`에서 context 생성 및 주입 로직 추가
- `execute_workflow()`에서 workflow context 생성 및 저장 로직 추가

**Context 주입 방식:**
```python
if self._current_workflow_id:
    work_ctx = self.context_manager.create_work_context(
        workflow_id=self._current_workflow_id,
        work_id=work.work_id,
        work_type=work.work_type,
        inputs=work.inputs,
        dependencies=work.dependencies
    )
    
    full_context = self.context_manager.get_full_context_for_work(
        self._current_workflow_id,
        work.work_id
    )
    
    inputs_with_context = {
        **work.inputs,
        "_context": full_context  # context를 포함하여 handler에 전달
    }
```

## 사용 예시

### 예제 1: WorkContext 기본 사용

```python
work_ctx = WorkContext(
    work_id="work_001",
    work_type="data_collection",
    inputs={"source": "data.csv"}
)

work_ctx.update_outputs({"rows": 100, "columns": 5})
work_ctx.add_to_context("summary", {"total_rows": 100})
```

### 예제 2: WorkflowContext를 통한 dependency 해결

```python
workflow_ctx = WorkflowContext(
    workflow_id="workflow_001",
    name="ML Pipeline"
)

# data_collection work
work1 = WorkContext(work_id="data_collection", ...)
work1.update_outputs({"data": [[1, 2], [3, 4]]})
workflow_ctx.add_work_context(work1)

# preprocessing work (data_collection에 의존)
work2 = WorkContext(
    work_id="preprocessing",
    inputs={"data": "data_collection"}
)
work2.metadata["dependencies"] = ["data_collection"]

resolved = workflow_ctx.resolve_dependencies(
    "preprocessing", 
    ["data_collection"]
)
# resolved: {'data_collection': {'outputs': {...}, 'accumulated': {...}}}
```

### 예제 3: ContextManager 사용

```python
ctx_manager = ContextManager()

# Workflow context 생성
ctx_manager.create_workflow_context(
    workflow_id="workflow_002",
    name="Image Classification"
)

# Work context 생성 및 dependency 해결
ctx_manager.create_work_context(
    workflow_id="workflow_002",
    work_id="train_model",
    work_type="training",
    inputs={"model_config": "resnet50"},
    dependencies=["data_prep"]
)

# Work 결과 업데이트
ctx_manager.update_work_outputs(
    "workflow_002",
    "data_prep",
    {"train_images": 1000, "val_images": 200}
)

# Work 실행에 필요한 전체 context 조회
full_ctx = ctx_manager.get_full_context_for_work(
    "workflow_002", 
    "train_model"
)
```

### 예제 4: Context 누적 및 전파

```python
# Work가 완료될 때마다 context가 누적됨
for work in works:
    ctx_manager.create_work_context(
        workflow_id="workflow_003",
        work_id=work["id"],
        work_type=work["type"],
        inputs=work["inputs"],
        dependencies=work.get("deps", [])
    )
    
    ctx_manager.update_work_outputs(
        "workflow_003",
        work["id"],
        outputs[work["id"]]
    )
    
    # Global context에 이전 work들의 결과들이 누적됨
    print(ctx_manager.get_global_context("workflow_003"))
    # {'collect': {...}, 'process': {...}, 'analyze': {...}, ...}
```

## 영속성 지원

### Memory Storage
```python
await ctx_manager.save_workflow_context(workflow_id)
await ctx_manager.load_workflow_context(workflow_id)
```

### Filesystem Storage
```python
await ctx_manager.save_workflow_context(workflow_id)
# /tmp/agent_factory/workflow_contexts/{workflow_id}.json에 저장
```

## Work Handler에서 Context 사용

Work handler에서 `_context` key를 통해 context에 접근:

```python
async def my_handler(inputs: Dict[str, Any], agent: AgentInstance):
    context = inputs.get("_context", {})
    
    work_inputs = context.get("work_inputs", {})
    global_context = context.get("global_context", {})
    dependencies = context.get("resolved_dependencies", {})
    
    # dependencies의 outputs 사용
    prev_outputs = dependencies.get("dependency_work_id", {}).get("outputs", {})
    
    # 처리 수행
    result = process(work_inputs, prev_outputs, global_context)
    
    return result
```

## 파일 구조

```
src/agent_factory/core/
├── context.py              # WorkContext, WorkflowContext
├── context_manager.py      # ContextManager
├── work.py                # (기존 파일, 변경 없음)
├── orchestrator.py         # ContextManager 통합
└── __init__.py            # export 추가

example_context_standalone.py  # 예제 코드
```

## 주요 메서드 정리

### WorkContext
- `update_outputs(outputs)`: outputs 업데이트
- `add_to_context(key, value)`: context에 데이터 추가
- `extend_context(context)`: context 병합
- `get_full_context()`: 전체 context 반환

### WorkflowContext
- `add_work_context(work_context)`: work context 추가
- `get_work_context(work_id)`: work context 조회
- `get_work_outputs(work_id)`: work의 outputs 조회
- `resolve_dependencies(work_id, dependency_ids)`: dependencies 해결
- `add_global_context(key, value)`: global context 추가
- `get_full_context_for_work(work_id)`: work 실행에 필요한 전체 context 반환
- `merge_work_outputs_to_global(work_id)`: work 결과를 global context에 병합

### ContextManager
- `set_mcp_sessions(memory_session, filesystem_session)`: MCP sessions 설정
- `create_workflow_context(workflow_id, name, description)`: workflow context 생성
- `get_workflow_context(workflow_id)`: workflow context 조회
- `create_work_context(workflow_id, work_id, work_type, inputs, dependencies)`: work context 생성
- `get_work_context(workflow_id, work_id)`: work context 조회
- `update_work_outputs(workflow_id, work_id, outputs, propagate_to_global)`: work 결과 업데이트
- `get_full_context_for_work(workflow_id, work_id)`: work 실행에 필요한 context 반환
- `get_global_context(workflow_id)`: global context 조회
- `add_global_context(workflow_id, key, value)`: global context 추가
- `save_workflow_context(workflow_id)`: workflow context 저장
- `load_workflow_context(workflow_id)`: workflow context 로드
- `save_all_contexts()`: 모든 context 저장
- `clear_workflow_context(workflow_id)`: workflow context 삭제
- `clear_all_contexts()`: 모든 context 삭제

## 테스트 실행

```bash
cd ~/source/agent-factory
python3 example_context_standalone.py
```

## 향후 개선 사항

1. **Context 크기 제한**: 너무 큰 context를 방지하기 위한 크기 제한 및 pruning 기능
2. **Context TTL**: 일정 시간이 지난 context 자동 삭제
3. **Context Versioning**: context 버전 관리 및 롤백 지원
4. **Context Compression**: context 압축으로 토큰 사용량 최적화
5. **Context Visualization**: context 시각화 도구

## 결론

이 Context Management System을 통해:
- Work 간 context 공유가 자동화됨
- Work가 진행될수록 context가 누적됨
- Context가 영구적으로 저장됨
- Workflow 수준에서 context를 통합 관리할 수 있음
- Work handler에서 쉽게 context에 접근 가능
