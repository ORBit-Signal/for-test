import streamlit as st
import pandas as pd
import plotly.express as px

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Hotel Amber 85 - Buffet Dashboard", layout="wide")

st.title("📊 แดชบอร์ดวิเคราะห์ข้อมูลบุฟเฟต์อาหารเช้า")
st.subheader("โรงแรมแอมเบอร์ 85 (Hotel Amber 85)")

# 2. โหลดข้อมูล (สมมติว่าไฟล์ชื่อ buffet_data.csv)
@st.cache_data # ใส่เพื่อช่วยให้เว็บโหลดเร็วขึ้น ไม่ต้องอ่านไฟล์ใหม่ทุกครั้งที่กดปุ่ม
def load_data():
    df = pd.read_csv("2026 Data Test1 Final - Busy Buffet Dataset.xlsx")
    # คุณสามารถเพิ่มโค้ด Clean Data หรือสร้างฟิลด์ใหม่ เช่น Walk-away ตรงนี้ได้เลย
    return df

try:
    df = load_data()
except:
    st.warning("⚠️ กรุณาตรวจสอบว่ามีไฟล์ข้อมูล 'buffet_data.csv' อยู่ในโฟลเดอร์แล้ว")
    df = None

if df is not None:
    # 3. แบ่งแท็บตามโจทย์หลัก
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 ข้อมูลภาพรวม", 
        "💬 พิสูจน์คำพูดพนักงาน (Task 1)", 
        "❌ โต้แย้งแนวทางที่ไม่เห็นผล (Task 2)", 
        "✅ ข้อเสนอแนะที่ดีที่สุด (Task 3)"
    ])

    with tab1:
        st.header("🔍 ภาพรวมข้อมูลดิบ")
        st.write(df.head()) # แสดงตัวอย่างข้อมูล
        # ใส่ตัวเลขสำคัญ (Metrics) เช่น จำนวนลูกค้าทั้งหมด, อัตรา Walk-away
        
    with tab2:
        st.header("📌 Task 1: พิสูจน์ความคิดเห็นของพนักงาน")
        # ข้อ 1: ลูกค้า In-house VS Walk-in เรื่องการรอคิว
        st.subheader("1. ปัญหารอคิวและการถอดใจเดินจากไป (Walk-away)")
        # ตัวอย่างการสร้างกราฟด้วย Plotly
        # fig = px.bar(...)
        # st.plotly_chart(fig, use_container_width=True)
        st.info("💡 **บทวิเคราะห์:** ใส่คำอธิบายของคุณตรงนี้ว่าจริงหรือไม่จริงตามข้อมูล")

    with tab3:
        st.header("📌 Task 2: ทำไมแนวทางปฏิบัติเหล่านี้ถึงใช้ไม่ได้ผล?")
        option = st.selectbox("เลือกแนวทางปฏิบัติที่ต้องการดูข้อมูลโต้แย้ง:", 
                                    ["1. ลดเวลานั่งทาน", "2. เพิ่มราคาเป็น 259 บาท", "3. ให้ In-house แซงคิว"])
        # เขียนเงื่อนไขแสดงกราฟตามที่เลือก
        
    with tab4:
        st.header("📌 Task 3: แนวทางแก้ไขปัญหาที่ดีที่สุด (ความเห็นส่วนตัว)")
        st.success("🎯 แนวทางที่แนะนำ: [ใส่แนวทางของคุณ] พร้อมกราฟและเหตุผลสนับสนุน")
