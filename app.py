# =====================
# 🎯 犀利媽法則分析
# =====================

st.markdown("---")
st.subheader("🎯 犀利媽法則分析結果")

if latest_rsi_5 >= 90 or latest_rsi_10 >= 90:

    status = "🔴 極度過熱區"
    stars = "⭐"
    score = 20

    advice = """
    ✅ 建議動作：分批獲利了結

    • 短線漲幅過大
    • 不建議追價
    • 可逐步落袋為安
    """

elif latest_rsi_5 >= 70:

    status = "🟠 過熱警戒區"
    stars = "⭐⭐"
    score = 40

    advice = """
    ✅ 建議動作：停止追價

    • 市場買氣過熱
    • 持股續抱即可
    • 不建議新資金追高
    """

elif latest_rsi_5 > latest_rsi_10 and latest_rsi_5 >= 50:

    status = "🟢 多頭攻擊區"
    stars = "⭐⭐⭐⭐⭐"
    score = 95

    advice = """
    ✅ 建議動作：買進或加碼

    • 5T突破10T
    • 短線動能強於中期
    • 多方主導盤勢
    • 為最佳進場區域
    """

elif latest_rsi_5 < latest_rsi_10 and latest_rsi_10 >= 50:

    status = "🟡 多頭整理區"
    stars = "⭐⭐⭐⭐"
    score = 80

    advice = """
    ✅ 建議動作：續抱等待

    • 多頭架構仍在
    • 短線拉回整理
    • 無須急著賣出
    • 等待下一次攻擊
    """

elif latest_rsi_5 < 30 and latest_rsi_10 < 40:

    status = "🔵 超賣觀察區"
    stars = "⭐⭐⭐"
    score = 75

    advice = """
    ✅ 建議動作：觀察反彈

    • 短線跌深
    • 留意打底訊號
    • 適合觀察布局
    """

else:

    status = "⚪ 多空拉鋸區"
    stars = "⭐⭐⭐"
    score = 50

    advice = """
    ✅ 建議動作：觀望

    • 多空方向不明
    • 等待突破
    • 暫不積極操作
    """

# =====================
# 一眼看懂區
# =====================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "目前狀態",
        status
    )

with col2:
    st.metric(
        "推薦指數",
        stars
    )

with col3:
    st.metric(
        "買進評分",
        f"{score}/100"
    )

st.progress(score)

# =====================
# 結論框
# =====================

if score >= 90:
    st.success(
        f"""
【犀利媽結論】

目前屬於 {status}

買進評分：{score}/100

建議：
✅ 可買進
✅ 可加碼
✅ 持股續抱
"""
    )

elif score >= 75:
    st.info(
        f"""
【犀利媽結論】

目前屬於 {status}

買進評分：{score}/100

建議：
✅ 持股續抱
✅ 等待下一次訊號
"""
    )

elif score >= 50:
    st.warning(
 
