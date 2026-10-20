import pandas as pd
import streamlit as st
import yfinance as yf

# 網頁標題
st.title("📈 台股專用 RSI 智慧查詢與診斷工具")
st.write(
    "本工具**僅支援台灣股市**。請輸入台股代號（例如：2330、6239），"
    "點擊確定後將自動計算 5T 與 10T RSI，並顯示最新收盤價、本日最高、最低、價差與詳細 RSI 狀態解析。"
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
                    latest_rsi_10 = float(df["RSI_10"].iloc[-1])

                    comp_name = stock_name_dict.get(stock_digits, "台股公司")

                    # 顯示自訂格式與最新收盤
                    st.success(
                        f"{comp_name}【{used_symbol}】最新收盤價：{latest_close:.2f} 元"
                    )

                    # 用 4 個欄位分別展示：本日最高、本日最低、價差、最新收盤
                    col_h, col_l, col_diff, col_c = st.columns(4)
                    with col_h:
                        st.metric(label="🔺 本日最高", value=f"{latest_high:.2f}")
                    with col_l:
                        st.metric(label="🔻 本日最低", value=f"{latest_low:.2f}")
                    with col_diff:
                        st.metric(
                            label="📊 最高最低價差",
                            value=f"{latest_diff:.2f}",
                            delta=f"{(latest_diff / latest_low * 100):.2f}%",
                        )
                    with col_c:
                        st.metric(label="💵 最新收盤", value=f"{latest_close:.2f}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            label="5日 RSI (5T)", value=f"{latest_rsi_5:.2f}"
                        )
                    with col2:
                        st.metric(
                            label="10日 RSI (10T)", value=f"{latest_rsi_10:.2f}"
                        )

                    # ==========================
                    # 🎯 犀利媽法則分析與 RSI 狀態解析
                    # ==========================
                    st.markdown("---")
                    st.subheader("🎯 犀利媽法則分析與 RSI 狀態解析")

                    # 燈號與評分判定邏輯
                    if latest_rsi_5 >= 90 or latest_rsi_10 >= 90:
                        light = "🔴 賣出燈"
                        score = 20
                        conclusion = "市場極度過熱"
                        action = "建議分批獲利了結"
                    elif latest_rsi_5 >= 70:
                        light = "🟠 警戒燈"
                        score = 40
                        conclusion = "市場偏熱"
                        action = "停止追價"
                    elif latest_rsi_5 > latest_rsi_10 and latest_rsi_5 >= 50:
                        light = "🟢 買進燈"
                        score = 95
                        conclusion = "多頭攻擊型態"
                        action = "可考慮買進或加碼"
                    elif latest_rsi_5 < latest_rsi_10 and latest_rsi_10 >= 50:
                        light = "🟡 續抱燈"
                        score = 80
                        conclusion = "多頭整理型態"
                        action = "持股續抱"
                    elif latest_rsi_5 < 30 and latest_rsi_10 < 40:
                        light = "🔵 觀察燈"
                        score = 75
                        conclusion = "超賣區"
                        action = "觀察反彈機會"
                    else:
                        light = "⚪ 觀望燈"
                        score = 50
                        conclusion = "方向未明"
                        action = "暫時觀望"

                    # 動態帶出 5T 與 10T 的多空分水嶺與超買超賣解析
                    def get_rsi_status_text(rsi_val, name):
                        if rsi_val >= 90:
                            return f"🔥 **{name} ({rsi_val:.2f})**：進入 90+ 極度超買區（市場極度過熱，短線隨時有回檔風險，高檔可準備賣出）"
                        elif rsi_val >= 70:
                            return f"🟠 **{name} ({rsi_val:.2f})**：進入 ≥70 超買區（市場偏熱，短線追價需留意風險）"
                        elif rsi_val >= 50:
                            return f"🟢 **{name} ({rsi_val:.2f})**：大於 50 多空分水嶺（代表買方力道較強，處於**多方市場**）"
                        elif rsi_val >= 30:
                            return f"🟡 **{name} ({rsi_val:.2f})**：小於 50 分水嶺但未達超賣區（代表賣方力道較強，處於**空方市場**或盤整）"
                        else:
                            return f"🔵 **{name} ({rsi_val:.2f})**：小於等於 30 進入超賣區（市場過冷，短線有反彈或尋求買點機會）"

                    st.markdown("#### 📌 個股 RSI 深度解析：")
                    st.markdown(
                        f"- {get_rsi_status_text(latest_rsi_5, '5
