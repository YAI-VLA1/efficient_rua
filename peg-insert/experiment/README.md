# Peg Insert 실험 재현

CaP-X 리비전은 upstream-revision.txt에 기록했다. 원본 저장소에서 다음을 실행한다. 경로를 그대로 사용하려면 체크아웃은 /root/cap-x, 이 백업의 복구 경로는 /root/capx-backup으로 둔다.

```bash
git checkout 53e9966d7a8e2fa7494676772bccc35280f5c0ed
git submodule update --init --depth 1 capx/third_party/robosuite capx/third_party/sam3
git apply /root/capx-backup/conditions.patch
UV_CACHE_DIR=/dev/shm/capx-uv UV_LINK_MODE=copy uv sync --frozen --python 3.11 --extra robosuite
python /root/capx-backup/experiment/router.py
```

별도 터미널에서 아래 명령을 사용한다. 프록시 실행자 홈의 .openrouter-key에서 인증하고 시뮬레이터는 별도 OS 사용자 capxtrial로 실행한다. capxtrial에는 runs 디렉터리 쓰기 권한이 필요하다. 시뮬레이터는 PyRoKi를 자동으로 실행한다.

```bash
runuser -u capxtrial -- /root/capx-backup/experiment/run.sh openai/gpt-oss-20b C1 50 4
```

C1 재현 허용 범위는 11~20/50이다. 통과하고 실패 원인을 검토한 뒤 C3 검증을 실행한다.

```bash
runuser -u capxtrial -- env C3_VALIDATION=1 /root/capx-backup/experiment/run.sh oracle C3 20 4 --use-oracle-code True
```

C2 API와 C3 API는 capx/integrations/franka/nut_assembly_forms.py, 등록은 capx/integrations/__init__.py에 있다. 두 config는 env_configs/nut_assembly/franka_nut_c2.yaml 및 franka_nut_c3.yaml이다. C1은 원본 franka_robosuite_nut_assembly_privileged.yaml이다.

모든 조건에서 카메라 렌더링과 영상 기록을 끄고, 기본 단일 턴 프롬프트와 샘플링 설정을 사용한다. 물리 초기 배치는 trial 번호로 시드하고 반환된 포즈를 기록한다. 성공 판정은 trial 디렉터리의 taskcompleted 값이다. reward는 shaping을 포함한다. 토큰과 비용은 응답 본문의 해시로 OpenRouter 사용량 레코드와 연결한다.

C3 검증에서는 각 episode 시작 시 공개 홈 복귀 API를 호출하는 버전도 실행했다. 원본 오라클, C3, 홈 복귀 후 C3를 각각 다른 출력 루트에 보존한다.

```bash
runuser -u capxtrial -- env HOME_FIRST=1 C3_VALIDATION=1 RUN_ROOT=/root/capx-backup/validation /root/capx-backup/experiment/run.sh oracle C3 20 4 --use-oracle-code True
runuser -u capxtrial -- env RUN_ROOT=/root/capx-backup/independent REPLAY_SOURCE=/root/capx-backup/runs/openai_gpt-oss-20b/C1 /root/capx-backup/experiment/run.sh openai/gpt-oss-20b C1 50 4
```

Qwen 모델은 Qwen/Qwen2.5-Coder-7B-Instruct-AWQ, HF 리비전 8e8ed243bbe6f9a5aff549a0924562fc719b2b8a을 /root/qwen-weights에 복구한다. 별도 /root/qwen-serving 환경에 vllm==0.15.0을 설치하고 qwen-server.sh를 실행한다. vLLM과 Codex 참조군 모두 local_models.py 프록시를 거친다. 같은 폴더의 main.sh가 모델별 실행 명령을 포함한다. 코드 실행 성공률은 sandbox_rc==0, 태스크 성공률은 task_completed를 사용한다. 로컬 GPU 원가나 Codex 구독료의 trial별 청구 내역은 제공되지 않으므로 비용을 빈칸으로 둔다.

Astra C1의 본 비교는 20회로 고정했다. C1 실패 코드 표본을 보충하려고 diagnostic 디렉터리에 21번 이후의 별도 초기 상태를 기록했다. diagnostic, independent, validation의 trial은 results.csv의 본 비교에서 제외한다. API 목록 이외의 기본 태스크 프롬프트가 조건 간 같은지와 초기 포즈 일치를 확인했다. Astra는 Codex 전용 시스템 컨텍스트가 추가되고 temperature를 직접 고정할 수 없어 모델 간 비교는 참고용이다. 같은 모델 내 C1과 C3의 Codex 설정은 같다.

OpenRouter에서 공급자를 고정하지 않아 GPT-OSS 150개 응답이 8개 공급자로 라우팅됐다(132개는 Groq). trial당 실제 비용은 프록시가 받은 청구 usage.cost를 사용했다. Qwen은 GPU 로컬 서빙, Astra는 기존 구독 인증을 사용했다. Astra 토큰 수에는 Codex 컨텍스트가 포함된다.

효과 추정은 동일 초기 자세끼리 묶은 성공 여부 차이의 평균이다. 모델 간 상호작용은 공통 20개 시드만 사용한다. 효과 구간은 시드 단위 비모수 부트스트랩(20,000회)이며, 0건이나 1~2건의 희소 성공에서는 근사 구간의 정밀도가 낮다.

```bash
/root/cap-x/.venv/bin/python /root/capx-backup/experiment/aggregate.py
/root/cap-x/.venv/bin/python /root/capx-backup/experiment/effects.py
python /root/capx-backup/experiment/api-use.py
/root/cap-x/.venv/bin/python /root/capx-backup/experiment/report.py
```

Astra의 추가 진단 배치는 DIAGNOSTIC_START=21, total=55 및 DIAGNOSTIC_START=56, total=75로 실행했다. 기존 run.sh 명령에 RUN_ROOT=/root/capx-backup/diagnostic과 --server-url http://127.0.0.1:8112/chat/completions를 사용한다.
