import os
import urllib.parse
import pandas as pd
import streamlit as st
import yfinance as yf
import feedparser

st.set_page_config(page_title="犀利媽 20年極端心法分析工具", page_icon="📈", layout="wide")

# 頂部開發者資訊與圖片展示區塊
col_img, col_header = st.columns([1, 4])

with col_img:
    image_path = "avatar.png"
    if os.path.exists(image_path):
        st.image(image_path, width=110)

with col_header:
    st.markdown("**開發者：尼克范 2026.10.21.V9（語法修正最終版）**")
    st.title("📈 犀利媽 20年極端心法與即時新聞動態分析工具")

st.write("本工具**支援全台灣上市櫃股票**。請輸入台股代號（例如：2330、6239、3231、2317）：")
st.write(
    "💡 **犀利媽 20年核心哲學**：「常態區間不看雜訊、極端行情絕不手軟、對照消息面靈活操作、破支撐手刀停損！」"
)

stock_name_dict = {
    "2330": "台積電",
    "6239": "力成",
    "2317": "鴻海",
    "3605": "宏致",
    "5347": "世界",
    "3231": "緯創",
    "2454": "聯發科",
    "2308": "台達電",
    "2382": "廣達",
    "3037": "欣興",
}

def fetch_stock_news(stock_code, stock_name, count=10):
    search_query = f"{stock_code} {stock_name}" if stock_name != "台股公司" else stock_code
    encoded_query = urllib.parse.quote(search_query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}+when:30d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    feed = feedparser.parse(rss_url)
    news_items = []
    
    if feed.entries:
        for entry in feed.entries[:count]:
            pub_date = getattr(entry, "published", "")[:16] if hasattr(entry, "published") else ""
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "date": pub_date,
                "source": entry.source.title if hasattr(entry, "source") else "財經新聞"
            })
    return news_items

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
            f"正在鎖定台股代號 {stock_digits} 抓取歷史數據，依據犀利媽心法計算 RSI 並動態聯網獲取新聞..."
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
                        f"找不到台股代號【{stock_digits}】的數據，請確認代號是否正確（僅支援台股上市櫃股票）。"
                    )
                else:
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
                    
                    latest_vol = float(volume.iloc[-1])
                    avg_vol_5 = float(volume.tail(5).mean())
                    is_volume_up = latest_vol > avg_vol_5

                    comp_name = stock_name_dict.get(stock_digits, "台股公司")

                    st.success(
                        f"{comp_name}【{used_symbol}】最新收盤價：{latest_close:.2f} 元"
                    )

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
                        st.metric(label="5日 RSI (5T)", value=f"{latest_rsi_5:.2f}")
                    with col2:
                        st.metric(label="10日 RSI (10T)", value=f"{latest_rsi_10:.2f}")

                    # ==========================================
                    # 🎯 犀利媽 20年極端心法核心判定引擎
                    # ==========================================
                    st.markdown("---")
                    st.subheader("🎯 犀利媽 20年極端心法實戰報告")

                    min_rsi = min(latest_rsi_5, latest_rsi_10)
                    max_rsi = max(latest_rsi_5, latest_rsi_10)

                    # 1. 極端位階狀態判定
                    if max_rsi >= 80:
                        market_state = f"🔥 **極端過熱區** (RSI: {max_rsi:.1f})：高檔過熱，隨時有急跌拉回風險。"
                    elif min_rsi <= 20:
                        market_state = f"❄️ **極端超跌區** (RSI: {min_rsi:.1f})：進入非理性恐慌低檔區，隨時注意止跌反彈！"
                    elif min_rsi <= 35:
                        market_state = f"📉 **偏弱超賣區** (RSI: {min_rsi:.1f})：指標逐漸偏弱接近低檔，密切觀察是否破底。"
                    elif max_rsi >= 65:
                        market_state = f"📈 **偏強過熱區** (RSI: {max_rsi:.1f})：指標偏強拉升中，隨時注意高檔追價風險。"
                    else:
                        market_state = f"⚖️ **常態雜訊區** (RSI: {min_rsi:.1f}~{max_rsi:.1f})：30~70 盤整中，犀利媽視為無效訊號。"

                    # 2. 犀利媽專屬燈號與評分判定
                    if max_rsi >= 85:
                        light = "🔴 賣出燈 (極端過熱)"
                        score = 15
                        action = "【心法執行】高檔爆量不漲，果斷獲利了結或順勢放空，絕不追高！"
                    elif min_rsi <= 20:
                        if is_volume_up:
                            light = "🟢 買進燈 (極端超跌 + 主力帶量)"
                            score = 90
                            action = "【心法執行】恐慌急殺且出現帶量止跌，符合犀利媽黃金低接點，分批進場！"
                        else:
                            light = "🔵 觀察燈 (極端超跌等待量能)"
                            score = 75
                            action = "【心法執行】指標已達個位數/低檔極端值，隨時盯盤，等帶量紅K一出立刻手刀買進！"
                    elif min_rsi <= 30:
                        light = "🟡 預警燈 (接近超跌位階)"
                        score = 60
                        action = "【心法執行】指標接近超跌區，先列入重點觀察清單，等 RSI 破 20 更好。"
                    elif max_rsi >= 70:
                        light = "🟠 警戒燈 (過熱拉高區)"
                        score = 35
                        action = "【心法執行】已有過熱跡象，停止追價，持股者開始調高停利點。"
                    else:
                        light = "⚪ 觀望燈 (常態雜訊區)"
                        score = 50
                        action = "【心法執行】按兵不動，常態區間不理它，專注盯緊少數核心主流股即可。"

                    # 結構化 4 大心法報告
                    st.markdown("#### 📋 犀利媽 20 年極端心法檢視報告：")
                    st.markdown(f"1. **【心法 1】極端值過濾**：{market_state}")
                    st.markdown(f"2. **【心法 2】持股精品化**：當前量能狀態為 **{'🔥 帶量突破（量能充足）' if is_volume_up else '❄️ 成交量偏冷（量能不足）'}**。")
                    st.markdown(f"3. **【心法 3】消息與籌碼對照**：請對照下方 10 則最新即時新聞，確認基本面有無重大變動。")
                    st.markdown(
                        f"4. **【心法 4】鐵血停損紀律**：\n"
                        f"   - **燈號判定**：{light}（評分：{score}/100）\n"
                        f"   - **操作方針**：{action}\n"
                        f"   - **⚠️ 鐵血原則**：方向不對或破支撐立刻**手刀停損**，絕不抱持「套牢變存股」的鴕鳥心態！"
                    )

                    # ===== 一眼看懂面板 =====
                    st.markdown("---")
                    col_a, col_b, col_c_status = st.columns(3)
                    with col_a:
                        st.metric("燈號", light)
                    with col_b:
                        st.metric("評分", f"{score}/100")
                    with col_c_status:
                        st.metric("建議方針", action.split("】")[1] if "】" in action else action)

                    st.progress(score)

                    # 近期 RSI 走勢圖
                    st.markdown("---")
                    st.subheader("📊 近期 RSI 走勢圖")
                    rsi_chart_df = pd.DataFrame(
                        {"RSI_5": df["RSI_5"], "RSI_10": df["RSI_10"]}
                    ).tail(60)
                    st.line_chart(rsi_chart_df)

                    # =======================================================
                    # 📰 動態抓取最新 10 則新聞
                    # =======================================================
                    st.markdown("---")
                    st.subheader(f"📰【{comp_name} ({stock_digits})】最新即時新聞與重大消息（動態抓取 10 則）")
                    
                    fetched_news = fetch_stock_news(stock_digits, comp_name, count=10)

                    if fetched_news:
                        for idx, item in enumerate(fetched_news, 1):
                            st.markdown(
                                f"**{idx}. [{item['title']}]({item['link']})**  \n"
                                f"⏱️ *發布時間：{item['date']}* | 🏢 *來源：{item['source']}*"
                            )
                            st.markdown("---")
                    else:
                        st.info("尚無查獲近期相關新聞，請至公開資訊觀測站參閱該股公告。")

            except Exception as e:
                st.error(f"讀取台股資料時發生錯誤：{e}")

# 頁面最下方心法備註說明
st.markdown("---")
with st.expander("📖 點擊展開：犀利媽 20 年極端操盤四大鐵則"):
    st.markdown("""
    1. **只抓極端值**：平時常態區間（30~70）的指標雜訊完全無視；唯有極端過熱（>90）或極端超跌（<10）才動作。
    2. **開精品店不開雜貨店**：持股精簡至 2~3 檔主流焦點股，不碰無量冷門股與低價水餃股。
    3. **消息與極端指標雙軌驗證**：主動解讀財經資訊，反向利用群體恐慌或過度樂觀。
    4. **絕不凹單、手刀停損**：方向不對立刻砍單，確保資金流動性與冷靜的思考能力。
    """)
