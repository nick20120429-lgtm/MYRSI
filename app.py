import os
import pandas as pd
import streamlit as st
import yfinance as yf

# 頂部開發者資訊與圖片展示區塊
col_img, col_header = st.columns([1, 4])

with col_img:
    # 預設載入與 app.py 同目錄下的 avatar.png
    image_path = "avatar.png"
    if os.path.exists(image_path):
        st.image(image_path, width=110)

with col_header:
    st.markdown("**開發者：尼克范2026.10.20.V1**")
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
            f"正在鎖定台股代號 {stock_digits} 抓取歷史數據並精準計算 RSI 與訊號..."
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
                    latest_high = float(high_prices.iloc[-1])
                    latest_low = float(low_prices.iloc[-1])
                    latest_diff = latest_high - latest_low  # 計算最高與最低價差
                    latest_rsi_5 = float(df["RSI_5"].iloc[-1])
                    latest_rsi_10 = float(df["RSI_10"].iloc[-1])
                    prev_rsi_5 = float(df["RSI_5"].iloc[-2])
                    prev_rsi_10 = float(df["RSI_10"].iloc[-2])

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
                    # 🎯 犀利媽法則分析與市場狀態報告
                    # ==========================
                    st.markdown("---")
                    st.subheader("🎯 犀利媽法則分析與市場狀態報告")

                    # 燈號與評分判定邏輯
                    if latest_rsi_5 >= 90 or latest_rsi_10 >= 90:
                        light = "🔴 賣出燈"
                        score = 20
                        conclusion = "市場極度過熱（鈍化風險高）"
                        action = "建議分批獲利了結"
                    elif latest_rsi_5 >= 70:
                        light = "🟠 警戒燈"
                        score = 40
                        conclusion = "市場偏熱（超買區）"
                        action = "停止追價，留意回檔"
                    elif latest_rsi_5 > latest_rsi_10 and latest_rsi_5 >= 50:
                        light = "🟢 買進燈"
                        score = 95
                        conclusion = "多頭攻擊型態（多方市場）"
                        action = "可考慮買進或加碼"
                    elif latest_rsi_5 < latest_rsi_10 and latest_rsi_10 >= 50:
                        light = "🟡 續抱燈"
                        score = 80
                        conclusion = "多頭整理型態"
                        action = "持股續抱"
                    elif latest_rsi_5 < 30 and latest_rsi_10 < 40:
                        light = "🔵 觀察燈"
                        score = 75
                        conclusion = "超賣區（市場過冷）"
                        action = "觀察止跌反彈機會"
                    else:
                        light = "⚪ 觀望燈"
                        score = 50
                        conclusion = "區間整理（方向未明）"
                        action = "暫時觀望"

                    # 1. 市場狀態分析判定
                    if latest_rsi_5 >= 70 or latest_rsi_10 >= 70:
                        market_state = "🔥 **市場過熱（超買區）**：RSI 進入高檔區，未來反轉向下機率高，需嚴防短線回檔。"
                    elif latest_rsi_5 <= 30 or latest_rsi_10 <= 30:
                        market_state = "❄️ **市場過冷（超賣區）**：RSI 進入低檔區，未來止跌回升機率高，可尋找低接契機。"
                    else:
                        market_state = "⚖️ **區間整理 / 多空拉鋸**：RSI 處於 30~70 之間，多空無明顯極端偏向。"

                    # 2. 交叉訊號判定
                    cross_signal = "無明顯交叉"
                    if prev_rsi_5 <= prev_rsi_10 and latest_rsi_5 > latest_rsi_10:
                        cross_signal = "🟢 **黃金交叉（買進訊號）**：5日 RSI 向上突破 10日 RSI，短期上漲力道強於長期。"
                    elif (
                        prev_rsi_5 >= prev_rsi_10 and latest_rsi_5 < latest_rsi_10
                    ):
                        cross_signal = "🔴 **死亡交叉（賣出訊號）**：5日 RSI 向下跌破 10日 RSI，短期下跌力道強於長期。"
                    else:
                        if latest_rsi_5 > latest_rsi_10:
                            cross_signal = (
                                "📈 **多頭排列**：5T 持續位於 10T 之上。"
                            )
                        else:
                            cross_signal = (
                                "📉 **空頭排列**：5T 持續位於 10T 之下。"
                            )

                    # 3. 背離與鈍化風險評估
                    recent_close = close_prices.tail(10)
                    recent_rsi = df["RSI_5"].tail(10)
                    divergence_note = "目前未偵測到明顯強烈背離型態。"

                    if (
                        recent_close.iloc[-1] >= recent_close.max() * 0.99
                        and latest_rsi_5 < recent_rsi.quantile(0.5)
                    ):
                        divergence_note = "⚠️ **注意下跌背離（頂背離轉弱訊號）**：股價處於高檔，但短天期 RSI 上漲力道減弱，慎防見高拉回。"
                    elif (
                        recent_close.iloc[-1] <= recent_close.min() * 1.01
                        and latest_rsi_5 > recent_rsi.quantile(0.5)
                    ):
                        divergence_note = "💡 **注意上漲背離（底背離轉強訊號）**：股價創新低但 RSI 未創新低且向上，下跌力道可能正逐漸減弱。"

                    # 輸出分析報告格式
                    st.markdown("#### 📋 犀利媽專屬結構化分析報告：")
                    st.markdown(f"1. **當前市場狀態**：{market_state}")
                    st.markdown(
                        f"2. **技術交叉與背離訊號**：\n   - {cross_signal}\n   - {divergence_note}"
                    )
                    st.markdown(
                        f"3. **綜合操作建議與風險提示**：\n   - **燈號判定**：{light}（評分：{score}/100）\n   - **操作方針**：{action}\n   - **⚠️ 核心風險提醒**：需注意 RSI 指標在極端行情可能發生「鈍化」（在 80~90+ 或 10~20 之間持續徘徊導致參考價值降低），技術指標僅能作為警示與機率評估，不可作為絕對預測，請務必配合個人資金控管與停損機制。"
                    )

                    # ===== 一眼看懂 =====
                    st.markdown("---")
                    col_a, col_b, col_c_status = st.columns(3)
                    with col_a:
                        st.metric("燈號", light)
                    with col_b:
                        st.metric("評分", f"{score}/100")
                    with col_c_status:
                        st.metric("建議", action)

                    st.progress(score)

                    # 顯示近期走勢圖表
                    st.markdown("---")
                    st.subheader("📊 近期 RSI 走勢圖")
                    rsi_chart_df = pd.DataFrame(
                        {"RSI_5": df["RSI_5"], "RSI_10": df["RSI_10"]}
                    ).tail(30)
                    st.line_chart(rsi_chart_df)

            except Exception as e:
                st.error(f"讀取台股資料時發生錯誤：{e}")

# 在頁面下方加入 RSI 核心概念備註說明區塊
st.markdown("---")
with st.expander("📖 點擊展開：RSI 的核心概念與數值範圍說明"):
    st.markdown("""
    * **數值範圍**：介於 0 到 100 之間。
    * **多空分水嶺（50）**：
        * **RSI > 50**：代表買方力道較強（多方市場）。
        * **RSI < 50**：代表賣方力道較強（空方市場）。
    * **超買與超賣區間**：
        * **RSI ≥ 70 或 80（甚至 90+）**：進入超買區（市場過熱，短線有回檔或下跌風險，高檔連續多日可準備賣出）。
        * **RSI ≤ 30 或 20**：進入超賣區（市場過冷，短線有反彈或上漲機會）。
    """)
