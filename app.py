import streamlit as st
import pandas as pd
import requests
import io
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="NSE Pro Delivery Scanner", page_icon="📈", layout="wide")

# டேட்டாவை சேவ் செய்து வைக்க ஒரு ஃபோல்டர் உருவாக்குதல் (NSE-க்கு அடிக்கடி போவதைத் தடுக்க)
CACHE_DIR = "nse_data_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

st.title("📈 NSE Pro Volume & Delivery Scanner")
st.markdown("🛡️ **Safe Mode Active:** ஒருமுறை டவுன்லோட் ஆகும் டேட்டா ஆப்பிலேயே சேவ் ஆகிவிடும். NSE பிளாக் செய்யும் பயம் இல்லை!")

# Sidebar Settings
st.sidebar.header("⚙️ Scanner Settings")
lookback_days = st.sidebar.slider("ஆவரேஜ் பார்க்க வேண்டிய நாட்கள் (Lookback Days)", 3, 10, 5)
min_turnover_cr = st.sidebar.number_input("குறைந்தபட்ச Turnover (₹ Crores)", value=15.0, step=5.0)
high_deliv_pct_limit = st.sidebar.slider("High Delivery % Limit", 50, 90, 70)
spike_multiplier = st.sidebar.slider("Volume / Delivery Spike மடங்கு (X times)", 1.2, 5.0, 2.0, step=0.1)
exclude_etfs = st.sidebar.checkbox("🚫 ETFs & Liquid Bees-ஐ தவிர்க்கவும்", value=True)

def clean_dataframe(df, date_str_label):
    df.columns = df.columns.str.strip()
    df['SERIES'] = df['SERIES'].astype(str).str.strip()
    df['SYMBOL'] = df['SYMBOL'].astype(str).str.strip()
    df = df[df['SERIES'] == 'EQ'].copy()
    
    num_cols = ['PREV_CLOSE', 'OPEN_PRICE', 'HIGH_PRICE', 'LOW_PRICE', 'CLOSE_PRICE', 
                'TTL_TRD_QNTY', 'TURNOVER_LACS', 'DELIV_QTY', 'DELIV_PER']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.strip(), errors='coerce')
        
    df['FETCH_DATE'] = date_str_label
    return df.dropna(subset=['DELIV_QTY', 'DELIV_PER', 'TTL_TRD_QNTY'])

# ஃபைல் ஏற்கனவே நம்ம ஃபோல்டரில் இருந்தால் அங்கிருந்தே எடுக்கும் (NSE-க்கு போகாது!)
def fetch_or_load_bhavcopy(date_obj):
    date_str = date_obj.strftime("%d%m%Y")
    local_file_path = os.path.join(CACHE_DIR, f"bhav_{date_str}.csv")
    
    # 1. முதலில் நம்ம சேவ் செய்த ஃபோல்டரில் இருக்கிறதா எனப் பார்க்கும்
    if os.path.exists(local_file_path):
        try:
            df = pd.read_csv(local_file_path)
            return df
        except Exception:
            pass

    # 2. ஃபோல்டரில் இல்லையென்றால் மட்டுமே NSE சர்வரில் இருந்து எடுக்கும்
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
            cleaned_df = clean_dataframe(raw_df, date_obj.strftime("%Y-%m-%d"))
            # அடுத்த முறை NSE-க்கு போகாமல் இருக்க உடனே ஃபோல்டரில் சேவ் செய்தல்!
            cleaned_df.to_csv(local_file_path, index=False)
            return cleaned_df
    except Exception:
        return None
    return None

def get_multi_day_data(target_days):
    collected_dfs = []
    check_date = datetime.now()
    attempts = 0
    progress_bar = st.progress(0, text="டேட்டா சரிபார்க்கப்படுகிறது...")
    
    while len(collected_dfs) < target_days and attempts < 25:
        if check_date.weekday() < 5:
            df = fetch_or_load_bhavcopy(check_date)
            if df is not None and not df.empty:
                collected_dfs.append((check_date.strftime("%d-%b-%Y"), df))
                progress_bar.progress(len(collected_dfs) / target_days, 
                                      text=f"Loaded: {check_date.strftime('%d-%b-%Y')} ({len(collected_dfs)}/{target_days})")
        check_date -= timedelta(days=1)
        attempts += 1
        
    progress_bar.empty()
    return collected_dfs

# Session State-ல் டேட்டாவை வைத்திருத்தல் (ஸ்லைடர் மாற்றும்போது ரீலோடு ஆகாமல் இருக்க)
if "market_data" not in st.session_state:
    st.session_state.market_data = None

col1, col2 = st.columns([2, 1])
with col1:
    if st.button("🚀 Load / Scan Market Data", type="primary"):
        st.session_state.market_data = get_multi_day_data(lookback_days + 1)
with col2:
    if st.button("🗑️ Clear Saved Cache"):
        for f in os.listdir(CACHE_DIR):
            os.remove(os.path.join(CACHE_DIR, f))
        st.session_state.market_data = None
        st.toast("பழைய கேட்ச் (Cache) கிளியர் செய்யப்பட்டது!")

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Manual CSV Upload (Backup)")
uploaded_files = st.sidebar.file_uploader("NSE CSV ஃபைல்கள்", type=['csv'], accept_multiple_files=True)

if uploaded_files:
    manual_list = []
    for file in uploaded_files:
        raw_df = pd.read_csv(file)
        cleaned_df = clean_dataframe(raw_df, file.name)
        manual_list.append((file.name, cleaned_df))
    st.session_state.market_data = manual_list

# டேட்டா தயாராக இருந்தால் ஸ்கேன்களைக் காட்டுதல்
data_list = st.session_state.market_data

if data_list:
    latest_date, today_df = data_list[0][0], data_list[0][1].copy()
    st.success(f"✅ லேட்டஸ்ட் மார்க்கெட் டேட்டா: **{latest_date}** (Saved Cache-ல் இருந்து உடனடியாக எடுக்கப்பட்டது!)")

    if exclude_etfs:
        etf_keywords = ['BEES', 'ETF', 'LIQUID', 'NIFTY', 'SENSEX', 'GOLD', 'SILVER', 'IETF', 'CASE', 'ADD', 'BETA', 'ALPHA']
        pattern = '|'.join(etf_keywords)
        today_df = today_df[~today_df['SYMBOL'].str.contains(pattern, case=False, na=False)].copy()
        today_df = today_df[~((today_df['CLOSE_PRICE'].between(999, 1001)) & (today_df['HIGH_PRICE'] - today_df['LOW_PRICE'] < 1))].copy()

    today_df['PRICE_CHG_PCT'] = (((today_df['CLOSE_PRICE'] - today_df['PREV_CLOSE']) / today_df['PREV_CLOSE']) * 100).round(2)
    today_df['TURNOVER_CR'] = (today_df['TURNOVER_LACS'] / 100).round(2)
    today_df['DELIV_VAL_CR'] = ((today_df['DELIV_QTY'] * today_df['CLOSE_PRICE']) / 10000000).round(2)

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

    display_cols = ['SYMBOL', 'CLOSE_PRICE', 'PRICE_CHG_PCT', 'DELIV_PER', 'DELIV_SPIKE_X', 'TRD_SPIKE_X', 'DELIV_VAL_CR', 'TURNOVER_CR', 'CHART']

    def show_table(df_to_show):
        st.dataframe(
            df_to_show[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "SYMBOL": st.column_config.TextColumn("Stock"),
                "CLOSE_PRICE": st.column_config.NumberColumn("Price (₹)", format="₹%.2f"),
                "PRICE_CHG_PCT": st.column_config.NumberColumn("Chg %", format="%.2f%%"),
                "DELIV_PER": st.column_config.NumberColumn("Deliv %", format="%.1f%%"),
                "DELIV_SPIKE_X": st.column_config.NumberColumn("Deliv Spike", format="%.2fX"),
                "TRD_SPIKE_X": st.column_config.NumberColumn("Vol Spike", format="%.2fX"),
                "DELIV_VAL_CR": st.column_config.NumberColumn("Deliv Val (Cr)", format="₹%.2f Cr"),
                "TURNOVER_CR": st.column_config.NumberColumn("Turnover (Cr)", format="₹%.2f Cr"),
                "CHART": st.column_config.LinkColumn("TradingView", display_text="📊 Chart")
            }
        )

    st.subheader("🎯 StockEdge 5 Scans + 4 Pro Institutional Scans")
    tabs = st.tabs([
        "1. High Deliv %", 
        "2. Higher Deliv Qty", 
        "3. Higher Trade Qty", 
        "🔒 4. Higher Deliv Qty & %", 
        "🔒 5. Higher Trade & Deliv Qty",
        "🔥 6. Bullish Accumulation",
        "🤫 7. Silent Accumulation",
        "📈 8. 3-Day Surge",
        "💰 9. High Delivery Value"
    ])

    with tabs[0]:
        st.caption(f"டெலிவரி பர்சன்டேஜ் {high_deliv_pct_limit}%-க்கு மேல் இருக்கும் Pure Stocks")
        show_table(base_df[base_df['DELIV_PER'] >= high_deliv_pct_limit].sort_values(by='DELIV_PER', ascending=False))

    with tabs[1]:
        st.caption(f"கடந்த நாட்களின் ஆவரேஜை விட {spike_multiplier}X மடங்கு அதிக டெலிவரி குவான்டிட்டி நடந்த ஸ்டாக்ஸ்")
        show_table(base_df[base_df['DELIV_SPIKE_X'] >= spike_multiplier].sort_values(by='DELIV_SPIKE_X', ascending=False))

    with tabs[2]:
        st.caption(f"கடந்த நாட்களின் ஆவரேஜை விட {spike_multiplier}X மடங்கு அதிக Total Trade Quantity நடந்த ஸ்டாக்ஸ்")
        show_table(base_df[base_df['TRD_SPIKE_X'] >= spike_multiplier].sort_values(by='TRD_SPIKE_X', ascending=False))

    with tabs[3]:
        st.caption(f"🔒 Premium Scan: டெலிவரி குவான்டிட்டி {spike_multiplier}X மடங்கு அதிகம் + டெலிவரி % >= 60%")
        show_table(base_df[(base_df['DELIV_SPIKE_X'] >= spike_multiplier) & (base_df['DELIV_PER'] >= 60)].sort_values(by='DELIV_SPIKE_X', ascending=False))

    with tabs[4]:
        st.caption(f"🔒 Premium Scan: Total Trade Quantity & Delivery Quantity இரண்டுமே {spike_multiplier}X மடங்கு எகிறிய ஸ்டாக்ஸ்")
        show_table(base_df[(base_df['TRD_SPIKE_X'] >= spike_multiplier) & (base_df['DELIV_SPIKE_X'] >= spike_multiplier)].sort_values(by='DELIV_SPIKE_X', ascending=False))

    with tabs[5]:
        st.caption("🔥 Pro Scan: Price > +1.5% Up + Delivery Spike + High Delivery % (பக்கா Institutional Buying!)")
        show_table(base_df[(base_df['PRICE_CHG_PCT'] >= 1.5) & (base_df['DELIV_SPIKE_X'] >= spike_multiplier) & (base_df['DELIV_PER'] >= 55)].sort_values(by='DELIV_SPIKE_X', ascending=False))

    with tabs[6]:
        st.caption("🤫 Pro Scan: விலை பெருசா மாறாமல் (-1% to +1.2%) சத்தமில்லாமல் Heavy Delivery நடந்த ஸ்டாக்ஸ் (Pre-Breakout)")
        show_table(base_df[(base_df['PRICE_CHG_PCT'].between(-1.0, 1.2)) & (base_df['DELIV_SPIKE_X'] >= spike_multiplier) & (base_df['DELIV_PER'] >= 60)].sort_values(by='DELIV_SPIKE_X', ascending=False))

    with tabs[7]:
        st.caption("📈 Pro Scan: தொடர்ந்து கடந்த 3 நாட்களாக டெலிவரி குவான்டிட்டி ஏறிக்கொண்டே போகும் ஸ்டாக்ஸ்")
        show_table(base_df[base_df['3D_STREAK'] == True].sort_values(by='DELIV_PER', ascending=False))

    with tabs[8]:
        st.caption("💰 Pro Scan: அதிக கோடி ரூபாய்க்கு (Delivery Value in Crores) டெலிவரி எடுக்கப்பட்ட டாப் 50 ஸ்டாக்ஸ்")
        show_table(base_df.sort_values(by='DELIV_VAL_CR', ascending=False).head(50))
