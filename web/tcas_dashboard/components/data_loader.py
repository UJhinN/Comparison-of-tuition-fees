"""
Data Loader for TCAS Dashboard
โหลดและประมวลผลข้อมูล TCAS
"""

import pandas as pd
import streamlit as st
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.helpers import clean_data, calculate_statistics

@st.cache_data
def load_tcas_data(file_path: str = "data/improved_tcas_data_with_province_updated.xlsx") -> pd.DataFrame:
    """
    โหลดข้อมูล TCAS จากไฟล์ Excel
    """
    try:
        df = pd.read_excel(file_path)
        df = clean_data(df)
        return df
    except FileNotFoundError:
        st.error(f"ไม่พบไฟล์ข้อมูล: {file_path}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {str(e)}")
        return pd.DataFrame()

def get_unique_values(df: pd.DataFrame) -> dict:
    """
    ดึงค่าที่ไม่ซ้ำจากแต่ละคอลัมน์สำหรับ filter
    """
    if df.empty:
        return {}
    
    return {
        'search_terms': sorted(df['คำค้น'].unique().tolist()),
        'universities': sorted(df['มหาวิทยาลัย'].unique().tolist()),
        'faculties': sorted(df['คณะ'].unique().tolist()),
        'course_types': sorted(df['ประเภทหลักสูตร'].unique().tolist()),
        'provinces': sorted(df['จังหวัด'].unique().tolist())
    }

def filter_data(df: pd.DataFrame, 
                field_filter: str = "All",
                province_filter: list = None,
                course_type_filter: list = None,
                cost_range: tuple = None) -> pd.DataFrame:
    """
    กรองข้อมูลตาม filter ต่างๆ
    """
    if df.empty:
        return df
    
    filtered_df = df.copy()
    
    # Filter ตามสาขา (All/AI/Computer)
    if field_filter != "All":
        if field_filter == "AI":
            filtered_df = filtered_df[filtered_df['คำค้น'] == 'วิศวกรรม ปัญญาประดิษฐ์']
        elif field_filter == "Computer":
            filtered_df = filtered_df[filtered_df['คำค้น'] == 'วิศวกรรม คอมพิวเตอร์']
    
    # Filter ตามจังหวัด
    if province_filter and len(province_filter) > 0:
        filtered_df = filtered_df[filtered_df['จังหวัด'].isin(province_filter)]
    
    # Filter ตามประเภทหลักสูตร
    if course_type_filter and len(course_type_filter) > 0:
        filtered_df = filtered_df[filtered_df['ประเภทหลักสูตร'].isin(course_type_filter)]
    
    # Filter ตามช่วงค่าใช้จ่าย
    if cost_range:
        min_cost, max_cost = cost_range
        filtered_df = filtered_df[
            (filtered_df['ค่าใช้จ่าย'] >= min_cost) & 
            (filtered_df['ค่าใช้จ่าย'] <= max_cost)
        ]
    
    return filtered_df

def get_summary_stats(df: pd.DataFrame, field_filter: str = "All") -> dict:
    """
    คำนวณสถิติสรุปของข้อมูล
    """
    if df.empty:
        return {}
    
    # สถิติรวม
    total_stats = calculate_statistics(df)
    
    summary = {
        'total_courses': len(df),
        'total_universities': df['มหาวิทยาลัย'].nunique(),
        'total_provinces': df['จังหวัด'].nunique(),
        'overall_stats': total_stats
    }
    
    # สถิติแยกตามสาขา
    if field_filter == "All":
        ai_data = df[df['คำค้น'] == 'วิศวกรรม ปัญญาประดิษฐ์']
        comp_data = df[df['คำค้น'] == 'วิศวกรรม คอมพิวเตอร์']
        
        summary['ai_stats'] = {
            'count': len(ai_data),
            'stats': calculate_statistics(ai_data)
        }
        summary['computer_stats'] = {
            'count': len(comp_data),
            'stats': calculate_statistics(comp_data)
        }
    
    return summary

def prepare_chart_data(df: pd.DataFrame, group_by: str = 'มหาวิทยาลัย') -> pd.DataFrame:
    """
    เตรียมข้อมูลสำหรับสร้างกราฟ
    """
    if df.empty:
        return pd.DataFrame()
    
    # กรองข้อมูลที่มีค่าใช้จ่าย > 0
    df_valid = df[df['ค่าใช้จ่าย'] > 0].copy()
    
    if df_valid.empty:
        return pd.DataFrame()
    
    # จัดกลุ่มข้อมูล
    chart_data = df_valid.groupby([group_by, 'คำค้น']).agg({
        'ค่าใช้จ่าย': ['mean', 'count'],
        'คณะ': 'first',
        'จังหวัด': 'first',
        'ประเภทหลักสูตร': 'first'
    }).round(0)
    
    # Flatten column names
    chart_data.columns = ['avg_cost', 'course_count', 'faculty', 'province', 'course_type']
    chart_data = chart_data.reset_index()
    
    # เรียงตามค่าใช้จ่ายจากน้อยไปมาก
    chart_data = chart_data.sort_values('avg_cost')
    
    return chart_data

def get_cost_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    เตรียมข้อมูลสำหรับ histogram การกระจายตัวของค่าใช้จ่าย
    """
    if df.empty:
        return pd.DataFrame()
    
    costs = df[df['ค่าใช้จ่าย'] > 0]['ค่าใช้จ่าย']
    
    if costs.empty:
        return pd.DataFrame()
    
    # สร้าง bins สำหรับ histogram
    bins = pd.cut(costs, bins=10, include_lowest=True)
    distribution = bins.value_counts().sort_index()
    
    # แปลงเป็น DataFrame
    dist_df = pd.DataFrame({
        'cost_range': [f"{int(interval.left):,} - {int(interval.right):,}" for interval in distribution.index],
        'count': distribution.values,
        'range_start': [interval.left for interval in distribution.index],
        'range_end': [interval.right for interval in distribution.index]
    })
    
    return dist_df