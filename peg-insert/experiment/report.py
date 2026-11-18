from pathlib import Path
from matplotlib import font_manager as fm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

root=Path(__file__).resolve().parents[1]
regular='/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
bold='/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf'
fig=plt.figure(figsize=(8.27,11.69),facecolor='white')
def line(y,text,size=11,weight=False,color='#182631'):
    fig.text(.085,y,text,va='top',fontproperties=fm.FontProperties(fname=bold if weight else regular,size=size),
             color=color,linespacing=1.48)
line(.95,'Peg Insert  /  CaP-X S1',12,True,'#37606b')
line(.909,'목표 포즈 제공의 성공률 개선은 확인되지 않았다',19,True)
line(.855,'손잡이·너트 중심·peg의 시뮬레이터 정답 포즈를 모든 조건에 제공했다. C2에는\n포즈로부터 얻을 수 있는 오프셋 조회, C3에는 삽입 목표 포즈 조회를 각각 추가했다.',11)
ax=fig.add_axes([.065,.508,.87,.295]); ax.imshow(Image.open(root/'success-rates.png')); ax.axis('off')
line(.502,'성공률보다 크게 변한 출력 길이와 코드 실행률',13,True)
line(.465,'GPT-OSS-20B는 40% → 28% → 36%였다. C3 코드 50개 모두 목표 포즈\n함수 호출을 포함했고 평균 출력은 C1 1,783토큰에서 C3 724토큰으로 59% 줄었다.\nQwen의 코드 실행 성공률은 10% → 48% → 32%였지만 실제 삽입은\n0/50 → 1/50 → 2/50에 그쳤다. Astra(Codex)는 C1 17/20, C3 16/20이었다.')
line(.337,'가설 판정',13,True)
line(.303,'H1의 단조 증가는 Qwen에서만 관찰됐고, C1 대비 추가 성공은 2건이었다.\nH2도 확인되지 않았다. 공통 초기 상태 20개의 C3-C1 변화량을 Astra와 비교한\n차이는 Qwen +5%p(95% 구간 -10~+20), GPT-OSS -10%p(-40~+20)였다.')
line(.204,'검증과 한계',13,True)
line(.171,'C3는 매회 홈에서 시작한 오라클로 20/20 성공했다. 기존 워커가 이전 IK 해를\n재사용하면 원본 오라클과 C3 모두 6/20이었다. 동일 GPT-OSS C1 코드를 IK\n초기화 후 재실행하면 20/50에서 23/50으로 바뀌었다. 본 실험은 기존 S1 동작을\n유지했다. Astra는 독립 Codex 세션으로 실행해 모델과 실행 환경 효과가 섞인다.',10)
line(.061,'단일 태스크 · 경량 모델은 조건당 50회 · 성공률 막대 오차는 Wilson 95% · 변화량은 시드별 부트스트랩',8,False,'#3d5360')
fig.savefig(root/'report-ko.pdf',metadata={'Title':'Peg Insert 정보 형태 실험'})
