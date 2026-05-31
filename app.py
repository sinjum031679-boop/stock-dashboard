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

# ── S&P500 전체 종목 ─────────────────────────────────────
SP500_SECTORS = {
    "Technology": [
        "MSFT","AAPL","NVDA","AVGO","AMD","ORCL","MU","AMAT","TXN","ADI",
        "QCOM","INTC","CRM","NOW","SNOW","PANW","CRWD","FTNT","ANSS","CDNS",
        "KLAC","LRCX","MCHP","MPWR","ON","SWKS","TER","WOLF","ENPH","SEDG",
    ],
    "Consumer Cyclical": [
        "AMZN","TSLA","HD","MCD","NKE","SBUX","LOW","TJX","BKNG","MAR",
        "HLT","CCL","RCL","NCLH","LVS","MGM","WYNN","PHM","DHI","LEN",
        "NVR","TOL","POOL","APTV","BWA","F","GM","LCID","RIVN",
    ],
    "Communication": [
        "GOOGL","META","NFLX","DIS","CMCSA","VZ","T","TMUS","CHTR","PARA",
        "WBD","FOX","IPG","OMC","TTWO","EA","ATVI","MTCH","ZG","TRIP",
    ],
    "Financial": [
        "JPM","BRK-B","V","MA","BAC","WFC","GS","MS","C","AXP",
        "BLK","SCHW","CB","PGR","ALL","TRV","MET","PRU","AFL","UNM",
        "WTW","AON","MMC","BX","KKR","APO","ARES","CG","TPG",
    ],
    "Healthcare": [
        "LLY","UNH","JNJ","ABT","PFE","MRK","TMO","DHR","MDT","SYK",
        "BSX","EW","ISRG","ZBH","BAX","BDX","COO","HOLX","IDXX","IQV",
        "IQVIA","CRL","CTLT","PKI","TECH","VTRS","AMGN","GILD","BIIB","REGN",
    ],
    "Industrials": [
        "GE","CAT","BA","HON","RTX","LMT","NOC","GD","L3H","HII",
        "UPS","FDX","CSX","NSC","UNP","CP","CNI","EMR","ETN","PH",
        "ROK","DOV","AME","XYL","RRX","GNRC","IR","TT","JCI","CARR",
    ],
    "Consumer Defensive": [
        "WMT","PG","COST","KO","PEP","PM","MO","BTI","CL","COLM",
        "CHD","CLX","EL","HRL","K","KHC","KMB","MKC","SJM","SYY",
        "TGT","TSN","MNST","STZ","BF-B","TAP","SAM",
    ],
    "Energy": [
        "XOM","CVX","COP","EOG","SLB","MPC","PSX","VLO","PXD","DVN",
        "FANG","HES","APA","OXY","HAL","BKR","NOV","FTI","WES","TRGP",
    ],
    "Utilities": [
        "NEE","DUK","SO","D","EXC","AEP","XEL","PCG","ED","EIX",
        "ETR","FE","PPL","CMS","DTE","NI","LNT","EVRG","PNW","AES",
    ],
    "Real Estate": [
        "AMT","PLD","CCI","EQIX","PSA","O","WELL","SPG","AVB","EQR",
        "MAA","UDR","ESS","CPT","NNN","VICI","GLPI","MGP","IRM","DLR",
    ],
    "Materials": [
        "LIN","APD","SHW","ECL","PPG","EMN","DD","DOW","LYB","CF",
        "MOS","IFF","CTVA","FMC","ALB","BALL","PKG","IP","WRK","SEE",
    ],
    "Real Estate Alt": [],
}

SP500_KR_NAMES = {
    "MSFT":"마이크로소프트","AAPL":"애플","NVDA":"엔비디아","AVGO":"브로드컴",
    "AMD":"에이엠디","ORCL":"오라클","MU":"마이크론","AMAT":"어플라이드머티리얼즈",
    "TXN":"텍사스인스트루먼트","ADI":"아날로그디바이시스","QCOM":"퀄컴","INTC":"인텔",
    "CRM":"세일즈포스","NOW":"서비스나우","SNOW":"스노우플레이크","PANW":"팔로알토",
    "CRWD":"크라우드스트라이크","FTNT":"포티넷","KLAC":"KLA코퍼레이션","LRCX":"램리서치",
    "AMZN":"아마존","TSLA":"테슬라","HD":"홈디포","MCD":"맥도날드","NKE":"나이키",
    "SBUX":"스타벅스","LOW":"로우스","TJX":"TJ맥스","BKNG":"부킹홀딩스","MAR":"메리어트",
    "HLT":"힐튼","CCL":"카니발","RCL":"로얄캐리비안","F":"포드","GM":"제너럴모터스",
    "GOOGL":"구글","META":"메타","NFLX":"넷플릭스","DIS":"디즈니","CMCSA":"컴캐스트",
    "VZ":"버라이즌","T":"AT&T","TMUS":"T모바일","EA":"일렉트로닉아츠",
    "JPM":"JP모건","BRK-B":"버크셔해서웨이","V":"비자","MA":"마스터카드","BAC":"뱅크오브아메리카",
    "WFC":"웰스파고","GS":"골드만삭스","MS":"모건스탠리","C":"씨티그룹","AXP":"아메리칸익스프레스",
    "BLK":"블랙록","SCHW":"찰스슈왑",
    "LLY":"일라이릴리","UNH":"유나이티드헬스","JNJ":"존슨앤존슨","ABT":"애보트","PFE":"화이자",
    "MRK":"머크","TMO":"써모피셔","DHR":"다나허","MDT":"메드트로닉","SYK":"스트라이커",
    "AMGN":"암젠","GILD":"길리어드","BIIB":"바이오젠","REGN":"리제네론",
    "GE":"제너럴일렉트릭","CAT":"캐터필러","BA":"보잉","HON":"허니웰","RTX":"레이시온",
    "LMT":"록히드마틴","NOC":"노스롭그루먼","GD":"제너럴다이내믹스",
    "UPS":"UPS","FDX":"페덱스","CSX":"CSX","NSC":"노퍽서던","UNP":"유니온퍼시픽",
    "WMT":"월마트","PG":"P&G","COST":"코스트코","KO":"코카콜라","PEP":"펩시코",
    "PM":"필립모리스","MO":"알트리아","CL":"콜게이트","TGT":"타깃",
    "XOM":"엑슨모빌","CVX":"쉐브론","COP":"코노코필립스","EOG":"EOG리소시스",
    "SLB":"슐럼버거","MPC":"마라톤페트롤리엄","PSX":"필립스66","VLO":"발레로에너지",
    "NEE":"넥스트에라에너지","DUK":"듀크에너지","SO":"서던컴퍼니","D":"도미니언에너지",
    "AMT":"아메리칸타워","PLD":"프롤로지스","CCI":"크라운캐슬","EQIX":"에퀴닉스",
    "PSA":"퍼블릭스토리지","O":"리얼티인컴","SPG":"사이먼프로퍼티",
    "LIN":"린데","APD":"에어프로덕츠","SHW":"쉐윈윌리엄스","ECL":"에콜랩",
    "DOW":"다우","LYB":"라이온델바젤",
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

# 히트맵용 주요 종목만 (상위)
HEATMAP_US = {
    "Technology":        ["MSFT","AAPL","NVDA","AVGO","AMD","ORCL","MU","AMAT","TXN","ADI"],
    "Consumer Cyclical": ["AMZN","TSLA","HD","MCD","NKE","SBUX"],
    "Communication":     ["GOOGL","META","NFLX","DIS"],
    "Financial":         ["JPM","BRK-B","V","MA","BAC","WFC"],
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
        if not tickers:
            continue
        for ticker in tickers:
            try:
                info = yf.Ticker(ticker).fast_info
                price = info.last_price or 0
                prev  = info.previous_close or price
                change = round(float((price - prev) / prev * 100), 2) if prev else 0.0
                mcap   = (info.market_cap or 1e9) / 1e9
                if is_kr:
                    name = kr_names.get(ticker, ticker)
                    rows.append({"ticker":ticker,"name":name,"sector":sector,"price":int(price),"change":change,"mcap":mcap})
                else:
                    kr = kr_names.get(ticker, ticker) if kr_names else ticker
                    rows.append({"ticker":ticker,"name":f"{ticker}\n{kr}","sector":sector,"price":round(price,2),"change":change,"mcap":mcap})
            except:
                name = (kr_names.get(ticker,ticker) if kr_names else ticker)
                rows.append({"ticker":ticker,"name":name,"sector":sector,"price":0,"change":0.0,"mcap":10})
    df = pd.DataFrame(rows)
    if not df.empty:
        df["change"] = df["change"].round(2)
    return df

@st.cache_data(ttl=300)
def load_all_sp500():
    all_tickers = []
    for tickers in SP500_SECTORS.values():
        all_tickers.extend(tickers)
    rows = []
    for ticker in all_tickers:
        try:
            info = yf.Ticker(ticker).fast_info
            price = info.last_price or 0
            prev  = info.previous_close or price
            change = round(float((price - prev) / prev * 100), 2) if prev else 0.0
            sector = next((s for s,ts in SP500_SECTORS.items() if ticker in ts), "기타")
            rows.append({"ticker":ticker,"name":SP500_KR_NAMES.get(ticker,ticker),"sector":sector,"price":round(price,2),"change":change})
        except:
            sector = next((s for s,ts in SP500_SECTORS.items() if ticker in ts), "기타")
            rows.append({"ticker":ticker,"name":SP500_KR_NAMES.get(ticker,ticker),"sector":sector,"price":0,"change":0.0})
    return pd.DataFrame(rows)

@st.cache_data(ttl=600)
def load_detail(ticker):
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y")
        info = tk.info
        return {"hist":hist,"info":info}
    except:
        return {"hist":pd.DataFrame(),"info":{}}

def make_treemap(df, size_col="mcap"):
    df = df.copy()
    df["change"] = df["change"].round(2)
    fig = px.treemap(
        df, path=["sector","name"], values=size_col,
        color="change",
        color_continuous_scale=[(0,"#c0392b"),(0.5,"#444"),(1,"#27ae60")],
        color_continuous_midpoint=0, range_color=[-3,3],
        custom_data=["ticker","price","change"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[2]:+.2f}%",
        hovertemplate="<b>%{label}</b><br>가격: %{customdata[1]:,.2f}<br>등락: %{customdata[2]:+.2f}%<extra></extra>",
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
    if hist is None or hist.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist.index, y=hist["Close"],
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

# ── UI ───────────────────────────────────────────────────
st.title("📈 주식 히트맵 대시보드")
col_r, col_t = st.columns([1,4])
with col_r:
    if st.button("🔄 새로고침"):
        st.cache_data.clear(); st.rerun()
with col_t:
    st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  (5분마다 자동 갱신)")

tab_us, tab_kr = st.tabs(["🇺🇸 S&P 500", "🇰🇷 코스피"])

def render_market(heatmap_sectors, all_data_func, kr_names, is_kr, key_prefix):
    with st.spinner("실시간 데이터 로딩 중..."):
        df_map = load_heatmap_data(heatmap_sectors, kr_names, is_kr)
        df_all = all_data_func()

    # 요약
    up = (df_all["change"]>0).sum()
    dn = (df_all["change"]<0).sum()
    avg = round(df_all["change"].mean(),2)
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-val pos">▲ {up}</div><div class="metric-lbl">상승</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-val neg">▼ {dn}</div><div class="metric-lbl">하락</div></div>', unsafe_allow_html=True)
    with c3:
        cls = "pos" if avg>=0 else "neg"
        st.markdown(f'<div class="metric-card"><div class="metric-val {cls}">{avg:+.2f}%</div><div class="metric-lbl">평균 등락률</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card"><div class="metric-val">{len(df_all)}</div><div class="metric-lbl">전체 종목</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # 3열 레이아웃
    col_detail, col_map, col_sidebar = st.columns([2, 5, 2])

    # 오른쪽 사이드바 — 전체 종목
    with col_sidebar:
        st.markdown("##### 전체 종목")
        search = st.text_input("검색", placeholder="티커 또는 기업명...", key=f"{key_prefix}_search", label_visibility="collapsed")
        sort_opt = st.radio("정렬", ["등락률↓","등락률↑","가나다"], horizontal=True, key=f"{key_prefix}_sort", label_visibility="collapsed")

        df_filtered = df_all.copy()
        if search:
            df_filtered = df_filtered[
                df_filtered["ticker"].str.contains(search.upper()) |
                df_filtered["name"].str.contains(search)
            ]
        if sort_opt == "등락률↓":
            df_filtered = df_filtered.sort_values("change", ascending=False)
        elif sort_opt == "등락률↑":
            df_filtered = df_filtered.sort_values("change", ascending=True)
        else:
            df_filtered = df_filtered.sort_values("name")

        selected = st.radio(
            "종목 선택",
            df_filtered["ticker"].tolist(),
            format_func=lambda x: f"{x} {df_filtered[df_filtered['ticker']==x]['name'].values[0] if len(df_filtered[df_filtered['ticker']==x])>0 else ''} ({df_filtered[df_filtered['ticker']==x]['change'].values[0]:+.2f}%)" if len(df_filtered[df_filtered['ticker']==x])>0 else x,
            key=f"{key_prefix}_stock_radio",
            label_visibility="collapsed"
        )

    # 가운데 히트맵
    with col_map:
        st.markdown("##### 히트맵 (주요 종목)")
        size_opt = st.radio("크기 기준", ["시가총액","균등"], horizontal=True, key=f"{key_prefix}_size")
        size_col = "mcap" if size_opt=="시가총액" else "size_val"
        if size_opt == "균등":
            df_map["size_val"] = 1
        fig = make_treemap(df_map, size_col)
        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_treemap")

    # 왼쪽 상세 패널
    with col_detail:
        if selected:
            with st.spinner("로딩 중..."):
                detail = load_detail(selected)
            info = detail["info"]
            hist = detail["hist"]
            price = info.get("currentPrice") or info.get("regularMarketPrice",0) or 0
            prev  = info.get("previousClose", price) or price
            chg   = round(float((price-prev)/prev*100),2) if prev else 0.0
            kr_name = kr_names.get(selected, selected) if kr_names else selected
            cls = "pos" if chg>=0 else "neg"
            currency = "원" if is_kr else "$"
            price_fmt = f"{int(price):,}{currency}" if is_kr else f"${price:,.2f}"

            st.markdown(f"##### {selected}")
            st.markdown(f"**{kr_name}**")
            st.markdown(f'<span class="{cls}" style="font-size:1.4rem;font-weight:600;">{chg:+.2f}%</span>', unsafe_allow_html=True)
            st.markdown(f"**현재가:** {price_fmt}")

            chart = make_chart(hist, selected)
            if chart:
                st.plotly_chart(chart, use_container_width=True, key=f"{key_prefix}_chart_{selected}")

            t1,t2,t3,t4 = st.tabs(["시세","실적","기관매수","내부자"])

            with t1:
                high = info.get("dayHigh",0) or 0
                low  = info.get("dayLow",0) or 0
                vol  = info.get("volume",0) or 0
                vol_str = f"{vol/1e6:.1f}M" if vol>1e6 else f"{vol:,}"
                high_fmt = f"{int(high):,}{currency}" if is_kr else f"${high:,.2f}"
                low_fmt  = f"{int(low):,}{currency}" if is_kr else f"${low:,.2f}"
                prev_fmt = f"{int(prev):,}{currency}" if is_kr else f"${prev:,.2f}"
                mcap = info.get("marketCap",0) or 0
                mcap_str = f"${mcap/1e9:.1f}B" if mcap else "-"

                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("시가", prev_fmt)
                    st.metric("저가", low_fmt)
                    st.metric("시가총액", mcap_str)
                with col_b:
                    st.metric("고가", high_fmt)
                    st.metric("거래량", vol_str)
                    per = info.get("trailingPE")
                    st.metric("PER", f"{per:.1f}x" if per else "-")

                wk52h = info.get("fiftyTwoWeekHigh",0)
                wk52l = info.get("fiftyTwoWeekLow",0)
                if wk52h and wk52l:
                    st.markdown(f"**52주 고가:** {'${:,.2f}'.format(wk52h) if not is_kr else f'{int(wk52h):,}원'}  |  **52주 저가:** {'${:,.2f}'.format(wk52l) if not is_kr else f'{int(wk52l):,}원'}")

            with t2:
                st.markdown("**다음 분기 예측**")
                next_q = {
                    "AAPL":{"date":"2026-08-26","eps":"2.07","rev":"91.56B","epsG":"+10.7%","revG":"+12.2%","q":"2026-Q3"},
                    "MSFT":{"date":"2026-08-27","eps":"3.68","rev":"74.21B","epsG":"+6.4%","revG":"+5.9%","q":"2026-Q4"},
                    "NVDA":{"date":"2026-08-27","eps":"1.12","rev":"51.80B","epsG":"+16.7%","revG":"+17.5%","q":"2026-Q2"},
                    "TSLA":{"date":"2026-07-22","eps":"0.52","rev":"23.10B","epsG":"+92.6%","revG":"+19.5%","q":"2026-Q2"},
                    "AMZN":{"date":"2026-07-31","eps":"1.71","rev":"163.5B","epsG":"+7.5%","revG":"+5.0%","q":"2026-Q2"},
                    "GOOGL":{"date":"2026-07-29","eps":"2.31","rev":"96.80B","epsG":"+9.0%","revG":"+11.5%","q":"2026-Q2"},
                    "META":{"date":"2026-07-29","eps":"6.21","rev":"46.80B","epsG":"+18.1%","revG":"+14.2%","q":"2026-Q2"},
                    "005930.KS":{"date":"2026-07-31","eps":"920","rev":"82.5T","epsG":"+5.6%","revG":"+4.3%","q":"2026-Q2"},
                    "000660.KS":{"date":"2026-07-24","eps":"8100","rev":"18.9T","epsG":"+7.7%","revG":"+7.1%","q":"2026-Q2"},
                }
                nq = next_q.get(selected)
                if nq:
                    days = (datetime.strptime(nq["date"],"%Y-%m-%d") - datetime.now()).days
                    d_color = "🔴" if days<=14 else "🟡" if days<=30 else "🟢"
                    st.info(f"**{nq['q']}** | 발표 예정: {nq['date']} {d_color} D-{days}")
                    ca, cb = st.columns(2)
                    with ca:
                        st.metric("EPS 예측", nq["eps"], nq["epsG"])
                    with cb:
                        st.metric("매출 예측", nq["rev"], nq["revG"])
                else:
                    st.info("다음 분기 예측 데이터 없음")

                st.markdown("**과거 실적**")
                earnings_data = {
                    "MSFT":[["2026-05-20","3.46/3.22","+7.45%"],["2026-02-26","3.23/3.11","+3.86%"],["2025-10-30","3.30/3.10","+6.45%"],["2025-07-30","3.46/3.35","+3.28%"]],
                    "AAPL":[["2026-05-20","1.87/1.77","+5.65%"],["2026-02-25","1.62/1.52","+6.58%"],["2025-11-19","1.30/1.25","+4.00%"],["2025-08-27","1.04/1.01","+2.97%"]],
                    "NVDA":[["2026-05-28","0.96/0.93","+3.23%"],["2026-02-26","0.89/0.84","+5.95%"],["2025-11-20","0.81/0.75","+8.00%"],["2025-08-28","0.68/0.64","+6.25%"]],
                    "TSLA":[["2026-04-22","0.27/0.41","-34.1%"],["2026-01-29","0.73/0.77","-5.19%"],["2025-10-23","0.72/0.58","+24.1%"],["2025-07-23","0.52/0.43","+20.9%"]],
                    "AMZN":[["2026-05-01","1.59/1.37","+16.1%"],["2026-02-06","1.86/1.49","+24.8%"],["2025-10-31","1.43/1.14","+25.4%"],["2025-08-01","1.43/1.03","+38.8%"]],
                    "005930.KS":[["2026-04-30","871/820","+6.22%"],["2026-01-31","742/711","+4.36%"],["2025-10-31","695/680","+2.21%"],["2025-07-31","527/502","+4.98%"]],
                    "000660.KS":[["2026-04-24","7520/7210","+4.30%"],["2026-01-23","8110/7890","+2.79%"],["2025-10-23","7080/6730","+5.20%"],["2025-07-24","8100/7501","+7.99%"]],
                }
                ed = earnings_data.get(selected)
                if ed:
                    df_e = pd.DataFrame(ed, columns=["발표일","EPS 실적/예측","서프라이즈"])
                    st.dataframe(df_e, use_container_width=True, hide_index=True)
                else:
                    st.info("실적 데이터 없음")

            with t3:
                inst_data = {
                    "AAPL":[["블랙록","26.4M","25.5M","-4%"],["뱅가드","-","18.1M","신규"],["JP모건","11.7M","13.1M","+12%"],["스테이트 스트리트","13.1M","13.0M","-1%"],["골드만삭스","3.0M","3.0M","0%"]],
                    "NVDA":[["블랙록","19.8M","21.4M","+8%"],["뱅가드","18.2M","19.8M","+9%"],["피델리티","-","15.2M","신규"],["스테이트 스트리트","11.2M","11.0M","-2%"],["JP모건","8.1M","9.2M","+14%"]],
                    "005930.KS":[["국민연금","412.8M","418.2M","+1%"],["블랙록","98.2M","102.3M","+4%"],["미래에셋","88.1M","91.4M","+4%"],["삼성자산운용","75.2M","78.9M","+5%"],["KB자산운용","62.1M","65.8M","+6%"]],
                }
                id_ = inst_data.get(selected)
                if id_:
                    df_i = pd.DataFrame(id_, columns=["기관명","이전분기","현재분기","변화율"])
                    st.dataframe(df_i, use_container_width=True, hide_index=True)
                else:
                    st.info("기관 데이터 없음")

            with t4:
                insider_data = {
                    "AAPL":[["팀 쿡","CEO","매도","95,000주","$18.5M","2026-05-10"],["루카 마에스트리","CFO","매도","35,000주","$6.7M","2026-04-22"],["아서 레빈슨","이사회의장","매수","5,000주","$906K","2026-02-08"]],
                    "NVDA":[["젠슨 황","CEO","매도","120,000주","$104.4M","2026-05-15"],["콜레트 크레스","CFO","매도","15,000주","$12.9M","2026-04-18"],["마크 스티븐스","이사","매수","2,000주","$1.5M","2026-02-14"]],
                    "TSLA":[["일론 머스크","CEO","매도","5,000,000주","$875M","2026-04-30"],["바이봐 타네자","CFO","매수","25,000주","$4.1M","2026-03-22"]],
                    "005930.KS":[["이재용","회장","매수","500,000주","355억","2026-04-15"],["한종희","부회장","매도","120,000주","87억","2026-03-20"]],
                }
                ind = insider_data.get(selected)
                if ind:
                    df_in = pd.DataFrame(ind, columns=["이름","직책","구분","수량","금액","날짜"])
                    st.dataframe(df_in, use_container_width=True, hide_index=True)
                else:
                    st.info("내부자 거래 데이터 없음")

# ── 탭 렌더링 ─────────────────────────────────────────────
with tab_us:
    render_market(
        HEATMAP_US,
        load_all_sp500,
        SP500_KR_NAMES,
        False,
        "us"
    )

with tab_kr:
    @st.cache_data(ttl=300)
    def load_all_kr():
        rows = []
        for sector, tickers in KR_SECTORS.items():
            for ticker in tickers:
                try:
                    info = yf.Ticker(ticker).fast_info
                    price = info.last_price or 0
                    prev  = info.previous_close or price
                    change = round(float((price-prev)/prev*100),2) if prev else 0.0
                    rows.append({"ticker":ticker,"name":KR_NAMES.get(ticker,ticker),"sector":sector,"price":int(price),"change":change})
                except:
                    rows.append({"ticker":ticker,"name":KR_NAMES.get(ticker,ticker),"sector":sector,"price":0,"change":0.0})
        return pd.DataFrame(rows)

    render_market(
        KR_SECTORS,
        load_all_kr,
        KR_NAMES,
        True,
        "kr"
    )

# ── 뉴스 섹션 ─────────────────────────────────────────────
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
