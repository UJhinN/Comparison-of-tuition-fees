# **241-353 AI ECOSYSTEM MODULE**
## **Thai University Tuition Fee Dashboard Computer and AI Engineering** ##

## **Project Overview**
This interactive web application leverages Streamlit technology to create a comprehensive analytical platform for exploring tuition fee structures across Thai universities, specifically focusing on Computer Engineering and Artificial Intelligence programs. By transforming raw data from the TCAS into meaningful visualizations, this dashboard empowers prospective students to make data-driven educational investment decisions.
The application features a multi-layered analysis approach, combining statistical with geographical distribution patterns to provide a 360-degree view of higher education costs in Thailand's technology sector. Through dynamic filtering capabilities and real-time chart updates, users can customize their exploration based on budget constraints, geographic preferences, and academic program types.


## **Data Extraction & Processing**
1. **Scrape course data** (university, faculty, program, type, link and tuition) using web scraping tools from MyTCAS.com.
2. **Clean,Remove,Add provinces** the dataset.
3. **Filter** only programs related to Computer and AI Engineering.
4. **Extract and normalize tuition fee** information (annual fees in Thai Baht).
5. **Categorize** course types (International, Thai Regular, Thai Special).
6. **Assign provinces** based on university locations across Thailand.


Final data is exported to `data/improved_tcas_data_with_province_updated.xlsx` for visualization.

## **Dashboard Features**

### **1. Main Charts (กราฟหลัก)**
* Displays interactive bar charts showing average tuition fees per university/faculty/province.
* Users can filter by program type (All/AI/Computer), provinces, course types, and tuition fee range.
* Includes mean line overlay for comparison reference.
* Shows top 5 cheapest and most expensive programs.
* Configurable grouping options: by university, faculty, or province.

### **2. Comparison Analysis (เปรียบเทียบ)**
* Side-by-side comparison between AI and Computer Engineering programs.
* Statistical breakdown including count, average, minimum, and maximum tuition fees.
* Visual charts showing differences in cost distribution between fields.
* Summary metrics for informed decision-making.

### **3. Advanced Statistics (สถิติขั้นสูง)**
* **Box Plot**: Shows tuition fee distribution and outliers by program type.
* **Histogram**: Displays frequency distribution of tuition costs.
* Statistical analysis tools for deeper insights into pricing patterns.

### **4. Province Data (ข้อมูลจังหวัด)**
* Interactive visualization of program availability by province.
* Charts showing number of programs available in each region.
* Summary table with statistics grouped by province.
* Geographic distribution analysis of educational opportunities.

### **5. Data Table (ตารางข้อมูล)**
* Comprehensive searchable table with all program details.
* Sortable columns for easy data exploration.
* Customizable column display options.
* Export functionality to download filtered data as CSV.
* Advanced filtering and search capabilities.

## **Interactive Filters**
* **Program Field**: All, AI (Artificial Intelligence), Computer Engineering
* **Province Selection**: Multi-select dropdown for 23 provinces
* **Course Type**: International, Thai Regular, Thai Special programs
* **Tuition Range**: Slider for budget-based filtering
* **Search Function**: Text search across universities, faculties, and programs
* **Advanced Options**: Sorting, data hiding options, and display preferences

## **Setup & Installation**
Ensure that you have Python installed on your system before proceeding.

1. Clone the repository:
```bash
git clone <https://github.com/UJhinN/Comparison-of-tuition-fees.git>
```

2. Navigate to the project directory:
```bash
cd web/tcas_dashboard
```

3. Create a virtual environment:
```bash
python -m venv venv
```

4. Activate the virtual environment:
   * On Windows:
```bash
venv\Scripts\activate
```
   * On macOS/Linux:
```bash
source venv/bin/activate
```

5. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## **Running and Viewing the Application**
Ensure you're inside the project directory and the virtual environment is activated.

1. Run the application:
```bash
streamlit run app.py
```

2. Open your browser and go to:
```
http://localhost:8501
```

## **Project Structure**
```
web/tcas_dashboard/
├── app.py                 # Main Streamlit application
├── data/
│   └── improved_tcas_data_with_province_updated.xlsx
├── components/
│   ├── __init__.py
│   ├── data_loader.py     # Data loading and processing functions
│   ├── filters.py         # UI filters and control components
│   └── charts.py          # Chart creation and visualization functions
├── utils/
│   ├── __init__.py
│   └── helpers.py         # Helper functions and utilities
├── requirements.txt       # Project dependencies
├── .gitignore            # Git ignore file
└── README.md             # Project documentation
```

## **Technologies Used**
- **Frontend Framework**: Streamlit
- **Data Visualization**: Plotly, Plotly Express
- **Data Processing**: Pandas, NumPy
- **File Handling**: OpenPyXL for Excel file operations
- **UI Enhancement**: Streamlit-aggrid, Streamlit-option-menu

## **Dataset Information**
- **Total Programs**: 74 engineering programs
- **Universities**: 48 institutions across Thailand
- **Provinces**: 23 provinces represented
- **Program Types**: 2 main fields (AI Engineering, Computer Engineering)
- **Tuition Range**: 15,000 - 200,000 THB per year
- **Course Categories**: International, Thai Regular, Thai Special

## **Key Features**
- **Real-time Filtering**: Instant chart updates based on user selections
- **Responsive Design**: Works on desktop and mobile devices
- **Interactive Visualizations**: Hover effects and clickable elements
- **Data Export**: Download filtered results for offline analysis
- **Multi-language Interface**: Thai language support with English technical terms
- **Statistical Analysis**: Built-in statistical calculations and insights

## **Educational Impact**
This dashboard serves as a valuable tool for:
- **High School Students**: Making informed decisions about university programs
- **Parents**: Understanding financial commitments for their children's education
- **Educational Counselors**: Providing data-driven guidance to students
- **Policy Makers**: Analyzing trends in engineering education costs
- **Universities**: Benchmarking their tuition fees against competitors

## **Future Enhancements**
- Integration with real-time TCAS data updates
- Addition of employment rate and salary data
- Mobile application development
- Multi-language support (English interface)
- Predictive modeling for future tuition trends
- Social media sharing capabilities
- User preference saving and recommendations

## **Contributing**
Contributions are welcome! Please feel free to submit issues, fork the repository, and create pull requests for any improvements.

## **License**
This project is developed for educational purposes as part of the AI Ecosystem Module coursework.

---
