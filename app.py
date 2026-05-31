import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="주식 히트맵 대시보드", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.main{padding:0.5rem 1rem;}
.block-container{padding-top:1rem;max-width:100%;}
.metric-card{background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:10px 14px;text-align:center;}
.metric-val{font-size:1.2rem;font-weight:600;}
.metric-lbl{font-size:0.72rem;color:#888;margin-top:2px;}
.pos{color:#27ae60;}.neg{color:#e74c3c;}
.news-card{background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:10px;margin-bottom:6px;}
.figure-card{background:#1e1e2e;border:1px solid #313244;border-radius:8px;padding:10px;margin-bottom:6px;}
h1,h2,h3{color:#cdd6f4!important;}
</style>
""", unsafe_allow_html=True)

def fmt2(v):
    """float를 소수점 2자리 문자열로 강제 변환"""
    try:
        return round(float(str(v).split('e')[0]), 2)
    except:
        return 0.0

SP500_SECTORS = {
    "Technology": ["MSFT","AAPL","NVDA","AVGO","AMD","ORCL","MU","AMAT","TXN","ADI","QCOM","INTC","CRM","NOW","PANW","CRWD","FTNT","KLAC","LRCX","MCHP"],
    "Consumer Cyclical": ["AMZN","TSLA","HD","MCD","NKE","SBUX","LOW","TJX","BKNG","MAR","HLT","CCL","RCL","F","GM","PHM","DHI","LEN"],
    "Communication": ["GOOGL","META","NFLX","DIS","CMCSA","VZ","T","TMUS","CHTR","EA","TTWO"],
    "Financial": ["JPM","BRK.B","V","MA","BAC","WFC","GS","MS","C","AXP","BLK","SCHW","CB","PGR","ALL","TRV","MET","PRU","AFL"],
    "Healthcare": ["LLY","UNH","JNJ","ABT","PFE","MRK","TMO","DHR","MDT","SYK","BSX","ISRG","AMGN","GILD","BIIB","REGN"],
    "Industrials": ["GE","CAT","BA","HON","RTX","LMT","NOC","GD","UPS","FDX","CSX","NSC","UNP","EMR","ETN","PH","ROK","AME"],
    "Consumer Defensive": ["WMT","PG","COST","KO","PEP","PM","MO","CL","TGT","K","KHC","KMB","SYY","TSN","MNST","STZ"],
    "Energy": ["XOM","CVX","COP","EOG","SLB","MPC","PSX","VLO","OXY","HAL","BKR"],
    "Utilities": ["NEE","DUK","SO","D","EXC","AEP","XEL","ED","ETR","FE","PPL"],
    "Real Estate": ["AMT","PLD","CCI","EQIX","PSA","O","WELL","SPG","AVB","EQR","DLR"],
    "Materials": ["LIN","APD","SHW","ECL","PPG","DOW","LYB","CF","ALB","IFF"],
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

KR_SECTORS = {
    "반도체·IT":   ["005930.KS","000660.KS","066570.KS","006400.KS","011070.KS"],
    "바이오·헬스": ["207940.KS","068270.KS","128940.KS","000100.KS"],
    "금융":        ["105560.KS","055550.KS","086790.KS","032830.KS"],
    "자동차·부품": ["005380.KS","000270.KS","012330.KS"],
    "화학·소재":   ["051910.KS","005490.KS","011170.KS","011780.KS"],
    "통신·플랫폼": ["035420.KS","035720.KS","017670.KS","030200.KS"],
}
KR_NAMES = {
    "005930.KS":"삼성전자","000660.KS":"SK하이닉스","066570.KS":"LG전자","006400.KS":"삼성SDI","011070.KS":"LG이노텍",
    "207940.KS":"삼성바이오","068270.KS":"셀트리온","128940.KS":"한미약품","000100.KS":"유한양행",
    "105560.KS":"KB금융","055550.KS":"신한지주","086790.KS":"하나금융","032830.KS":"삼성생명",
    "005380.KS":"현대차","000270.KS":"기아","012330.KS":"현대모비스",
    "051910.KS":"LG화학","005490.KS":"POSCO홀딩스","011170.KS":"롯데케미칼","011780.KS":"금호석유",
    "035420.KS":"네이버","035720.KS":"카카오","017670.KS":"SK텔레콤","030200.KS":"KT",
}

HEATMAP_US = {
    "Technology":        ["MSFT","AAPL","NVDA","AVGO","AMD","ORCL","MU","AMAT","TXN","ADI"],
    "Consumer Cyclical": ["AMZN","TSLA","HD","MCD","NKE","SBUX"],
    "Communication":     ["GOOGL","META","NFLX","DIS"],
    "Financial":         ["JPM","BRK.B","V","MA","BAC","WFC"],
    "Healthcare":        ["LLY","UNH","JNJ","ABT","PFE"],
    "Industrials":       ["GE","CAT","BA","HON","RTX"],
    "Consumer Defensive":["WMT","PG","COST","KO","PEP"],
    "Energy":            ["XOM","CVX","COP"],
}

NEWS = [
    {"headline":"Fed, 6월 금리 동결 신호… 연내 2회 인하 전망 유지","source":"Bloomberg","time":"2시간 전","impact":"악재","tags":["연준","금리"]},
    {"headline":"NVIDIA, 차세대 블랙웰 울트라 출하 본격화… AI 수요 급증","source":"Reuters","time":"3시간 전","impact":"호재","tags":["NVDA","AI"]},
    {"headline":"S&P500, 5거래일 연속 상승… 기술주 중심 랠리","source":"CNBC","time":"4시간 전","impact":"호재","tags":["S&P500"]},
    {"headline":"삼성전자 HBM4 양산 앞당겨… SK하이닉스와 경쟁 가열","source":"한국경제","time":"5시간 전","impact":"호재","tags":["삼성전자","HBM"]},
    {"headline":"미중 관세 협상 재개… 반도체·전기차 품목 제외 논의","source":"WSJ","time":"6시간 전","impact":"중립","tags":["무역","관세"]},
    {"headline":"국제유가 WTI 배럴당 $71 하락… OPEC+ 증산 우려","source":"Reuters","time":"9시간 전","impact":"악재","tags":["유가","에너지"]},
]
FIGURES = [
    {"name":"도널드 트럼프","role":"미국 대통령","quote":"우리는 중국과의 무역에서 엄청난 진전을 이루고 있다. 반도체 관세는 협상 카드로 활용할 것이다.","time":"1시간 전","tags":["무역","관세","반도체"]},
    {"name":"제롬 파월","role":"연준 의장","quote":"인플레이션이 2% 목표로 지속 하락하는 것을 확인한 후 금리 인하를 검토할 것이다.","time":"3시간 전","tags":["금리","인플레이션"]},
    {"name":"젠슨 황","role":"NVIDIA CEO","quote":"AI 인프라 수요는 우리의 예상을 훨씬 뛰어넘고 있다. 블랙웰 수요는 공급을 크게 앞서고 있다.","time":"5시간 전","tags":["NVDA","AI"]},
    {"name":"이창용","role":"한국은행 총재","quote":"국내 물가 안정세가 이어지고 있으나 환율 불확실성을 감안해 신중한 접근이 필요하다.","time":"6시간 전","tags":["한국은행","금리","환율"]},
    {"name":"일론 머스크","role":"Tesla CEO","quote":"테슬라의 자율주행 기술은 내년까지 완전 자율 수준에 도달할 것이다.","time":"8시간 전","tags":["TSLA","자율주행"]},
]

@st.cache_data(ttl=300)
def load_heatmap_data(sectors, kr_names=None, is_kr=False):
    rows = []
    for sector, tickers in sectors.items():
        if not tickers: continue
        for ticker in tickers:
            try:
                info = yf.Ticker(ticker).fast_info
                price = info.last_price or 0
                prev  = info.previous_close or price
                change = fmt2((price - prev) / prev * 100) if prev else 0.0
                mcap   = (info.market_cap or 1e9) / 1e9
                kr = kr_names.get(ticker, ticker) if kr_names else ticker
                label = kr if is_kr else f"{ticker}\n{kr}"
                rows.append({"ticker":ticker,"name":label,"sector":sector,"price":fmt2(price),"change":change,"mcap":fmt2(mcap)})
            except:
                kr = (kr_names.get(ticker,ticker) if kr_names else ticker)
                rows.append({"ticker":ticker,"name":kr,"sector":sector,"price":0.0,"change":0.0,"mcap":10.0})
    return pd.DataFrame(rows)

@st.cache_data(ttl=300)
def load_all_sp500():
    rows = []
    for sector, tickers in SP500_SECTORS.items():
        for ticker in tickers:
            try:
                info = yf.Ticker(ticker).fast_info
                price = info.last_price or 0
                prev  = info.previous_close or price
                change = fmt2((price - prev) / prev * 100) if prev else 0.0
                rows.append({"ticker":ticker,"name":SP500_KR.get(ticker,ticker),"sector":sector,"price":fmt2(price),"change":change})
            except:
                rows.append({"ticker":ticker,"name":SP500_KR.get(ticker,ticker),"sector":sector,"price":0.0,"change":0.0})
    return pd.DataFrame(rows)

@st.cache_data(ttl=300)
def load_all_kr():
    rows = []
    for sector, tickers in KR_SECTORS.items():
        for ticker in tickers:
            try:
                info = yf.Ticker(ticker).fast_info
                price = info.last_price or 0
                prev  = info.previous_close or price
                change = fmt2((price - prev) / prev * 100) if prev else 0.0
                rows.append({"ticker":ticker,"name":KR_NAMES.get(ticker,ticker),"sector":sector,"price":int(price),"change":change})
            except:
                rows.append({"ticker":ticker,"name":KR_NAMES.get(ticker,ticker),"sector":sector,"price":0,"change":0.0})
    return pd.DataFrame(rows)

@st.cache_data(ttl=600)
def load_detail(ticker):
    result = {"fast":{},"info":{},"hist":pd.DataFrame(),"inst":None,"insider":None,"earnings":None}
    try:
        fi = yf.Ticker(ticker).fast_info
        result["fast"] = {
            "price": fmt2(fi.last_price or 0),
            "prev":  fmt2(fi.previous_close or 0),
            "high":  fmt2(fi.day_high or 0),
            "low":   fmt2(fi.day_low or 0),
            "volume": int(fi.three_month_average_volume or 0),
            "mcap":  int(fi.market_cap or 0),
        }
    except: pass
    try:
        result["hist"] = yf.Ticker(ticker).history(period="1y")
    except: pass
    try:
        result["info"] = yf.Ticker(ticker).info
    except: pass
    try:
        result["inst"] = yf.Ticker(ticker).institutional_holders
    except: pass
    try:
        result["insider"] = yf.Ticker(ticker).insider_transactions
    except: pass
    try:
        result["earnings"] = yf.Ticker(ticker).quarterly_income_stmt
    except: pass
    return result

def make_treemap(df):
    df = df.copy()
    df["change"] = df["change"].apply(fmt2)
    df["change_str"] = df["change"].apply(lambda x: f"{x:+.2f}%")
    fig = px.treemap(
        df, path=["sector","name"], values="mcap",
        color="change",
        color_continuous_scale=[(0,"#c0392b"),(0.5,"#444"),(1,"#27ae60")],
        color_continuous_midpoint=0, range_color=[-3,3],
        custom_data=["ticker","price","change_str"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[2]}",
        hovertemplate="<b>%{label}</b><br>가격: %{customdata[1]:,.2f}<br>등락: %{customdata[2]}<extra></extra>",
        textfont_size=11,
        marker_line_width=2,
        marker_line_color="rgba(0,0,0,0.4)",
        marker_pad_t=18,
    )
    fig.update_layout(
        margin=dict(t=0,l=0,r=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
        height=500,
    )
    return fig

def make_chart(hist, ticker):
    if hist is None or hist.empty: return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist.index, y=hist["Close"].round(2),
        fill="tozeroy", fillcolor="rgba(39,174,96,0.1)",
        line=dict(color="#27ae60",width=1.5), name=ticker,
    ))
    fig.update_layout(
        margin=dict(t=5,l=0,r=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False,color="#888"),
        yaxis=dict(showgrid=True,gridcolor="#313244",color="#888"),
        height=160, showlegend=False,
    )
    return fig

st.title("📈 주식 히트맵 대시보드")
col_r, col_t = st.columns([1,4])
with col_r:
    if st.button("🔄 새로고침"):
        st.cache_data.clear(); st.rerun()
with col_t:
    st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  (5분마다 자동 갱신)")

tab_us, tab_kr = st.tabs(["🇺🇸 S&P 500", "🇰🇷 코스피"])

NEXT_Q = {
    "AAPL":{"date":"2026-08-26","eps":"2.07","rev":"91.56B","epsG":"+10.7%","revG":"+12.2%","q":"2026-Q3"},
    "MSFT":{"date":"2026-08-27","eps":"3.68","rev":"74.21B","epsG":"+6.4%","revG":"+5.9%","q":"2026-Q4"},
    "NVDA":{"date":"2026-08-27","eps":"1.12","rev":"51.80B","epsG":"+16.7%","revG":"+17.5%","q":"2026-Q2"},
    "TSLA":{"date":"2026-07-22","eps":"0.52","rev":"23.10B","epsG":"+92.6%","revG":"+19.5%","q":"2026-Q2"},
    "AMZN":{"date":"2026-07-31","eps":"1.71","rev":"163.5B","epsG":"+7.5%","revG":"+5.0%","q":"2026-Q2"},
    "GOOGL":{"date":"2026-07-29","eps":"2.31","rev":"96.80B","epsG":"+9.0%","revG":"+11.5%","q":"2026-Q2"},
    "META":{"date":"2026-07-29","eps":"6.21","rev":"46.80B","epsG":"+18.1%","revG":"+14.2%","q":"2026-Q2"},
    "005930.KS":{"date":"2026-07-31","eps":"920원","rev":"82.5T","epsG":"+5.6%","revG":"+4.3%","q":"2026-Q2"},
    "000660.KS":{"date":"2026-07-24","eps":"8,100원","rev":"18.9T","epsG":"+7.7%","revG":"+7.1%","q":"2026-Q2"},
}

def render_detail(selected, kr_names, is_kr, key_prefix):
    with st.spinner("종목 데이터 로딩 중..."):
        detail = load_detail(selected)
    info   = detail["info"]
    hist   = detail["hist"]
    inst   = detail["inst"]
    insider = detail["insider"]
    earnings = detail["earnings"]

    fast  = detail.get("fast", {})
    price = fast.get("price") or fmt2(info.get("currentPrice") or info.get("regularMarketPrice") or 0)
    prev  = fast.get("prev") or fmt2(info.get("previousClose") or price)
    chg   = fmt2((price-prev)/prev*100) if prev else 0.0
    kr_name = kr_names.get(selected, selected) if kr_names else selected
    cls = "pos" if chg>=0 else "neg"
    currency = "원" if is_kr else "$"
    price_fmt = f"{int(price):,}{currency}" if is_kr else f"${price:,.2f}"

    st.markdown(f"##### {selected}  {kr_name}")
    st.markdown(f'<span class="{cls}" style="font-size:1.3rem;font-weight:600;">{chg:+.2f}%</span>&nbsp;&nbsp;<span style="font-size:1.1rem;">{price_fmt}</span>', unsafe_allow_html=True)

    chart = make_chart(hist, selected)
    if chart:
        st.plotly_chart(chart, use_container_width=True, key=f"{key_prefix}_chart_{selected}")

    t1,t2,t3,t4 = st.tabs(["시세","실적","기관매수","내부자"])

    with t1:
        high = fast.get("high") or fmt2(info.get("dayHigh") or 0)
        low  = fast.get("low") or fmt2(info.get("dayLow") or 0)
        vol  = fast.get("volume") or info.get("volume") or 0
        prev_close = fast.get("prev") or fmt2(info.get("previousClose") or 0)
        mcap = fast.get("mcap") or info.get("marketCap") or 0
        per  = info.get("trailingPE")
        pbr  = info.get("priceToBook")
        div  = info.get("dividendYield")
        wk52h = fmt2(info.get("fiftyTwoWeekHigh") or 0)
        wk52l = fmt2(info.get("fiftyTwoWeekLow") or 0)
        vol_str = f"{vol/1e6:.1f}M" if vol>1e6 else f"{vol:,}"
        mcap_str = f"${mcap/1e9:.1f}B" if mcap and not is_kr else (f"{mcap/1e12:.1f}T원" if mcap else "-")

        def pf(v): return f"{int(v):,}{currency}" if is_kr else f"${v:,.2f}"

        ca,cb = st.columns(2)
        with ca:
            st.metric("시가(전일종가)", pf(prev_close))
            st.metric("저가", pf(low))
            st.metric("시가총액", mcap_str)
            st.metric("PBR", f"{fmt2(pbr)}x" if pbr else "-")
        with cb:
            st.metric("고가", pf(high))
            st.metric("거래량", vol_str)
            st.metric("PER", f"{fmt2(per)}x" if per else "-")
            st.metric("배당수익률", f"{fmt2(div*100)}%" if div else "-")
        st.markdown(f"**52주 고가:** {pf(wk52h)}  |  **52주 저가:** {pf(wk52l)}")

    with t2:
        nq = NEXT_Q.get(selected)
        if nq:
            days = (datetime.strptime(nq["date"],"%Y-%m-%d") - datetime.now()).days
            d_icon = "🔴" if days<=14 else "🟡" if days<=30 else "🟢"
            st.info(f"**다음분기 예측 ({nq['q']})** | 발표 예정: {nq['date']} {d_icon} D-{days}")
            ca,cb = st.columns(2)
            with ca: st.metric("EPS 예측", nq["eps"], nq["epsG"])
            with cb: st.metric("매출 예측", nq["rev"], nq["revG"])
            st.markdown("---")

        st.markdown("**과거 실적 (분기)**")
        if earnings is not None and not earnings.empty:
            try:
                rows = []
                for col in earnings.columns[:5]:
                    rev = earnings.loc["Total Revenue", col] if "Total Revenue" in earnings.index else None
                    ni  = earnings.loc["Net Income", col] if "Net Income" in earnings.index else None
                    rows.append({
                        "분기": str(col)[:10],
                        "매출": f"${rev/1e9:.2f}B" if rev and not is_kr else (f"{rev/1e12:.2f}T원" if rev else "-"),
                        "순이익": f"${ni/1e9:.2f}B" if ni and not is_kr else (f"{ni/1e12:.2f}T원" if ni else "-"),
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            except:
                st.info("실적 데이터 파싱 중 오류")
        else:
            st.info("실적 데이터 없음")

    with t3:
        st.markdown("**기관 보유 현황 (실시간)**")
        if inst is not None and not inst.empty:
            try:
                df_i = inst.copy()
                df_i.columns = [str(c) for c in df_i.columns]
                if "% Out" in df_i.columns:
                    df_i["% Out"] = df_i["% Out"].apply(lambda x: f"{fmt2(x*100)}%" if x else "-")
                if "Value" in df_i.columns:
                    df_i["Value"] = df_i["Value"].apply(lambda x: f"${x/1e6:.1f}M" if x else "-")
                st.dataframe(df_i.head(15), use_container_width=True, hide_index=True)
            except:
                st.info("기관 데이터 파싱 중 오류")
        else:
            st.info("기관 데이터 없음")

    with t4:
        st.markdown("**내부자 거래 (실시간)**")
        if insider is not None and not insider.empty:
            try:
                df_in = insider.copy()
                df_in.columns = [str(c) for c in df_in.columns]
                col_map = {}
                for c in df_in.columns:
                    if "insider" in c.lower() or "name" in c.lower(): col_map[c] = "이름"
                    elif "title" in c.lower() or "position" in c.lower(): col_map[c] = "직책"
                    elif "transaction" in c.lower() or "type" in c.lower(): col_map[c] = "구분"
                    elif "shares" in c.lower(): col_map[c] = "수량"
                    elif "value" in c.lower(): col_map[c] = "금액"
                    elif "date" in c.lower(): col_map[c] = "날짜"
                df_in = df_in.rename(columns=col_map)
                if "금액" in df_in.columns:
                    df_in["금액"] = df_in["금액"].apply(lambda x: f"${fmt2(x/1e6)}M" if x and x>0 else "-")
                st.dataframe(df_in.head(10), use_container_width=True, hide_index=True)
            except:
                st.info("내부자 거래 데이터 파싱 중 오류")
        else:
            st.info("내부자 거래 데이터 없음")

def render_market(heatmap_sectors, all_data_fn, kr_names, is_kr, key_prefix):
    with st.spinner("실시간 데이터 로딩 중..."):
        df_map = load_heatmap_data(heatmap_sectors, kr_names, is_kr)
        df_all = all_data_fn()

    up  = int((df_all["change"]>0).sum())
    dn  = int((df_all["change"]<0).sum())
    avg = fmt2(df_all["change"].mean())
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-val pos">▲ {up}</div><div class="metric-lbl">상승</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-val neg">▼ {dn}</div><div class="metric-lbl">하락</div></div>', unsafe_allow_html=True)
    with c3:
        cls = "pos" if avg>=0 else "neg"
        st.markdown(f'<div class="metric-card"><div class="metric-val {cls}">{avg:+.2f}%</div><div class="metric-lbl">평균 등락률</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card"><div class="metric-val">{len(df_all)}</div><div class="metric-lbl">전체 종목</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    col_detail, col_map, col_sidebar = st.columns([2,5,2])

    with col_sidebar:
        st.markdown("##### 전체 종목")
        search = st.text_input("검색", placeholder="티커 또는 기업명...", key=f"{key_prefix}_search", label_visibility="collapsed")
        sort_opt = st.radio("정렬", ["등락률↓","등락률↑","가나다"], horizontal=True, key=f"{key_prefix}_sort", label_visibility="collapsed")

        df_f = df_all.copy()
        if search:
            df_f = df_f[df_f["ticker"].str.upper().str.contains(search.upper()) | df_f["name"].str.contains(search)]
        if sort_opt == "등락률↓": df_f = df_f.sort_values("change", ascending=False)
        elif sort_opt == "등락률↑": df_f = df_f.sort_values("change", ascending=True)
        else: df_f = df_f.sort_values("name")

        def fmt_label(row):
            chg = row["change"]
            sign = "▲" if chg>0 else "▼" if chg<0 else "―"
            return f"{row['ticker']} {row['name']} {sign}{abs(chg):.2f}%"

        options = df_f["ticker"].tolist()
        labels  = {row["ticker"]: fmt_label(row) for _, row in df_f.iterrows()}
        selected = st.radio("종목 선택", options, format_func=lambda x: labels.get(x,x), key=f"{key_prefix}_radio", label_visibility="collapsed")

    with col_map:
        st.markdown("##### 히트맵 (주요 종목, 시가총액 기준)")
        fig = make_treemap(df_map)
        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_treemap")

    with col_detail:
        if selected:
            render_detail(selected, kr_names, is_kr, key_prefix)

with tab_us:
    render_market(HEATMAP_US, load_all_sp500, SP500_KR, False, "us")

with tab_kr:
    render_market(KR_SECTORS, load_all_kr, KR_NAMES, True, "kr")

st.markdown("---")
col_news, col_fig = st.columns(2)
with col_news:
    st.markdown("#### 📰 주요 시장 뉴스")
    for n in NEWS:
        icon = "🟢" if n["impact"]=="호재" else "🔴" if n["impact"]=="악재" else "⚪"
        tags = " ".join([f"#{t}" for t in n["tags"]])
        st.markdown(f'<div class="news-card"><div style="font-size:.85rem;font-weight:500;">{icon} {n["headline"]}</div><div style="font-size:.72rem;color:#888;margin-top:3px;">{n["source"]} · {n["time"]} · {tags}</div></div>', unsafe_allow_html=True)

with col_fig:
    st.markdown("#### 🎙️ 주요 인물 발언")
    for f in FIGURES:
        tags = " ".join([f"#{t}" for t in f["tags"]])
        st.markdown(f'<div class="figure-card"><div style="font-size:.85rem;font-weight:600;">{f["name"]} <span style="font-size:.75rem;color:#888;">| {f["role"]}</span></div><div style="font-size:.8rem;color:#ccc;margin:5px 0;padding:5px 8px;background:#2a2a3e;border-left:3px solid #555;border-radius:4px;">"{f["quote"]}"</div><div style="font-size:.72rem;color:#888;">{f["time"]} · {tags}</div></div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("💡 데이터는 5분마다 자동 갱신됩니다. 수동 새로고침은 상단 버튼을 이용하세요.")
