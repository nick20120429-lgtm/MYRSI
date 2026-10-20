import pandas as pd
import streamlit as st
import yfinance as yf

# 網頁標題
st.title("📈 台股專用 RSI 智慧查詢與診斷工具")
st.write(
    "本工具**僅支援台灣股市**。請輸入台股代號（例如：2330、3605 或 5347），"
    "點擊確定後將自動計算 5T 與 10T RSI 並對照犀利媽買賣策略提供燈號建議。"
)

# 使用欄位排版讓輸入框跟按鈕並排
col_input, col_btn = st.columns([3, 1])

with col_input:
  stock_input = st.text_input(
      "請輸入台股代號（例如 2330）：", value="2330", label_visibility="collapsed"
  )

with col_btn:
  st.write("")
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
        f"正在鎖定台股代號 {stock_digits} 抓取歷史數據並精準計算 RSI..."
    ):
      try:
        for sym in symbols_to_try:
          temp_df = yf.download(sym, period="6mo", interval="1d", progress=False)
          if not temp_df.empty:
            df = temp_df
            used_symbol = sym
            break

        if df.empty:
          st.error(
              f"找不到台股代號【{stock_digits}】的資料，請確認代號是否正確（僅支援台股上市櫃股票）。"
          )
        else:
          if isinstance(df.columns, pd.MultiIndex):
            close_prices = df[("Close", used_symbol)]
          else:
            close_prices = df["Close"]


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

          col1, col2 = st.columns(2)
          with col1:
            st.metric(label="5日 RSI (5T)", value=f"{latest_rsi_5:.2f}")
          with col2:
            st.metric(label="10日 RSI (10T)", value=f"{latest_rsi_10:.2f}")

          # ==========================
          # 🎯 犀利媽法則分析
          # ==========================
          st.markdown("---")
          st.subheader("🎯 犀利媽法則分析")

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

          # ===== 一眼看懂 =====
          col_a, col_b, col_c = st.columns(3)
          with col_a:
            st.metric("燈號", light)
          with col_b:
            st.metric("評分", f"{score}/100")
          with col_c:
            st.metric("建議", action)

          st.progress(score)

          # ===== 結論 =====
          if score >= 90:
            st.success(f"""
🎯 犀利媽結論
{light}
{conclusion}
買進評分：{score}/100
✅ 可考慮買進
✅ 可考慮加碼
✅ 持股續抱
""")
          elif score >= 75:
            st.info(f"""
🎯 犀利媽結論
{light}
{conclusion}
買進評分：{score}/100
✅ 持股續抱
✅ 等待下一次訊號
""")
          elif score >= 50:
            st.warning(f"""
🎯 犀利媽結論
{light}
{conclusion}
買進評分：{score}/100
⚠️ 建議觀望
⚠️ 等待方向確認
""")
          else:
            st.error(f"""
🎯 犀利媽結論
{light}
{conclusion}
買進評分：{score}/100
❌ 不建議追價
❌ 建議分批賣出
❌ 保留現金
""")

          st.markdown("### 📌 操作建議")
          st.write(action)

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
        * **RSI > 50**：代表買方力道
