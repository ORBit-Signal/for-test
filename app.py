import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. ตั้งค่าหน้าเว็บให้เป็นแบบกว้างพิเศษ (Wide Mode) เพื่อขยายพื้นที่การมองเห็น
st.set_page_config(page_title="Hotel Amber 85 - Buffet Dashboard", layout="wide")

@st.cache_data
def load_and_clean_data():
    file_path = "2026 Data Test1 Final - Busy Buffet Dataset.xlsx"
    all_sheets = pd.read_excel(file_path, sheet_name=None)
    df_list = []
    
    for sheet_name, data in all_sheets.items():
        data['date'] = sheet_name
        df_list.append(data)
        
    df = pd.concat(df_list, ignore_index=True)
    df.columns = df.columns.str.strip().str.lower()
    df.rename(columns={'table_no.': 'table_no', 'service_no.': 'service_no'}, inplace=True)
    
# 1. แปลงข้อมูลเวลา (โค้ดเดิมของคุณ)
    time_cols = ['queue_start', 'queue_end', 'meal_start', 'meal_end']
    for col in time_cols:
        df[col] = pd.to_datetime(df[col], format='%H:%M:%S', errors='coerce')
        
    # ==========================================
    # 🌟 NEW: เพิ่มโค้ดซ่อมข้อมูลเวลา (Data Correction) ตรงนี้
    # ==========================================
    # วนลูปเช็กทุกคอลัมน์เวลา ถ้าเจอชั่วโมงที่ 2 (ตี 2) ให้บวกเวลาเพิ่ม 5 ชั่วโมง (กลายเป็น 7 โมง)
    for col in time_cols:
        # หาแถวที่คอลัมน์เวลานั้นไม่เป็นค่าว่าง และมีชั่วโมงเท่ากับ 2
        mask = df[col].notna() & (df[col].dt.hour == 2)
        # ทำการบวกเวลาเพิ่ม 5 ชั่วโมง
        df.loc[mask, col] = df.loc[mask, col] + pd.Timedelta(hours=5)
    # ==========================================

    # 2. คำนวณนาที (โค้ดเดิมของคุณ)
    df['wait_time_mins'] = (df['queue_end'] - df['queue_start']).dt.total_seconds() / 60
    df['meal_time_mins'] = (df['meal_end'] - df['meal_start']).dt.total_seconds() / 60
    
    # สร้างคอลัมน์สำหรับวิเคราะห์ช่วงเวลา Peak (ดึงชั่วโมงที่ลูกค้ามาถึงคิว หรือเวลาเริ่มทานถ้าไม่มีคิว)
    df['arrival_time'] = df['queue_start'].fillna(df['meal_start'])
    df['arrival_hour'] = df['arrival_time'].dt.hour
    
    # คัดกรอง Edge Cases ออก
    df = df.dropna(subset=['queue_start', 'meal_start'], how='all')
    
    # กำหนดสถานะลูกค้า
    df['is_walk_away'] = df['queue_start'].notna() & df['meal_start'].isna()
    df['is_waited'] = df['queue_start'].notna()
    df['is_direct_seating'] = df['queue_start'].isna() & df['meal_start'].notna()
    
    def get_status(row):
        if row['is_walk_away']: return 'Walk-away'
        if row['is_direct_seating']: return 'Direct Seating'
        if row['is_waited']: return 'Waited & Seated'
        return 'Unknown'
    df['customer_status'] = df.apply(get_status, axis=1)
    
    # ล้างกลุ่มข้อมูลโซนให้เข้าใจง่าย ป้องกันการเกิดข้อความ Unknown ซ้ำซ้อน
    def get_zone(t):
        if pd.isna(t) or str(t).strip().lower() in ['nan', '']: return 'Walk-away (No Table)'
        t_str = str(t).strip().upper()
        match = re.search(r'\d+', t_str)
        if match:
            num = int(match.group())
            if 1 <= num <= 6: return 'Indoor'
            elif 7 <= num <= 20: return 'Outdoor'
            elif num == 99: return 'Queue Area (99)'
        return 'Other / Messy Data'
    df['zone'] = df['table_no'].apply(get_zone)
    
    # --- ตารางที่ 1: สำหรับวิเคราะห์มุมมองลูกค้า ---
    df_customer = df.copy()
    
    # --- ตารางที่ 2: สำหรับวิเคราะห์มุมมองรายโต๊ะ (แตกบรรทัดย่อย) ---
    df_table_raw = df.copy()
    df_table_raw = df_table_raw[~df_table_raw['is_walk_away']] # เอาเฉพาะคนที่ได้โต๊ะจริง
    df_table_raw['table_no'] = df_table_raw['table_no'].astype(str).str.replace(" ", "")
    
    # ใช้ Regex แยกทั้งกรณีใช้เครื่องหมายขีดกลาง '-' และ เครื่องหมายสแลช '/' เพื่อครอบคลุมโต๊ะรวมทุกรูปแบบ
    df_table_raw['table_list'] = df_table_raw['table_no'].apply(lambda x: re.split(r'[-/]', x))
    df_table = df_table_raw.explode('table_list')
    df_table.rename(columns={'table_list': 'single_table'}, inplace=True)
    df_table = df_table[df_table['single_table'].str.strip() != '']
    
    return df_customer, df_table

# โหลดข้อมูลเข้าสู่ระบบ
try:
    df_customer, df_table = load_and_clean_data()
    data_loaded = True
except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
    data_loaded = False

if data_loaded:
    # ---------------------------------------------------------
    # หัวเว็บขนาดกะทัดรัด (Compact Header)
    # ---------------------------------------------------------
    st.markdown("<h2 style='text-align: center; margin-bottom: 0px;'>🍽️ Hotel Amber 85 - Buffet Dashboard</h2>", unsafe_allow_html=True)
    
    # ---------------------------------------------------------
    # ตัวกรองแถวบนสุด (Top Filter Row) - แถวที่ 1
    # ---------------------------------------------------------
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        selected_dates = st.multiselect("📅 วันที่ (Date)", options=df_customer['date'].unique(), default=df_customer['date'].unique(), label_visibility="collapsed")
    with col_f2:
        selected_guests = st.multiselect("👥 ประเภทลูกค้า", options=df_customer['guest_type'].dropna().unique(), default=df_customer['guest_type'].dropna().unique(), label_visibility="collapsed")
    with col_f3:
        selected_zones = st.multiselect("📍 โซนที่นั่ง", options=df_customer['zone'].unique(), default=df_customer['zone'].unique(), label_visibility="collapsed")
    with col_f4:
        selected_status = st.multiselect("🚦 สถานะลูกค้า", options=df_customer['customer_status'].unique(), default=df_customer['customer_status'].unique(), label_visibility="collapsed")
        
    # ทำการกรองข้อมูลทั้งสองตาราง
    df_c_filtered = df_customer[
        (df_customer['date'].isin(selected_dates)) & 
        (df_customer['guest_type'].isin(selected_guests)) &
        (df_customer['zone'].isin(selected_zones)) &
        (df_customer['customer_status'].isin(selected_status))
    ]
    df_t_filtered = df_table[
        (df_table['date'].isin(selected_dates)) & 
        (df_table['guest_type'].isin(selected_guests)) &
        (df_table['zone'].isin(selected_zones)) &
        (df_table['customer_status'].isin(selected_status))
    ]

    # ---------------------------------------------------------
    # ตัวเลขสรุปสำคัญ (Key Metrics Row) - แถวที่ 2
    # ---------------------------------------------------------
    st.markdown("<div style='margin-top: -10px; margin-bottom: -10px;'>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    total_g = len(df_c_filtered)
    total_p = df_c_filtered['pax'].sum() if total_g > 0 else 0
    w_away = df_c_filtered['is_walk_away'].sum()
    w_rate = (w_away / total_g) * 100 if total_g > 0 else 0
    a_wait = df_c_filtered['wait_time_mins'].mean()
    
    m1.metric("กลุ่มลูกค้าทั้งหมด", f"{total_g} กลุ่ม")
    m2.metric("จำนวนคนรวม (Pax)", f"{total_p:,.0f} คน")
    m3.metric("อัตรา Walk-away", f"{w_rate:.1f}%")
    m4.metric("เวลารอคิวเฉลี่ย", f"{a_wait:.1f} นาที" if pd.notna(a_wait) else "0.0 นาที")
    st.markdown("</div>", unsafe_allow_html=True)

    # ตั้งค่าความสูงของกราฟให้มีขนาดเล็กกะทัดรัดเพื่อบีบให้อยู่ในหน้าจอเดียว (ความสูงปกติประมาณ 180-200 พิกเซล)
    CHART_HEIGHT = 190
    
    # ---------------------------------------------------------
    # แผงกราฟแถวที่ 1 (Row 1 Charts: Focus on Times & Volume)
    # ---------------------------------------------------------
    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
    
    with r1_c1:
        st.caption("⏱️ เวลารอคิวแยกตามประเภทลูกค้า")
        df_w = df_c_filtered[df_c_filtered['is_waited'] == True]
        fig_w = px.box(df_w, x='guest_type', y='wait_time_mins', color='guest_type', height=CHART_HEIGHT)
        fig_w.update_layout(margin=dict(l=10, r=10, t=10, b=10), showlegend=False, xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_w, use_container_width=True)

    with r1_c2:
        st.caption("⏳ ระยะเวลานั่งทานจริง (Meal Time)")
        df_s = df_c_filtered[df_c_filtered['meal_time_mins'].notna()]
        fig_m = px.box(df_s, x='guest_type', y='meal_time_mins', color='guest_type', height=CHART_HEIGHT)
        fig_m.update_layout(margin=dict(l=10, r=10, t=10, b=10), showlegend=False, xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_m, use_container_width=True)

    with r1_c3:
        st.caption("📈 ปริมาณลูกค้าตามช่วงเวลา (Peak Hours)")
        if unhappiness_trend := True:
            peak_data = df_c_filtered.groupby('arrival_hour').size().reset_index(name='count')
            fig_peak = px.line(peak_data, x='arrival_hour', y='count', height=CHART_HEIGHT, markers=True)
            fig_peak.update_layout(margin=dict(l=10, r=10, t=10, b=10), xaxis_title="ชั่วโมง", yaxis_title=None)
            st.plotly_chart(fig_peak, use_container_width=True)

    with r1_c4:
        st.caption("🚶‍♂️ จำนวนลูกค้าที่เดินจากไป (Walk-away)")
        df_wa = df_c_filtered[df_c_filtered['is_walk_away'] == True]
        if not df_wa.empty:
            wa_counts = df_wa.groupby('date').size().reset_index(name='count')
            fig_wa = px.bar(wa_counts, x='date', y='count', height=CHART_HEIGHT)
            fig_wa.update_layout(margin=dict(l=10, r=10, t=10, b=10), xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_wa, use_container_width=True)
        else:
            st.info("ไม่มีข้อมูล")

    # ---------------------------------------------------------
    # แผงกราฟแถวที่ 2 (Row 2 Charts: Focus on Tables & Correlations)
    # ---------------------------------------------------------
    r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
    
    with r2_c1:
        st.caption("🔍 จำนวนคน (Pax) VS เวลารอคิว")
        fig_scat = px.scatter(df_c_filtered, x='pax', y='wait_time_mins', color='guest_type', height=CHART_HEIGHT)
        fig_scat.update_layout(margin=dict(l=10, r=10, t=10, b=10), showlegend=False, xaxis_title="จำนวนคน", yaxis_title=None)
        st.plotly_chart(fig_scat, use_container_width=True)

    with r2_c2:
        st.caption("📊 ความถี่การใช้โต๊ะย่อย (Table Utilization)")
        if not df_t_filtered.empty:
            t_util = df_t_filtered.groupby('single_table').size().reset_index(name='use_count').sort_values(by='use_count', ascending=False).head(10)
            fig_util = px.bar(t_util, x='single_table', y='use_count', height=CHART_HEIGHT)
            fig_util.update_layout(margin=dict(l=10, r=10, t=10, b=10), xaxis_title="เลขโต๊ะ", yaxis_title=None)
            st.plotly_chart(fig_util, use_container_width=True)
        else:
            st.info("ไม่มีข้อมูล")

    with r2_c3:
        st.caption("🪑 เวลานั่งทานเฉลี่ยแยกตามโต๊ะ (นาที)")
        if not df_t_filtered.empty:
            t_meal = df_t_filtered.groupby('single_table')['meal_time_mins'].mean().reset_index().sort_values(by='meal_time_mins', ascending=False).head(10)
            fig_t_meal = px.bar(t_meal, x='meal_time_mins', y='single_table', orientation='h', height=CHART_HEIGHT)
            fig_t_meal.update_layout(margin=dict(l=10, r=10, t=10, b=10), xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_t_meal, use_container_width=True)
        else:
            st.info("ไม่มีข้อมูล")

    with r2_c4:
        st.caption("📍 สัดส่วนกลุ่มลูกค้าแยกตามโซน")
        z_counts = df_c_filtered.groupby('zone').size().reset_index(name='count')
        fig_zone = px.pie(z_counts, names='zone', values='count', hole=0.3, height=CHART_HEIGHT)
        fig_zone.update_layout(margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
        st.plotly_chart(fig_zone, use_container_width=True)
