"""
Filter Components for TCAS Dashboard
สร้าง UI filters สำหรับ dashboard
"""

import streamlit as st
import pandas as pd
from typing import Tuple, List

def create_main_filters(unique_values: dict, df: pd.DataFrame) -> Tuple[str, List[str], List[str], Tuple[float, float], str]:
    """
    สร้าง main filters ใน sidebar
    """
    st.sidebar.header("🔍 เลือกข้อมูลที่ต้องการดู")
    
    # 1. Filter สาขา (All/AI/Computer)
    field_options = ["All", "AI", "Computer"]
    field_labels = {
        "All": "ทั้งหมด",
        "AI": "ปัญญาประดิษฐ์ (AI)", 
        "Computer": "คอมพิวเตอร์"
    }
    
    field_filter = st.sidebar.selectbox(
        "🎯 เลือกสาขา:",
        options=field_options,
        format_func=lambda x: field_labels[x],
        index=0
    )
    
    # 2. Filter จังหวัด (multiselect)
    st.sidebar.subheader("📍 เลือกจังหวัด")
    provinces = unique_values.get('provinces', [])
    
    # เพิ่มตัวเลือก "เลือกทั้งหมด"
    select_all_provinces = st.sidebar.checkbox("เลือกทั้งหมด (จังหวัด)", value=True)
    
    if select_all_provinces:
        province_filter = provinces
        st.sidebar.info(f"เลือกแล้ว: {len(provinces)} จังหวัด")
    else:
        province_filter = st.sidebar.multiselect(
            "เลือกจังหวัด:",
            options=provinces,
            default=provinces[:5] if len(provinces) > 5 else provinces
        )
    
    # 3. Filter ประเภทหลักสูตร
    st.sidebar.subheader("📚 ประเภทหลักสูตร")
    course_types = unique_values.get('course_types', [])
    
    select_all_types = st.sidebar.checkbox("เลือกทั้งหมด (ประเภท)", value=True)
    
    if select_all_types:
        course_type_filter = course_types
        st.sidebar.info(f"เลือกแล้ว: {len(course_types)} ประเภท")
    else:
        course_type_filter = st.sidebar.multiselect(
            "เลือกประเภทหลักสูตร:",
            options=course_types,
            default=course_types
        )
    
    # 4. Filter ช่วงค่าใช้จ่าย
    st.sidebar.subheader("💰 ช่วงค่าใช้จ่าย")
    
    if not df.empty:
        valid_costs = df[df['ค่าใช้จ่าย'] > 0]['ค่าใช้จ่าย']
        if not valid_costs.empty:
            min_cost = int(valid_costs.min())
            max_cost = int(valid_costs.max())
            
            cost_range = st.sidebar.slider(
                "เลือกช่วงค่าใช้จ่าย (บาท):",
                min_value=min_cost,
                max_value=max_cost,
                value=(min_cost, max_cost),
                step=1000,
                format="%d"
            )
            
            st.sidebar.caption(f"ช่วง: {cost_range[0]:,} - {cost_range[1]:,} บาท")
        else:
            cost_range = (0, 0)
    else:
        cost_range = (0, 0)
    
    # 5. Search box
    st.sidebar.subheader("🔎 ค้นหา")
    search_term = st.sidebar.text_input(
        "ค้นหามหาวิทยาลัย, คณะ, หลักสูตร:",
        placeholder="เช่น จุฬาลงกรณ์, วิศวกรรม..."
    )
    
    return field_filter, province_filter, course_type_filter, cost_range, search_term

def create_chart_options() -> Tuple[str, bool, int]:
    """
    สร้าง options สำหรับการแสดงกราฟ
    """
    st.sidebar.subheader("📊 ตัวเลือกการแสดงกราฟ")
    
    # เลือกวิธีจัดกลุ่มข้อมูล
    group_options = {
        'มหาวิทยาลัย': 'ตามมหาวิทยาลัย',
        'คณะ': 'ตามคณะ',
        'จังหวัด': 'ตามจังหวัด'
    }
    
    group_by = st.sidebar.selectbox(
        "จัดกลุ่มข้อมูล:",
        options=list(group_options.keys()),
        format_func=lambda x: group_options[x],
        index=0
    )
    
    # แสดงเส้นค่าเฉลี่ย
    show_mean_line = st.sidebar.checkbox("แสดงเส้นค่าเฉลี่ย", value=True)
    
    # จำนวนรายการที่จะแสดง
    max_items = st.sidebar.slider(
        "จำนวนรายการที่แสดง:",
        min_value=10,
        max_value=50,
        value=20,
        step=5
    )
    
    return group_by, show_mean_line, max_items

def display_filter_summary(field_filter: str, filtered_df: pd.DataFrame, original_df: pd.DataFrame):
    """
    แสดงสรุปผลการ filter
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="หลักสูตรที่แสดง",
            value=len(filtered_df),
            delta=f"{len(filtered_df) - len(original_df)} จากทั้งหมด"
        )
    
    with col2:
        universities = filtered_df['มหาวิทยาลัย'].nunique() if not filtered_df.empty else 0
        st.metric(
            label="มหาวิทยาลัย",
            value=universities
        )
    
    with col3:
        provinces = filtered_df['จังหวัด'].nunique() if not filtered_df.empty else 0
        st.metric(
            label="จังหวัด",
            value=provinces
        )
    
    with col4:
        if not filtered_df.empty:
            valid_costs = filtered_df[filtered_df['ค่าใช้จ่าย'] > 0]['ค่าใช้จ่าย']
            avg_cost = valid_costs.mean() if not valid_costs.empty else 0
        else:
            avg_cost = 0
        
        st.metric(
            label="ค่าใช้จ่ายเฉลี่ย",
            value=f"{avg_cost:,.0f} บาท" if avg_cost > 0 else "ไม่มีข้อมูล"
        )
    
    # แสดง filter ที่ใช้
    if field_filter != "All":
        field_label = "ปัญญาประดิษฐ์" if field_filter == "AI" else "คอมพิวเตอร์"
        st.info(f"🎯 กำลังแสดงข้อมูล: วิศวกรรม{field_label}")

def create_advanced_filters(df: pd.DataFrame) -> dict:
    """
    สร้าง advanced filters ในส่วน expander
    """
    with st.sidebar.expander("⚙️ ตัวเลือกขั้นสูง"):
        # เรียงลำดับ
        sort_options = {
            'ค่าใช้จ่าย_asc': 'ค่าใช้จ่าย (น้อย → มาก)',
            'ค่าใช้จ่าย_desc': 'ค่าใช้จ่าย (มาก → น้อย)',
            'มหาวิทยาลัย_asc': 'ชื่อมหาวิทยาลัย (A → Z)',
            'จังหวัด_asc': 'จังหวัด (A → Z)'
        }
        
        sort_by = st.selectbox(
            "เรียงลำดับตาม:",
            options=list(sort_options.keys()),
            format_func=lambda x: sort_options[x],
            index=0
        )
        
        # แสดงเฉพาะหลักสูตรที่มีค่าใช้จ่าย
        hide_no_cost = st.checkbox("ซ่อนหลักสูตรที่ไม่มีข้อมูลค่าใช้จ่าย", value=True)
        
        # แสดง outliers
        show_outliers = st.checkbox("แสดง outliers (ค่าผิดปกติ)", value=True)
        
        return {
            'sort_by': sort_by,
            'hide_no_cost': hide_no_cost,
            'show_outliers': show_outliers
        }

def apply_advanced_filters(df: pd.DataFrame, advanced_options: dict) -> pd.DataFrame:
    """
    ใช้ advanced filters กับข้อมูล
    """
    if df.empty:
        return df
    
    result_df = df.copy()
    
    # ซ่อนหลักสูตรที่ไม่มีค่าใช้จ่าย
    if advanced_options.get('hide_no_cost', True):
        result_df = result_df[result_df['ค่าใช้จ่าย'] > 0]
    
    # เรียงลำดับ
    sort_by = advanced_options.get('sort_by', 'ค่าใช้จ่าย_asc')
    
    if sort_by == 'ค่าใช้จ่าย_asc':
        result_df = result_df.sort_values('ค่าใช้จ่าย', ascending=True)
    elif sort_by == 'ค่าใช้จ่าย_desc':
        result_df = result_df.sort_values('ค่าใช้จ่าย', ascending=False)
    elif sort_by == 'มหาวิทยาลัย_asc':
        result_df = result_df.sort_values('มหาวิทยาลัย', ascending=True)
    elif sort_by == 'จังหวัด_asc':
        result_df = result_df.sort_values('จังหวัด', ascending=True)
    
    return result_df