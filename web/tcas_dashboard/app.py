"""
TCAS Tuition Fee Dashboard
Dashboard แสดงค่าใช้จ่ายหลักสูตรวิศวกรรม AI และ Computer จาก TCAS
"""

import streamlit as st
import pandas as pd
from pathlib import Path

# Import components
from components.data_loader import (
    load_tcas_data, get_unique_values, filter_data, 
    get_summary_stats, prepare_chart_data
)
from components.filters import (
    create_main_filters, create_chart_options, display_filter_summary,
    create_advanced_filters, apply_advanced_filters
)
from components.charts import (
    create_main_bar_chart, create_comparison_chart, create_box_plot,
    create_province_chart, create_cost_histogram
)
from utils.helpers import filter_by_search_term, get_top_bottom_records

# Page configuration
st.set_page_config(
    page_title="TCAS Engineering Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .metric-container {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    .filter-section {
        background: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """
    Main application function
    """
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎓 TCAS Tuition Fee Dashboard</h1>
        <h3>ค่าใช้จ่ายหลักสูตรวิศวกรรม AI และ Computer</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    with st.spinner("กำลังโหลดข้อมูล..."):
        df = load_tcas_data()
    
    if df.empty:
        st.error("❌ ไม่สามารถโหลดข้อมูลได้ กรุณาตรวจสอบไฟล์ข้อมูล")
        st.stop()
    
    # Get unique values for filters
    unique_values = get_unique_values(df)
    
    # Sidebar filters
    st.sidebar.title("🎛️ ตัวเลือกการแสดงผล")
    
    # Main filters
    field_filter, province_filter, course_type_filter, cost_range, search_term = create_main_filters(unique_values, df)
    
    # Chart options
    group_by, show_mean_line, max_items = create_chart_options()
    
    # Advanced filters
    advanced_options = create_advanced_filters(df)
    
    # Apply filters
    filtered_df = filter_data(
        df, 
        field_filter=field_filter,
        province_filter=province_filter,
        course_type_filter=course_type_filter,
        cost_range=cost_range
    )
    
    # Apply search
    if search_term:
        filtered_df = filter_by_search_term(filtered_df, search_term)
    
    # Apply advanced filters
    filtered_df = apply_advanced_filters(filtered_df, advanced_options)
    
    # Display filter summary
    st.markdown("### 📊 สรุปข้อมูล")
    display_filter_summary(field_filter, filtered_df, df)
    
    if filtered_df.empty:
        st.warning("⚠️ ไม่พบข้อมูลที่ตรงกับเงื่อนไขที่เลือก กรุณาปรับเปลี่ยน filter")
        return
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 กราฟหลัก", "🔄 เปรียบเทียบ", "📊 สถิติขั้นสูง", 
        "🗺️ ข้อมูลจังหวัด", "📋 ตารางข้อมูล"
    ])
    
    with tab1:
        st.markdown("### 📈 ค่าใช้จ่ายเฉลี่ยต่อปี")
        
        # Main bar chart
        title_suffix = ""
        if field_filter == "AI":
            title_suffix = " - วิศวกรรมปัญญาประดิษฐ์"
        elif field_filter == "Computer":
            title_suffix = " - วิศวกรรมคอมพิวเตอร์"
        
        main_chart = create_main_bar_chart(
            filtered_df, 
            group_by=group_by, 
            show_mean_line=show_mean_line, 
            max_items=max_items,
            title_suffix=title_suffix
        )
        st.plotly_chart(main_chart, use_container_width=True)
        
        # Quick stats
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏆 ค่าใช้จ่ายถูกที่สุด (Top 5)")
            top_expensive, top_cheapest = get_top_bottom_records(filtered_df, n=5)
            if not top_cheapest.empty:
                for idx, row in top_cheapest.iterrows():
                    st.write(f"• **{row['มหาวิทยาลัย']}** - {row['ค่าใช้จ่าย']:,.0f} บาท")
        
        with col2:
            st.markdown("#### 💰 ค่าใช้จ่ายแพงที่สุด (Top 5)")
            if not top_expensive.empty:
                for idx, row in top_expensive.iterrows():
                    st.write(f"• **{row['มหาวิทยาลัย']}** - {row['ค่าใช้จ่าย']:,.0f} บาท")
    
    with tab2:
        st.markdown("### 🔄 เปรียบเทียบ AI vs Computer Engineering")
        
        if field_filter == "All":
            comparison_chart = create_comparison_chart(filtered_df)
            st.plotly_chart(comparison_chart, use_container_width=True)
            
            # Summary stats
            summary_stats = get_summary_stats(filtered_df, field_filter)
            
            if 'ai_stats' in summary_stats and 'computer_stats' in summary_stats:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 🤖 วิศวกรรมปัญญาประดิษฐ์")
                    ai_stats = summary_stats['ai_stats']
                    st.metric("จำนวนหลักสูตร", ai_stats['count'])
                    st.metric("ค่าใช้จ่ายเฉลี่ย", f"{ai_stats['stats']['mean']:,.0f} บาท")
                    st.metric("ช่วงค่าใช้จ่าย", f"{ai_stats['stats']['min']:,.0f} - {ai_stats['stats']['max']:,.0f} บาท")
                
                with col2:
                    st.markdown("#### 💻 วิศวกรรมคอมพิวเตอร์")
                    comp_stats = summary_stats['computer_stats']
                    st.metric("จำนวนหลักสูตร", comp_stats['count'])
                    st.metric("ค่าใช้จ่ายเฉลี่ย", f"{comp_stats['stats']['mean']:,.0f} บาท")
                    st.metric("ช่วงค่าใช้จ่าย", f"{comp_stats['stats']['min']:,.0f} - {comp_stats['stats']['max']:,.0f} บาท")
        else:
            st.info("💡 เลือก 'ทั้งหมด' ใน filter สาขาเพื่อดูการเปรียบเทียบ")
    
    with tab3:
        st.markdown("### 📊 สถิติขั้นสูง")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📦 Box Plot - การกระจายตัว")
            box_plot = create_box_plot(filtered_df)
            st.plotly_chart(box_plot, use_container_width=True)
        
        with col2:
            st.markdown("#### 📊 Histogram - การกระจายตัว")
            histogram = create_cost_histogram(filtered_df)
            st.plotly_chart(histogram, use_container_width=True)
    
    with tab4:
        st.markdown("### 🗺️ ข้อมูลตามจังหวัด")
        
        province_chart = create_province_chart(filtered_df)
        st.plotly_chart(province_chart, use_container_width=True)
        
        # Province summary table
        st.markdown("#### 📋 สรุปข้อมูลตามจังหวัด")
        province_summary = filtered_df.groupby('จังหวัด').agg({
            'ค่าใช้จ่าย': ['count', 'mean', 'min', 'max'],
            'มหาวิทยาลัย': 'nunique'
        }).round(0)
        
        province_summary.columns = ['จำนวนหลักสูตร', 'ค่าใช้จ่ายเฉลี่ย', 'ค่าใช้จ่ายต่ำสุด', 'ค่าใช้จ่ายสูงสุด', 'จำนวนมหาวิทยาลัย']
        province_summary = province_summary.sort_values('ค่าใช้จ่ายเฉลี่ย', ascending=False)
        
        st.dataframe(province_summary, use_container_width=True)
    
    with tab5:
        st.markdown("### 📋 ตารางข้อมูลโดยละเอียด")
        
        # Display options
        col1, col2, col3 = st.columns(3)
        with col1:
            show_columns = st.multiselect(
                "เลือกคอลัมน์ที่ต้องการแสดง:",
                options=filtered_df.columns.tolist(),
                default=['มหาวิทยาลัย', 'คณะ', 'ค่าใช้จ่าย', 'จังหวัด', 'ประเภทหลักสูตร']
            )
        
        with col2:
            rows_per_page = st.selectbox("จำนวนแถวต่อหน้า:", [10, 25, 50, 100], index=1)
        
        with col3:
            download_data = filtered_df.copy()
            csv = download_data.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 ดาวน์โหลด CSV",
                data=csv,
                file_name=f"tcas_data_{field_filter.lower()}.csv",
                mime="text/csv"
            )
        
        # Display table
        if show_columns:
            display_df = filtered_df[show_columns].copy()
            
            # Format currency column
            if 'ค่าใช้จ่าย' in display_df.columns:
                display_df['ค่าใช้จ่าย'] = display_df['ค่าใช้จ่าย'].apply(
                    lambda x: f"{x:,.0f} บาท" if pd.notna(x) and x > 0 else "ไม่ระบุ"
                )
            
            st.dataframe(display_df.head(rows_per_page), use_container_width=True)
            
            if len(filtered_df) > rows_per_page:
                st.info(f"แสดง {rows_per_page} แถวจากทั้งหมด {len(filtered_df)} แถว")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>📊 TCAS Engineering Dashboard | สร้างด้วย Streamlit & Plotly</p>
        <p>ข้อมูลจาก: TCAS (Thailand College Admission System)</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()