from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
import yfinance as yf

# 設定網頁標題與 RWD 寬螢幕自適應
st.set_page_config(
    page_title="台股 RSI 智慧診斷工具", page_icon="📈", layout="centered"
)

# 注入自訂樣式：輸入框與查詢按鈕高度同為 40px 等高對齊
st.markdown(
    """
    <style>
    .stTextInput input {
        font-size: 16px !important;
        height: 40px !important;
        border-radius: 6px !important;
        border: 1px solid #CBD5E1 !important;
    }
    .stButton > button {
        height: 40px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        width: 100%;
        border-radius: 6px !important;
        background-color: #2563EB !important;
        color: white !important;
        border: none !important;
    }
    .stButton > button:hover {
        background-color: #1D4ED8 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 取得台灣當前時間
tz_taiwan = pytz.timezone("Asia/Taipei")
now_taiwan = datetime.now(tz_taiwan)
current_date_str = now_taiwan.strftime("%Y/%m/%d")
current_time_str = now_taiwan.strftime("%H:%M")

# 網頁頂部標題與開發者署名
st.markdown(
    "<div style='text-align: center; margin-bottom: 15px;'>"
    "<h2 style='font-weight: 700; color: #202124; margin-bottom: 5px;'>📈"
    " 台股 RSI 智慧診斷工具</h2>"
    f"<p style='color: #70757a; font-size: 12px;'>📅 <b>日期：</b>{current_date_str}"
    f" 🕒 <b>時間：</b>{current_time_str} | <span style='color: #4285F4;"
    " font-weight: 600;'>👨‍💻 尼克范 V.1.0.2.0</span></p>"
    "</div>",
    unsafe_allow_html=True,
)

# 固定實戰口訣看板
st.info(
    "💡 **實戰操作口訣：**\n\n"
    "> * 🚀 **站上 5T（強勢）**：極強勢攻擊 ➔ 短線買進 / 多單續抱\n"
    "> * ⚠️ **跌破 5T（轉弱）**：攻勢受阻、轉弱警訊 ➔ 減碼停利 / 試探性建倉\n"
    "> * 🛑 **跌破 10T（破防）**：趨勢轉空、防線失守 ➔ 全數停損離場 / 加碼放空"
)

st.write(
    "本工具**僅支援台灣股市**。請輸入台股代號（例如：2330、3605 或 2377），"
    "點擊確定後將自動計算 5T 與 10T RSI、極高低價並對照口訣提供操作建議。"
)

# 使用欄位排版讓輸入框跟按鈕並排
col_input, col_btn = st.columns([3, 1])

with col_input:
  stock_input = st.text_input(
      "請輸入台股代號（例如 2330）：", value="2330", label_visibility="collapsed"
  )

with col_btn:
  submit_btn = st.button("確定查詢", type="primary")

if submit_btn and stock_input:
  raw_input = stock_input.strip()
  stock_digits = "".join(filter(str.isdigit, raw_input))

  if not stock_digits:
    st.error("請輸入正確的台股數字代號（例如：2330、3605）！")
  else:
    symbols_to_try = [f"{stock_digits}.TW", f"{stock_digits}.TWO"]
    df = pd.DataFrame()
    used_symbol = ""

    with st.spinner(
        f"正在鎖定台股代號 {stock_digits} 抓取歷史數據並精準計算..."
    ):
      try:
        for sym in symbols_to_try:
          temp_df = yf.download(sym, period="1y", interval="1d", progress=False)
          if not temp_df.empty and len(temp_df) > 10:
            df = temp_df
            used_symbol = sym
            break

        if df.empty:
          st.error(
              f"找不到台股代號【{stock_digits}】的資料，請確認代號是否正確（僅支援台股上市櫃股票）。"
          )
        else:
          # 確保欄位為單一階層
          if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

          close_prices = df["Close"]
          high_prices = df["High"]
          low_prices = df["Low"]

          # 計算本日、本月、本年最高/最低價
          latest_date = df.index[-1]
          current_year = latest_date.year
          current_month = latest_date.month

          day_high = float(high_prices.iloc[-1])
          day_low = float(low_prices.iloc[-1])

          month_mask = (df.index.year == current_year) & (
              df.index.month == current_month
          )
          month_df = df[month_mask]
          month_high = (
              float(month_df["High"].max()) if not month_df.empty else day_high
          )
          month_low = (
              float(month_df["Low"].min()) if not month_df.empty else day_low
          )

          year_mask = df.index.year == current_year
          year_df = df[year_mask]
          year_high = (
              float(year_df["High"].max()) if not year_df.empty else day_high
          )
          year_low = float(year_df["Low"].min()) if not year_df.empty else day_low


          def calculate_rsi(data, window=14):
            delta = data.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.ewm(
                alpha=1 / window, min_periods=window, adjust=False
            ).mean()
            avg_loss = loss.ewm(
                alpha=1 / window, min_periods=window, adjust=False
            ).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi


          df["RSI_5"] = calculate_rsi(close_prices, window=5)
          df["RSI_10"] = calculate_rsi(close_prices, window=10)

          latest_close = float(close_prices.iloc[-1])
          latest_rsi_5 = float(df["RSI_5"].iloc[-1])
          latest_rsi_10 = float(df["RSI_10"].iloc[-1])

          st.success(
              f"成功取得台股【{used_symbol}】最新收盤價：{latest_close:.2f} 元"
          )

          # 顯示 RSI 指標
          col1, col2 = st.columns(2)
          with col1:
            st.metric(label="5日 RSI (5T)", value=f"{latest_rsi_5:.2f}")
          with col2:
            st.metric(label="10日 RSI (10
