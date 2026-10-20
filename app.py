import streamlit as st
import pandas as pd
import requests
import io
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="NSE Pro Institutional Scanner", page_icon="🎯", layout="wide")

CACHE_DIR = "nse_data_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

st.title("🎯 NSE Pro Multi-Data Institutional Scanner")
st.markdown("🛡️ **Bhavcopy + Bulk Deals + Price Action Correlation Active**")

# ---------------- SIDEBAR SETTINGS ----------------
st.sidebar.header("⚙️ Scanner Settings")

min_deliv_pct_global = st.sidebar.slider(
    "🎯 குறைந்தபட்ச Delivery % (Global Filter)", 
    min_value=10, max_value=95, value=75, step=5,
    help="75% என வைத்தால், 75%-க்கு மேல் டெலிவரி நடந்த ஸ்டாக்ஸ் மட்டுமே எல்லா ஸ்கேன்களிலும் வரும்."
)

lookback_days = st.sidebar.slider("ஆவரேஜ் பார்க்க வேண்டிய நாட்கள்", 3, 15, 6)
min_turnover_cr = st.sidebar.number_input("குறைந்தபட்ச Turnover (₹ Crores)", value=10.0, step=5.0)
min_deliv_val_cr = st.sidebar.number_input("குறைந்தபட்ச Delivery Value (₹ Crores)", value=5.0, step=1.0)
spike_multiplier = st.sidebar.slider("Volume / Delivery Spike மடங்கு (X)", 1.2, 5.0, 1.5, step=0.1)
exclude_etfs = st.sidebar.checkbox("🚫 ETFs & Liquid Bees-ஐ தவிர்க்கவும்", value=True)

# ---------------- TOP F&O STOCKS LIST ----------------
FO_STOCKS = set([
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL", "SBIN", "LICI", "ITC", "HINDUNILVR",
    "LT", "BAJFINANCE", "HCLTECH", "MARUTI", "SUNPHARMA", "TATAMOTORS", "ONGC", "NTPC", "KOTAKBANK",
    "TITAN", "POWERGRID", "ADANIENT", "AXISBANK", "COALINDIA", "TATASTEEL", "ASIANPAINT", "BAJAJFINSV",
    "ULTRACEMCO", "SIEMENS", "BEL", "NESTLEIND", "GRASIM", "TECHM", "JSWSTEEL", "ADANIPORTS", "WIPRO",
    "SBILIFE", "TRENT", "DIVISLAB", "HINDALCO", "BPCL", "DRREDDY", "SHRIRAMFIN", "CIPLA", "APOLLOHOSP",
    "EICHERMOT", "BAJAJ-AUTO", "BRITANNIA", "TATACONSUM", "HAL", "HEROMOTOCO", "VEDL", "INDUSINDBK",
    "CHOLAFIN", "TVSMOTOR", "HAVELLS", "PIDILITIND", "POLYCAB", "DABUR", "AMBUJACEM", "JINDALSTEL",
    "BANKBARODA", "MUTHOOTFIN", "AUROPHARMA", "CANBK", "PNB", "TATACOMM", "DLF", "LUPIN", "CUMMINSIND",
    "ZYDUSLIFE", "BERGEPAINT", "PERSISTENT", "COFORGE", "VOLTAS", "DIXON", "ASTRAL", "ASHOKLEY", "OBEROIRLTY",
    "FEDERALBNK", "IDFCFIRSTB", "CONCOR", "SAIL", "ESCORTS", "PIIND", "MAXHEALTH", "PAGEIND", "ABCAPITAL"
])

def get_sector_tag(symbol):
    sym = str(symbol).upper()
    if any(k in sym for k in ["BANK", "FIN", "HDFC", "ICICI", "AXIS", "KOTAK", "BAJAJ", "CHOLA", "MUTHOOT"]):
        return "BFSI"
    if any(k in sym for k in ["TCS", "INFY", "TECH", "WIPRO", "HCL", "COFORGE", "PERSIST"]):
        return "IT"
    if any(k in sym for k in ["AUTO", "MOTOR", "MARUTI", "BAJAJ", "EICHER", "ASHOK", "TVS"]):
        return "AUTO"
    if any(k in sym for k in ["PHARMA", "LAB", "DRREDDY", "CIPLA", "SUN", "LUPIN", "ZYDUS", "DIVIS"]):
        return "PHARMA"
    if any(k in sym for k in ["STEEL", "METAL", "HINDALCO", "COAL", "VEDL", "JINDAL", "SAIL", "TATASTEEL"]):
        return "METALS"
    if any(k in sym for k in ["POWER", "NTPC", "GRID", "ENERGY", "RELIANCE", "ONGC", "BPCL", "IOC"]):
        return "ENERGY"
    return "OTHERS"

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
    return df.dropna(subset=['DELIV_QTY', 'DELIV_PER', 'TTL_TRD_QNTY', 'HIGH_PRICE', 'LOW_PRICE'])

def fetch_or_load_bhavcopy(date_obj):
    date_str = date_obj.strftime("%d%m%Y")
    local_file_path = os.path.join(CACHE_DIR, f"bhav_{date_str}.csv")
    
    if os.path.exists(local_file_path):
        try:
            return pd.read_csv(local_file_path)
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

def fetch_or_load_bulk_deals(date_obj):
    date_str = date_obj.strftime("%d%m%Y")
    local_file_path = os.path.join(CACHE_DIR, f"bulk_{date_str}.csv")
    
    if os.path.exists(local_file_path):
        try:
            return pd.read_csv(local_file_path)
        except Exception:
            pass

    url = f"https://nsearchives.nseindia.com/content/equities/bulkdeals/bulk_{date_str}.csv"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.nseindia.com/"
    }
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200 and len(r.text) > 50:
            df = pd.read_csv(io.StringIO(r.text))
            df.columns = df.columns.str.strip().str.upper()
            df.to_csv(local_file_path, index=False)
            return df
    except Exception:
        pass
    return pd.DataFrame()

def get_multi_day_data(target_days):
    collected_dfs = []
    check_date = datetime.now()
    attempts = 0
    progress_bar = st.progress(0, text="NSE Data Correlation & Download...")
    
    while len(collected_dfs) < target_days and attempts < 35:
        if check_date.weekday() < 5:
            df = fetch_or_load_bhavcopy(check_date)
            if df is not None and not df.empty:
                b_deals = fetch_or_load_bulk_deals(check_date)
                collected_dfs.append({
                    "date": check_date.strftime("%d-%b-%Y"),
                    "df": df,
                    "bulk": b_deals
                })
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
    if st.button("🚀 Load / Sync Multi-Source NSE Data", type="primary", use_container_width=True):
        st.session_state.market_data = get_multi_day_data(lookback_days + 1)
with col2:
    if st.button("🗑️ Clear Cache", use_container_width=True):
        for f in os.listdir(CACHE_DIR):
            os.remove(os.path.join(CACHE_DIR, f))
        st.session_state.market_data = None
        st.toast("கேட்ச் (Cache) கிளியர் செய்யப்பட்டது!")
        st.rerun()

# ---------------- DATA PROCESSING & CORRELATION ----------------
raw_data_list = st.session_state.market_data

# Convert legacy tuple data if stored previously in session
data_list = []
if raw_data_list:
    for item in raw_data_list:
        if isinstance(item, dict):
            data_list.append(item)
        elif isinstance(item, (list, tuple)):
            d_label = item[0]
            d_df = item[1]
            d_bulk = item[2] if len(item) > 2 else pd.DataFrame()
            data_list.append({"date": d_label, "df": d_df, "bulk": d_bulk})

if data_list:
    available_dates = [d["date"] for d in data_list]
    
    st.markdown("---")
    c_date, c_info = st.columns([1.5, 2.5])
    with c_date:
        selected_date_label = st.selectbox("📅 தேர்ந்தெடுக்கப்பட்ட தேதி:", options=available_dates, index=0)
    with c_info:
        st.info(f"தேதி: **{selected_date_label}** | ஃபில்டர்: **>= {min_deliv_pct_global}% Deliv** & **₹{min_turnover_cr} Cr Turnover**")

    selected_idx = available_dates.index(selected_date_label)
    target_day_df = data_list[selected_idx]["df"].copy()
    bulk_df = data_list[selected_idx]["bulk"]

    if exclude_etfs:
        etf_keywords = ['BEES', 'ETF', 'LIQUID', 'NIFTY', 'SENSEX', 'GOLD', 'SILVER', 'IETF', 'CASE', 'ADD', 'BETA', 'ALPHA', 'GILT', 'BOND']
        pattern = '|'.join(etf_keywords)
        target_day_df = target_day_df[~target_day_df['SYMBOL'].str.contains(pattern, case=False, na=False)].copy()
        target_day_df = target_day_df[~((target_day_df['CLOSE_PRICE'].between(999, 1001)) & (target_day_df['HIGH_PRICE'] - target_day_df['LOW_PRICE'] < 1))].copy()

    target_day_df['PRICE_CHG_PCT'] = (((target_day_df['CLOSE_PRICE'] - target_day_df['PREV_CLOSE']) / target_day_df['PREV_CLOSE']) * 100).round(2)
    target_day_df['TURNOVER_CR'] = (target_day_df['TURNOVER_LACS'] / 100).round(2)
    target_day_df['DELIV_VAL_CR'] = ((target_day_df['DELIV_QTY'] * target_day_df['CLOSE_PRICE']) / 10000000).round(2)
    target_day_df['CANDLE'] = target_day_df.apply(lambda r: "🟢 Green" if r['CLOSE_PRICE'] >= r['OPEN_PRICE'] else "🔴 Red", axis=1)

    high_low_diff = target_day_df['HIGH_PRICE'] - target_day_df['LOW_PRICE']
    target_day_df['CLOSE_NEAR_HIGH'] = (
        (target_day_df['CLOSE_PRICE'] - target_day_df['LOW_PRICE']) / 
        high_low_diff.replace(0, 0.001) * 100
    ).round(1)

    remaining_days = data_list[selected_idx + 1:]
    if len(remaining_days) > 0:
        hist_dfs = [d["df"] for d in remaining_days]
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

    if len(data_list) >= (selected_idx + 3):
        d0 = data_list[selected_idx]["df"].set_index('SYMBOL')['DELIV_QTY']
        d1 = data_list[selected_idx + 1]["df"].set_index('SYMBOL')['DELIV_QTY']
        d2 = data_list[selected_idx + 2]["df"].set_index('SYMBOL')['DELIV_QTY']
        streak_df = pd.DataFrame({'D0': d0, 'D1': d1, 'D2': d2}).dropna()
        streak_symbols = streak_df[(streak_df['D0'] > streak_df['D1']) & (streak_df['D1'] > streak_df['D2'])].index.tolist()
        merged['3D_STREAK'] = merged['SYMBOL'].isin(streak_symbols)
    else:
        merged['3D_STREAK'] = False

    merged['SEGMENT'] = merged['SYMBOL'].apply(lambda x: "⚡ F&O" if x in FO_STOCKS else "CASH")
    merged['SECTOR'] = merged['SYMBOL'].apply(get_sector_tag)

    if isinstance(bulk_df, pd.DataFrame) and not bulk_df.empty and 'SYMBOL' in bulk_df.columns:
        b_col_buy = 'BUY/SELL' if 'BUY/SELL' in bulk_df.columns else ('BUY_SELL' if 'BUY_SELL' in bulk_df.columns else None)
        b_col_client = 'CLIENT NAME' if 'CLIENT NAME' in bulk_df.columns else ('CLIENT_NAME' if 'CLIENT_NAME' in bulk_df.columns else None)
        
        if b_col_buy and b_col_client:
            bulk_deals_summary = bulk_df.groupby('SYMBOL').agg(
                BUY_COUNT=(b_col_buy, lambda x: (x.astype(str).str.strip().str.upper() == 'BUY').sum()),
                CLIENT=(b_col_client, lambda x: ', '.join(x.dropna().astype(str).unique()[:2]))
            ).reset_index()
            merged = pd.merge(merged, bulk_deals_summary, on='SYMBOL', how='left')
            merged['BULK_DEAL'] = merged['BUY_COUNT'].apply(lambda x: "🔥 YES" if x > 0 else ("⚠️ SELL" if pd.notnull(x) else "-"))
            merged['CLIENT'] = merged['CLIENT'].fillna("-")
        else:
            merged['BULK_DEAL'] = "-"
            merged['CLIENT'] = "-"
    else:
        merged['BULK_DEAL'] = "-"
        merged['CLIENT'] = "-"

    base_df = merged[
        (merged['TURNOVER_CR'] >= min_turnover_cr) & 
        (merged['DELIV_VAL_CR'] >= min_deliv_val_cr) &
        (merged['DELIV_PER'] >= min_deliv_pct_global)
    ].copy()
    
    base_df['CHART'] = "https://in.tradingview.com/chart/?symbol=NSE:" + base_df['SYMBOL']

    display_cols = ['SYMBOL', 'CHART', 'SEGMENT', 'SECTOR', 'CANDLE', 'CLOSE_NEAR_HIGH', 'DELIV_PER', 'DELIV_SPIKE_X', 'PRICE_CHG_PCT', 'CLOSE_PRICE', 'DELIV_VAL_CR', 'BULK_DEAL', 'CLIENT']

    def show_table(df_to_show, scan_name):
        st.markdown(f"**தேதி:** `{selected_date_label}` | **தேர்ந்தெடுக்கப்பட்ட ஸ்டாக்ஸ்:** `{len(df_to_show)}`")
        
        if df_to_show.empty:
            st.warning("இந்த கண்டிஷனில் ஸ்டாக்ஸ் எதுவும் வரவில்லை. ஃபில்டரை சற்று தளர்த்திப் பார்க்கவும்.")
            return

        st.dataframe(
            df_to_show[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "SYMBOL": st.column_config.TextColumn("Stock"),
                "CHART": st.column_config.LinkColumn("Chart", display_text="📊 View"),
                "SEGMENT": st.column_config.TextColumn("Seg"),
                "SECTOR": st.column_config.TextColumn("Sector"),
                "CANDLE": st.column_config.TextColumn("Candle"),
                "CLOSE_NEAR_HIGH": st.column_config.NumberColumn("Near High %", format="%.0f%%"),
                "DELIV_PER": st.column_config.NumberColumn("Deliv %", format="%.1f%%"),
                "DELIV_SPIKE_X": st.column_config.NumberColumn("Deliv Spike", format="%.2fX"),
                "PRICE_CHG_PCT": st.column_config.NumberColumn("Chg %", format="%.2f%%"),
                "CLOSE_PRICE": st.column_config.NumberColumn("Price (₹)", format="₹%.2f"),
                "DELIV_VAL_CR": st.column_config.NumberColumn("Deliv Val", format="₹%.1f Cr"),
                "BULK_DEAL": st.column_config.TextColumn("Bulk Deal"),
                "CLIENT": st.column_config.TextColumn("Major Buyer"),
            }
        )
        
        csv_data = df_to_show[display_cols].to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"📥 Download {scan_name} CSV",
            data=csv_data,
            file_name=f"{scan_name}_{selected_date_label}.csv",
            mime="text/csv",
            key=f"dl_{scan_name}_{selected_date_label}"
        )

    # ---------------- TABBED INTERFACE ----------------
    tabs = st.tabs([
        "👑 Super Sniper (High Accuracy)",
        "🔥 Bullish Accumulation",
        "🤝 Bulk Deal Correlation",
        "⚡ F&O Institutional Stocks",
        "🤫 Silent Accumulation",
        "📈 3-Day Delivery Streak",
        "💰 High Delivery Value"
    ])

    with tabs[0]:
        st.caption("👑 **Super Sniper Strategy:** Green Candle + Day High அருகில் முடிந்தவை (>=65%) + Heavy Delivery Value + 75%+ Delivery % (No Selling Trap!)")
        sniper_df = base_df[
            (base_df['CANDLE'] == "🟢 Green") & 
            (base_df['CLOSE_NEAR_HIGH'] >= 65.0) & 
            (base_df['PRICE_CHG_PCT'] >= 1.0) & 
            (base_df['DELIV_SPIKE_X'] >= spike_multiplier)
        ].sort_values(by=['CLOSE_NEAR_HIGH', 'DELIV_VAL_CR'], ascending=[False, False])
        show_table(sniper_df, "Super_Sniper")

    with tabs[1]:
        st.caption("🔥 **Bullish Accumulation:** Price > +1.5% Up + Delivery Spike + High Delivery %")
        bull_df = base_df[(base_df['PRICE_CHG_PCT'] >= 1.5) & (base_df['DELIV_SPIKE_X'] >= spike_multiplier)].sort_values(by='DELIV_SPIKE_X', ascending=False)
        show_table(bull_df, "Bullish_Accumulation")

    with tabs[2]:
        st.caption("🤝 **NSE Bulk / Block Deals:** அன்று அதிகாரப்பூர்வமாக பெரிய முதலீட்டாளர்களால் வாங்கப்பட்ட பங்குகள்")
        bulk_matches = base_df[base_df['BULK_DEAL'] == "🔥 YES"].sort_values(by='DELIV_VAL_CR', ascending=False)
        show_table(bulk_matches, "Bulk_Deals_Matches")

    with tabs[3]:
        st.caption("⚡ **F&O Segment Only:** பெரிய Liquidity உள்ள Top F&O Stocks மட்டுமே (Circuit Trap இருக்காது)")
        fo_df = base_df[base_df['SEGMENT'] == "⚡ F&O"].sort_values(by='DELIV_VAL_CR', ascending=False)
        show_table(fo_df, "FO_Institutional")

    with tabs[4]:
        st.caption("🤫 **Silent Accumulation:** விலை பெருசா மாறாமல் (-1% to +1.2%) சத்தமில்லாமல் Heavy Delivery நடந்தவை")
        silent_df = base_df[(base_df['PRICE_CHG_PCT'].between(-1.0, 1.2)) & (base_df['DELIV_SPIKE_X'] >= spike_multiplier)].sort_values(by='DELIV_SPIKE_X', ascending=False)
        show_table(silent_df, "Silent_Accumulation")

    with tabs[5]:
        st.caption("📈 **3-Day Surge:** தொடர்ந்து 3 நாட்களாக Delivery Volume ஏறிக்கொண்டே போகும் பங்குகள்")
        show_table(base_df[base_df['3D_STREAK'] == True].sort_values(by='DELIV_PER', ascending=False), "3Day_Surge")

    with tabs[6]:
        st.caption("💰 **High Delivery Value:** அதிக கோடி ரூபாய்க்கு Delivery எடுக்கப்பட்ட Top 50 Stocks")
        show_table(base_df.sort_values(by='DELIV_VAL_CR', ascending=False).head(50), "High_Deliv_Value")
