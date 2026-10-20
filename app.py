import pandas as pd
import streamlit as st
import yfinance as yf

# 網頁標題
st.title("📈 個股 RSI 自動查詢與診斷工具")
st.write("輸入台股代號（例如：3605 或 2377），系統將自動計算 5T 與 10T RSI 並提供操作建議。")

# 使用者輸入股票代號
stock_input = st.text_input("請輸入台股代號（例如 3605）：", value="3605")

if stock_input:
  # 自動補上 Yahoo Finance 的台股後綴 (.TW)
  # 如果您的股票是櫃買中心(興櫃/上櫃)通常也是 .TW 或 .TWO，多數 .TW 即可對應
  ticker = stock_input.strip()
  if not ticker.endswith(".TW") and not ticker.endswith(".TWO"):
    stock_symbol = ticker + ".TW"
  else:
    stock_symbol = ticker

  with st.spinner(f"正在抓取 {stock_symbol} 的最新數據並計算 RSI..."):
    try:
      # 1. 下載最近 2 個月的歷史資料
      df = yf.download(stock_symbol, period="2mo", interval="1d")

      if df.empty:
        st.error(
            "找不到該代號的資料，請確認代號是否正確（例如台股請輸入 3605）。"
        )
      else:
        # 處理 yfinance 多重索引欄位問題（確保抓到 Close）
        if isinstance(df.columns, pd.MultiIndex):
          close_prices = df[("Close", stock_symbol)]
        else:
          close_prices = df["Close"]

        # 2. 計算 RSI 的函數
        def calculate_rsi(data, window=14):
          delta = data.diff()
          gain = delta.where(delta > 0, 0).rolling(window=window).mean()
          loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
          rs = gain / loss
          rsi = 100 - (100 / (1 + rs))
          return rsi

        # 計算 5T 與 10T
        df["RSI_5"] = calculate_rsi(close_prices, window=5)
        df["RSI_10"] = calculate_rsi(close_prices, window=10)

        # 取得最新一筆的數據
        latest_close = float(close_prices.iloc[-1])
        latest_rsi_5 = float(df["RSI_5"].iloc[-1])
        latest_rsi_10 = float(df["RSI_10"].iloc[-1])

        # 顯示最新數據卡片
        st.success(f"成功取得【{stock_symbol}】最新收盤價：{latest_close:.2f} 元")

        col1, col2 = st.columns(2)
        with col1:
          st.metric(label="5日 RSI (5T)", value=f"{latest_rsi_5:.2f}")
        with col2:
          st.metric(label="10日 RSI (10T)", value=f"{latest_rsi_10:.2f}")

        # 3. 系統自動判定與建議邏輯
        st.markdown("---")
        st.subheader("🤖 系統智慧診斷與操作建議")

        # 簡單的判定規則
        if latest_rsi_5 > 70:
          diagnosis = "🔥 **短線過熱（超買區）**"
          advice = "短線漲幅過快，買氣過熱。若有持股可考慮獲利了結一部分，不宜盲目追高。"
        elif latest_rsi_5 < 30 and latest_rsi_10 < 40:
          diagnosis = "💧 **短線超賣 / 弱勢**"
          advice = "短線跌幅較重進入超賣區。若中期指標（10T）也跟著崩跌，需注意停損；若 10T 仍有守，可觀察是否有打底機會。"
        elif latest_rsi_5 < latest_rsi_10 and latest_rsi_10 >= 50:
          diagnosis = "🔄 **高檔技術性回檔 / 整理中**"
          advice = "如同宏致目前的狀態：短線買氣稍微降溫（5T < 50），但中期多頭防線（10T >= 50）仍穩固。**建議：持股續抱，耐心等待短線止穩。**"
        elif latest_rsi_5 > latest_rsi_10 and latest_rsi_5 >= 50:
          diagnosis = "🚀 **短線轉強 / 多頭排列**"
          advice = "短天期動能大於中天期，且雙雙站在 50 中軸之上，短線買氣回溫，多方佔優勢。"
        else:
          diagnosis = "⚖️ **多空拉鋸 / 盤整格局**"
          advice = "目前數值顯示多空力道均衡，建議觀望，等待方向明確再行操作。"

        st.markdown(f"**目前狀態：** {diagnosis}")
        st.markdown(f"**操作參考：** {advice}")

        # 顯示近期走勢圖表
        st.markdown("---")
        st.subheader("📊 近期 RSI 走勢圖")
        st.line_chart(df[["RSI_5", "RSI_10"]].tail(30))

    except Exception as e:
      st.error(f"讀取資料時發生錯誤：{e}")