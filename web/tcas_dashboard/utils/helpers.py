"""
Helper functions for TCAS Dashboard
ฟังก์ชันช่วยเหลือสำหรับคำนวณและจัดรูปแบบข้อมูล
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

def calculate_statistics(df: pd.DataFrame, cost_column: str = 'ค่าใช้จ่าย') -> Dict:
    """
    คำนวณสถิติพื้นฐานของค่าใช้จ่าย
    """
    costs = df[cost_column].dropna()
    costs = costs[costs > 0]  # กรองค่า 0 ออก
    
    if len(costs) == 0:
        return {
            'count': 0,
            'mean': 0,
            'median': 0,
            'min': 0,
            'max': 0,
            'std': 0
        }
    
    return {
        'count': len(costs),
        'mean': costs.mean(),
        'median': costs.median(),
        'min': costs.min(),
        'max': costs.max(),
        'std': costs.std()
    }

def format_currency(amount: float) -> str:
    """
    จัดรูปแบบตัวเลขเป็นสกุลเงินไทย
    """
    if pd.isna(amount) or amount == 0:
        return "ไม่ระบุ"
    return f"{amount:,.0f} บาท"

def format_number(number: float) -> str:
    """
    จัดรูปแบบตัวเลขทั่วไป
    """
    if pd.isna(number):
        return "N/A"
    return f"{number:,.0f}"

def get_color_palette(n_colors: int) -> List[str]:
    """
    สร้างชุดสีสำหรับกราฟ
    """
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
        '#c49c94', '#f7b6d3', '#c7c7c7', '#dbdb8d', '#9edae5'
    ]
    
    if n_colors <= len(colors):
        return colors[:n_colors]
    else:
        # ถ้าต้องการสีเยอะ ให้ repeat pattern
        multiplier = (n_colors // len(colors)) + 1
        extended_colors = (colors * multiplier)[:n_colors]
        return extended_colors

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    ทำความสะอาดข้อมูล
    """
    df_clean = df.copy()
    
    # ทำความสะอาดชื่อคอลัมน์
    df_clean.columns = df_clean.columns.str.strip()
    
    # แทนที่ค่าว่างใน cost ด้วย 0
    df_clean['ค่าใช้จ่าย'] = pd.to_numeric(df_clean['ค่าใช้จ่าย'], errors='coerce').fillna(0)
    
    # ทำความสะอาดข้อมูลจังหวัด
    df_clean['จังหวัด'] = df_clean['จังหวัด'].str.strip()
    df_clean['จังหวัด'] = df_clean['จังหวัด'].replace('ไม่ทราบจังหวัด', 'ไม่ระบุ')
    
    return df_clean

def get_top_bottom_records(df: pd.DataFrame, cost_column: str = 'ค่าใช้จ่าย', 
                          n: int = 10) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    หา Top N แพงที่สุดและถูกที่สุด
    """
    # กรองข้อมูลที่มีค่าใช้จ่าย > 0
    df_valid = df[df[cost_column] > 0].copy()
    
    if len(df_valid) == 0:
        return pd.DataFrame(), pd.DataFrame()
    
    # เรียงจากแพงไปถูก
    df_sorted = df_valid.sort_values(cost_column, ascending=False)
    
    top_expensive = df_sorted.head(n)
    top_cheapest = df_sorted.tail(n).sort_values(cost_column, ascending=True)
    
    return top_expensive, top_cheapest

def filter_by_search_term(df: pd.DataFrame, search_term: str) -> pd.DataFrame:
    """
    ค้นหาข้อมูลตามคำค้น
    """
    if not search_term:
        return df
    
    search_term = search_term.lower()
    
    # ค้นหาในคอลัมน์ที่สำคัญ
    mask = (
        df['มหาวิทยาลัย'].str.lower().str.contains(search_term, na=False) |
        df['คณะ'].str.lower().str.contains(search_term, na=False) |
        df['หลักสูตร'].str.lower().str.contains(search_term, na=False) |
        df['จังหวัด'].str.lower().str.contains(search_term, na=False)
    )
    
    return df[mask]