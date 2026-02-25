# OpenCode MCP 서버 추가 방법

## 설정 파일 위치

OpenCode의 설정 파일은 다음 경로에 있습니다:

```bash
~/.config/opencode/opencode.json
```

## 설정 형식

OpenCode 설정 파일의 형식은 다음과 같습니다:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "서버_이름": {
      "type": "local",
      "command": [
        "/full/path/to/executable",
        "/path/to/script"
      ],
    }
  }
}
```

## agent-factory 설정

### 자동 설정 (권장)

```bash
cd $WORKDIR/agent-factory
./opencode-integrate.sh
```

이 스크립트가 `~/.config/opencode/opencode.json`의 `mcp` 객체에 자동으로 다음을 추가합니다:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "agent-factory": {
      "type": "local",
      "command": [
        "$WORKDIR/agent-factory/venv/bin/python",
        "-m",
        "agent_factory.mcp_server"
      ],
      "cwd": "$WORKDIR/agent-factory",
      "env": {
        "PYTHONPATH": "$WORKDIR/agent-factory/src"
      }
    }
  }
}
```

## OpenCode에서 사용

1. OpenCode 재시작
2. MCP 서버가 자동으로 로드됩니다
3. MCP 툴을 사용할 수 있습니다:
   - `execute_workflow` - 완전한 워크플로우 실행
   - `define_problem` - 문제 정의
   - `collect_data` - 데이터 수집
   - `preprocess_data` - 데이터 전처리
   - `design_architecture` - 아키텍처 설계
   - `generate_implementation` - 코드 생성
   - `optimize_process` - 최적화
   - `evaluate_results` - 결과 평가
   - `deploy_system` - 시스템 배포
   - `monitor_system` - 시스템 모니터링
   - `submit_work_plan` - 작업 계획 제출
   - `approve_work_plan` - 작업 계획 승인
   - `reject_work_plan` - 작업 계획 거절

## 다른 MCP 서버와 함께 사용

다른 MCP 서버들(`search` 등)은 `~/.config/opencode/opencode.json`의 `mcp` 객체 아래에 이미 존재합니다. `opencode-integrate.sh` 스크립트가 기존 설정을 보존하면서 agent-factory를 추가합니다.

## 문제 해결

### 서버가 로드되지 않음

1. venv가 존재하는지 확인:
   ```bash
   ls -la $WORKDIR/agent-factory/venv/bin/python
   ```

2. MCP 모듈 설치 확인:
   ```bash
   source $WORKDIR/agent-factory/venv/bin/activate
   python -c "import mcp; print('MCP OK')"
   ```

3. OpenCode 로그 확인 (Ctrl+Shift+I)

4. 설정 파일 구문 확인:
   ```bash
   cat ~/.config/opencode/opencode.json | python -m json.tool
   ```

### 툴이 나타나지 않음

1. MCP 서버가 실행 중인지 확인:
   ```bash
   source $WORKDIR/agent-factory/venv/bin/activate
   python -m agent_factory.mcp_server
   ```

2. OpenCode 재시작

3. opencode-integrate.sh가 제대로 실행되었는지 확인:
   ```bash
   cd $WORKDIR/agent-factory
   ./opencode-integrate.sh
   ```
