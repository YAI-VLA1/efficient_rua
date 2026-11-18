"""Render the corrected primary measurements and positive controls on one A4 page."""
import csv
from pathlib import Path
from matplotlib import font_manager as fm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

root=Path(__file__).resolve().parents[1]
rows={(r['model'],r['condition']):r for r in csv.DictReader((root/'results.csv').open())}
q='Qwen3-14B-AWQ'
g='openai_gpt-oss-20b'
def counts(model):
    return ' / '.join(str(rows[model,c]['successes'])+'회' if (model,c) in rows else '미실행' for c in ('C1','C2','C3'))
fig=plt.figure(figsize=(8.27,11.69),facecolor='white')
def line(y,text,size=10,bold=False):
    font='/usr/share/fonts/truetype/nanum/NanumGothic'+('Bold' if bold else '')+'.ttf'
    fig.text(.075,y,text,va='top',fontproperties=fm.FontProperties(fname=font,size=size),linespacing=1.48)
line(.951,'Peg Insert  /  독립 trial 재실험',12,True)
line(.911,'매회 IK를 초기화한 뒤 다시 측정한 삽입 성공률',20,True)
line(.86,'같은 시뮬레이터 정답 포즈를 사용했다. C1은 원본 포즈, C2는 오프셋 조회 추가,\nC3는 목표 포즈 조회 추가다. 각 시드의 초기 자세와 프롬프트 차이를 대조했다.')
ax=fig.add_axes([.06,.50,.88,.32])
ax.imshow(Image.open(root/'success-rates.png'))
ax.axis('off')
line(.495,'환경 검증',13,True)
line(.461,'홈 복귀를 추가하지 않고 원본 오라클과 C3 오라클이 각각 20/20회 성공했다.\n50개 자세에서 C2 오프셋 부호가 일치했고 C3 위치의 최대 오차는 2.3×10⁻¹⁶ m 미만이었다.'.replace('2.3×10⁻¹⁶','0.00000000000000023'))
line(.386,'새로 생성한 코드',13,True)
line(.351,'GPT-OSS-20B(Groq)는 19/50 → 13/50 → 10/50이었다. C1과 C3의 공통 시드에서\n성공으로 바뀐 경우는 5개, 실패로 바뀐 경우는 14개였다(정확 McNemar p=0.064).\n평균 출력은 1,814 → 811토큰으로 줄었다. 성공률 개선은 관찰되지 않았다.')
if (q,'C1') in rows:
    rate=100*float(rows[q,'C1']['execution_rate'])
    line(.254,f'대체 모델 Qwen3-14B의 C1 코드 실행률은 {rate:.0f}%였다.\nC1 / C2 / C3 삽입 성공은 조건당 50회 중 {counts(q)}였다.')
line(.176,'비교 범위',13,True)
line(.141,'GPT-OSS와 Qwen3-14B는 새 코드를 생성했다. Qwen2.5-7B와 Astra는 기존 코드를\n수정된 환경에서 다시 실행했다. Astra는 Codex 전용 컨텍스트를 사용했다.\n한 가지 정답 포즈 태스크의 결과이며 모델 전반의 능력 차이로 일반화하기 어렵다.')
line(.055,'성공은 robosuite 내장 판정 · 주 지표 구간은 Wilson 95% · Astra는 조건당 20회',8)
fig.savefig(root/'report-ko.pdf')
