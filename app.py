
import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time

# ── 페이지 설정 ──────────────────────────────────────────
st.set_page_config(
    page_title="주식 히트맵 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
    .main { padding: 0.5rem 1rem; }
    .block-container { padding-top: 1rem; max-width: 100%; }
    .metric-card {
        background: #1e1e2e;
        border: 1px solid #313244;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
    }
    .metric-val { font-size: 1.3rem; font-weight: 600; }
    .metric-lbl { font-size: 0.75rem; color: #888; margin-top: 2px; }
    .pos { color: #27ae60; }
    .neg { color: #e74c3c; }
    .news-card {
        background: #1e1e2e;
        border: 1px solid #313244;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
    }
    .news-headline { font-size: 0.85rem; font-weight: 500; margin-bottom: 4px; }
    .news-meta { font-size: 0.75rem; color: #888; }
    .figure-card {
        background: #1e1e2e;
        border: 1px solid #313244;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
    }
    h1, h2, h3 { color: #cdd6f4 !important; }
    .stTabs [data-baseweb="tab"] { font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# ── 종목 정의 ────────────────────────────────────────────
US_SECTORS = {
    "Technology":        ["MSFT","AAPL","NVDA","AVGO","AMD","ORCL","MU","AMAT","TXN","ADI"],
    "Consumer Cyclical": ["AMZN","TSLA","HD","MCD","NKE","SBUX"],
    "Communication":     ["GOOGL","META","NFLX","DIS"],
    "Financial":         ["JPM","BRK-B","V","MA","BAC","WFC"],
    "Healthcare":        ["LLY","UNH","JNJ","ABT","PFE"],
    "Industrials":       ["GE","CAT","BA","HON","RTX"],
    "Consumer Defensive":["WMT","PG","COST","KO","PEP"],
    "Energy":            ["XOM","CVX","COP"],
}

KR_SECTORS = {
    "반도체·IT":   ["005930.KS","000660.KS","066570.KS","006400.KS"],
    "바이오·헬스": ["207940.KS","068270.KS","128940.KS","000100.KS"],
    "금융":        ["105560.KS","055550.KS","086790.KS","032830.KS"],
    "자동차·부품": ["005380.KS","000270.KS","012330.KS"],
    "화학·소재":   ["051910.KS","005490.KS","011170.KS"],
    "통신·플랫폼": ["035420.KS","035720.KS","017670.KS","030200.KS"],
}

KR_NAMES = {
    "005930.KS":"삼성전자","000660.KS":"SK하이닉스","066570.KS":"LG전자","006400.KS":"삼성SDI",
    "207940.KS":"삼성바이오","068270.KS":"셀트리온","128940.KS":"한미약품","000100.KS":"유한양행",
    "105560.KS":"KB금융","055550.KS":"신한지주","086790.KS":"하나금융","032830.KS":"삼성생명",
    "005380.KS":"현대차","000270.KS":"기아","012330.KS":"현대모비스",
    "051910.KS":"LG화학","005490.KS":"POSCO홀딩스","011170.KS":"롯데케미칼",
    "035420.KS":"네이버","035720.KS":"카카오","017670.KS":"SK텔레콤","030200.KS":"KT",
}

# ── 데이터 로드 ──────────────────────────────────────────
@st.cache_data(ttl=300)  # 5분 캐시
def load_us_data():
    all_tickers = [t for tickers in US_SECTORS.values() for t in tickers]
    rows = []
    for sector, tickers in US_SECTORS.items():
        for ticker in tickers:
            try:
                info = yf.Ticker(ticker).fast_info
                price = info.last_price or 0
                prev  = info.previous_close or price
                change = round(((price - prev) / prev * 100), 2) if prev else 0
                mcap  = (info.market_cap or 1e9) / 1e9
                rows.append({
                    "ticker": ticker,
                    "name":   ticker,
                    "sector": sector,
                    "price":  round(price, 2),
                    "change": change,
                    "mcap":   mcap,
                })
            except:
                rows.append({"ticker":ticker,"name":ticker,"sector":sector,"price":0,"change":0,"mcap":10})
    return pd.DataFrame(rows)

@st.cache_data(ttl=300)
def load_kr_data():
    rows = []
    for sector, tickers in KR_SECTORS.items():
        for ticker in tickers:
            try:
                info = yf.Ticker(ticker).fast_info
                price = info.last_price or 0
                prev  = info.previous_close or price
                change = round(((price - prev) / prev * 100), 2) if prev else 0
                mcap  = (info.market_cap or 1e12) / 1e12
                rows.append({
                    "ticker": ticker,
                    "name":   KR_NAMES.get(ticker, ticker),
                    "sector": sector,
                    "price":  int(price),
                    "change": change,
                    "mcap":   mcap,
                })
            except:
                rows.append({"ticker":ticker,"name":KR_NAMES.get(ticker,ticker),"sector":sector,"price":0,"change":0,"mcap":1})
    return pd.DataFrame(rows)

@st.cache_data(ttl=600)
def load_stock_detail(ticker, is_kr=False):
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y")
        info = tk.info
        earnings = tk.quarterly_earnings
        return {"hist": hist, "info": info, "earnings": earnings}
    except:
        return {"hist": pd.DataFrame(), "info": {}, "earnings": None}

# ── 히트맵 생성 ──────────────────────────────────────────
def make_treemap(df, size_col="mcap"):
    fig = px.treemap(
        df,
        path=["sector", "name"],
        values=size_col,
        color="change",
        color_continuous_scale=[(0,"#c0392b"),(0.5,"#555"),(1,"#27ae60")],
        color_continuous_midpoint=0,
        range_color=[-3, 3],
        custom_data=["ticker","price","change"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[2]:+.2f}%",
        hovertemplate="<b>%{label}</b><br>가격: %{customdata[1]:,.0f}<br>등락: %{customdata[2]:+.2f}%<extra></extra>",
        textfont_size=12,
    )
    fig.update_layout(
        margin=dict(t=0,l=0,r=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
        height=520,
    )
    return fig

# ── 차트 ────────────────────────────────────────────────
def make_price_chart(hist, ticker):
    if hist.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist.index, y=hist["Close"],
        fill="tozeroy",
        fillcolor="rgba(39,174,96,0.1)",
        line=dict(color="#27ae60", width=1.5),
        name=ticker,
    ))
    fig.update_layout(
        margin=dict(t=10,l=0,r=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, color="#888"),
        yaxis=dict(showgrid=True, gridcolor="#313244", color="#888"),
        height=200,
        showlegend=False,
    )
    return fig

# ── 뉴스 (샘플) ──────────────────────────────────────────
NEWS = [
    {"headline":"Fed, 6월 금리 동결 신호… 연내 2회 인하 전망 유지","source":"Bloomberg","time":"2시간 전","impact":"악재","tags":["연준","금리"]},
    {"headline":"NVIDIA, 차세대 블랙웰 울트라 출하 본격화… 데이터센터 수요 급증","source":"Reuters","time":"3시간 전","impact":"호재","tags":["NVDA","AI"]},
    {"headline":"S&P500, 5거래일 연속 상승… 기술주 중심 랠리 지속","source":"CNBC","time":"4시간 전","impact":"호재","tags":["S&P500"]},
    {"headline":"삼성전자, HBM4 양산 일정 앞당겨… SK하이닉스와 경쟁 가열","source":"한국경제","time":"5시간 전","impact":"호재","tags":["삼성전자","HBM"]},
    {"headline":"미중 관세 협상 재개… 반도체·전기차 품목 제외 논의","source":"WSJ","time":"6시간 전","impact":"중립","tags":["무역","관세"]},
    {"headline":"국제유가 WTI 배럴당 $71 하락… OPEC+ 증산 우려","source":"Reuters","time":"9시간 전","impact":"악재","tags":["유가","에너지"]},
]

FIGURES = [
    {"name":"도널드 트럼프","role":"미국 대통령","quote":"우리는 중국과의 무역에서 엄청난 진전을 이루고 있다. 반도체 관세는 협상 카드로 활용할 것이다.","time":"1시간 전","tags":["무역","관세","반도체"]},
    {"name":"제롬 파월","role":"연준 의장","quote":"인플레이션이 2% 목표로 지속 하락하는 것을 확인한 후 금리 인하를 검토할 것이다.","time":"3시간 전","tags":["금리","인플레이션"]},
    {"name":"젠슨 황","role":"NVIDIA CEO","quote":"AI 인프라 수요는 우리의 예상을 훨씬 뛰어넘고 있다. 블랙웰 수요는 공급을 크게 앞서고 있다.","time":"5시간 전","tags":["NVDA","AI"]},
    {"name":"이창용","role":"한국은행 총재","quote":"국내 물가 안정세가 이어지고 있으나 환율 불확실성을 감안해 신중한 접근이 필요하다.","time":"6시간 전","tags":["한국은행","금리","환율"]},
    {"name":"일론 머스크","role":"Tesla CEO","quote":"테슬라의 자율주행 기술은 내년까지 완전 자율 수준에 도달할 것이다. 로보택시도 곧 시작한다.","time":"8시간 전","tags":["TSLA","자율주행"]},
]

# ── 메인 UI ──────────────────────────────────────────────
st.title("📈 주식 히트맵 대시보드")

col_refresh, col_time = st.columns([1, 3])
with col_refresh:
    if st.button("🔄 새로고침"):
        st.cache_data.clear()
        st.rerun()
with col_time:
    st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  (5분마다 자동 갱신)")

# 탭
tab_us, tab_kr = st.tabs(["🇺🇸 S&P 500", "🇰🇷 코스피"])

# ── 미국 탭 ─────────────────────────────────────────────
with tab_us:
    with st.spinner("실시간 데이터 로딩 중..."):
        df_us = load_us_data()

    # 시장 요약
    up   = (df_us["change"] > 0).sum()
    down = (df_us["change"] < 0).sum()
    avg  = df_us["change"].mean()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-val pos">▲ {up}</div><div class="metric-lbl">상승 종목</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-val neg">▼ {down}</div><div class="metric-lbl">하락 종목</div></div>', unsafe_allow_html=True)
    with c3:
        cls = "pos" if avg >= 0 else "neg"
        st.markdown(f'<div class="metric-card"><div class="metric-val {cls}">{avg:+.2f}%</div><div class="metric-lbl">평균 등락률</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{len(df_us)}</div><div class="metric-lbl">전체 종목</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # 크기 기준 선택
    size_opt = st.radio("박스 크기 기준", ["시가총액", "균등"], horizontal=True)
    if size_opt == "균등":
        df_us["size_val"] = 1
        size_col = "size_val"
    else:
        size_col = "mcap"

    # 히트맵
    fig = make_treemap(df_us, size_col)
    selected = st.plotly_chart(fig, use_container_width=True, key="us_treemap")

    # 종목 상세
    st.markdown("#### 종목 상세 보기")
    col_sel, col_dummy = st.columns([2, 4])
    with col_sel:
        ticker_sel = st.selectbox(
            "종목 선택",
            df_us["ticker"].tolist(),
            format_func=lambda x: f"{x}",
            key="us_select"
        )

    if ticker_sel:
        with st.spinner("종목 데이터 로딩..."):
            detail = load_stock_detail(ticker_sel)

        info = detail["info"]
        hist = detail["hist"]

        d1, d2, d3, d4, d5 = st.columns(5)
        price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        prev  = info.get("previousClose", price)
        chg   = ((price - prev) / prev * 100) if prev else 0
        mcap  = info.get("marketCap", 0)

        with d1:
            cls = "pos" if chg >= 0 else "neg"
            st.markdown(f'<div class="metric-card"><div class="metric-val {cls}">${price:,.2f}</div><div class="metric-lbl">현재가</div></div>', unsafe_allow_html=True)
        with d2:
            st.markdown(f'<div class="metric-card"><div class="metric-val {cls}">{chg:+.2f}%</div><div class="metric-lbl">등락률</div></div>', unsafe_allow_html=True)
        with d3:
            st.markdown(f'<div class="metric-card"><div class="metric-val">${info.get("dayHigh",0):,.2f}</div><div class="metric-lbl">고가</div></div>', unsafe_allow_html=True)
        with d4:
            st.markdown(f'<div class="metric-card"><div class="metric-val">${info.get("dayLow",0):,.2f}</div><div class="metric-lbl">저가</div></div>', unsafe_allow_html=True)
        with d5:
            vol = info.get("volume", 0)
            vol_str = f"{vol/1e6:.1f}M" if vol > 1e6 else f"{vol:,}"
            st.markdown(f'<div class="metric-card"><div class="metric-val">{vol_str}</div><div class="metric-lbl">거래량</div></div>', unsafe_allow_html=True)

        # 차트
        chart = make_price_chart(hist, ticker_sel)
        if chart:
            st.plotly_chart(chart, use_container_width=True, key="us_chart")

        # 실적
        t1, t2 = st.tabs(["📊 실적", "ℹ️ 기업 정보"])
        with t1:
            earnings = detail["earnings"]
            if earnings is not None and not earnings.empty:
                st.dataframe(earnings.tail(8), use_container_width=True)
            else:
                st.info("실적 데이터를 불러오는 중입니다.")
        with t2:
            cols_info = st.columns(2)
            fields = [
                ("섹터", info.get("sector","-")),
                ("산업", info.get("industry","-")),
                ("시가총액", f"${mcap/1e9:.1f}B" if mcap else "-"),
                ("PER", f"{info.get('trailingPE',0):.1f}x" if info.get('trailingPE') else "-"),
                ("PBR", f"{info.get('priceToBook',0):.2f}x" if info.get('priceToBook') else "-"),
                ("배당수익률", f"{info.get('dividendYield',0)*100:.2f}%" if info.get('dividendYield') else "-"),
                ("52주 고가", f"${info.get('fiftyTwoWeekHigh',0):,.2f}"),
                ("52주 저가", f"${info.get('fiftyTwoWeekLow',0):,.2f}"),
            ]
            for i, (k, v) in enumerate(fields):
                with cols_info[i % 2]:
                    st.metric(k, v)

    # 전체 등락률 테이블
    st.markdown("---")
    st.markdown("#### 전체 종목 등락률")
    df_show = df_us[["ticker","name","sector","price","change"]].copy()
    df_show.columns = ["티커","종목명","섹터","현재가($)","등락률(%)"]
    df_show = df_show.sort_values("등락률(%)", ascending=False)
    st.dataframe(
        df_show.style.background_gradient(subset=["등락률(%)"], cmap="RdYlGn", vmin=-3, vmax=3),
        use_container_width=True, height=300
    )

# ── 코스피 탭 ────────────────────────────────────────────
with tab_kr:
    with st.spinner("실시간 데이터 로딩 중..."):
        df_kr = load_kr_data()

    up_kr   = (df_kr["change"] > 0).sum()
    down_kr = (df_kr["change"] < 0).sum()
    avg_kr  = df_kr["change"].mean()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-val pos">▲ {up_kr}</div><div class="metric-lbl">상승 종목</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-val neg">▼ {down_kr}</div><div class="metric-lbl">하락 종목</div></div>', unsafe_allow_html=True)
    with c3:
        cls = "pos" if avg_kr >= 0 else "neg"
        st.markdown(f'<div class="metric-card"><div class="metric-val {cls}">{avg_kr:+.2f}%</div><div class="metric-lbl">평균 등락률</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{len(df_kr)}</div><div class="metric-lbl">전체 종목</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    size_opt_kr = st.radio("박스 크기 기준", ["시가총액", "균등"], horizontal=True, key="kr_size")
    if size_opt_kr == "균등":
        df_kr["size_val"] = 1
        size_col_kr = "size_val"
    else:
        size_col_kr = "mcap"

    fig_kr = make_treemap(df_kr.rename(columns={"name":"ticker_orig"}), size_col_kr) if False else px.treemap(
        df_kr, path=["sector","name"], values=size_col_kr,
        color="change",
        color_continuous_scale=[(0,"#c0392b"),(0.5,"#555"),(1,"#27ae60")],
        color_continuous_midpoint=0, range_color=[-3,3],
        custom_data=["ticker","price","change"],
    )
    fig_kr.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[2]:+.2f}%",
        hovertemplate="<b>%{label}</b><br>가격: %{customdata[1]:,.0f}원<br>등락: %{customdata[2]:+.2f}%<extra></extra>",
    )
    fig_kr.update_layout(margin=dict(t=0,l=0,r=0,b=0),paper_bgcolor="rgba(0,0,0,0)",coloraxis_showscale=False,height=520)
    st.plotly_chart(fig_kr, use_container_width=True, key="kr_treemap")

    # 종목 상세
    st.markdown("#### 종목 상세 보기")
    col_sel_kr, _ = st.columns([2, 4])
    with col_sel_kr:
        ticker_kr = st.selectbox(
            "종목 선택",
            df_kr["ticker"].tolist(),
            format_func=lambda x: KR_NAMES.get(x, x),
            key="kr_select"
        )

    if ticker_kr:
        with st.spinner("종목 데이터 로딩..."):
            detail_kr = load_stock_detail(ticker_kr, is_kr=True)

        info_kr = detail_kr["info"]
        hist_kr = detail_kr["hist"]

        price_kr = info_kr.get("currentPrice") or info_kr.get("regularMarketPrice", 0)
        prev_kr  = info_kr.get("previousClose", price_kr)
        chg_kr   = ((price_kr - prev_kr) / prev_kr * 100) if prev_kr else 0

        d1,d2,d3,d4,d5 = st.columns(5)
        cls = "pos" if chg_kr >= 0 else "neg"
        with d1: st.markdown(f'<div class="metric-card"><div class="metric-val {cls}">{int(price_kr):,}원</div><div class="metric-lbl">현재가</div></div>', unsafe_allow_html=True)
        with d2: st.markdown(f'<div class="metric-card"><div class="metric-val {cls}">{chg_kr:+.2f}%</div><div class="metric-lbl">등락률</div></div>', unsafe_allow_html=True)
        with d3: st.markdown(f'<div class="metric-card"><div class="metric-val">{int(info_kr.get("dayHigh",0)):,}원</div><div class="metric-lbl">고가</div></div>', unsafe_allow_html=True)
        with d4: st.markdown(f'<div class="metric-card"><div class="metric-val">{int(info_kr.get("dayLow",0)):,}원</div><div class="metric-lbl">저가</div></div>', unsafe_allow_html=True)
        with d5:
            vol = info_kr.get("volume", 0)
            vol_str = f"{vol/1e6:.1f}M" if vol > 1e6 else f"{vol:,}"
            st.markdown(f'<div class="metric-card"><div class="metric-val">{vol_str}</div><div class="metric-lbl">거래량</div></div>', unsafe_allow_html=True)

        chart_kr = make_price_chart(hist_kr, KR_NAMES.get(ticker_kr, ticker_kr))
        if chart_kr:
            st.plotly_chart(chart_kr, use_container_width=True, key="kr_chart")

    st.markdown("---")
    st.markdown("#### 전체 종목 등락률")
    df_show_kr = df_kr[["name","sector","price","change"]].copy()
    df_show_kr.columns = ["종목명","섹터","현재가(원)","등락률(%)"]
    df_show_kr = df_show_kr.sort_values("등락률(%)", ascending=False)
    st.dataframe(
        df_show_kr.style.background_gradient(subset=["등락률(%)"], cmap="RdYlGn", vmin=-3, vmax=3),
        use_container_width=True, height=300
    )

# ── 뉴스 섹션 ────────────────────────────────────────────
st.markdown("---")
col_news, col_figure = st.columns(2)

with col_news:
    st.markdown("#### 📰 주요 시장 뉴스")
    for n in NEWS:
        impact_color = "🟢" if n["impact"]=="호재" else "🔴" if n["impact"]=="악재" else "⚪"
        tags = " ".join([f"`{t}`" for t in n["tags"]])
        st.markdown(f"""
<div class="news-card">
  <div class="news-headline">{impact_color} {n['headline']}</div>
  <div class="news-meta">{n['source']} · {n['time']} · {' '.join(['#'+t for t in n['tags']])}</div>
</div>
""", unsafe_allow_html=True)

with col_figure:
    st.markdown("#### 🎙️ 주요 인물 발언")
    for f in FIGURES:
        tags = " ".join([f"#{t}" for t in f["tags"]])
        st.markdown(f"""
<div class="figure-card">
  <div style="font-size:0.85rem;font-weight:600;">{f['name']} <span style="font-size:0.75rem;color:#888;">| {f['role']}</span></div>
  <div style="font-size:0.8rem;color:#ccc;margin:6px 0;padding:6px 10px;background:#2a2a3e;border-left:3px solid #555;border-radius:4px;">"{f['quote']}"</div>
  <div style="font-size:0.72rem;color:#888;">{f['time']} · {tags}</div>
</div>
""", unsafe_allow_html=True)

# ── 자동 새로고침 (5분) ──────────────────────────────────
st.markdown("---")
st.caption("💡 데이터는 5분마다 자동 캐시 갱신됩니다. 수동 새로고침은 상단 버튼을 이용하세요.")
