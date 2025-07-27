"""
Chart Components for TCAS Dashboard
สร้างกราฟต่างๆ สำหรับ dashboard
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.helpers import get_color_palette, format_currency, calculate_statistics

def create_main_bar_chart(df: pd.DataFrame, group_by: str = 'มหาวิทยาลัย', 
                         show_mean_line: bool = True, max_items: int = 20,
                         title_suffix: str = "") -> go.Figure:
    """
    สร้างกราฟแท่งหลักพร้อมเส้นค่าเฉลี่ย
    """
    if df.empty:
        # สร้างกราฟว่าง
        fig = go.Figure()
        fig.add_annotation(
            text="ไม่มีข้อมูลที่จะแสดง",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        fig.update_layout(
            title="ไม่มีข้อมูล",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    # เตรียมข้อมูล
    chart_data = df[df['ค่าใช้จ่าย'] > 0].copy()
    
    if chart_data.empty:
        return create_empty_chart("ไม่มีข้อมูลค่าใช้จ่าย")
    
    # จัดกลุ่มข้อมูล
    if group_by == 'จังหวัด':
        grouped = chart_data.groupby([group_by, 'คำค้น']).agg({
            'ค่าใช้จ่าย': 'mean',
            'คณะ': 'first',
            'มหาวิทยาลัย': 'first'
        }).reset_index()
    elif group_by == 'คณะ':
        grouped = chart_data.groupby([group_by, 'คำค้น']).agg({
            'ค่าใช้จ่าย': 'mean',
            'จังหวัด': 'first',
            'มหาวิทยาลัย': 'first'
        }).reset_index()
    else:  # มหาวิทยาลัย
        grouped = chart_data.groupby([group_by, 'คำค้น']).agg({
            'ค่าใช้จ่าย': 'mean',
            'คณะ': 'first',
            'จังหวัด': 'first'
        }).reset_index()
    
    grouped['ค่าใช้จ่าย'] = grouped['ค่าใช้จ่าย'].round(0)
    
    # เรียงลำดับและจำกัดจำนวน
    grouped = grouped.sort_values('ค่าใช้จ่าย').tail(max_items)
    
    # เตรียม hover data ตาม group_by
    if group_by == 'จังหวัด':
        hover_data_dict = {
            'ค่าใช้จ่าย': ':,.0f',
            'คณะ': True,
            'มหาวิทยาลัย': True
        }
        hover_template = "<b>%{y}</b><br>" + \
                        "ค่าใช้จ่าย: %{x:,.0f} บาท<br>" + \
                        "คณะ: %{customdata[0]}<br>" + \
                        "มหาวิทยาลัย: %{customdata[1]}<br>" + \
                        "<extra></extra>"
    elif group_by == 'คณะ':
        hover_data_dict = {
            'ค่าใช้จ่าย': ':,.0f',
            'จังหวัด': True,
            'มหาวิทยาลัย': True
        }
        hover_template = "<b>%{y}</b><br>" + \
                        "ค่าใช้จ่าย: %{x:,.0f} บาท<br>" + \
                        "จังหวัด: %{customdata[0]}<br>" + \
                        "มหาวิทยาลัย: %{customdata[1]}<br>" + \
                        "<extra></extra>"
    else:  # มหาวิทยาลัย
        hover_data_dict = {
            'ค่าใช้จ่าย': ':,.0f',
            'คณะ': True,
            'จังหวัด': True
        }
        hover_template = "<b>%{y}</b><br>" + \
                        "ค่าใช้จ่าย: %{x:,.0f} บาท<br>" + \
                        "คณะ: %{customdata[0]}<br>" + \
                        "จังหวัด: %{customdata[1]}<br>" + \
                        "<extra></extra>"

    # สร้างกราฟ
    fig = px.bar(
        grouped,
        x='ค่าใช้จ่าย',
        y=group_by,
        color='คำค้น',
        title=f"ค่าใช้จ่ายเฉลี่ยต่อปี (แสดง {len(grouped)} รายการ){title_suffix}",
        orientation='h',
        hover_data=hover_data_dict,
        color_discrete_map={
            'วิศวกรรม ปัญญาประดิษฐ์': '#FF6B6B',
            'วิศวกรรม คอมพิวเตอร์': '#4ECDC4'
        }
    )
    
    # ปรับแต่งกราฟ
    fig.update_traces(hovertemplate=hover_template)
    
    # เพิ่มเส้นค่าเฉลี่ย
    if show_mean_line and not chart_data.empty:
        mean_cost = chart_data['ค่าใช้จ่าย'].mean()
        fig.add_vline(
            x=mean_cost,
            line_dash="dash",
            line_color="red",
            annotation_text=f"ค่าเฉลี่ย: {mean_cost:,.0f} บาท",
            annotation_position="top"
        )
    
    # ปรับแต่ง layout
    fig.update_layout(
        height=max(600, len(grouped) * 25),
        xaxis_title="ค่าใช้จ่าย (บาท)",
        yaxis_title=group_by,
        legend_title="สาขา",
        hovermode='closest',
        template='plotly_white'
    )
    
    # ปรับรูปแบบ axis
    fig.update_layout(
        xaxis=dict(tickformat=","),
        yaxis=dict(tickmode='linear')
    )
    
    return fig

def create_comparison_chart(df: pd.DataFrame) -> go.Figure:
    """
    สร้างกราฟเปรียบเทียบ AI vs Computer
    """
    if df.empty:
        return create_empty_chart("ไม่มีข้อมูลสำหรับเปรียบเทียบ")
    
    # คำนวณสถิติแยกตามสาขา
    stats_data = []
    
    for search_term in df['คำค้น'].unique():
        subset = df[df['คำค้น'] == search_term]
        valid_costs = subset[subset['ค่าใช้จ่าย'] > 0]['ค่าใช้จ่าย']
        
        if not valid_costs.empty:
            stats = calculate_statistics(subset)
            field_name = "AI" if "ปัญญาประดิษฐ์" in search_term else "Computer"
            
            stats_data.append({
                'สาขา': field_name,
                'จำนวนหลักสูตร': len(subset),
                'ค่าใช้จ่ายเฉลี่ย': stats['mean'],
                'ค่าใช้จ่ายต่ำสุด': stats['min'],
                'ค่าใช้จ่ายสูงสุด': stats['max'],
                'ค่ามัธยฐาน': stats['median']
            })
    
    if not stats_data:
        return create_empty_chart("ไม่มีข้อมูลค่าใช้จ่าย")
    
    stats_df = pd.DataFrame(stats_data)
    
    # สร้าง subplot
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'จำนวนหลักสูตร', 'ค่าใช้จ่ายเฉลี่ย', 
            'ค่าใช้จ่ายต่ำสุด', 'ค่าใช้จ่ายสูงสุด'
        ),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "bar"}]]
    )
    
    colors = ['#FF6B6B', '#4ECDC4']
    
    # กราฟ 1: จำนวนหลักสูตร
    fig.add_trace(
        go.Bar(x=stats_df['สาขา'], y=stats_df['จำนวนหลักสูตร'], 
               name='จำนวนหลักสูตร', marker_color=colors,
               text=stats_df['จำนวนหลักสูตร'], textposition='auto'),
        row=1, col=1
    )
    
    # กราฟ 2: ค่าใช้จ่ายเฉลี่ย
    fig.add_trace(
        go.Bar(x=stats_df['สาขา'], y=stats_df['ค่าใช้จ่ายเฉลี่ย'], 
               name='ค่าใช้จ่ายเฉลี่ย', marker_color=colors,
               text=[f"{x:,.0f}" for x in stats_df['ค่าใช้จ่ายเฉลี่ย']], 
               textposition='auto'),
        row=1, col=2
    )
    
    # กราฟ 3: ค่าใช้จ่ายต่ำสุด
    fig.add_trace(
        go.Bar(x=stats_df['สาขา'], y=stats_df['ค่าใช้จ่ายต่ำสุด'], 
               name='ค่าใช้จ่ายต่ำสุด', marker_color=colors,
               text=[f"{x:,.0f}" for x in stats_df['ค่าใช้จ่ายต่ำสุด']], 
               textposition='auto'),
        row=2, col=1
    )
    
    # กราฟ 4: ค่าใช้จ่ายสูงสุด
    fig.add_trace(
        go.Bar(x=stats_df['สาขา'], y=stats_df['ค่าใช้จ่ายสูงสุด'], 
               name='ค่าใช้จ่ายสูงสุด', marker_color=colors,
               text=[f"{x:,.0f}" for x in stats_df['ค่าใช้จ่ายสูงสุด']], 
               textposition='auto'),
        row=2, col=2
    )
    
    fig.update_layout(
        title_text="เปรียบเทียบ AI vs Computer Engineering",
        showlegend=False,
        height=800,
        template='plotly_white'
    )
    
    return fig

def create_box_plot(df: pd.DataFrame) -> go.Figure:
    """
    สร้าง Box Plot แสดงการกระจายตัวของค่าใช้จ่าย
    """
    if df.empty:
        return create_empty_chart("ไม่มีข้อมูลสำหรับ Box Plot")
    
    valid_data = df[df['ค่าใช้จ่าย'] > 0]
    
    if valid_data.empty:
        return create_empty_chart("ไม่มีข้อมูลค่าใช้จ่าย")
    
    fig = px.box(
        valid_data,
        x='คำค้น',
        y='ค่าใช้จ่าย',
        title="การกระจายตัวของค่าใช้จ่าย",
        color='คำค้น',
        color_discrete_map={
            'วิศวกรรม ปัญญาประดิษฐ์': '#FF6B6B',
            'วิศวกรรม คอมพิวเตอร์': '#4ECDC4'
        }
    )
    
    fig.update_layout(
        xaxis_title="สาขา",
        yaxis_title="ค่าใช้จ่าย (บาท)",
        yaxis=dict(tickformat=","),
        template='plotly_white',
        height=500
    )
    
    return fig

def create_province_chart(df: pd.DataFrame) -> go.Figure:
    """
    สร้างกราฟแสดงจำนวนหลักสูตรต่อจังหวัด
    """
    if df.empty:
        return create_empty_chart("ไม่มีข้อมูลจังหวัด")
    
    province_counts = df.groupby(['จังหวัด', 'คำค้น']).size().reset_index(name='จำนวนหลักสูตร')
    province_summary = province_counts.groupby('จังหวัด')['จำนวนหลักสูตร'].sum().reset_index()
    province_summary = province_summary.sort_values('จำนวนหลักสูตร', ascending=True).tail(15)
    
    fig = px.bar(
        province_summary,
        x='จำนวนหลักสูตร',
        y='จังหวัด',
        title="จำนวนหลักสูตรต่อจังหวัด (15 อันดับแรก)",
        orientation='h',
        color='จำนวนหลักสูตร',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        height=600,
        xaxis_title="จำนวนหลักสูตร",
        yaxis_title="จังหวัด",
        template='plotly_white'
    )
    
    return fig

def create_cost_histogram(df: pd.DataFrame) -> go.Figure:
    """
    สร้าง Histogram แสดงการกระจายตัวของค่าใช้จ่าย
    """
    if df.empty:
        return create_empty_chart("ไม่มีข้อมูลสำหรับ Histogram")
    
    valid_costs = df[df['ค่าใช้จ่าย'] > 0]['ค่าใช้จ่าย']
    
    if valid_costs.empty:
        return create_empty_chart("ไม่มีข้อมูลค่าใช้จ่าย")
    
    fig = px.histogram(
        df[df['ค่าใช้จ่าย'] > 0],
        x='ค่าใช้จ่าย',
        color='คำค้น',
        title="การกระจายตัวของค่าใช้จ่าย",
        nbins=20,
        color_discrete_map={
            'วิศวกรรม ปัญญาประดิษฐ์': '#FF6B6B',
            'วิศวกรรม คอมพิวเตอร์': '#4ECDC4'
        }
    )
    
    fig.update_layout(
        xaxis_title="ค่าใช้จ่าย (บาท)",
        yaxis_title="จำนวนหลักสูตร",
        xaxis=dict(tickformat=","),
        template='plotly_white',
        height=400
    )
    
    return fig

def create_empty_chart(message: str) -> go.Figure:
    """
    สร้างกราฟว่างพร้อมข้อความ
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5, xanchor='center', yanchor='middle',
        showarrow=False, font=dict(size=16, color="gray")
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        template='plotly_white',
        height=400
    )
    return fig