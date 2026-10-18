import streamlit as st
import pandas as pd
import requests
import io
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="NSE Pro Terminal", page_icon="💎", layout="wide")

# ==========================================
# 🎨 ULTRA-PREMIUM FINTECH UI CSS (DESIGNER EDITION)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: #090D16 !important;
        color: #F8FAFC !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        padding-left: 0.9rem !important;
        padding-right: 0.9rem !important;
        max-width: 650px !important;
        margin: auto !important;
    }
    
    /* Premium Header Banner */
    .hero-card {
        background: radial-gradient(circle at top right, #1E293B, #0F172A 70%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 18px 20px;
        margin-bottom: 14px;
        box-shadow: 0 12px 30px -10px rgba(0, 0, 0, 0.6);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .hero-title {
        font-size: 1.35rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38BDF8, #818CF8, #C084FC);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero-sub {
        font-size: 0.75rem;
        color: #94A3B8;
        margin-top: 3px;
        font-weight: 500;
    }
    .live-pill {
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.35);
        color: #34D399;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 5px 10px;
        border-radius: 99px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    /* Bento Summary Grid */
    .bento-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-bottom: 16px;
    }
    .bento-box {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 10px 12px;
        text-align: center;
    }
    .bento-label {
        font-size: 0.65rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }
    .bento-val {
        font-size: 0.95rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-top: 3px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Glassmorphism Stock Card */
    .stock-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.65), rgba(15, 23, 42, 0.85));
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 18px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 8px 20px -6px rgba(0, 0, 0, 0.5);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .stock-card:hover {
        border-color: rgba(56, 189, 248, 0.4);
    }
    
    .sc-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
    }
    .sc-symbol-wrap {
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
    }
    .sc-symbol {
        font-size: 1.15rem;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.3px;
    }
    .badge-fno {
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid rgba(245, 158, 11, 0.4);
        color: #FBBF24;
        font-size: 0.6rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 6px;
    }
    .badge-streak {
        background: rgba(168, 85, 247, 0.18);
        border: 1px solid rgba(168, 85, 247, 0.45);
        color: #C084FC;
        font-size: 0.6rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 6px;
    }
    .sc-sub-pills {
        display: flex;
        gap: 6px;
        margin-top: 5px;
        align-items: center;
    }
    .pill-buyer {
        background: rgba(16, 185, 129, 0.12);
        color: #34D399;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 6px;
    }
    .pill-seller {
        background: rgba(239, 68, 68, 0.12);
        color: #F87171;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 6px;
    }
    .pill-neutral {
        background: rgba(148, 163, 184, 0.12);
        color: #94A3B8;
        font-size: 0.65rem;
        font-weight: 600;
        padding: 2px 7px;
        border-radius: 6px;
    }

    .sc-price-box {
        text-align: right;
    }
    .sc-price {
        font-size: 1.15rem;
        font-weight: 800;
        color: #F8FAFC;
    }
    .chg-up {
        display: inline-block;
        background: rgba(16, 185, 129, 0.18);
        color: #34D399;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 6px;
        margin-top: 3px;
    }
    .chg-down {
        display: inline-block;
        background: rgba(239, 68, 68, 0.18);
        color: #F87171;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 6px;
        margin-top: 3px;
    }

    /* Metrics Inner Box */
    .sc-metrics {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        background: rgba(9, 13, 22, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 12px;
        text-align: center;
    }
    .m-lbl {
        font-size: 0.63rem;
        color: #64748B;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.4px;
    }
    .m-val {
        font-size: 0.92rem;
        font-weight: 800;
        color: #E2E8F0;
        margin-top: 2px;
    }
    .m-val-accent {
        font-size: 0.92rem;
        font-weight: 800;
        color: #38BDF8;
        margin-top: 2px;
    }
    .m-val-gold {
        font-size: 0.92rem;
        font-weight: 800;
        color: #FBBF24;
        margin-top: 2px;
    }

    /* Footer Progress & Chart Link */
    .sc-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
    }
    .prog-wrap {
        flex-grow: 1;
    }
    .prog-bg {
        width: 100%;
        height: 6px;
        background: rgba(255, 255, 255, 0.07);
        border-radius: 99px;
        overflow: hidden;
    }
    .prog-fill {
        height: 100%;
        background: linear-gradient(90deg, #06B6D4, #3B82F6, #8B5CF6);
        border-radius: 99px;
    }
    .tv-btn {
        background: rgba(56, 189, 248, 0.12);
        border: 1px solid rgba(56, 189, 248, 0.3);
        color: #38BDF8 !important;
        text-decoration: none !important;
        font-size: 0.73rem;
        font-weight: 700;
        padding: 6px 12px;
        border-radius: 10px;
        white-space: nowrap;
        transition: all 0.2s;
    }
    .tv-btn:hover {
        background: rgba(56, 189, 248, 0.25);
    }

    /* Button Overrides */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563EB, #7C3AED) !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 0.65rem 1rem !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 8px 20px -6px rgba(124, 58, 237, 0.6) !important;
    }
</style>
""", unsafe_allow_html=True)

CACHE_DIR = "nse_data_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

FNO_STOCKS = {
    'AARTIIND', 'ABB', 'ABBOTINDIA', 'ABCAPITAL', 'ABFRL', 'ACC', 'ADANIENT', 'ADANIPORTS', 'ALKEM', 'AMBUJACEM',
    'APOLLOHOSP', 'APOLLOTYRE', 'ASHOKLEY', 'ASIANPAINT', 'ASTRAL', 'ATUL', 'AUBANK', 'AUROPHARMA', 'AXISBANK', 'BAJAJ-AUTO',
    'BAJAJFINSV', 'BAJFINANCE', 'BALKRISIND', 'BANDHANBNK', 'BANKBARODA', 'BATAINDIA', 'BEL', 'BERGEPAINT', 'BHARATFORG', 'BHARTIARTL',
    'BHEL', 'BIOCON', 'BOSCHLTD', 'BPCL', 'BRITANNIA', 'BSOFT', 'CANBK', 'CANFINHOME', 'CHAMBLFERT', 'CHOLAFIN',
    'CIPLA', 'COALINDIA', 'COFORGE', 'COLPAL', 'CONCOR', 'COROMANDEL', 'CROMPTON', 'CUB', 'CUMMINSIND', 'DABUR',
    'DALBHARAT', 'DEEPAKNTR', 'DIVISLAB', 'DIXON', 'DLF', 'DRREDDY', 'EICHERMOT', 'ESCORTS', 'EXIDEIND', 'FEDERALBNK',
    'GAIL', 'GLENMARK', 'GMRINFRA', 'GNFC', 'GODREJCP', 'GODREJPROP', 'GRANULES', 'GRASIM', 'GUJGASLTD', 'HAL',
    'HAVELLS', 'HCLTECH', 'HDFCAMC', 'HDFCBANK', 'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 'HINDCOPPER', 'HINDPETRO', 'HINDUNILVR',
    'ICICIBANK', 'ICICIGI', 'ICICIPRULI', 'IDEA', 'IDFCFIRSTB', 'IEX', 'IGL', 'INDHOTEL', 'INDIAMART', 'INDIGO',
    'INDUSINDBK', 'INDUSTOWER', 'INFY', 'IOC', 'IPCALAB', 'IRCTC', 'ITC', 'JINDALSTEL', 'JKCEMENT', 'JSWSTEEL',
    'JUBLFOOD', 'KOTAKBANK', 'LALPATHLAB', 'LAURUSLABS', 'LICHSGFIN', 'LT', 'LTF', 'LTIM', 'LTTS', 'LUPIN',
    'M&M', 'M&MFIN', 'MANAPPURAM', 'MARICO', 'MARUTI', 'MCX', 'METROPOLIS', 'MFSL', 'MGL', 'MOTHERSON',
    'MPHASIS', 'MRF', 'MUTHOOTFIN', 'NATIONALUM', 'NAUKRI', 'NAVINFLUOR', 'NESTLEIND', 'NMDC', 'NTPC', 'OBEROIRLTY',
    'OFSS', 'ONGC', 'PAGEIND', 'PEL', 'PERSISTENT', 'PETRONET', 'PFC', 'PIDILITIND', 'PIIND', 'PNB',
    'POLYCAB', 'POWERGRID', 'PVRINOX', 'RAMCOCEM', 'RBLBANK', 'RECLTD', 'RELIANCE', 'SAIL', 'SBICARD', 'SBILIFE',
    'SBIN', 'SHREECEM', 'SHRIRAMFIN', 'SIEMENS', 'SRF', 'SUNPHARMA', 'SUNTV', 'SYNGENE', 'TATACHEM', 'TATACOMM',
    'TATACONSUM', 'TATAMOTORS', 'TATAPOWER', 'TATASTEEL', 'TCS', 'TECHM', 'TITAN', 'TORNTPHARM', 'TRENT', 'TVSMOTOR',
    'UBL', 'ULTRACEMCO', 'UNITDSPR', 'UPL', 'VEDL', 'VOLTAS', 'WIPRO', 'ZYDUSLIFE', 'ZOMATO', 'JIOFIN', 'NHPC', 'IRFC'
}

# Hero Header Render
st.markdown("""
<div class="hero-card">
    <div>
        <div class="hero-title">💎 NSE Pro Terminal</div>
        <div class="hero-sub">Institutional Volume & Delivery Intelligence</div>
    </div>
    <div class="live-pill">🛡️ Safe Cache</div>
</div>
""", unsafe_allow_html=True)

# Settings & X-Ray Controls
with st.expander("🎛️ Scanner Filters & Settings", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        lookback_days = st.slider("Lookback Days", 3, 10, 5)
        high_deliv_pct_limit = st.slider("Min Delivery %", 50, 90, 70)
        fno_only = st.checkbox("⚡ F&O Stocks Only", value=False)
    with c2:
        min_turnover_cr = st.number_input("Min Turnover (₹ Cr)", value=15.0, step=5.0)
        spike_multiplier = st.slider("Volume Spike (X)", 1.2, 5.0, 2.0, step=0.1)
        exclude_etfs = st.checkbox("🚫 Hide ETFs/Bees", value=True)
        
    st.markdown("---")
    uploaded_files = st.file_uploader("📂 Manual CSV Upload", type=['csv'], accept_multiple_files=True)
    if st.button("🗑️ Clear Saved Cache", use_container_width=True):
        for f in os.listdir(CACHE_DIR):
            os.remove(os.path.join(CACHE_DIR, f))
        st.session_state.market_data = None
        st.toast("Cache கிளியர் செய்யப்பட்டது!")

def clean_dataframe(df, date_str_label):
    df.columns = df.columns.str.strip()
    df['SERIES'] = df['SERIES'].astype(str).str.strip()
    df['SYMBOL'] = df['SYMBOL'].astype(str).str.strip()
    df = df[df['SERIES'] == 'EQ'].copy()
    
    num_cols = ['PREV_CLOSE', 'OPEN_PRICE', 'HIGH_PRICE', 'LOW_PRICE', 'CLOSE_PRICE', 
                'AVG_PRICE', 'TTL_TRD_QNTY', 'TURNOVER_LACS', 'DELIV_QTY', 'DELIV_PER']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.strip(), errors='coerce')
            
    df['FETCH_DATE'] = date_str_label
    return df.dropna(subset=['DELIV_QTY', 'DELIV_PER', 'TTL_TRD_QNTY'])

def fetch_or_load_bhavcopy(date_obj):
    date_str = date_obj.strftime("%d%m%Y")
    local_file_path = os.path.join(CACHE_DIR, f"bhav_{date_str}.csv")
    
    if os.path.exists(local_file_path):
        try:
            df = pd.read_csv(local_file_path)
            if 'AVG_PRICE' in df.columns:
                return df
        except Exception:
            pass

    url = f"https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{date_str}.csv"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.nseindia.com/"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200 and "SYMBOL" in r.text:
            raw_df = pd.read_csv(io.StringIO(r.text))
            cleaned_df = clean_dataframe(raw_df, date_obj.strftime("%d-%b-%Y"))
            cleaned_df.to_csv(local_file_path, index=False)
            return cleaned_df
    except Exception:
        return None
    return None

def get_multi_day_data(target_days):
    collected_dfs = []
    check_date = datetime.now()
    attempts = 0
    progress_bar = st.progress(0, text="Syncing Market Data...")
    
    while len(collected_dfs) < target_days and attempts < 25:
        if check_date.weekday() < 5:
            df = fetch_or_load_bhavcopy(check_date)
            if df is not None and not df.empty:
                collected_dfs.append((check_date.strftime("%d-%b-%Y"), df))
                progress_bar.progress(len(collected_dfs) / target_days, 
                                      text=f"Synced: {check_date.strftime('%d-%b-%Y')}")
        check_date -= timedelta(days=1)
        attempts += 1
        
    progress_bar.empty()
    return collected_dfs

if "market_data" not in st.session_state:
    st.session_state.market_data = None

# Auto-load if cache already exists on startup
if st.session_state.market_data is None and len(os.listdir(CACHE_DIR)) >= 3:
    st.session_state.market_data = get_multi_day_data(lookback_days + 1)

if st.button("⚡ Sync / Refresh Market Data", type="primary", use_container_width=True):
    st.session_state.market_data = get_multi_day_data(lookback_days + 1)

if uploaded_files:
    manual_list = []
    for file in uploaded_files:
        raw_df = pd.read_csv(file)
        cleaned_df = clean_dataframe(raw_df, file.name)
        manual_list.append((file.name, cleaned_df))
    st.session_state.market_data = manual_list

data_list = st.session_state.market_data

if data_list:
    latest_date, today_df = data_list[0][0], data_list[0][1].copy()

    # Single Stock X-Ray Expander
    with st.expander("🔍 Single Stock X-Ray (தனி ஸ்டாக் ஜாதகம்)", expanded=False):
        all_symbols = sorted(today_df['SYMBOL'].unique().tolist())
        default_idx = all_symbols.index("RELIANCE") if "RELIANCE" in all_symbols else 0
        selected_stock = st.selectbox("Select Stock:", all_symbols, index=default_idx)
        
        if selected_stock:
            for d_label, df_day in data_list:
                row = df_day[df_day['SYMBOL'] == selected_stock]
                if not row.empty:
                    r = row.iloc[0]
                    chg = round(((r['CLOSE_PRICE'] - r['PREV_CLOSE']) / r['PREV_CLOSE']) * 100, 2)
                    vwap = r['AVG_PRICE'] if 'AVG_PRICE' in r and pd.notna(r['AVG_PRICE']) else r['CLOSE_PRICE']
                    is_buyer = r['CLOSE_PRICE'] >= vwap
                    ctrl_badge = '<span class="pill-buyer">🟢 Buyers</span>' if is_buyer else '<span class="pill-seller">🔴 Sellers</span>'
                    chg_badge = f'<span class="chg-up">+{chg}%</span>' if chg >= 0 else f'<span class="chg-down">{chg}%</span>'
                    deliv_cr = round((r['DELIV_QTY'] * r['CLOSE_PRICE']) / 10000000, 2)
                    
                    st.markdown(f"""
                    <div style="background:rgba(30,41,59,0.5); border:1px solid rgba(255,255,255,0.06); border-radius:12px; padding:10px 14px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-weight:700; font-size:0.85rem; color:#E2E8F0;">{d_label}</div>
                            <div style="margin-top:4px;">{ctrl_badge} <span class="pill-neutral">₹{deliv_cr} Cr Deliv</span></div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-weight:800; font-size:0.95rem;">₹{r['CLOSE_PRICE']:.1f} {chg_badge}</div>
                            <div style="font-size:0.75rem; color:#38BDF8; font-weight:700; margin-top:3px;">Delivery: {r['DELIV_PER']:.1f}%</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # Filtering Logic
    if exclude_etfs:
        etf_keywords = ['BEES', 'ETF', 'LIQUID', 'NIFTY', 'SENSEX', 'GOLD', 'SILVER', 'IETF', 'CASE', 'ADD', 'BETA', 'ALPHA']
        pattern = '|'.join(etf_keywords)
        today_df = today_df[~today_df['SYMBOL'].str.contains(pattern, case=False, na=False)].copy()
        today_df = today_df[~((today_df['CLOSE_PRICE'].between(999, 1001)) & (today_df['HIGH_PRICE'] - today_df['LOW_PRICE'] < 1))].copy()

    if fno_only:
        today_df = today_df[today_df['SYMBOL'].isin(FNO_STOCKS)].copy()

    today_df['PRICE_CHG_PCT'] = (((today_df['CLOSE_PRICE'] - today_df['PREV_CLOSE']) / today_df['PREV_CLOSE']) * 100).round(2)
    today_df['TURNOVER_CR'] = (today_df['TURNOVER_LACS'] / 100).round(2)
    today_df['DELIV_VAL_CR'] = ((today_df['DELIV_QTY'] * today_df['CLOSE_PRICE']) / 10000000).round(2)

    if 'AVG_PRICE' in today_df.columns:
        today_df['IS_BUYER'] = today_df['CLOSE_PRICE'] >= today_df['AVG_PRICE']
    else:
        today_df['IS_BUYER'] = True

    day_range = (today_df['HIGH_PRICE'] - today_df['LOW_PRICE']).replace(0, 0.01)
    today_df['RANGE_POS_PCT'] = (((today_df['CLOSE_PRICE'] - today_df['LOW_PRICE']) / day_range) * 100).round(0)

    if len(data_list) > 1:
        hist_dfs = [d[1] for d in data_list[1:]]
        hist_concat = pd.concat(hist_dfs)
        avg_stats = hist_concat.groupby('SYMBOL').agg(
            AVG_DELIV_QTY=('DELIV_QTY', 'mean'),
            AVG_TRD_QTY=('TTL_TRD_QNTY', 'mean')
        ).reset_index()
        
        merged = pd.merge(today_df, avg_stats, on='SYMBOL', how='left')
        merged['DELIV_SPIKE_X'] = (merged['DELIV_QTY'] / merged['AVG_DELIV_QTY']).round(2)
        merged['TRD_SPIKE_X'] = (merged['TTL_TRD_QNTY'] / merged['AVG_TRD_QTY']).round(2)
    else:
        merged = today_df.copy()
        merged['DELIV_SPIKE_X'] = 1.0
        merged['TRD_SPIKE_X'] = 1.0

    if len(data_list) >= 3:
        d0 = data_list[0][1].set_index('SYMBOL')['DELIV_QTY']
        d1 = data_list[1][1].set_index('SYMBOL')['DELIV_QTY']
        d2 = data_list[2][1].set_index('SYMBOL')['DELIV_QTY']
        streak_df = pd.DataFrame({'D0': d0, 'D1': d1, 'D2': d2}).dropna()
        streak_symbols = streak_df[(streak_df['D0'] > streak_df['D1']) & (streak_df['D1'] > streak_df['D2'])].index.tolist()
        merged['3D_STREAK'] = merged['SYMBOL'].isin(streak_symbols)
    else:
        merged['3D_STREAK'] = False

    base_df = merged[merged['TURNOVER_CR'] >= min_turnover_cr].copy()

    # Scan Selector
    scan_options = [
        "🔥 1. Bullish Accumulation (Price Up + Deliv Spike)",
        "⚡ 2. Day's High Close + Heavy Delivery (Strong Close)",
        "🤫 3. Silent Accumulation (Sideways + Heavy Deliv)",
        "🔒 4. Higher Delivery Qty & % (StockEdge Premium)",
        "🔒 5. Higher Trade & Delivery Qty (StockEdge Premium)",
        "📈 6. 3-Day Continuous Delivery Surge",
        "📊 7. High Delivery Percentage (>70%)",
        "🚀 8. Higher Delivery Quantity (Delivery Spike)",
        "📢 9. Higher Trade Quantity (Volume Spike)",
        "💰 10. High Delivery Value (Top Crores)"
    ]
    
    selected_scan = st.selectbox("🎯 Select Institutional Scan:", scan_options)

    if selected_scan.startswith("🔥 1."):
        res = base_df[(base_df['PRICE_CHG_PCT'] >= 1.5) & (base_df['DELIV_SPIKE_X'] >= spike_multiplier) & (base_df['DELIV_PER'] >= 55) & (base_df['IS_BUYER'] == True)].sort_values(by='DELIV_SPIKE_X', ascending=False)
    elif selected_scan.startswith("⚡ 2."):
        res = base_df[(base_df['RANGE_POS_PCT'] >= 75) & (base_df['PRICE_CHG_PCT'] > 0.5) & (base_df['DELIV_SPIKE_X'] >= 1.5) & (base_df['DELIV_PER'] >= 55)].sort_values(by='DELIV_SPIKE_X', ascending=False)
    elif selected_scan.startswith("🤫 3."):
        res = base_df[(base_df['PRICE_CHG_PCT'].between(-1.0, 1.2)) & (base_df['DELIV_SPIKE_X'] >= spike_multiplier) & (base_df['DELIV_PER'] >= 60)].sort_values(by='DELIV_SPIKE_X', ascending=False)
    elif selected_scan.startswith("🔒 4."):
        res = base_df[(base_df['DELIV_SPIKE_X'] >= spike_multiplier) & (base_df['DELIV_PER'] >= 60)].sort_values(by='DELIV_SPIKE_X', ascending=False)
    elif selected_scan.startswith("🔒 5."):
        res = base_df[(base_df['TRD_SPIKE_X'] >= spike_multiplier) & (base_df['DELIV_SPIKE_X'] >= spike_multiplier)].sort_values(by='DELIV_SPIKE_X', ascending=False)
    elif selected_scan.startswith("📈 6."):
        res = base_df[base_df['3D_STREAK'] == True].sort_values(by='DELIV_PER', ascending=False)
    elif selected_scan.startswith("📊 7."):
        res = base_df[base_df['DELIV_PER'] >= high_deliv_pct_limit].sort_values(by='DELIV_PER', ascending=False)
    elif selected_scan.startswith("🚀 8."):
        res = base_df[base_df['DELIV_SPIKE_X'] >= spike_multiplier].sort_values(by='DELIV_SPIKE_X', ascending=False)
    elif selected_scan.startswith("📢 9."):
        res = base_df[base_df['TRD_SPIKE_X'] >= spike_multiplier].sort_values(by='TRD_SPIKE_X', ascending=False)
    else:
        res = base_df.sort_values(by='DELIV_VAL_CR', ascending=False).head(50)

    # ==========================================
    # 📊 BENTO SUMMARY METRICS
    # ==========================================
    top_spike_str = f"{res['DELIV_SPIKE_X'].max():.1f}X" if not res.empty else "0X"
    st.markdown(f"""
    <div class="bento-grid">
        <div class="bento-box">
            <div class="bento-label">📅 Market Date</div>
            <div class="bento-val">{latest_date[:6]}</div>
        </div>
        <div class="bento-box">
            <div class="bento-label">🎯 Stocks Found</div>
            <div class="bento-val" style="color:#38BDF8;">{len(res)} Stocks</div>
        </div>
        <div class="bento-box">
            <div class="bento-label">🚀 Max Spike</div>
            <div class="bento-val" style="color:#FBBF24;">{top_spike_str}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ==========================================
    # 💎 RENDER DESIGNER GLASS STOCK CARDS
    # ==========================================
    if res.empty:
        st.warning("இந்த ஃபில்டரில் ஸ்டாக்ஸ் எதுவும் சிக்கவில்லை. Settings-ல் Spike அல்லது Turnover அளவைக் குறைத்துப் பார்க்கவும்.")
    else:
        for _, row in res.head(60).iterrows():
            sym = row['SYMBOL']
            price = row['CLOSE_PRICE']
            chg = row['PRICE_CHG_PCT']
            deliv_pct = min(max(row['DELIV_PER'], 0), 100)
            d_spike = row['DELIV_SPIKE_X'] if pd.notna(row['DELIV_SPIKE_X']) else 1.0
            v_spike = row['TRD_SPIKE_X'] if pd.notna(row['TRD_SPIKE_X']) else 1.0
            deliv_cr = row['DELIV_VAL_CR']
            rng_pos = int(row['RANGE_POS_PCT']) if pd.notna(row['RANGE_POS_PCT']) else 50
            
            # Badges
            fno_html = '<span class="badge-fno">⚡ F&O</span>' if sym in FNO_STOCKS else ''
            streak_html = '<span class="badge-streak">🔥 3D SURGE</span>' if row.get('3D_STREAK', False) else ''
            
            chg_html = f'<span class="chg-up">▲ +{chg:.2f}%</span>' if chg >= 0 else f'<span class="chg-down">▼ {chg:.2f}%</span>'
            ctrl_html = '<span class="pill-buyer">🟢 Buyers > VWAP</span>' if row['IS_BUYER'] else '<span class="pill-seller">🔴 Below VWAP</span>'
            
            tv_url = f"https://in.tradingview.com/chart/?symbol=NSE:{sym}"

            card_html = f"""
            <div class="stock-card">
                <div class="sc-top">
                    <div>
                        <div class="sc-symbol-wrap">
                            <span class="sc-symbol">{sym}</span>
                            {fno_html}
                            {streak_html}
                        </div>
                        <div class="sc-sub-pills">
                            {ctrl_html}
                            <span class="pill-neutral">Day High Pos: {rng_pos}%</span>
                        </div>
                    </div>
                    <div class="sc-price-box">
                        <div class="sc-price">₹{price:,.2f}</div>
                        {chg_html}
                    </div>
                </div>
                <div class="sc-metrics">
                    <div>
                        <div class="m-lbl">Delivery %</div>
                        <div class="m-val-accent">{deliv_pct:.1f}%</div>
                    </div>
                    <div>
                        <div class="m-lbl">Deliv Spike</div>
                        <div class="m-val-gold">{d_spike:.2f}x</div>
                    </div>
                    <div>
                        <div class="m-lbl">Deliv Value</div>
                        <div class="m-val">₹{deliv_cr:,.1f} Cr</div>
                    </div>
                </div>
                <div class="sc-footer">
                    <div class="prog-wrap">
                        <div class="prog-bg">
                            <div class="prog-fill" style="width: {deliv_pct}%;"></div>
                        </div>
                    </div>
                    <a href="{tv_url}" target="_blank" class="tv-btn">📈 Chart ↗</a>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
