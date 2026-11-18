# 독립 trial 재실험

CaP-X 리비전 53e9966d7a8e2fa7494676772bccc35280f5c0ed와 conditions.patch를 사용했다. 원본 API와 프롬프트는 보존했다. 실행 진입점 run.py가 매 환경 reset 전에 privileged API의 직전 역기구학 해를 지운다. 홈 복귀 동작을 생성 코드에 추가하지 않는다. 시드를 robosuite의 배치 RNG에 전달하고 실제 반환 포즈를 저장한다.

## 실행 환경

CaP-X를 /root/cap-x에 체크아웃하고 robosuite 및 sam3 서브모듈을 초기화한다. conditions.patch 적용 뒤 uv sync --frozen --python 3.11 --extra robosuite로 설치한다. libegl1과 libgl1이 필요하다. 생성 코드는 별도 사용자 capxtrial로 실행한다. 아래 예시에서 /root/capx-backup/corrected/runs는 해당 사용자가 쓰기 가능한 빈 디렉터리이며, experiment는 이 스크립트 디렉터리다. 기존 측정 결과에 덮어쓰지 않도록 새 출력 위치를 사용할 수 있다.

## 검증 및 주 분석

```bash
cd /root/capx-backup/corrected
runuser -u capxtrial -- experiment/run.sh oracle C1 20 4 --use-oracle-code True
runuser -u capxtrial -- env C3_VALIDATION=1 experiment/run.sh oracle C3 20 4 --use-oracle-code True
PYTHONPATH=/root/cap-x /root/cap-x/.venv/bin/python experiment/verify_frames.py runs/poses/oracle/C1
```

별도 터미널에서 experiment/router.py를 실행한다. 사용자의 ~/.openrouter-key에서 인증하고 공급자는 Groq 하나로 고정한다. 두 오라클이 각각 18/20 이상이고 포즈 검증을 통과하면 실행한다.

```bash
for c in C1 C2 C3; do
    runuser -u capxtrial -- experiment/run.sh openai/gpt-oss-20b "$c" 50 4
done
```

HTTP 429 등으로 응답을 받지 못한 trial은 실패로 채점하지 않는다. trial 디렉터리에서 빠진 번호만 MISSING_TRIALS(쉼표 구분)로 전달하여 같은 모델·조건·시드로 다시 실행한다. 집계 전 조건별 고유 시드 수를 확인한다.

## 모델 교체와 기존 코드 대조

Qwen3-14B-AWQ는 HF 리비전 31c69efc29464b6bb0aee1398b5a7b50a99340c3, vLLM 0.15.0, 단일 RTX 3090을 사용한다. 모델은 /root/qwen14-weights, vLLM 환경은 /root/qwen-serving이다. qwen14-server.sh와 local_models.py를 실행하고 screen_qwen.sh로 C1 코드 실행률을 먼저 검사한다. 35/50 이상이면 같은 설정으로 C2와 C3를 진행한다.

Qwen2.5-Coder-7B와 Astra는 이전에 생성한 응답을 동일 시드에 대응시킨 다음 수정된 환경에서 전부 재실행한다. 이 대조는 프로그램을 고정하고 시뮬레이터 수정을 격리한다. 토큰은 원래 생성 시점의 기록이고 재실행에는 생성 비용이 들지 않는다. 소스 해시로 토큰을 연결하려면 기존 local-usage.jsonl을 corrected/experiment/archived-local-usage.jsonl로 복사한다.

```bash
model=gpt-6-astra
cond=C1
runuser -u capxtrial -- env REPLAY_SOURCE=/root/capx-backup/runs/$model/$cond experiment/run.sh "$model" "$cond" 20 4
/root/cap-x/.venv/bin/python experiment/aggregate.py
/root/cap-x/.venv/bin/python experiment/effects.py
/root/cap-x/.venv/bin/python experiment/score_check.py
```

성공 판정은 내장 _check_success(), 신뢰구간은 Wilson 95%다. score_check.py는 'API 한 개만 추가됨', 동일 초기 자세 및 동일 시드 집합을 확인하고 짝지은 정확 McNemar 검정을 수행한다. 효과량의 보조 구간은 시드 단위 부트스트랩이다. Astra 전용 Codex 컨텍스트와 로컬 vLLM 모델 사이의 차이 때문에 모델 간 상호작용 해석에는 제약이 있다.

14B 모델은 기본 thinking 템플릿과 qwen3 reasoning parser를 사용했다. 프롬프트의 모델 호출 한도는 20,480토큰이다. 타이밍 점검에서 RTX 3090의 긴 응답이 기존 HTTP 180~200초 제한을 넘길 수 있어, 본 14B 실행 전에 로컬 모델 HTTP 대기 시간을 830/850초로 조정했다. 초기 점검 프로그램은 timing-pilot에 별도 보존했다. 본 비교의 세 조건에는 동일한 설정을 적용했다.
