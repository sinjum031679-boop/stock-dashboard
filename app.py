import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ══════════════════════════════════════════════════════════
# 페이지 설정
# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Kang's View",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
.main { padding: 0.2rem 0.5rem; }
.block-container { padding-top: 2rem; max-width: 100%; }
.metric-card {
    background: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 4px 8px;
    text-align: center;
}
.metric-val { font-size: 0.82rem; font-weight: 600; }
.metric-lbl { font-size: 0.62rem; color: #888; margin-top: 1px; }
.pos { color: #27ae60; }
.neg { color: #e74c3c; }
.card {
    background: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 8px;
    padding: 10px;
    margin-bottom: 8px;
}
h1, h2, h3 { color: #cdd6f4 !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 유틸 함수
# ══════════════════════════════════════════════════════════
def fmt2(v):
    """float를 소수점 2자리로 안전하게 변환"""
    try:
        return round(float(str(v).split('e')[0]), 2)
    except Exception:
        return 0.0

def chg_color(v):
    return "#27ae60" if v >= 0 else "#e74c3c"

def badge_html(tag):
    if tag == "매수":
        style = "background:rgba(39,174,96,.15);color:#27ae60;"
    elif tag == "매도":
        style = "background:rgba(231,76,60,.15);color:#e74c3c;"
    else:
        style = "background:#2a2a3e;color:#888;border:0.5px solid #313244;"
    return f'<span style="font-size:9px;font-weight:500;padding:1px 5px;border-radius:4px;{style}flex-shrink:0;">{tag}</span>'

# ══════════════════════════════════════════════════════════
# 상수 — S&P500
# ══════════════════════════════════════════════════════════
SP500_SECTORS = {
    "Technology":        ["MSFT","AAPL","NVDA","AVGO","AMD","ORCL","MU","AMAT","TXN","ADI","QCOM","INTC","CRM","NOW","PANW","CRWD","FTNT","KLAC","LRCX","MCHP"],
    "Consumer Cyclical": ["AMZN","TSLA","HD","MCD","NKE","SBUX","LOW","TJX","BKNG","MAR","HLT","CCL","RCL","F","GM","PHM","DHI","LEN"],
    "Communication":     ["GOOGL","META","NFLX","DIS","CMCSA","VZ","T","TMUS","CHTR","EA","TTWO"],
    "Financial":         ["JPM","BRK.B","V","MA","BAC","WFC","GS","MS","C","AXP","BLK","SCHW","CB","PGR","ALL","TRV","MET","PRU","AFL"],
    "Healthcare":        ["LLY","UNH","JNJ","ABT","PFE","MRK","TMO","DHR","MDT","SYK","BSX","ISRG","AMGN","GILD","BIIB","REGN"],
    "Industrials":       ["GE","CAT","BA","HON","RTX","LMT","NOC","GD","UPS","FDX","CSX","NSC","UNP","EMR","ETN","PH","ROK","AME"],
    "Consumer Defensive":["WMT","PG","COST","KO","PEP","PM","MO","CL","TGT","K","KHC","KMB","SYY","TSN","MNST","STZ"],
    "Energy":            ["XOM","CVX","COP","EOG","SLB","MPC","PSX","VLO","OXY","HAL","BKR"],
    "Utilities":         ["NEE","DUK","SO","D","EXC","AEP","XEL","ED","ETR","FE","PPL"],
    "Real Estate":       ["AMT","PLD","CCI","EQIX","PSA","O","WELL","SPG","AVB","EQR","DLR"],
    "Materials":         ["LIN","APD","SHW","ECL","PPG","DOW","LYB","CF","ALB","IFF"],
}

HEATMAP_SP500 = {
    "Technology":        ["MSFT","AAPL","NVDA","AVGO","AMD","ORCL","MU","AMAT","TXN","ADI"],
    "Consumer Cyclical": ["AMZN","TSLA","HD","MCD","NKE","SBUX"],
    "Communication":     ["GOOGL","META","NFLX","DIS"],
    "Financial":         ["JPM","BRK.B","V","MA","BAC","WFC"],
    "Healthcare":        ["LLY","UNH","JNJ","ABT","PFE"],
    "Industrials":       ["GE","CAT","BA","HON","RTX"],
    "Consumer Defensive":["WMT","PG","COST","KO","PEP"],
    "Energy":            ["XOM","CVX","COP"],
}

SP500_KR = {
    "MSFT":"마이크로소프트","AAPL":"애플","NVDA":"엔비디아","AVGO":"브로드컴","AMD":"에이엠디",
    "ORCL":"오라클","MU":"마이크론","AMAT":"어플라이드","TXN":"텍사스인스트루","ADI":"아날로그디바이",
    "QCOM":"퀄컴","INTC":"인텔","CRM":"세일즈포스","NOW":"서비스나우","PANW":"팔로알토",
    "CRWD":"크라우드스트라이크","FTNT":"포티넷","KLAC":"KLA코퍼레이션","LRCX":"램리서치","MCHP":"마이크로칩",
    "AMZN":"아마존","TSLA":"테슬라","HD":"홈디포","MCD":"맥도날드","NKE":"나이키",
    "SBUX":"스타벅스","LOW":"로우스","TJX":"TJ맥스","BKNG":"부킹홀딩스","MAR":"메리어트",
    "HLT":"힐튼","CCL":"카니발","RCL":"로얄캐리비안","F":"포드","GM":"제너럴모터스",
    "PHM":"풀테홈스","DHI":"DR호튼","LEN":"레나",
    "GOOGL":"구글","META":"메타","NFLX":"넷플릭스","DIS":"디즈니","CMCSA":"컴캐스트",
    "VZ":"버라이즌","T":"AT&T","TMUS":"T모바일","CHTR":"차터커뮤니케이션","EA":"일렉트로닉아츠","TTWO":"테이크투",
    "JPM":"JP모건","BRK.B":"버크셔해서웨이","V":"비자","MA":"마스터카드","BAC":"뱅크오브아메리카",
    "WFC":"웰스파고","GS":"골드만삭스","MS":"모건스탠리","C":"씨티그룹","AXP":"아메리칸익스프레스",
    "BLK":"블랙록","SCHW":"찰스슈왑","CB":"처브","PGR":"프로그레시브","ALL":"올스테이트",
    "TRV":"트래블러스","MET":"메트라이프","PRU":"프루덴셜","AFL":"에이플락",
    "LLY":"일라이릴리","UNH":"유나이티드헬스","JNJ":"존슨앤존슨","ABT":"애보트","PFE":"화이자",
    "MRK":"머크","TMO":"써모피셔","DHR":"다나허","MDT":"메드트로닉","SYK":"스트라이커",
    "BSX":"보스턴사이언티픽","ISRG":"인튜이티브서지컬","AMGN":"암젠","GILD":"길리어드","BIIB":"바이오젠","REGN":"리제네론",
    "GE":"제너럴일렉트릭","CAT":"캐터필러","BA":"보잉","HON":"허니웰","RTX":"레이시온",
    "LMT":"록히드마틴","NOC":"노스롭그루먼","GD":"제너럴다이내믹스",
    "UPS":"UPS","FDX":"페덱스","CSX":"CSX","NSC":"노퍽서던","UNP":"유니온퍼시픽",
    "EMR":"에머슨","ETN":"이튼","PH":"파커하니핀","ROK":"로크웰오토메이션","AME":"암텍",
    "WMT":"월마트","PG":"P&G","COST":"코스트코","KO":"코카콜라","PEP":"펩시코",
    "PM":"필립모리스","MO":"알트리아","CL":"콜게이트","TGT":"타깃","K":"켈로그",
    "KHC":"크래프트하인즈","KMB":"킴벌리클라크","SYY":"시스코","TSN":"타이슨푸드","MNST":"몬스터","STZ":"컨스텔레이션",
    "XOM":"엑슨모빌","CVX":"쉐브론","COP":"코노코필립스","EOG":"EOG리소시스",
    "SLB":"슐럼버거","MPC":"마라톤페트롤리엄","PSX":"필립스66","VLO":"발레로에너지",
    "OXY":"옥시덴탈","HAL":"할리버튼","BKR":"베이커휴즈",
    "NEE":"넥스트에라에너지","DUK":"듀크에너지","SO":"서던컴퍼니","D":"도미니언에너지",
    "EXC":"엑셀론","AEP":"아메리칸일렉트릭","XEL":"엑셀에너지","ED":"콘에디슨","ETR":"엔터지","FE":"퍼스트에너지","PPL":"PPL",
    "AMT":"아메리칸타워","PLD":"프롤로지스","CCI":"크라운캐슬","EQIX":"에퀴닉스",
    "PSA":"퍼블릭스토리지","O":"리얼티인컴","WELL":"웰타워","SPG":"사이먼프로퍼티",
    "AVB":"어밸론베이","EQR":"에퀴티레지덴셜","DLR":"디지털리얼티",
    "LIN":"린데","APD":"에어프로덕츠","SHW":"쉐윈윌리엄스","ECL":"에콜랩",
    "PPG":"PPG인더스트리즈","DOW":"다우","LYB":"라이온델바젤","CF":"CF인더스트리즈","ALB":"알베마를","IFF":"IFF",
}

# ══════════════════════════════════════════════════════════
# 상수 — 나스닥
# ══════════════════════════════════════════════════════════
NASDAQ_SECTORS = {
    "Technology":    ["MSFT","AAPL","NVDA","AVGO","AMD","QCOM","INTC","MU","AMAT","LRCX","KLAC","MCHP","ADI","TXN","ON"],
    "Communication": ["GOOGL","META","NFLX","CMCSA","TTWO","EA","MTCH"],
    "Healthcare":    ["AMGN","GILD","BIIB","REGN","ILMN","VRTX","IDXX"],
    "Consumer":      ["AMZN","TSLA","SBUX","BKNG","ABNB","LULU","NTES"],
    "Finance":       ["PYPL","COIN","HOOD"],
    "Other":         ["CRWD","PANW","FTNT","ZS","SNOW","PLTR","NOW","DDOG"],
}

HEATMAP_NASDAQ = {
    "Technology":    ["MSFT","AAPL","NVDA","AVGO","AMD","QCOM","MU","AMAT","LRCX","ADI"],
    "Communication": ["GOOGL","META","NFLX","CMCSA"],
    "Healthcare":    ["AMGN","GILD","BIIB","REGN"],
    "Consumer":      ["AMZN","TSLA","SBUX","BKNG"],
    "Finance":       ["PYPL","COIN"],
    "Other":         ["CRWD","PANW","SNOW","PLTR"],
}

NASDAQ_KR = {**SP500_KR,
    "ABNB":"에어비앤비","LULU":"룰루레몬","NTES":"넷이즈",
    "PYPL":"페이팔","COIN":"코인베이스","HOOD":"로빈후드",
    "ZS":"지스케일러","DDOG":"데이터독","VRTX":"버텍스파마",
    "ILMN":"일루미나","MTCH":"매치그룹","ON":"온세미컨덕터",
}

# ══════════════════════════════════════════════════════════
# 상수 — 국내 주식 (코스피 + 코스닥)
# ══════════════════════════════════════════════════════════
KOSPI_SECTORS = {
    "반도체·IT":   ["005930.KS","000660.KS","066570.KS","006400.KS","011070.KS"],
    "바이오·헬스": ["207940.KS","068270.KS","128940.KS","000100.KS"],
    "금융":        ["105560.KS","055550.KS","086790.KS","032830.KS"],
    "자동차·부품": ["005380.KS","000270.KS","012330.KS"],
    "화학·소재":   ["051910.KS","005490.KS","011170.KS","011780.KS"],
    "통신·플랫폼": ["035420.KS","035720.KS","017670.KS","030200.KS"],
}

KOSDAQ_SECTORS = {
    "바이오":      ["091990.KQ","196170.KQ","145020.KQ","214450.KQ"],
    "IT·소프트웨어":["035420.KQ","067160.KQ","053800.KQ"],
    "반도체 소재": ["357780.KQ","336370.KQ","122830.KQ"],
    "엔터·콘텐츠": ["041510.KQ","035900.KQ","263750.KQ"],
}

KR_NAMES = {
    "005930.KS":"삼성전자","000660.KS":"SK하이닉스","066570.KS":"LG전자",
    "006400.KS":"삼성SDI","011070.KS":"LG이노텍",
    "207940.KS":"삼성바이오","068270.KS":"셀트리온","128940.KS":"한미약품","000100.KS":"유한양행",
    "105560.KS":"KB금융","055550.KS":"신한지주","086790.KS":"하나금융","032830.KS":"삼성생명",
    "005380.KS":"현대차","000270.KS":"기아","012330.KS":"현대모비스",
    "051910.KS":"LG화학","005490.KS":"POSCO홀딩스","011170.KS":"롯데케미칼","011780.KS":"금호석유",
    "035420.KS":"네이버","035720.KS":"카카오","017670.KS":"SK텔레콤","030200.KS":"KT",
    "091990.KQ":"셀트리온헬스케어","196170.KQ":"알테오젠","145020.KQ":"휴젤","214450.KQ":"파마리서치",
    "067160.KQ":"아프리카TV","053800.KQ":"안랩","035420.KQ":"네이버(코스닥)",
    "357780.KQ":"솔브레인","336370.KQ":"솔브레인홀딩스","122830.KQ":"원익IPS",
    "041510.KQ":"에스엠","035900.KQ":"JYP엔터","263750.KQ":"펄어비스",
}

# ══════════════════════════════════════════════════════════
# 상수 — 잠재주 (미국 + 국내)
# ══════════════════════════════════════════════════════════
POTENTIAL_STOCKS = [
    # 미국
    {"ticker":"RGTI",    "name":"리게티컴퓨팅",    "country":"미국", "theme":["양자컴퓨터"],        "summary":"양자-클래식 하이브리드 선도. 구글·IBM 협력.","growth":142,"pos52":88,"mcap":"$1.8B","score":82},
    {"ticker":"IONQ",    "name":"아이온큐",         "country":"미국", "theme":["양자컴퓨터"],        "summary":"AWS·Azure 클라우드 통합. 오류율 개선.","growth":95,"pos52":79,"mcap":"$6.1B","score":74},
    {"ticker":"RKLB",    "name":"로켓랩",           "country":"미국", "theme":["우주"],              "summary":"소형 발사체 스페이스X 대안. 정부 계약 급증.","growth":78,"pos52":71,"mcap":"$10.8B","score":70},
    {"ticker":"MRVL",    "name":"마벨테크놀로지",   "country":"미국", "theme":["AI"],                "summary":"AI ASIC 맞춤 반도체. 아마존·구글 공급.","growth":87,"pos52":95,"mcap":"$112B","score":88},
    {"ticker":"SMCI",    "name":"슈퍼마이크로",     "country":"미국", "theme":["AI"],                "summary":"AI 서버 전문. 엔비디아 GPU 탑재 서버.","growth":110,"pos52":68,"mcap":"$28B","score":76},
    {"ticker":"PLTR",    "name":"팔란티어",         "country":"미국", "theme":["AI"],                "summary":"AI 데이터 분석 플랫폼. 정부·기업 계약 급증.","growth":36,"pos52":92,"mcap":"$58B","score":72},
    {"ticker":"ACHR",    "name":"아처에비에이션",   "country":"미국", "theme":["우주"],              "summary":"전기 항공 모빌리티(UAM). 시장 선도.","growth":120,"pos52":85,"mcap":"$2.1B","score":68},
    {"ticker":"QUBT",    "name":"퀀텀컴퓨팅",       "country":"미국", "theme":["양자컴퓨터"],        "summary":"소형 양자 컴퓨터 제조. NASA 협력.","growth":200,"pos52":76,"mcap":"$0.9B","score":65},
    # 국내
    {"ticker":"086520.KS","name":"에코프로",        "country":"국내", "theme":["2차전지"],           "summary":"양극재 소재 국내 1위. 북미 생산기지 확장.","growth":38,"pos52":94,"mcap":"₩6.2T","score":76},
    {"ticker":"373220.KS","name":"LG에너지솔루션",  "country":"국내", "theme":["2차전지"],           "summary":"배터리 글로벌 2위. GM·현대차 공급.","growth":22,"pos52":65,"mcap":"₩62T","score":70},
    {"ticker":"247540.KS","name":"에코프로비엠",    "country":"국내", "theme":["2차전지"],           "summary":"에코프로 핵심 자회사. 양극재 양산 확대.","growth":42,"pos52":82,"mcap":"₩8.2T","score":71},
    {"ticker":"196170.KQ","name":"알테오젠",        "country":"국내", "theme":["바이오"],            "summary":"피하주사 플랫폼. 글로벌 빅파마 기술이전.","growth":180,"pos52":91,"mcap":"₩4.8T","score":83},
    {"ticker":"214450.KQ","name":"파마리서치",      "country":"국내", "theme":["바이오"],            "summary":"리쥬란 의료기기 수출 급증. 아시아 확장.","growth":55,"pos52":78,"mcap":"₩1.2T","score":68},
]

# ══════════════════════════════════════════════════════════
# 상수 — 섹터 전망
# ══════════════════════════════════════════════════════════
SECTOR_DATA = [
    {"name":"AI · 반도체",     "chg": 3.42, "score":94, "badge":"급상승", "growth":96,"inflow":92,"theme":98,"risk":35},
    {"name":"우주 · 방산",     "chg": 2.18, "score":82, "badge":"상승중", "growth":85,"inflow":78,"theme":88,"risk":28},
    {"name":"금융",            "chg": 1.24, "score":74, "badge":"보통",   "growth":70,"inflow":75,"theme":65,"risk":42},
    {"name":"헬스케어 · 바이오","chg": 0.88, "score":68, "badge":"보통",   "growth":72,"inflow":65,"theme":70,"risk":55},
    {"name":"에너지",          "chg":-0.55, "score":52, "badge":"중립",   "growth":48,"inflow":55,"theme":45,"risk":62},
    {"name":"2차전지",         "chg":-2.10, "score":31, "badge":"침체",   "growth":28,"inflow":25,"theme":32,"risk":85},
]

SECTOR_ETFS = {
    "AI · 반도체":"SOXX", "우주 · 방산":"ITA", "금융":"XLF",
    "헬스케어 · 바이오":"XLV", "에너지":"XLE", "2차전지":"LIT",
}

# ══════════════════════════════════════════════════════════
# 상수 — 다음 분기 예측
# ══════════════════════════════════════════════════════════
NEXT_Q = {
    "AAPL":      {"date":"2026-08-26","eps":"2.07",    "rev":"91.56B","epsG":"+10.7%","revG":"+12.2%","q":"2026-Q3"},
    "MSFT":      {"date":"2026-08-27","eps":"3.68",    "rev":"74.21B","epsG":"+6.4%", "revG":"+5.9%", "q":"2026-Q4"},
    "NVDA":      {"date":"2026-08-27","eps":"1.12",    "rev":"51.80B","epsG":"+16.7%","revG":"+17.5%","q":"2026-Q2"},
    "TSLA":      {"date":"2026-07-22","eps":"0.52",    "rev":"23.10B","epsG":"+92.6%","revG":"+19.5%","q":"2026-Q2"},
    "AMZN":      {"date":"2026-07-31","eps":"1.71",    "rev":"163.5B","epsG":"+7.5%", "revG":"+5.0%", "q":"2026-Q2"},
    "GOOGL":     {"date":"2026-07-29","eps":"2.31",    "rev":"96.80B","epsG":"+9.0%", "revG":"+11.5%","q":"2026-Q2"},
    "META":      {"date":"2026-07-29","eps":"6.21",    "rev":"46.80B","epsG":"+18.1%","revG":"+14.2%","q":"2026-Q2"},
    "005930.KS": {"date":"2026-07-31","eps":"920원",   "rev":"82.5T", "epsG":"+5.6%", "revG":"+4.3%", "q":"2026-Q2"},
    "000660.KS": {"date":"2026-07-24","eps":"8,100원", "rev":"18.9T", "epsG":"+7.7%", "revG":"+7.1%", "q":"2026-Q2"},
}

# ══════════════════════════════════════════════════════════
# 상수 — 뉴스 · 발언
# ══════════════════════════════════════════════════════════
NEWS = [
    {"headline":"Fed, 6월 금리 동결 신호… 연내 2회 인하 전망 유지",       "source":"Bloomberg","time":"2시간 전","impact":"악재","tags":["연준","금리"]},
    {"headline":"NVIDIA, 블랙웰 울트라 출하 본격화… AI 수요 급증",        "source":"Reuters",  "time":"3시간 전","impact":"호재","tags":["NVDA","AI"]},
    {"headline":"S&P500, 5거래일 연속 상승… 기술주 중심 랠리",            "source":"CNBC",     "time":"4시간 전","impact":"호재","tags":["S&P500"]},
    {"headline":"삼성전자 HBM4 양산 앞당겨… SK하이닉스와 경쟁 가열",      "source":"한국경제", "time":"5시간 전","impact":"호재","tags":["삼성전자","HBM"]},
    {"headline":"미중 관세 협상 재개… 반도체·전기차 품목 제외 논의",       "source":"WSJ",      "time":"6시간 전","impact":"중립","tags":["무역","관세"]},
    {"headline":"국제유가 WTI 배럴당 $71 하락… OPEC+ 증산 우려",         "source":"Reuters",  "time":"9시간 전","impact":"악재","tags":["유가","에너지"]},
]

FIGURES = [
    {"name":"도널드 트럼프","role":"미국 대통령",  "quote":"우리는 중국과의 무역에서 엄청난 진전을 이루고 있다. 반도체 관세는 협상 카드로 활용할 것이다.","time":"1시간 전","tags":["무역","반도체"]},
    {"name":"제롬 파월",   "role":"연준 의장",    "quote":"인플레이션이 2% 목표로 지속 하락하는 것을 확인한 후 금리 인하를 검토할 것이다.","time":"3시간 전","tags":["금리","인플레이션"]},
    {"name":"젠슨 황",     "role":"NVIDIA CEO",   "quote":"AI 인프라 수요는 우리의 예상을 훨씬 뛰어넘고 있다. 블랙웰 수요는 공급을 크게 앞서고 있다.","time":"5시간 전","tags":["NVDA","AI"]},
    {"name":"이창용",      "role":"한국은행 총재", "quote":"국내 물가 안정세가 이어지고 있으나 환율 불확실성을 감안해 신중한 접근이 필요하다.","time":"6시간 전","tags":["금리","환율"]},
    {"name":"일론 머스크", "role":"Tesla CEO",    "quote":"테슬라의 자율주행 기술은 내년까지 완전 자율 수준에 도달할 것이다.","time":"8시간 전","tags":["TSLA","자율주행"]},
]

# ══════════════════════════════════════════════════════════
# 상수 — 디지털·실물 자산
# ══════════════════════════════════════════════════════════
COINS = [
    {"ticker":"BTC-USD","name":"비트코인","sym":"BTC","icon":"₿","color":"rgba(247,147,26,.15)","icolor":"#F7931A"},
    {"ticker":"ETH-USD","name":"이더리움","sym":"ETH","icon":"Ξ","color":"rgba(98,126,234,.15)","icolor":"#627EEA"},
    {"ticker":"SOL-USD","name":"솔라나",  "sym":"SOL","icon":"◎","color":"rgba(153,101,21,.15)","icolor":"#996615"},
    {"ticker":"BNB-USD","name":"바이낸스","sym":"BNB","icon":"B","color":"rgba(240,185,11,.15)","icolor":"#F0B90B"},
    {"ticker":"XRP-USD","name":"리플",    "sym":"XRP","icon":"X","color":"rgba(83,74,183,.15)", "icolor":"#534AB7"},
    {"ticker":"ADA-USD","name":"에이다",  "sym":"ADA","icon":"A","color":"rgba(29,158,117,.15)","icolor":"#0F6E56"},
]

ALT_COINS = [
    {"ticker":"SOL-USD","name":"솔라나",   "tag":"레이어1","summary":"ETH 대안. 디파이·NFT 생태계 급성장.","score":82},
    {"ticker":"AVAX-USD","name":"아발란체","tag":"레이어1","summary":"서브넷 기반 확장성. 기관 채택 증가.","score":74},
    {"ticker":"LINK-USD","name":"체인링크","tag":"오라클", "summary":"블록체인 오라클 1위. AI+블록체인 연결.","score":78},
    {"ticker":"DOT-USD","name":"폴카닷",   "tag":"인터체인","summary":"크로스체인 인터오퍼러빌리티 선도.","score":65},
]

COMMODITIES = [
    {"ticker":"GC=F",   "name":"금(Gold)",       "unit":"$/oz"},
    {"ticker":"SI=F",   "name":"은(Silver)",      "unit":"$/oz"},
    {"ticker":"CL=F",   "name":"WTI 원유",        "unit":"$/barrel"},
    {"ticker":"NG=F",   "name":"천연가스",         "unit":"$/MMBtu"},
    {"ticker":"HG=F",   "name":"구리",            "unit":"$/lb"},
]

FX_PAIRS = [
    {"ticker":"USDKRW=X","name":"달러/원",  "base":"USD","quote":"KRW"},
    {"ticker":"USDJPY=X","name":"달러/엔",  "base":"USD","quote":"JPY"},
    {"ticker":"EURUSD=X","name":"유로/달러","base":"EUR","quote":"USD"},
    {"ticker":"USDCNY=X","name":"달러/위안","base":"USD","quote":"CNY"},
]

# ══════════════════════════════════════════════════════════
# 캐시 함수
# ══════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def load_heatmap_data(sectors_key, kr_names_key, is_kr):
    sectors  = dict(sectors_key)
    kr_names = dict(kr_names_key)
    rows = []
    for sector, tickers in sectors.items():
        if not tickers:
            continue
        for ticker in tickers:
            kr = kr_names.get(ticker, ticker)
            try:
                fi     = yf.Ticker(ticker).fast_info
                price  = fi.last_price or 0
                prev   = fi.previous_close or price
                change = fmt2((price - prev) / prev * 100) if prev else 0.0
                mcap   = (fi.market_cap or 1e9) / 1e9
                label  = kr if is_kr else f"{ticker}\n{kr}"
                rows.append({"ticker":ticker,"name":label,"sector":sector,
                             "price":fmt2(price),"change":change,"mcap":fmt2(mcap)})
            except Exception:
                rows.append({"ticker":ticker,"name":kr,"sector":sector,
                             "price":0.0,"change":0.0,"mcap":10.0})
    return pd.DataFrame(rows)

@st.cache_data(ttl=300)
def load_all_tickers(sectors_dict, names_dict):
    rows = []
    for sector, tickers in sectors_dict.items():
        for ticker in tickers:
            try:
                fi     = yf.Ticker(ticker).fast_info
                price  = fi.last_price or 0
                prev   = fi.previous_close or price
                change = fmt2((price - prev) / prev * 100) if prev else 0.0
                rows.append({"ticker":ticker,"name":names_dict.get(ticker,ticker),
                             "sector":sector,"price":fmt2(price),"change":change})
            except Exception:
                rows.append({"ticker":ticker,"name":names_dict.get(ticker,ticker),
                             "sector":sector,"price":0.0,"change":0.0})
    return pd.DataFrame(rows)

@st.cache_data(ttl=600)
def load_detail(ticker):
    result = {"fast":{},"info":{},"hist":pd.DataFrame(),"inst":None,"insider":None,"earnings":None}
    try:
        fi = yf.Ticker(ticker).fast_info
        result["fast"] = {
            "price":  fmt2(fi.last_price or 0),
            "prev":   fmt2(fi.previous_close or 0),
            "high":   fmt2(fi.day_high or 0),
            "low":    fmt2(fi.day_low or 0),
            "volume": int(fi.three_month_average_volume or 0),
            "mcap":   int(fi.market_cap or 0),
        }
    except Exception: pass
    for key, fn in [
        ("hist",    lambda t: yf.Ticker(t).history(period="1y")),
        ("info",    lambda t: yf.Ticker(t).info),
        ("inst",    lambda t: yf.Ticker(t).institutional_holders),
        ("insider", lambda t: yf.Ticker(t).insider_transactions),
        ("earnings",lambda t: yf.Ticker(t).quarterly_income_stmt),
    ]:
        try:
            result[key] = fn(ticker)
        except Exception:
            pass
    return result

@st.cache_data(ttl=300)
def load_asset_price(ticker):
    """단일 자산 시세 로드 (코인/원자재/환율)"""
    try:
        fi    = yf.Ticker(ticker).fast_info
        price = fi.last_price or 0
        prev  = fi.previous_close or price
        change = fmt2((price - prev) / prev * 100) if prev else 0.0
        return {"price": fmt2(price), "change": change}
    except Exception:
        return {"price": 0.0, "change": 0.0}

@st.cache_data(ttl=300)
def load_asset_history(ticker, period="3mo"):
    """자산 가격 히스토리 로드"""
    try:
        return yf.Ticker(ticker).history(period=period)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_sector_realtime():
    result = []
    for sd in SECTOR_DATA:
        etf = SECTOR_ETFS.get(sd["name"])
        chg = sd["chg"]
        if etf:
            try:
                fi  = yf.Ticker(etf).fast_info
                p   = fi.last_price or 0
                pv  = fi.previous_close or p
                chg = fmt2((p - pv) / pv * 100) if pv else sd["chg"]
            except Exception:
                pass
        result.append({**sd, "chg": chg})
    return result

# ══════════════════════════════════════════════════════════
# 차트 함수
# ══════════════════════════════════════════════════════════
def make_treemap(df):
    df = df.copy()
    df["change"]     = df["change"].apply(fmt2)
    df["change_str"] = df["change"].apply(lambda x: f"{x:+.2f}%")
    fig = px.treemap(
        df,
        path=["sector","name"],
        values="mcap",
        color="change",
        color_continuous_scale=[(0,"#c0392b"),(0.5,"#444"),(1,"#27ae60")],
        color_continuous_midpoint=0,
        range_color=[-3, 3],
        custom_data=["ticker","price","change_str"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[2]}",
        hovertemplate="<b>%{label}</b><br>가격: %{customdata[1]:,.2f}<br>등락: %{customdata[2]}<extra></extra>",
        textfont_size=11,
        marker_line_width=2,
        marker_line_color="rgba(0,0,0,0.4)",
        marker_pad_t=18,
        maxdepth=2,
        root_color="rgba(0,0,0,0)",
    )
    fig.update_layout(
        margin=dict(t=0,l=0,r=60,b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=True,
        height=460,
    )
    fig.update_coloraxes(
        colorbar=dict(
            title=dict(text="등락률", font=dict(color="#888",size=10)),
            tickfont=dict(color="#888",size=9),
            thickness=12, len=0.8, x=1.01,
            tickvals=[-3,-2,-1,0,1,2,3],
            ticktext=["-3%","-2%","-1%","0","+1%","+2%","+3%"],
        )
    )
    return fig

def make_line_chart(hist, ticker, height=150):
    if hist is None or hist.empty:
        return None
    fig = go.Figure()
    close = hist["Close"].round(2)
    fig.add_trace(go.Scatter(
        x=hist.index, y=close,
        fill="tozeroy",
        fillcolor="rgba(39,174,96,0.08)",
        line=dict(color="#27ae60", width=1.5),
        name=ticker,
    ))
    fig.update_layout(
        margin=dict(t=5,l=0,r=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, color="#888"),
        yaxis=dict(showgrid=True, gridcolor="#313244", color="#888"),
        height=height,
        showlegend=False,
    )
    return fig

def make_bar_chart(hist, ticker, height=120):
    """월별 수익률 막대 차트"""
    if hist is None or hist.empty:
        return None
    monthly = hist["Close"].resample("ME").last().pct_change().dropna() * 100
    monthly = monthly.round(2)
    colors  = ["#27ae60" if v >= 0 else "#e74c3c" for v in monthly.values]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[d.strftime("%y.%m") for d in monthly.index],
        y=monthly.values,
        marker_color=colors,
        name=ticker,
    ))
    fig.update_layout(
        margin=dict(t=5,l=0,r=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, color="#888", tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor="#313244", color="#888", tickfont=dict(size=9)),
        height=height,
        showlegend=False,
    )
    return fig

def calc_indicators(hist):
    """기술적 지표 계산"""
    if hist is None or hist.empty:
        return {}
    close = hist["Close"].round(2)
    # RSI
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, 1e-10)
    rsi   = round(float((100 - 100 / (1 + rs)).iloc[-1]), 2) if len(rs) > 14 else 50.0
    # MACD
    ema12   = close.ewm(span=12).mean()
    ema26   = close.ewm(span=26).mean()
    macd    = round(float((ema12 - ema26).iloc[-1]), 2)
    signal  = round(float((ema12 - ema26).ewm(span=9).mean().iloc[-1]), 2)
    # 볼린저밴드
    ma20   = close.rolling(20).mean()
    std20  = close.rolling(20).std()
    upper  = float((ma20 + 2 * std20).iloc[-1]) if len(ma20.dropna()) > 0 else 0
    lower  = float((ma20 - 2 * std20).iloc[-1]) if len(ma20.dropna()) > 0 else 0
    ma20v  = round(float(ma20.iloc[-1]), 2) if len(ma20.dropna()) > 0 else 0
    curr   = float(close.iloc[-1])
    # 거래량
    avg_vol  = float(hist["Volume"].mean()) if "Volume" in hist.columns else 0
    curr_vol = float(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0
    vol_pct  = round((curr_vol / avg_vol - 1) * 100, 1) if avg_vol > 0 else 0
    # 52주
    high52 = float(close.rolling(252).max().iloc[-1]) if len(close) > 20 else curr
    low52  = float(close.rolling(252).min().iloc[-1]) if len(close) > 20 else curr
    pos52  = round((curr - low52) / (high52 - low52) * 100, 1) if high52 != low52 else 50.0
    return {
        "rsi": rsi, "macd": macd, "signal": signal,
        "upper_band": round(upper, 2), "lower_band": round(lower, 2),
        "ma20": ma20v, "vol_pct": vol_pct, "pos52": pos52, "curr_price": round(curr, 2),
    }

def calc_buy_sell(indicators, info):
    """매수/매도 종합 점수 계산"""
    score   = 0
    reasons = []
    rsi     = indicators.get("rsi", 50)
    macd    = indicators.get("macd", 0)
    signal  = indicators.get("signal", 0)
    curr    = indicators.get("curr_price", 0)
    ma20    = indicators.get("ma20", curr)
    lower   = indicators.get("lower_band", curr)
    upper   = indicators.get("upper_band", curr)
    vol_pct = indicators.get("vol_pct", 0)
    pos52   = indicators.get("pos52", 50)

    # 기술적 분석 (25%)
    ts = 0
    if rsi < 35:
        ts += 25; reasons.append(("매수", f"RSI {rsi} — 과매도 구간, 반등 가능성"))
    elif rsi > 70:
        ts -= 15; reasons.append(("매도", f"RSI {rsi} — 과매수 구간, 조정 가능성"))
    else:
        ts += 10; reasons.append(("중립", f"RSI {rsi} — 중립 구간"))
    if macd > signal:
        ts += 15; reasons.append(("매수", f"MACD 골든크로스 (MACD:{macd:+.2f})"))
    else:
        ts -= 10; reasons.append(("매도", f"MACD 데드크로스 (MACD:{macd:+.2f})"))
    if curr < lower * 1.02:
        ts += 15; reasons.append(("매수", "볼린저밴드 하단 근접 — 통계적 저점"))
    elif curr > upper * 0.98:
        ts -= 15; reasons.append(("매도", "볼린저밴드 상단 근접 — 과열 구간"))
    if curr > ma20:
        ts += 10; reasons.append(("매수", f"20일 이평선 상회 (MA20:{ma20:,.2f})"))
    else:
        ts -= 10; reasons.append(("매도", f"20일 이평선 하회 (MA20:{ma20:,.2f})"))
    score += max(min(ts, 25), 0)

    # 기업 분석 (25%)
    fs  = 0
    per = info.get("trailingPE")
    rev = info.get("revenueGrowth")
    if per and per < 20:
        fs += 15; reasons.append(("매수", f"PER {fmt2(per)}x — 저평가"))
    elif per and per > 50:
        fs -= 10; reasons.append(("매도", f"PER {fmt2(per)}x — 고평가"))
    if rev and rev > 0.1:
        fs += 15; reasons.append(("매수", f"매출 성장률 {fmt2(rev*100)}% — 견조한 성장"))
    elif rev and rev < 0:
        fs -= 10; reasons.append(("매도", f"매출 역성장 {fmt2(rev*100)}%"))
    score += max(min(fs, 25), 0)

    # 기관 투자의견 (20%)
    ins = 0
    target = info.get("targetMeanPrice")
    if target and curr > 0:
        up = (target - curr) / curr * 100
        if up > 15:
            ins += 20; reasons.append(("매수", f"기관 목표주가 ${fmt2(target)} — 상승여력 {fmt2(up)}%"))
        elif up < -5:
            ins -= 10; reasons.append(("매도", f"기관 목표주가 ${fmt2(target)} — 하락여지"))
        else:
            ins += 8; reasons.append(("중립", f"기관 목표주가 ${fmt2(target)} — 현재가 근접"))
    score += max(min(ins, 20), 0)

    # 매수세/매도세 (10%)
    ms = 0
    if vol_pct > 50:
        ms += 10; reasons.append(("매수", f"거래량 평균 대비 +{vol_pct}% — 매수세 강함"))
    elif vol_pct < -30:
        ms -= 5;  reasons.append(("매도", f"거래량 평균 대비 {vol_pct}% — 관심 감소"))
    else:
        ms += 5;  reasons.append(("중립", f"거래량 평균 대비 {vol_pct:+.1f}%"))
    score += max(min(ms, 10), 0)

    # 발전 가능성 (10%)
    ds = 0
    if pos52 > 80:
        ds += 10; reasons.append(("매수", f"52주 고점 {pos52}% — 강한 모멘텀"))
    elif pos52 < 30:
        ds += 5;  reasons.append(("중립", f"52주 저점 근처 {pos52}% — 저점 매수 가능성"))
    else:
        ds += 3
    score += max(min(ds, 10), 0)

    # 섹터·뉴스/심리 기본값 (10%)
    score += 5

    score    = max(min(score, 100), 0)
    buy_pct  = score
    sell_pct = 100 - score
    verdict  = "매수" if score >= 65 else ("매도" if score <= 35 else "관망")
    return score, buy_pct, sell_pct, verdict, reasons[:8]

# ══════════════════════════════════════════════════════════
# UI 컴포넌트 — 기업 정보 패널
# ══════════════════════════════════════════════════════════
def render_detail(selected, kr_names, is_kr, key_prefix):
    with st.spinner("로딩 중..."):
        detail = load_detail(selected)

    info    = detail["info"]
    hist    = detail["hist"]
    inst    = detail["inst"]
    insider = detail["insider"]
    earnings = detail["earnings"]
    fast    = detail.get("fast", {})

    price = fast.get("price") or fmt2(info.get("currentPrice") or info.get("regularMarketPrice") or 0)
    prev  = fast.get("prev")  or fmt2(info.get("previousClose") or price)
    chg   = fmt2((price - prev) / prev * 100) if prev else 0.0
    kr_name  = kr_names.get(selected, selected) if kr_names else selected
    currency = "원" if is_kr else "$"
    price_fmt = f"{int(price):,}{currency}" if is_kr else f"${price:,.2f}"
    color    = chg_color(chg)

    st.markdown(f"**{selected}** {kr_name}")
    st.markdown(
        f'<span style="font-size:1.2rem;font-weight:600;color:{color};">{chg:+.2f}%</span>'
        f'&nbsp;<span style="font-size:1rem;">{price_fmt}</span>',
        unsafe_allow_html=True,
    )

    chart = make_line_chart(hist, selected)
    if chart:
        st.plotly_chart(chart, use_container_width=True, key=f"{key_prefix}_chart_{selected}")

    t1, t2, t3, t4 = st.tabs(["시세","실적","기관매수","내부자"])

    with t1:
        high = fast.get("high") or fmt2(info.get("dayHigh") or 0)
        low  = fast.get("low")  or fmt2(info.get("dayLow") or 0)
        vol  = fast.get("volume") or info.get("volume") or 0
        prev_close = fast.get("prev") or fmt2(info.get("previousClose") or 0)
        mcap = fast.get("mcap") or info.get("marketCap") or 0
        per  = info.get("trailingPE")
        pbr  = info.get("priceToBook")
        div  = info.get("dividendYield")
        wk52h = fmt2(info.get("fiftyTwoWeekHigh") or 0)
        wk52l = fmt2(info.get("fiftyTwoWeekLow") or 0)
        vol_str  = f"{vol/1e6:.1f}M" if vol > 1e6 else f"{vol:,}"
        mcap_str = f"${mcap/1e9:.1f}B" if mcap and not is_kr else (f"{mcap/1e12:.1f}T원" if mcap else "-")
        def pf(v): return f"{int(v):,}{currency}" if is_kr else f"${v:,.2f}"
        ca, cb = st.columns(2)
        with ca:
            st.metric("시가",   pf(prev_close))
            st.metric("저가",   pf(low))
            st.metric("시총",   mcap_str)
            st.metric("PBR",   f"{fmt2(pbr)}x" if pbr else "-")
        with cb:
            st.metric("고가",   pf(high))
            st.metric("거래량", vol_str)
            st.metric("PER",   f"{fmt2(per)}x" if per else "-")
            st.metric("배당",  f"{fmt2(div*100)}%" if div else "-")
        st.caption(f"52주 고가: {pf(wk52h)} | 저가: {pf(wk52l)}")

    with t2:
        nq = NEXT_Q.get(selected)
        if nq:
            days   = (datetime.strptime(nq["date"],"%Y-%m-%d") - datetime.now()).days
            d_icon = "🔴" if days <= 14 else ("🟡" if days <= 30 else "🟢")
            st.info(f"**{nq['q']}** 발표예정: {nq['date']} {d_icon} D-{days}")
            ca, cb = st.columns(2)
            with ca: st.metric("EPS 예측", nq["eps"], nq["epsG"])
            with cb: st.metric("매출 예측", nq["rev"], nq["revG"])
        if earnings is not None and not earnings.empty:
            try:
                rows_e = []
                for col in earnings.columns[:4]:
                    rev_v = earnings.loc["Total Revenue", col] if "Total Revenue" in earnings.index else None
                    ni_v  = earnings.loc["Net Income", col]    if "Net Income" in earnings.index else None
                    rows_e.append({
                        "분기":  str(col)[:10],
                        "매출":  f"${rev_v/1e9:.2f}B" if rev_v and not is_kr else (f"{rev_v/1e12:.2f}T원" if rev_v else "-"),
                        "순이익":f"${ni_v/1e9:.2f}B"  if ni_v  and not is_kr else (f"{ni_v/1e12:.2f}T원"  if ni_v  else "-"),
                    })
                st.dataframe(pd.DataFrame(rows_e), use_container_width=True, hide_index=True)
            except Exception:
                st.info("실적 데이터 파싱 오류")
        else:
            st.info("실적 데이터 없음")

    with t3:
        if inst is not None and not inst.empty:
            try:
                df_i = inst.copy()
                df_i.columns = [str(c) for c in df_i.columns]
                if "% Out" in df_i.columns:
                    df_i["% Out"] = df_i["% Out"].apply(lambda x: f"{fmt2(x*100)}%" if x else "-")
                if "Value" in df_i.columns:
                    df_i["Value"] = df_i["Value"].apply(lambda x: f"${x/1e6:.1f}M" if x else "-")
                st.dataframe(df_i.head(10), use_container_width=True, hide_index=True)
            except Exception:
                st.info("기관 데이터 파싱 오류")
        else:
            st.info("기관 데이터 없음")

    with t4:
        if insider is not None and not insider.empty:
            try:
                df_in = insider.copy()
                df_in.columns = [str(c) for c in df_in.columns]
                col_map = {}
                for c in df_in.columns:
                    cl = c.lower()
                    if   "insider" in cl or "name"        in cl: col_map[c] = "이름"
                    elif "title"   in cl or "position"    in cl: col_map[c] = "직책"
                    elif "transact" in cl or "type"       in cl: col_map[c] = "구분"
                    elif "shares"  in cl:                        col_map[c] = "수량"
                    elif "value"   in cl:                        col_map[c] = "금액"
                    elif "date"    in cl:                        col_map[c] = "날짜"
                df_in = df_in.rename(columns=col_map)
                if "금액" in df_in.columns:
                    df_in["금액"] = df_in["금액"].apply(lambda x: f"${fmt2(x/1e6)}M" if x and x > 0 else "-")
                st.dataframe(df_in.head(8), use_container_width=True, hide_index=True)
            except Exception:
                st.info("내부자 거래 파싱 오류")
        else:
            st.info("내부자 거래 데이터 없음")

# ══════════════════════════════════════════════════════════
# UI 컴포넌트 — 매수/매도 분석 패널
# ══════════════════════════════════════════════════════════
def render_analysis(all_df, kr_names, is_kr, key_prefix):
    st.markdown("##### 매수/매도 분석")

    # 검색창 + 자동완성
    search_q = st.text_input(
        "종목 검색",
        placeholder="티커 또는 기업명 입력 (예: AAPL, 애플)",
        key=f"{key_prefix}_analysis_search",
        label_visibility="collapsed",
    )

    if search_q:
        sq = search_q.upper()
        matched = all_df[
            all_df["ticker"].str.upper().str.contains(sq) |
            all_df["name"].str.contains(search_q)
        ]
        if not matched.empty:
            options = matched["ticker"].tolist()
        else:
            options = all_df["ticker"].tolist()
    else:
        options = all_df["ticker"].tolist()

    analysis_ticker = st.selectbox(
        "종목 선택",
        options=options,
        format_func=lambda x: (
            f"{x}  {all_df[all_df['ticker']==x]['name'].values[0]}"
            if len(all_df[all_df['ticker']==x]) > 0 else x
        ),
        key=f"{key_prefix}_analysis_select",
        label_visibility="collapsed",
    )

    if not analysis_ticker:
        return

    with st.spinner("분석 중..."):
        a_detail = load_detail(analysis_ticker)

    indicators = calc_indicators(a_detail["hist"])
    if not indicators:
        st.info("분석 데이터를 불러올 수 없습니다.")
        return

    score, buy_pct, sell_pct, verdict, reasons = calc_buy_sell(indicators, a_detail["info"])

    # 미니 차트
    mini_fig = make_line_chart(a_detail["hist"], analysis_ticker, height=100)
    if mini_fig:
        st.plotly_chart(mini_fig, use_container_width=True, key=f"{key_prefix}_a_mini")

    c_bar, c_ind, c_ev, c_final = st.columns([2, 2, 3, 2])

    with c_bar:
        st.markdown("**매수세 vs 매도세**")
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:5px;margin-top:4px;">
          <span style="font-size:10px;color:#27ae60;font-weight:500;width:26px;">매수</span>
          <div style="flex:1;height:16px;background:#1e1e2e;border-radius:4px;overflow:hidden;display:flex;border:0.5px solid #313244;">
            <div style="width:{buy_pct}%;background:#27ae60;display:flex;align-items:center;justify-content:flex-end;padding-right:3px;">
              <span style="font-size:8px;color:white;font-weight:500;">{buy_pct}%</span>
            </div>
            <div style="width:{sell_pct}%;background:#e74c3c;display:flex;align-items:center;padding-left:3px;">
              <span style="font-size:8px;color:white;font-weight:500;">{sell_pct}%</span>
            </div>
          </div>
          <span style="font-size:10px;color:#e74c3c;font-weight:500;width:26px;text-align:right;">매도</span>
        </div>
        """, unsafe_allow_html=True)

    with c_ind:
        st.markdown("**기술적 지표**")
        rsi_c  = "#27ae60" if indicators["rsi"]<40  else ("#e74c3c" if indicators["rsi"]>70  else "#888")
        macd_c = "#27ae60" if indicators["macd"]>indicators["signal"] else "#e74c3c"
        curr   = indicators["curr_price"]
        band   = "하단" if curr < indicators["lower_band"]*1.05 else ("상단" if curr > indicators["upper_band"]*0.95 else "중간")
        band_c = "#27ae60" if band=="하단" else ("#e74c3c" if band=="상단" else "#888")
        ma_c   = "#27ae60" if curr > indicators["ma20"] else "#e74c3c"
        vol_c  = "#27ae60" if indicators["vol_pct"]>0  else "#e74c3c"
        p52_c  = "#27ae60" if indicators["pos52"]>70   else ("#e74c3c" if indicators["pos52"]<30 else "#888")
        for lbl, val, color in [
            ("RSI(14)",    str(indicators["rsi"]),        rsi_c),
            ("MACD",       f"{indicators['macd']:+.2f}",  macd_c),
            ("볼린저밴드", band,                           band_c),
            ("20일 이평선",f"${indicators['ma20']:,.2f}", ma_c),
            ("거래량",     f"{indicators['vol_pct']:+.1f}%", vol_c),
            ("52주 위치",  f"{indicators['pos52']}%",     p52_c),
        ]:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:2px 0;border-bottom:0.5px solid #313244;">'
                f'<span style="font-size:10px;color:#888;">{lbl}</span>'
                f'<span style="font-size:10px;font-weight:500;color:{color};">{val}</span></div>',
                unsafe_allow_html=True,
            )

    with c_ev:
        st.markdown("**매수/매도 근거**")
        for tag, text in reasons:
            st.markdown(
                f'<div style="display:flex;align-items:flex-start;gap:5px;padding:3px 0;border-bottom:0.5px solid #313244;">'
                f'{badge_html(tag)}'
                f'<span style="font-size:10px;color:#cdd6f4;line-height:1.4;">{text}</span></div>',
                unsafe_allow_html=True,
            )

    with c_final:
        vcolor  = "#27ae60" if verdict=="매수" else ("#e74c3c" if verdict=="매도" else "#888")
        vbg     = f"rgba({'39,174,96' if verdict=='매수' else ('231,76,60' if verdict=='매도' else '136,136,136')},.08)"
        vborder = f"rgba({'39,174,96' if verdict=='매수' else ('231,76,60' if verdict=='매도' else '136,136,136')},.3)"
        st.markdown(f"""
        <div style="background:{vbg};border:0.5px solid {vborder};border-radius:8px;padding:10px 12px;">
          <div style="font-size:10px;color:#888;margin-bottom:3px;">최종 추천</div>
          <div style="font-size:22px;font-weight:600;color:{vcolor};">{verdict}</div>
          <div style="font-size:10px;color:#888;margin-top:4px;">종합 점수</div>
          <div style="height:4px;background:#313244;border-radius:2px;overflow:hidden;margin:3px 0;">
            <div style="width:{score}%;height:100%;border-radius:2px;background:{vcolor};"></div>
          </div>
          <div style="font-size:11px;font-weight:500;color:{vcolor};">{score}점 / 100</div>
          <div style="font-size:9px;color:#555;margin-top:5px;">※ 참고용, 투자 책임은 본인에게</div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# UI 컴포넌트 — 시장 탭 (히트맵 + 기업정보 + 전체종목)
# ══════════════════════════════════════════════════════════
def render_market(heatmap_sectors, all_sectors, kr_names, is_kr, key_prefix):
    with st.spinner("실시간 데이터 로딩 중..."):
        df_map = load_heatmap_data(
            tuple((k, tuple(v)) for k, v in heatmap_sectors.items()),
            tuple(kr_names.items()),
            is_kr,
        )
        df_all = load_all_tickers(all_sectors, kr_names)

    # 요약 카드
    up  = int((df_all["change"] > 0).sum())
    dn  = int((df_all["change"] < 0).sum())
    avg = fmt2(df_all["change"].mean())
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-val pos">▲ {up}</div><div class="metric-lbl">상승</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-val neg">▼ {dn}</div><div class="metric-lbl">하락</div></div>', unsafe_allow_html=True)
    with c3:
        cls = "pos" if avg >= 0 else "neg"
        st.markdown(f'<div class="metric-card"><div class="metric-val {cls}">{avg:+.2f}%</div><div class="metric-lbl">평균</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card"><div class="metric-val">{len(df_all)}</div><div class="metric-lbl">전체</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # 3열 레이아웃
    col_detail, col_map, col_sidebar = st.columns([3, 4, 2])

    # 전체 종목 사이드바
    with col_sidebar:
        st.markdown("##### 전체 종목")
        search = st.text_input(
            "검색", placeholder="티커/기업명...",
            key=f"{key_prefix}_search", label_visibility="collapsed",
        )
        sort_opt = st.radio(
            "정렬", ["등락률↓","등락률↑","가나다"],
            horizontal=True, key=f"{key_prefix}_sort", label_visibility="collapsed",
        )
        df_f = df_all.copy()
        if search:
            mask = (
                df_f["ticker"].str.upper().str.contains(search.upper()) |
                df_f["name"].str.contains(search)
            )
            df_f = df_f[mask]
        if sort_opt == "등락률↓":   df_f = df_f.sort_values("change", ascending=False)
        elif sort_opt == "등락률↑": df_f = df_f.sort_values("change", ascending=True)
        else:                       df_f = df_f.sort_values("name")

        df_display = df_f[["ticker","name","change"]].copy()
        df_display.columns = ["티커","기업명","등락률(%)"]
        df_display["등락률(%)"] = df_display["등락률(%)"].apply(lambda x: f"{x:+.2f}%")
        selected_row = st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=420,
            on_select="rerun",
            selection_mode="single-row",
            key=f"{key_prefix}_table",
        )
        sel_rows = selected_row.selection.rows if hasattr(selected_row, "selection") else []
        selected = df_f.iloc[sel_rows[0]]["ticker"] if sel_rows else df_f.iloc[0]["ticker"]

    # 히트맵
    with col_map:
        st.markdown("##### 히트맵 (시가총액 기준)")
        fig = make_treemap(df_map)
        st.plotly_chart(
            fig, use_container_width=True,
            key=f"{key_prefix}_treemap",
            config={"scrollZoom":False,"doubleClick":False,"displayModeBar":False},
        )

    # 기업 정보
    with col_detail:
        st.markdown("##### 기업 정보")
        if selected:
            render_detail(selected, kr_names, is_kr, key_prefix)

    # 매수/매도 분석 (하단)
    st.markdown("---")
    render_analysis(df_all, kr_names, is_kr, key_prefix)

# ══════════════════════════════════════════════════════════
# UI 컴포넌트 — 투자 인사이트 탭
# ══════════════════════════════════════════════════════════
def render_insight():
    # ── 잠재주 발굴 ─────────────────────────────────────
    st.markdown("##### 잠재주 발굴")
    fc1, fc2, fc3 = st.columns([3, 3, 1])
    with fc1:
        country_filter = st.radio(
            "국적", ["전체","미국","국내"],
            horizontal=True, key="pot_country", label_visibility="collapsed",
        )
    with fc2:
        theme_filter = st.radio(
            "테마", ["전체","AI","양자컴퓨터","2차전지","바이오","우주"],
            horizontal=True, key="pot_theme", label_visibility="collapsed",
        )
    with fc3:
        full_scan = st.button("전체 조회하기", key="pot_full")

    # 국적 + 테마 필터 적용
    filtered = []
    for p in POTENTIAL_STOCKS:
        country_ok = (country_filter == "전체") or (p["country"] == country_filter)
        theme_ok   = (theme_filter   == "전체") or (theme_filter in p["theme"])
        if country_ok and theme_ok:
            filtered.append(p)

    # 실시간 데이터 로드
    if full_scan:
        with st.spinner("전체 종목 스캔 중..."):
            live = []
            for p in filtered:
                d = load_asset_price(p["ticker"])
                live.append({**p, "price":d["price"], "change":d["change"]})
        filtered = live
    else:
        for p in filtered:
            p.setdefault("price", 0.0)
            p.setdefault("change", 0.0)

    cols = st.columns(3)
    for i, p in enumerate(filtered):
        chg        = p.get("change", 0.0)
        price_str  = f"${p.get('price',0):,.2f}" if p["country"]=="미국" and p.get("price",0)>0 else (f"₩{int(p.get('price',0)):,}" if p.get("price",0)>0 else "")
        theme_tags = " ".join([
            f'<span style="font-size:9px;padding:1px 5px;border-radius:3px;background:rgba(83,74,183,.12);color:#534AB7;">{t}</span>'
            for t in p.get("theme",[])
        ])
        country_tag = f'<span style="font-size:9px;padding:1px 5px;border-radius:3px;background:rgba(39,174,96,.1);color:#27ae60;">{p["country"]}</span>'
        with cols[i % 3]:
            st.markdown(f"""
            <div class="card">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:5px;">
                <div>
                  <span style="font-size:13px;font-weight:500;color:#cdd6f4;">{p['ticker']}</span>
                  <span style="font-size:10px;color:#888;margin-left:5px;">{p['name']}</span>
                </div>
                <div style="text-align:right;">
                  <div style="font-size:11px;font-weight:500;color:{chg_color(chg)};">{chg:+.2f}%</div>
                  <div style="font-size:10px;color:#888;">{price_str}</div>
                </div>
              </div>
              <div style="display:flex;gap:3px;margin-bottom:5px;">{country_tag}{theme_tags}</div>
              <div style="font-size:10px;color:#888;line-height:1.4;margin-bottom:5px;">{p['summary']}</div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:3px;margin-bottom:5px;">
                <div style="background:#313244;border-radius:4px;padding:3px 6px;">
                  <div style="font-size:8px;color:#888;">매출 성장률</div>
                  <div style="font-size:10px;font-weight:500;color:#27ae60;">+{p['growth']}%</div>
                </div>
                <div style="background:#313244;border-radius:4px;padding:3px 6px;">
                  <div style="font-size:8px;color:#888;">52주 위치</div>
                  <div style="font-size:10px;font-weight:500;color:#cdd6f4;">{p['pos52']}%</div>
                </div>
              </div>
              <div style="display:flex;align-items:center;gap:5px;">
                <span style="font-size:9px;color:#888;">잠재력</span>
                <div style="flex:1;height:4px;background:#313244;border-radius:2px;overflow:hidden;">
                  <div style="width:{p['score']}%;height:100%;border-radius:2px;background:#27ae60;"></div>
                </div>
                <span style="font-size:10px;font-weight:500;color:#27ae60;">{p['score']}점</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ── 섹터 전망 ────────────────────────────────────────
    st.markdown("##### 섹터 전망")
    sc1, sc2 = st.columns([5, 1])
    with sc1:
        sec_sort = st.radio(
            "정렬", ["종합점수순","등락률순","자금유입순"],
            horizontal=True, key="sec_sort", label_visibility="collapsed",
        )
    with sc2:
        sec_full = st.button("전체 조회하기", key="sec_full")

    sec_data = load_sector_realtime() if sec_full else list(SECTOR_DATA)

    if sec_sort == "등락률순":
        sec_data = sorted(sec_data, key=lambda x: x["chg"], reverse=True)
    elif sec_sort == "자금유입순":
        sec_data = sorted(sec_data, key=lambda x: x["inflow"], reverse=True)
    else:
        sec_data = sorted(sec_data, key=lambda x: x["score"], reverse=True)

    sec_cols = st.columns(3)
    for i, s in enumerate(sec_data):
        s_color = "#27ae60" if s["score"]>=70 else ("#e74c3c" if s["score"]<40 else "#854F0B")
        if s["badge"] in ["급상승","상승중"]:
            b_style = "background:rgba(39,174,96,.15);color:#27ae60;"
        elif s["badge"] == "침체":
            b_style = "background:rgba(231,76,60,.15);color:#e74c3c;"
        else:
            b_style = "background:#2a2a3e;color:#888;border:0.5px solid #313244;"
        bars = ""
        for bl, bk, bc in [
            ("성장성","growth", "#27ae60" if s["growth"]>=60 else "#854F0B"),
            ("자금유입","inflow","#27ae60" if s["inflow"]>=60 else "#854F0B"),
            ("테마인기","theme", "#27ae60" if s["theme"] >=60 else "#854F0B"),
            ("리스크","risk",   "#e74c3c" if s["risk"]  >=60 else "#27ae60"),
        ]:
            bars += (
                f'<div style="display:flex;align-items:center;gap:5px;margin-bottom:2px;">'
                f'<span style="font-size:8px;color:#888;width:40px;flex-shrink:0;">{bl}</span>'
                f'<div style="flex:1;height:3px;background:#313244;border-radius:2px;overflow:hidden;">'
                f'<div style="width:{s[bk]}%;height:100%;background:{bc};border-radius:2px;"></div></div>'
                f'<span style="font-size:8px;font-weight:500;color:{bc};width:20px;text-align:right;">{s[bk]}</span></div>'
            )
        with sec_cols[i % 3]:
            st.markdown(f"""
            <div class="card">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:5px;">
                <div>
                  <div style="font-size:12px;font-weight:500;color:#cdd6f4;">{s['name']}</div>
                  <div style="font-size:10px;color:{chg_color(s['chg'])};">{s['chg']:+.2f}% 이번주</div>
                </div>
                <span style="font-size:9px;color:#555;">#{i+1}</span>
              </div>
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                <span style="font-size:18px;font-weight:500;color:{s_color};">{s['score']}점</span>
                <span style="font-size:9px;font-weight:500;padding:2px 6px;border-radius:4px;{b_style}">{s['badge']}</span>
              </div>
              {bars}
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# UI 컴포넌트 — 디지털·실물 자산 탭
# ══════════════════════════════════════════════════════════
def render_asset():
    sub1, sub2, sub3, sub4 = st.tabs(["코인","귀금속·원자재","환율","코인 분석"])

    # ── 코인 시세 ────────────────────────────────────────
    with sub1:
        st.markdown("##### 주요 코인 실시간 시세")
        coin_cols = st.columns(3)
        for i, c in enumerate(COINS):
            d = load_asset_price(c["ticker"])
            p, chg = d["price"], d["change"]
            color  = chg_color(chg)
            with coin_cols[i % 3]:
                st.markdown(f"""
                <div class="card" style="display:flex;align-items:center;gap:10px;">
                  <div style="width:32px;height:32px;border-radius:50%;background:{c['color']};
                       display:flex;align-items:center;justify-content:center;
                       font-size:14px;font-weight:500;color:{c['icolor']};flex-shrink:0;">{c['icon']}</div>
                  <div style="flex:1;">
                    <div style="font-size:12px;font-weight:500;color:#cdd6f4;">{c['name']} <span style="font-size:10px;color:#888;">{c['sym']}</span></div>
                    <div style="font-size:14px;font-weight:500;color:#cdd6f4;">${p:,.2f}</div>
                  </div>
                  <div style="font-size:13px;font-weight:500;color:{color};">{chg:+.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("##### 주목할 알트코인")
        alt_cols = st.columns(4)
        for i, a in enumerate(ALT_COINS):
            d   = load_asset_price(a["ticker"])
            chg = d["change"]
            with alt_cols[i % 4]:
                st.markdown(f"""
                <div class="card">
                  <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                    <span style="font-size:12px;font-weight:500;color:#cdd6f4;">{a['name']}</span>
                    <span style="font-size:11px;font-weight:500;color:{chg_color(chg)};">{chg:+.2f}%</span>
                  </div>
                  <span style="font-size:9px;padding:1px 5px;border-radius:3px;background:rgba(83,74,183,.12);color:#534AB7;">{a['tag']}</span>
                  <div style="font-size:10px;color:#888;line-height:1.4;margin-top:4px;">{a['summary']}</div>
                  <div style="display:flex;align-items:center;gap:5px;margin-top:5px;">
                    <span style="font-size:9px;color:#888;">잠재력</span>
                    <div style="flex:1;height:3px;background:#313244;border-radius:2px;overflow:hidden;">
                      <div style="width:{a['score']}%;height:100%;background:#27ae60;border-radius:2px;"></div>
                    </div>
                    <span style="font-size:10px;font-weight:500;color:#27ae60;">{a['score']}점</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    # ── 귀금속·원자재 ────────────────────────────────────
    with sub2:
        st.markdown("##### 귀금속 · 원자재")
        for c in COMMODITIES:
            d    = load_asset_price(c["ticker"])
            hist = load_asset_history(c["ticker"])
            p, chg = d["price"], d["change"]
            color  = chg_color(chg)
            col_info, col_line, col_bar = st.columns([1, 2, 2])
            with col_info:
                st.markdown(f"""
                <div class="card" style="height:100%;">
                  <div style="font-size:13px;font-weight:500;color:#cdd6f4;">{c['name']}</div>
                  <div style="font-size:16px;font-weight:500;color:#cdd6f4;margin-top:4px;">{p:,.2f}</div>
                  <div style="font-size:11px;color:#888;">{c['unit']}</div>
                  <div style="font-size:14px;font-weight:500;color:{color};margin-top:4px;">{chg:+.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with col_line:
                fig = make_line_chart(hist, c["ticker"], height=100)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"com_line_{c['ticker']}")
                else:
                    st.caption("차트 데이터 없음")
            with col_bar:
                fig = make_bar_chart(hist, c["ticker"], height=100)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"com_bar_{c['ticker']}")
                else:
                    st.caption("월별 데이터 없음")
            st.markdown("---")

    # ── 환율 ─────────────────────────────────────────────
    with sub3:
        st.markdown("##### 환율")
        for fx in FX_PAIRS:
            d    = load_asset_price(fx["ticker"])
            hist = load_asset_history(fx["ticker"])
            p, chg = d["price"], d["change"]
            color  = chg_color(chg)
            col_info, col_line, col_bar = st.columns([1, 2, 2])
            with col_info:
                st.markdown(f"""
                <div class="card">
                  <div style="font-size:13px;font-weight:500;color:#cdd6f4;">{fx['name']}</div>
                  <div style="font-size:16px;font-weight:500;color:#cdd6f4;margin-top:4px;">{p:,.4f}</div>
                  <div style="font-size:14px;font-weight:500;color:{color};margin-top:4px;">{chg:+.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with col_line:
                fig = make_line_chart(hist, fx["ticker"], height=100)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"fx_line_{fx['ticker']}")
            with col_bar:
                fig = make_bar_chart(hist, fx["ticker"], height=100)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"fx_bar_{fx['ticker']}")
            st.markdown("---")

    # ── 코인 매수/매도 분석 ──────────────────────────────
    with sub4:
        st.markdown("##### 코인 매수/매도 분석")
        coin_options = [c["ticker"] for c in COINS] + [a["ticker"] for a in ALT_COINS]
        coin_names   = {c["ticker"]: f"{c['name']} ({c['sym']})" for c in COINS}
        coin_names.update({a["ticker"]: a["name"] for a in ALT_COINS})

        search_coin = st.text_input(
            "코인 검색",
            placeholder="예: BTC-USD, ETH-USD",
            key="coin_analysis_search",
            label_visibility="collapsed",
        )
        if search_coin:
            sq = search_coin.upper()
            matched = [t for t in coin_options if sq in t.upper() or sq in coin_names.get(t,"").upper()]
            opts = matched if matched else coin_options
        else:
            opts = coin_options

        sel_coin = st.selectbox(
            "코인 선택",
            options=opts,
            format_func=lambda x: coin_names.get(x, x),
            key="coin_analysis_select",
            label_visibility="collapsed",
        )

        if sel_coin:
            with st.spinner("코인 데이터 로딩 중..."):
                coin_hist = load_asset_history(sel_coin, "1y")
                coin_info = {}  # 코인은 기관/내부자 없음

            indicators = calc_indicators(coin_hist)
            if indicators:
                score, buy_pct, sell_pct, verdict, reasons = calc_buy_sell(indicators, coin_info)
                mini = make_line_chart(coin_hist, sel_coin, height=100)
                if mini:
                    st.plotly_chart(mini, use_container_width=True, key="coin_mini_chart")

                c_bar, c_ind, c_ev, c_final = st.columns([2,2,3,2])
                with c_bar:
                    st.markdown("**매수세 vs 매도세**")
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:5px;margin-top:4px;">
                      <span style="font-size:10px;color:#27ae60;font-weight:500;width:26px;">매수</span>
                      <div style="flex:1;height:16px;background:#1e1e2e;border-radius:4px;overflow:hidden;display:flex;border:0.5px solid #313244;">
                        <div style="width:{buy_pct}%;background:#27ae60;display:flex;align-items:center;justify-content:flex-end;padding-right:3px;">
                          <span style="font-size:8px;color:white;font-weight:500;">{buy_pct}%</span>
                        </div>
                        <div style="width:{sell_pct}%;background:#e74c3c;display:flex;align-items:center;padding-left:3px;">
                          <span style="font-size:8px;color:white;font-weight:500;">{sell_pct}%</span>
                        </div>
                      </div>
                      <span style="font-size:10px;color:#e74c3c;font-weight:500;width:26px;text-align:right;">매도</span>
                    </div>
                    """, unsafe_allow_html=True)
                with c_ind:
                    st.markdown("**기술적 지표**")
                    rsi_c  = "#27ae60" if indicators["rsi"]<40  else ("#e74c3c" if indicators["rsi"]>70 else "#888")
                    macd_c = "#27ae60" if indicators["macd"]>indicators["signal"] else "#e74c3c"
                    curr   = indicators["curr_price"]
                    band   = "하단" if curr<indicators["lower_band"]*1.05 else ("상단" if curr>indicators["upper_band"]*0.95 else "중간")
                    band_c = "#27ae60" if band=="하단" else ("#e74c3c" if band=="상단" else "#888")
                    ma_c   = "#27ae60" if curr>indicators["ma20"] else "#e74c3c"
                    for lbl, val, color in [
                        ("RSI(14)",    str(indicators["rsi"]),       rsi_c),
                        ("MACD",       f"{indicators['macd']:+.2f}", macd_c),
                        ("볼린저밴드", band,                          band_c),
                        ("20일 이평선",f"${indicators['ma20']:,.2f}", ma_c),
                        ("52주 위치",  f"{indicators['pos52']}%",    "#27ae60" if indicators["pos52"]>70 else "#888"),
                    ]:
                        st.markdown(
                            f'<div style="display:flex;justify-content:space-between;padding:2px 0;border-bottom:0.5px solid #313244;">'
                            f'<span style="font-size:10px;color:#888;">{lbl}</span>'
                            f'<span style="font-size:10px;font-weight:500;color:{color};">{val}</span></div>',
                            unsafe_allow_html=True,
                        )
                with c_ev:
                    st.markdown("**매수/매도 근거**")
                    for tag, text in reasons:
                        st.markdown(
                            f'<div style="display:flex;align-items:flex-start;gap:5px;padding:3px 0;border-bottom:0.5px solid #313244;">'
                            f'{badge_html(tag)}'
                            f'<span style="font-size:10px;color:#cdd6f4;line-height:1.4;">{text}</span></div>',
                            unsafe_allow_html=True,
                        )
                with c_final:
                    vcolor = "#27ae60" if verdict=="매수" else ("#e74c3c" if verdict=="매도" else "#888")
                    vbg    = f"rgba({'39,174,96' if verdict=='매수' else ('231,76,60' if verdict=='매도' else '136,136,136')},.08)"
                    vbrd   = f"rgba({'39,174,96' if verdict=='매수' else ('231,76,60' if verdict=='매도' else '136,136,136')},.3)"
                    st.markdown(f"""
                    <div style="background:{vbg};border:0.5px solid {vbrd};border-radius:8px;padding:10px 12px;">
                      <div style="font-size:10px;color:#888;margin-bottom:3px;">최종 추천</div>
                      <div style="font-size:22px;font-weight:600;color:{vcolor};">{verdict}</div>
                      <div style="height:4px;background:#313244;border-radius:2px;overflow:hidden;margin:6px 0 3px;">
                        <div style="width:{score}%;height:100%;border-radius:2px;background:{vcolor};"></div>
                      </div>
                      <div style="font-size:11px;font-weight:500;color:{vcolor};">{score}점 / 100</div>
                      <div style="font-size:9px;color:#555;margin-top:5px;">※ 코인은 변동성이 높습니다. 참고용으로만 활용하세요.</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("코인 데이터를 불러올 수 없습니다.")

# ══════════════════════════════════════════════════════════
# UI 컴포넌트 — 뉴스·발언 탭
# ══════════════════════════════════════════════════════════
def render_news():
    col_news, col_fig = st.columns(2)
    with col_news:
        st.markdown("##### 주요 시장 뉴스")
        for n in NEWS:
            icon = "🟢" if n["impact"]=="호재" else ("🔴" if n["impact"]=="악재" else "⚪")
            tags = " ".join(f"#{t}" for t in n["tags"])
            st.markdown(
                f'<div class="card">'
                f'<div style="font-size:.85rem;font-weight:500;">{icon} {n["headline"]}</div>'
                f'<div style="font-size:.72rem;color:#888;margin-top:3px;">{n["source"]} · {n["time"]} · {tags}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    with col_fig:
        st.markdown("##### 주요 인물 발언")
        for f in FIGURES:
            tags = " ".join(f"#{t}" for t in f["tags"])
            st.markdown(
                f'<div class="card">'
                f'<div style="font-size:.85rem;font-weight:600;">{f["name"]} '
                f'<span style="font-size:.75rem;color:#888;">| {f["role"]}</span></div>'
                f'<div style="font-size:.8rem;color:#ccc;margin:5px 0;padding:5px 8px;'
                f'background:#2a2a3e;border-left:3px solid #555;border-radius:0 4px 4px 0;">'
                f'"{f["quote"]}"</div>'
                f'<div style="font-size:.72rem;color:#888;">{f["time"]} · {tags}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════════════════
# 메인 헤더
# ══════════════════════════════════════════════════════════
col_h1, col_h2, col_h3 = st.columns([3, 5, 2])
with col_h1:
    st.markdown("#### 📈 Kang's View")
    st.caption("by 2.i.n.7.u.n")
with col_h2:
    st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  (5분마다 자동 갱신)")
with col_h3:
    if st.button("🔄 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ══════════════════════════════════════════════════════════
# 탭 구성
# ══════════════════════════════════════════════════════════
tab_us, tab_kr, tab_asset, tab_insight, tab_news = st.tabs([
    "🇺🇸 미국 주식",
    "🇰🇷 국내 주식",
    "💎 디지털·실물 자산",
    "💡 투자 인사이트",
    "📰 뉴스·발언",
])

with tab_us:
    us_sub1, us_sub2 = st.tabs(["S&P 500","나스닥"])
    with us_sub1:
        render_market(HEATMAP_SP500, SP500_SECTORS, SP500_KR, False, "sp500")
    with us_sub2:
        render_market(HEATMAP_NASDAQ, NASDAQ_SECTORS, NASDAQ_KR, False, "nasdaq")

with tab_kr:
    kr_sub1, kr_sub2 = st.tabs(["코스피","코스닥"])
    with kr_sub1:
        render_market(KOSPI_SECTORS, KOSPI_SECTORS, KR_NAMES, True, "kospi")
    with kr_sub2:
        render_market(KOSDAQ_SECTORS, KOSDAQ_SECTORS, KR_NAMES, True, "kosdaq")

with tab_asset:
    render_asset()

with tab_insight:
    render_insight()

with tab_news:
    render_news()

st.markdown("---")
st.caption("💡 데이터는 5분마다 자동 갱신됩니다. 본 자료는 참고용이며 투자 판단은 본인 책임입니다.")
