import pandas as pd
import streamlit as st
import yfinance as yf

# 網頁標題與說明
st.title("📈 RSI工具")
st.write("本工具**僅支援台灣股市**。請輸入台股代號（例如：2330、6239）：")
st.write(
    "人生自強，先搞好自己： 犀利媽曾言：「沒有把自己的人生弄好，再會賺錢也沒有用。」 "
)

# 簡易台股中文名稱對照字典（可自行擴充）
stock_name_dict = {
    "2330": "台積電",
    "6239": "力成",
    "2317": "鴻海",
    "3605": "宏致",
    "5347": "世界",
}

# 使用欄位排版讓輸入框跟按鈕並排
col_input, col_btn = st.columns([3, 1])

with col_input:
    stock_input = st.text_input(
        "請輸入台股代號（例如 6239）：", value="6239", label_visibility="collapsed"
    )

with col_btn:
    st.write("")
    submit_btn = st.button("確定查詢", type="primary")

if submit_btn and stock_input:
    raw_input = stock_input.strip()
    stock_digits = "".join(filter(str.isdigit, raw_input))

    if not stock_digits:
        st.error("請輸入正確的台股數字代號（例如：2330、6239）！")
    else:
        symbols_to_try = [f"{stock_digits}.TW", f"{stock_digits}.TWO"]
        df = pd.DataFrame()
        used_symbol = ""

        with st.spinner(
            f"正在鎖定台股代號 {stock_digits} 抓取歷史數據並精準計算 RSI..."
        ):
            try:
                for sym in symbols_to_try:
                    temp_df = yf.download(
                        sym, period="6mo", interval="1d", progress=False
                    )
                    if not temp_df.empty:
                        df = temp_df
                        used_symbol = sym
                        break

                if df.empty:
                    st.error(
                        f"找不到台股代號【{stock_digits}】的資料，請確認代號是否正確（僅支援台股上市櫃股票）。"
                    )
                else:
                    # 兼容不同 pandas 版本的欄位結構
                    if isinstance(df.columns, pd.MultiIndex):
                        close_prices = df[("Close", used_symbol)]
                        high_prices = df[("High", used_symbol)]
                        low_prices = df[("Low", used_symbol)]
                    else:
                        close_prices = df["Close"]
                        high_prices = df["High"]
                        low_prices = df["Low"]

                    def calculate_rsi(data, window=14):
                        delta = data.diff()
                        gain = delta.clip(lower=0)
                        loss = -delta.clip(upper=0)
                        avg_gain = (
                            gain.ewm(
                                alpha=1 / window,
                                min_periods=window,
                                adjust=False,
                            )
                            .mean()
                        )
                        avg_loss = (
                            loss.ewm(
                                alpha=1 / window,
                                min_periods=window,
                                adjust=False,
                            )
                            .mean()
                        )
                        rs = avg_gain / avg_loss
                        rsi = 100 - (100 / (1 + rs))
                        return rsi

                    df["RSI_5"] = calculate_rsi(close_prices, window=5)
                    df["RSI_10"] = calculate_rsi(close_prices, window=10)

                    latest_close = float(close_prices.iloc[-1])
                    latest_high = float(high_prices.iloc[-1])
                    latest_low = float(low_prices.iloc[-1])
                    latest_diff = latest_high - latest_low  # 計算最高與最低價差
                    latest_rsi_5 = float(df["RSI_5"].iloc[-1])
                    latest_rsi_10 = float(df
