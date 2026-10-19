import streamlit as st
import pandas as pd
import requests
import io
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="NSE Pro Delivery Scanner", page_icon="📈", layout="wide")

# டேட்டாவை சேவ் செய்து வைக்க Cache ஃபோல்டர்
CACHE_DIR = "nse_data_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

st.title("📈 NSE Pro Volume & Delivery Scanner")
st.markdown("🛡️ **Safe Mode Active:** ஒருமுறை டவுன்லோட் ஆகும் டேட்டா ஆப்பிலேயே சேவ் ஆகிவிடும். NSE பிளாக் செய்யும் பயம் இல்லை!")

# ---------------- SIDEBAR SETTINGS ----------------
st.sidebar.header("⚙️ Scanner Settings")

# 75% Delivery Master Filter (Default 75%)
min_deliv_pct_global = st.sidebar.slider(
    "🎯 குறைந்தபட்ச Delivery % (Global Filter)", 
    min_value=10, max_value=95, value=75, step=5,
    help="75% என வைத்தால், 75%-க்கு மேல் டெலிவரி நடந்த ஸ்டாக்ஸ் மட்டுமே எல்லா ஸ்கேன்களிலும் வரும்."
)

lookback_days = st.sidebar.slider("ஆவரேஜ் & ஹிஸ்டரி பார்க்க வேண்டிய நாட்கள்", 3, 15, 6)
min_turnover_cr = st.sidebar.number_input("குறைந்தபட்ச Turnover (₹ Crores)", value=15.0, step=5.0)
spike_multiplier = st.sidebar.slider("Volume / Delivery Spike மடங்கு (X times)", 1.2, 5.0, 2.0, step=0.1)
exclude_etfs = st.sidebar.checkbox("🚫 ETFs & Liquid Bees-ஐ தவிர்க்கவும்", value=True)

# ---------------- DATA FETCHING FUNCTIONS ----------------
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

def fetch_or_load_bhavcopy(date_obj):
    date_str = date_obj.strftime("%d%m%Y")
    local_file_path = os.path.join(CACHE_DIR, f"bhav_{date_str}.csv")
    
    if os.path.exists(local_file_path):
        try:
            df = pd.read_csv(local_file_path)
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
    progress_bar = st.progress(0, text="டேட்டா சரிபார்க்கப்படுகிறது...")
    
    while len(collected_dfs) < target_days and attempts < 35:
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

if "market_data" not in st.session_state:
    st.session_state.market_data = None

col1, col2 = st.columns([2, 1])
with col1:
    if st.button("🚀 Load / Scan Market Data", type="primary", use_container_width=True):
        st.session_state.market_data = get_multi_day_data(lookback_days + 1)
with col2:
    if st.button("🗑️ Clear Saved Cache", use_container_width=True):
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

# ---------------- DATA PROCESSING ----------------
data_list = st.session_state.market_data

if data_list:
    available_dates = [d[0] for d in data_list]
    
    # 📅 PREVIOUS DAYS SELECTION DROPDOWN
    st.markdown("---")
    c_date, c_info = st.columns([1.5, 2.5])
    with c_date:
        selected_date_label = st.selectbox(
            "📅 எந்த நாளுக்கான ஸ்கேன் பார்க்க வேண்டும்?",
            options=available_dates,
            index=0,
            help="லேட்டஸ்ட் தேதி மட்டுமல்லாமல் முந்தைய நாட்களையும் இங்கே தேர்வு செய்து பார்க்கலாம்."
        )
    with c_info:
        st.info(f"தேர்வு செய்த தேதி: **{selected_date_label}** | ஃபில்டர்: **>= {min_deliv_pct_global}% Deliv** & **₹{min_turnover_cr} Cr Turnover**")

    # தேர்ந்தெடுக்கப்பட்ட தேதியின் இன்டெக்ஸ்
    selected_idx = available_dates.index(selected_date_label)
    target_day_df = data_list[selected_idx][1].copy()

    # ETF Exclusion
    if exclude_etfs:
        etf_keywords = ['BEES', 'ETF', 'LIQUID', 'NIFTY', 'SENSEX', 'GOLD', 'SILVER', 'IETF', 'CASE', 'ADD', 'BETA', 'ALPHA', 'GILT', 'BOND']
        pattern = '|'.join(etf_keywords)
        target_day_df = target_day_df[~target_day_df['SYMBOL'].str.contains(pattern, case=False, na=False)].copy()
        target_day_df = target_day_df[~((target_day_df['CLOSE_PRICE'].between(999, 1001)) & (target_day_df['HIGH_PRICE'] - target_day_df['LOW_PRICE'] < 1))].copy()

    target_day_df['PRICE_CHG_PCT'] = (((target_day_df['CLOSE_PRICE'] - target_day_df['PREV_CLOSE']) / target_day_df['PREV_CLOSE']) * 100).round(2)
    target_day_df['TURNOVER_CR'] = (target_day_df['TURNOVER_LACS'] / 100).round(2)
    target_day_df['DELIV_VAL_CR'] = ((target_day_df['DELIV_QTY'] * target_day_df['CLOSE_PRICE']) / 10000000).round(2)

    # முந்தைய நாட்களின் சராசரியைக் கணக்கிடுதல் (Selected Date-க்கு முந்தைய நாட்கள்)
    remaining_days = data_list[selected_idx + 1:]
    if len(remaining_days) > 0:
        hist_dfs = [d[1] for d in remaining_days]
        hist_concat = pd.concat(hist_dfs)
        avg_stats = hist_concat.groupby('SYMBOL').agg(
            AVG_DELIV_QTY=('DELIV_QTY', 'mean'),
            AVG_TRD_QTY=('TTL_TRD_QNTY', 'mean')
        ).reset_index()
        
        merged = pd.merge(target_day_df, avg_stats, on='SYMBOL', how='left')
        merged['DELIV_SPIKE_X'] = (merged['DELIV_QTY'] / merged['AVG_DELIV_QTY']).round(2)
        merged['TRD_SPIKE_X'] = (merged['TTL_TRD_QNTY'] / merged['AVG_TRD_QTY']).round(2)
    else:
        merged = target_day_df.copy()
        merged['DELIV_SPIKE_X'] = 1.0
        merged['TRD_SPIKE_X'] = 1.0

    # 3-Day Streak Calculation
    if len(data_list) >= (selected_idx + 3):
        d0 = data_list[selected_idx][1].set_index('SYMBOL')['DELIV_QTY']
        d1 = data_list[selected_idx + 1][1].set_index('SYMBOL')['DELIV_QTY']
        d2 = data_list[selected_idx + 2][1].set_index('SYMBOL')['DELIV_QTY']
        streak_df = pd.DataFrame({'D0': d0, 'D1': d1, 'D2': d2}).dropna()
        streak_symbols = streak_df[(streak_df['D0'] > streak_df['D1']) & (streak_df['D1'] > streak_df['D2'])].index.tolist()
        merged['3D_STREAK'] = merged['SYMBOL'].isin(streak_symbols)
    else:
        merged['3D_STREAK'] = False

    # Base Filter: Turnover & Global Delivery % Filter
    base_df = merged[
        (merged['TURNOVER_CR'] >= min_turnover_cr) & 
        (merged['DELIV_PER'] >= min_deliv_pct_global)
    ].copy()
    
    base_df['CHART'] = "https://in.tradingview.com/chart/?symbol=NSE:" + base_df['SYMBOL']

    # ---------------- SINGLE STOCK TRACKER ----------------
    with st.expander("🔍 தனிப்பட்ட ஸ்டாக்கின் Multi-Day Delivery History பார்க்க (Click to Expand)"):
        all_symbols = sorted(target_day_df['SYMBOL'].unique().tolist())
        selected_stock = st.selectbox("ஸ்டாக் பெயரைத் தேர்ந்தெடுக்கவும்:", all_symbols)
        
        if selected_stock:
            stock_history = []
            for date_label, df_day in data_list:
                row = df_day[df_day['SYMBOL'] == selected_stock]
                if not row.empty:
                    r = row.iloc[0]
                    chg = round(((r['CLOSE_PRICE'] - r['PREV_CLOSE']) / r['PREV_CLOSE']) * 100, 2)
                    deliv_cr = round((r['DELIV_QTY'] * r['CLOSE_PRICE']) / 10000000, 2)
                    stock_history.append({
                        "Date": date_label,
                        "Close (₹)": r['CLOSE_PRICE'],
                        "Chg %": chg,
                        "Delivery %": r['DELIV_PER'],
                        "Delivery Qty": int(r['DELIV_QTY']),
                        "Total Vol": int(r['TTL_TRD_QNTY']),
                        "Deliv Value (Cr)": deliv_cr
                    })
            if stock_history:
                hist_df_view = pd.DataFrame(stock_history)
                st.markdown(f"📊 **{selected_stock}** - [Open TradingView Chart](https://in.tradingview.com/chart/?symbol=NSE:{selected_stock})")
                st.dataframe(hist_df_view, use_container_width=True, hide_index=True)

    # ---------------- MOBILE VIEW & DOWNLOAD TABLE ----------------
    display_cols = ['SYMBOL', 'CHART', 'DELIV_PER', 'DELIV_SPIKE_X', 'PRICE_CHG_PCT', 'CLOSE_PRICE', 'DELIV_VAL_CR', 'TRD_SPIKE_X', 'TURNOVER_CR']

    def show_table(df_to_show, scan_name):
        st.markdown(f"**தேதி:** `{selected_date_label}` | **ஸ்டாக்ஸ் எண்ணிக்கை:** `{len(df_to_show)}`")
        
        if df_to_show.empty:
            st.warning(f"இந்த தேதியில் {min_deliv_pct_global}% Delivery & ₹{min_turnover_cr} Cr Turnover கண்டிஷனில் ஸ்டாக்ஸ் எதுவும் வரவில்லை.")
            return

        st.dataframe(
            df_to_show[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "SYMBOL": st.column_config.TextColumn("Stock"),
                "CHART": st.column_config.LinkColumn("Chart", display_text="📊 View"),
                "DELIV_PER": st.column_config.NumberColumn("Deliv %", format="%.1f%%"),
                "DELIV_SPIKE_X": st.column_config.NumberColumn("Deliv Spike", format="%.2fX"),
                "PRICE_CHG_PCT": st.column_config.NumberColumn("Chg %", format="%.2f%%"),
                "CLOSE_PRICE": st.column_config.NumberColumn("Price (₹)", format="₹%.2f"),
                "DELIV_VAL_CR": st.column_config.NumberColumn("Deliv Val", format="₹%.2f Cr"),
                "TRD_SPIKE_X": st.column_config.NumberColumn("Vol Spike", format="%.2fX"),
                "TURNOVER_CR": st.column_config.NumberColumn("Turnover", format="₹%.2f Cr"),
            }
        )
        
        csv_data = df_to_show[display_cols].to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"📥 Download ({selected_date_label}) CSV",
            data=csv_data,
            file_name=f"{scan_name}_{selected_date_label}.csv",
            mime="text/csv",
            key=f"dl_{scan_name}_{selected_date_label}"
        )

    st.subheader(f"🎯 Scans for {selected_date_label} (Filtered: >= {min_deliv_pct_global}% Delivery)")
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
        st.caption(f"டெலிவரி பர்சன்டேஜ் {min_deliv_pct_global}%-க்கு மேல் உள்ள Pure Stocks")
        show_table(base_df.sort_values(by='DELIV_PER', ascending=False), "High_Deliv_Pct")

    with tabs[1]:
        st.caption(f"முந்தைய நாட்களின் ஆவரேஜை விட {spike_multiplier}X மடங்கு அதிக டெலிவரி குவான்டிட்டி")
        show_table(base_df[base_df['DELIV_SPIKE_X'] >= spike_multiplier].sort_values(by='DELIV_SPIKE_X', ascending=False), "Higher_Deliv_Qty")

    with tabs[2]:
        st.caption(f"முந்தைய நாட்களின் ஆவரேஜை விட {spike_multiplier}X மடங்கு அதிக Total Volume")
        show_table(base_df[base_df['TRD_SPIKE_X'] >= spike_multiplier].sort_values(by='TRD_SPIKE_X', ascending=False), "Higher_Trade_Qty")

    with tabs[3]:
        st.caption(f"🔒 Premium Scan: டெலிவரி குவான்டிட்டி {spike_multiplier}X மடங்கு அதிகம் + டெலிவரி % >= {min_deliv_pct_global}%")
        show_table(base_df[base_df['DELIV_SPIKE_X'] >= spike_multiplier].sort_values(by='DELIV_PER', ascending=False), "Higher_Deliv_Qty_And_Pct")

    with tabs[4]:
        st.caption(f"🔒 Premium Scan: Total Volume & Delivery Quantity இரண்டுமே {spike_multiplier}X மடங்கு எகிறிய ஸ்டாக்ஸ்")
        show_table(base_df[(base_df['TRD_SPIKE_X'] >= spike_multiplier) & (base_df['DELIV_SPIKE_X'] >= spike_multiplier)].sort_values(by='DELIV_SPIKE_X', ascending=False), "Higher_Trade_And_Deliv_Qty")

    with tabs[5]:
        st.caption("🔥 Pro Scan: Price > +1.5% Up + Delivery Spike + High Delivery % (Institutional Buying)")
        show_table(base_df[(base_df['PRICE_CHG_PCT'] >= 1.5) & (base_df['DELIV_SPIKE_X'] >= spike_multiplier)].sort_values(by='DELIV_SPIKE_X', ascending=False), "Bullish_Accumulation")

    with tabs[6]:
        st.caption("🤫 Pro Scan: விலை பெருசா மாறாமல் (-1% to +1.2%) சத்தமில்லாமல் Heavy Delivery நடந்த ஸ்டாக்ஸ்")
        show_table(base_df[(base_df['PRICE_CHG_PCT'].between(-1.0, 1.2)) & (base_df['DELIV_SPIKE_X'] >= spike_multiplier)].sort_values(by='DELIV_SPIKE_X', ascending=False), "Silent_Accumulation")

    with tabs[7]:
        st.caption("📈 Pro Scan: முந்தைய 3 நாட்களாக தொடர்ந்து டெலிவரி குவான்டிட்டி ஏறிய ஸ்டாக்ஸ்")
        show_table(base_df[base_df['3D_STREAK'] == True].sort_values(by='DELIV_PER', ascending=False), "3Day_Delivery_Surge")

    with tabs[8]:
        st.caption("💰 Pro Scan: அதிக கோடி ரூபாய்க்கு (Delivery Value in Crores) வாங்கப்பட்ட டாப் ஸ்டாக்ஸ்")
        show_table(base_df.sort_values(by='DELIV_VAL_CR', ascending=False).head(50), "High_Delivery_Value")
