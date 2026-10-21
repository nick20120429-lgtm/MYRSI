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
    st.markdown("**開發者：尼克范2026.10.20.V2（真·犀利媽實戰版）**")
    st.title("📈 犀利媽極端 RSI 實戰分析工具")

st.write("本工具**僅支援台灣股市**。請輸入台股代號（例如：2330、6239）：")
st.write(
    "人生自強，先搞好自己： 犀利媽曾言：「平時常態區間不看雜訊，專抓極端過熱與極端超跌！」"
)

# 簡易台股中文名稱對照字典（可自行擴充）
stock_name_dict = {
    "2330": "台積電",
    "6239": "力成",
    "2317": "鴻海",
    "3605": "宏致",
    "5347": "世界",
    "3231": "緯創",
}

# 使用欄位排版讓輸入框跟按鈕並排
col_input, col_btn = st.columns([3, 1])

with col_input:
    stock_input = st.text_input(
        "請輸入台股代號（例如 3231）：", value="3231", label_visibility="collapsed"
    )

with col_btn:
    st.write("")
    submit_btn = st.button("確定查詢", type="primary")

if submit_btn and stock_input:
    raw_input = stock_input.strip()
    stock_digits = "".join(filter(str.isdigit, raw_input))

    if not stock_digits:
        st.error("請輸入正確的台股數字代號（例如：2330、3231）！")
    else:
        symbols_to_try = [f"{stock_digits}.TW", f"{stock_digits}.TWO"]
        df = pd.DataFrame()
        used_symbol = ""

        with st.spinner(
            f"正在鎖定台股代號 {stock_digits} 抓取歷史數據並以犀利媽極端邏輯分析..."
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
                        f"找不到台股代號【{stock_digits}】的資料，請確認代號是否正確。"
                    )
                else:
                    # 兼容不同 pandas 版本的欄位結構
                    if isinstance(df.columns, pd.MultiIndex):
                        close_prices = df[("Close", used_symbol)]
                        high_prices = df[("High", used_symbol)]
                        low_prices = df[("Low", used_symbol)]
                        volume = df[("Volume", used_symbol)]
                    else:
                        close_prices = df["Close"]
                        high_prices = df["High"]
                        low_prices = df["Low"]
                        volume = df["Volume"]

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
                    latest_diff = latest_high - latest_low
                    latest_rsi_5 = float(df["RSI_5"].iloc[-1])
                    latest_rsi_10 = float(df["RSI_10"].iloc[-1])
                    prev_rsi_5 = float(df["RSI_5"].iloc[-2])
                    prev_rsi_10 = float(df["RSI_10"].iloc[-2])
                    
                    # 計算成交量與 5 日均量比對
                    latest_vol = float(volume.iloc[-1])
                    avg_vol_5 = float(volume.tail(5).mean())
                    is_volume_up = latest_vol > avg_vol_5

                    comp_name = stock_name_dict.get(stock_digits, "台股公司")

                    st.success(
                        f"{comp_name}【{used_symbol}】最新收盤價：{latest_close:.2f} 元"
                    )

                    # 4 個欄位展示：最高、最低、價差、最新收盤
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
                    # 🎯 犀利媽真實極端法則分析引擎
                    # ==========================
                    st.markdown("---")
                    st.subheader("🎯 犀利媽實戰極端法則分析報告")

                    # 修正後的判定邏輯：嚴格對齊「極端值優先」與「過濾常態雜訊」
                    if latest_rsi_5 >= 90 or latest_rsi_10 >= 90:
                        light = "🔴 賣出燈 (過熱警戒)"
                        score = 15
                        conclusion = "市場極度過熱（高檔鈍化或隨時回檔）"
                        action = "果斷獲利了結，絕對不追高"
                    elif latest_rsi_5 <= 10 or latest_rsi_10 <= 15:
                        if is_volume_up:
                            light = "🟢 買進燈 (極端超跌爆量)"
                            score = 90
                            conclusion = "非理性恐慌急殺 + 爆量止跌"
                            action = "分批進場低接搶反彈"
                        else:
                            light = "🔵 觀察燈 (極端超跌等待量)"
                            score = 65
                            conclusion = "進入極端超跌區，但量能尚未放大"
                            action = "持續盯盤，等待帶量紅K再出手"
                    else:
                        # 30~70 常態區間一律降評，避免過去軟體在 50~60 亂給 95 分的失真
                        light = "⚪ 觀望燈 (常態震盪區)"
                        score = 50
                        conclusion = "常態區間多空拉鋸（無極端訊號）"
                        action = "按兵不動，專心等待極端機會"

                    # 1. 市場狀態分析判定
                    if latest_rsi_5 >= 80 or latest_rsi_10 >= 80:
                        market_state = "🔥 **極端過熱區**：RSI 飆高，隨時有急跌反轉風險。"
                    elif latest_rsi_5 <= 20 or latest_rsi_10 <= 20:
                        market_state = "❄️ **極端超跌區**：RSI 進入個位數或低檔，留意恐慌盤後的反彈契機。"
                    else:
                        market_state = "⚖️ **常態震盪區**：RSI 停留在 30~70 之間（犀利媽視為無效雜訊區）。"

                    # 2. 交叉訊號判定（加上過濾說明）
                    cross_signal = "無明顯極端交叉"
                    if latest_rsi_5 > latest_rsi_10:
                        cross_signal = "📈 **多頭排列**：5T 位於 10T 之上（常態區間不盲目追價）。"
                    else:
                        cross_signal = "📉 **空頭排列**：5T 位於 10T 之下（留意低檔鈍化風險）。"

                    # 3. 成交量與動能評估
                    vol_note = f"當日成交量 {'大於' if is_volume_up else '小於'} 5日均量（{'主力有動作' if is_volume_up else '量能偏冷'}）。"

                    # 輸出結構化分析報告
                    st.markdown("#### 📋 犀利媽 20 年極端心法報告：")
                    st.markdown(f"1. **市場位階狀態**：{market_state}")
                    st.markdown(f"2. **均線與量能結構**：\n   - {cross_signal}\n   - 📊 **量能狀態**：{vol_note}")
                    st.markdown(
                        f"3. **綜合實戰決策**：\n   - **燈號判定**：{light}（評分：{score}/100）\n   - **操作方針**：{action}\n   - **💡 核心原則**：平時常態區間不亂動，專心等待極端過熱（>90）或極端超跌（<10）再精準出手！"
                    )

                    # ===== 一眼看懂面板 =====
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
                    ).tail(60)
                    st.line_chart(rsi_chart_df)

            except Exception as e:
                st.error(f"讀取台股資料時發生錯誤：{e}")

# 在頁面下方加入 RSI 核心概念備註說明區塊
st.markdown("---")
with st.expander("📖 點擊展開：犀利媽心法與 RSI 極端值操作守則"):
    st.markdown("""
    * **常態區間（RSI 30~70）**：不看黃金交叉、不亂買。此區間雜訊極多，盲目操作容易在盤整中被洗盤。
    * **極端過熱（RSI ≥ 90）**：強勢飆股的過熱區。連續多日黏在高檔且漲不動時，準備獲利出場或順勢放空。
    * **極端超跌（RSI ≤ 10）**：非理性恐慌的黃金買點。此時需配合成交量放大（帶量紅K），才是高勝率的搶反彈時機。
    """)
