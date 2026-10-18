import streamlit as st
import pandas as pd
import requests
import io
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="NSE Pro Scanner", page_icon="📱", layout="wide")

# மொபைல் ஸ்கிரீனுக்கு ஏற்றவாறு மேல் மற்றும் பக்கவாட்டு இடைவெளிகளைக் குறைக்கும் CSS
st.markdown("""
<style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.3rem;
    }
</style>
""", unsafe_allow_html=True)

CACHE_DIR = "nse_data_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# முக்கிய F&O ஸ்டாக்ஸ் பட்டியல் (⚡ F&O Filter-க்காக)
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

st.markdown("### 📱 NSE Pro Delivery Scanner")

# மொபைலுக்கு ஏற்ற மெயின் ஸ்கிரீன் செட்டிங்ஸ் பாக்ஸ் (Sidebar தேட வேண்டாம்!)
with st.expander("⚙️ Scanner Filters & Settings (மாற்ற இங்கே தொடவும்)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        lookback_days = st.slider("Lookback Days (ஆவரேஜ்)", 3, 10, 5)
        high_deliv_pct_limit = st.slider("High Delivery % Limit", 50, 90, 70)
        fno_only = st.checkbox("⚡ F&O Stocks Only", value=False)
    with c2:
        min_turnover_cr = st.number_input("Min Turnover (₹ Cr)", value=15.0, step=5.0)
        spike_multiplier = st.slider("Volume Spike (X times)", 1.2, 5.0, 2.0, step=0.1)
        exclude_etfs = st.checkbox("🚫 ETFs & Bees தவிர்க்க", value=True)
        
    st.markdown("---")
    uploaded_files = st.file_uploader("📂 Manual CSV Upload (ஆப்ஷனல்)", type=['csv'], accept_multiple_files=True)
    if st.button("🗑️ Clear Saved Cache"):
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
    progress_bar = st.progress(0, text="டேட்டா லோடு ஆகிறது...")
    
    while len(collected_dfs) < target_days and attempts < 25:
        if check_date.weekday() < 5:
            df = fetch_or_load_bhavcopy(check_date)
            if df is not None and not df.empty:
                collected_dfs.append((check_date.strftime("%d-%b-%Y"), df))
                progress_bar.progress(len(collected_dfs) / target_days, 
                                      text=f"Loaded: {check_date.strftime('%d-%b-%Y')}")
        check_date -= timedelta(days=1)
        attempts += 1
        
    progress_bar.empty()
    return collected_dfs

if "market_data" not in st.session_state:
    st.session_state.market_data = None

# மெயின் பட்டன் (மொபைல் முழு அகலத்திற்கு)
if st.button("🚀 Load / Scan Market Data", type="primary", use_container_width=True):
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
    st.caption(f"🛡️ **Safe Cache Active** | 📅 Date: **{latest_date}** ({len(data_list)} Days Data)")

    # ==========================================
    # 🔍 FEATURE 1: SINGLE STOCK X-RAY SEARCH
    # ==========================================
    with st.expander("🔍 Single Stock X-Ray (தனி ஸ்டாக் ஜாதகம் பார்க்க)", expanded=False):
        all_symbols = sorted(today_df['SYMBOL'].unique().tolist())
        default_idx = all_symbols.index("RELIANCE") if "RELIANCE" in all_symbols else 0
        selected_stock = st.selectbox("ஸ்டாக் பெயரை டைப் செய்யவும்:", all_symbols, index=default_idx)
        
        if selected_stock:
            xray_rows = []
            for d_label, df_day in data_list:
                row = df_day[df_day['SYMBOL'] == selected_stock]
                if not row.empty:
                    r = row.iloc[0]
                    chg = round(((r['CLOSE_PRICE'] - r['PREV_CLOSE']) / r['PREV_CLOSE']) * 100, 2)
                    vwap = r['AVG_PRICE'] if 'AVG_PRICE' in r and pd.notna(r['AVG_PRICE']) else r['CLOSE_PRICE']
                    ctrl = "🟢 Buyers" if r['CLOSE_PRICE'] >= vwap else "🔴 Sellers"
                    deliv_cr = round((r['DELIV_QTY'] * r['CLOSE_PRICE']) / 10000000, 2)
                    xray_rows.append({
                        "Date": d_label[:6],
                        "Close": f"₹{r['CLOSE_PRICE']:.1f}",
                        "Chg%": f"{chg}%",
                        "Deliv%": f"{r['DELIV_PER']:.1f}%",
                        "Deliv(Cr)": f"₹{deliv_cr}Cr",
                        "Control": ctrl
                    })
            st.dataframe(pd.DataFrame(xray_rows), use_container_width=True, hide_index=True)

    # ==========================================
    # FILTERS & PRO CALCULATIONS
    # ==========================================
    if exclude_etfs:
        etf_keywords = ['BEES', 'ETF', 'LIQUID', 'NIFTY', 'SENSEX', 'GOLD', 'SILVER', 'IETF', 'CASE', 'ADD', 'BETA', 'ALPHA']
        pattern = '|'.join(etf_keywords)
        today_df = today_df[~today_df['SYMBOL'].str.contains(pattern, case=False, na=False)].copy()
        today_df = today_df[~((today_df['CLOSE_PRICE'].between(999, 1001)) & (today_df['HIGH_PRICE'] - today_df['LOW_PRICE'] < 1))].copy()

    # ⚡ FEATURE 2: F&O ONLY FILTER
    if fno_only:
        today_df = today_df[today_df['SYMBOL'].isin(FNO_STOCKS)].copy()

    today_df['PRICE_CHG_PCT'] = (((today_df['CLOSE_PRICE'] - today_df['PREV_CLOSE']) / today_df['PREV_CLOSE']) * 100).round(2)
    today_df['TURNOVER_CR'] = (today_df['TURNOVER_LACS'] / 100).round(2)
    today_df['DELIV_VAL_CR'] = ((today_df['DELIV_QTY'] * today_df['CLOSE_PRICE']) / 10000000).round(2)

    # 📊 FEATURE 3: VWAP vs CLOSE PRICE (Buyer/Seller Control)
    if 'AVG_PRICE' in today_df.columns:
        today_df['VWAP_SIGNAL'] = today_df.apply(
            lambda r: "🟢 Buyer" if r['CLOSE_PRICE'] >= r['AVG_PRICE'] else "🔴 Seller", axis=1
        )
    else:
        today_df['VWAP_SIGNAL'] = "⚪ N/A"

    # ⚡ FEATURE 4: INTRADAY RECOVERY / DAY'S HIGH CLOSE (Close in Top 25% of Day's Range)
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
    base_df['CHART'] = "https://in.tradingview.com/chart/?symbol=NSE:" + base_df['SYMBOL']

    # மொபைலுக்கு ஏற்ற கச்சிதமான காலம் வரிசை (Compact Columns)
    display_cols = ['SYMBOL', 'CLOSE_PRICE', 'PRICE_CHG_PCT', 'DELIV_PER', 'DELIV_SPIKE_X', 'VWAP_SIGNAL', 'DELIV_VAL_CR', 'CHART']

    def show_mobile_table(df_to_show):
        st.caption(f"📊 மொத்தம் **{len(df_to_show)} ஸ்டாக்ஸ்** ஃபில்டர் செய்யப்பட்டுள்ளன:")
        st.dataframe(
            df_to_show[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "SYMBOL": st.column_config.TextColumn("Stock"),
                "CLOSE_PRICE": st.column_config.NumberColumn("Price", format="₹%.1f"),
                "PRICE_CHG_PCT": st.column_config.NumberColumn("Chg%", format="%.1f%%"),
                "DELIV_PER": st.column_config.NumberColumn("Deliv%", format="%.1f%%"),
                "DELIV_SPIKE_X": st.column_config.NumberColumn("Spike", format="%.1fX"),
                "VWAP_SIGNAL": st.column_config.TextColumn("Control"),
                "DELIV_VAL_CR": st.column_config.NumberColumn("Deliv(Cr)", format="₹%.1fCr"),
                "CHART": st.column_config.LinkColumn("Chart", display_text="📈 View")
            }
        )

    # ==========================================
    # 📱 MOBILE-FRIENDLY SCAN SELECTOR (DROPDOWN)
    # ==========================================
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
    
    selected_scan = st.selectbox("🎯 பார்க்க வேண்டிய ஸ்கேனை தேர்வு செய்யவும்:", scan_options)

    if selected_scan.startswith("🔥 1."):
        st.info("💡 Price > +1.5% Up + Delivery Spike + Buyers above VWAP (பக்கா Institutional Buying!)")
        res = base_df[(base_df['PRICE_CHG_PCT'] >= 1.5) & (base_df['DELIV_SPIKE_X'] >= spike_multiplier) & (base_df['DELIV_PER'] >= 55) & (base_df['VWAP_SIGNAL'] == "🟢 Buyer")].sort_values(by='DELIV_SPIKE_X', ascending=False)
        show_mobile_table(res)

    elif selected_scan.startswith("⚡ 2."):
        st.info("💡 மார்க்கெட் முடியும்போது அன்றைய உச்ச விலைக்கு (Day's High-க்கு மிக அருகில்) Heavy Delivery-யுடன் க்ளோஸ் ஆன ஸ்டாக்ஸ்!")
        res = base_df[(base_df['RANGE_POS_PCT'] >= 75) & (base_df['PRICE_CHG_PCT'] > 0.5) & (base_df['DELIV_SPIKE_X'] >= 1.5) & (base_df['DELIV_PER'] >= 55)].sort_values(by='DELIV_SPIKE_X', ascending=False)
        show_mobile_table(res)

    elif selected_scan.startswith("🤫 3."):
        st.info("💡 விலை பெருசா மாறாமல் (-1% to +1.2%) சத்தமில்லாமல் Heavy Delivery நடந்த ஸ்டாக்ஸ் (Pre-Breakout)")
        res = base_df[(base_df['PRICE_CHG_PCT'].between(-1.0, 1.2)) & (base_df['DELIV_SPIKE_X'] >= spike_multiplier) & (base_df['DELIV_PER'] >= 60)].sort_values(by='DELIV_SPIKE_X', ascending=False)
        show_mobile_table(res)

    elif selected_scan.startswith("🔒 4."):
        st.info(f"💡 StockEdge Premium: டெலிவரி குவான்டிட்டி {spike_multiplier}X மடங்கு அதிகம் + டெலிவரி % >= 60%")
        res = base_df[(base_df['DELIV_SPIKE_X'] >= spike_multiplier) & (base_df['DELIV_PER'] >= 60)].sort_values(by='DELIV_SPIKE_X', ascending=False)
        show_mobile_table(res)

    elif selected_scan.startswith("🔒 5."):
        st.info(f"💡 StockEdge Premium: Total Trade Quantity & Delivery Quantity இரண்டுமே {spike_multiplier}X மடங்கு எகிறிய ஸ்டாக்ஸ்")
        res = base_df[(base_df['TRD_SPIKE_X'] >= spike_multiplier) & (base_df['DELIV_SPIKE_X'] >= spike_multiplier)].sort_values(by='DELIV_SPIKE_X', ascending=False)
        show_mobile_table(res)

    elif selected_scan.startswith("📈 6."):
        st.info("💡 தொடர்ந்து கடந்த 3 நாட்களாக டெலிவரி குவான்டிட்டி ஏறிக்கொண்டே போகும் ஸ்டாக்ஸ்")
        res = base_df[base_df['3D_STREAK'] == True].sort_values(by='DELIV_PER', ascending=False)
        show_mobile_table(res)

    elif selected_scan.startswith("📊 7."):
        st.info(f"💡 டெலிவரி பர்சன்டேஜ் {high_deliv_pct_limit}%-க்கு மேல் இருக்கும் Pure Stocks")
        res = base_df[base_df['DELIV_PER'] >= high_deliv_pct_limit].sort_values(by='DELIV_PER', ascending=False)
        show_mobile_table(res)

    elif selected_scan.startswith("🚀 8."):
        st.info(f"💡 கடந்த நாட்களின் ஆவரேஜை விட {spike_multiplier}X மடங்கு அதிக டெலிவரி குவான்டிட்டி நடந்த ஸ்டாக்ஸ்")
        res = base_df[base_df['DELIV_SPIKE_X'] >= spike_multiplier].sort_values(by='DELIV_SPIKE_X', ascending=False)
        show_mobile_table(res)

    elif selected_scan.startswith("📢 9."):
        st.info(f"💡 கடந்த நாட்களின் ஆவரேஜை விட {spike_multiplier}X மடங்கு அதிக Total Trade Quantity நடந்த ஸ்டாக்ஸ்")
        res = base_df[base_df['TRD_SPIKE_X'] >= spike_multiplier].sort_values(by='TRD_SPIKE_X', ascending=False)
        show_mobile_table(res)

    elif selected_scan.startswith("💰 10."):
        st.info("💡 அதிக கோடி ரூபாய்க்கு (Delivery Value in Crores) டெலிவரி எடுக்கப்பட்ட டாப் 50 ஸ்டாக்ஸ்")
        res = base_df.sort_values(by='DELIV_VAL_CR', ascending=False).head(50)
        show_mobile_table(res)
