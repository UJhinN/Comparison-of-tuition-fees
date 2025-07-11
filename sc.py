import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re
from datetime import datetime
import time

class TCASSimpleScraper:
    def __init__(self):
        self.programs_data = []
        self.base_url = "https://course.mytcas.com"

    async def search_and_collect_all_programs(self, page):
        """ค้นหาและรวบรวมหลักสูตรทั้งหมด - แยกชัดเจน"""
        all_programs = []
        
        # ค้นหาแยกชัดเจน
        search_terms = [
            {
                'term': 'วิศวกรรม คอมพิวเตอร์',
                'exclude_keywords': ['ปัญญาประดิษฐ์', 'AI', 'Artificial Intelligence']
            },
            {
                'term': 'วิศวกรรมปัญญาประดิษฐ์',
                'exclude_keywords': []
            }
        ]
        
        for search_config in search_terms:
            print(f"\n🔍 ค้นหา: {search_config['term']}")
            programs = await self._search_single_term(page, search_config)
            all_programs.extend(programs)
            await asyncio.sleep(2)
        
        # ลบรายการซ้ำ
        unique_programs = []
        seen_urls = set()
        
        for program in all_programs:
            if program['url'] not in seen_urls:
                unique_programs.append(program)
                seen_urls.add(program['url'])
        
        print(f"\n📊 รวมหลักสูตรทั้งหมด: {len(unique_programs)} หลักสูตร")
        return unique_programs

    async def _search_single_term(self, page, search_config):
        """ค้นหาหลักสูตรด้วยการกรองที่ชัดเจน"""
        try:
            search_term = search_config['term']
            exclude_keywords = search_config['exclude_keywords']
            
            # ไปหน้าหลัก
            await page.goto(self.base_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(3000)
            
            # ลองหาช่องค้นหาหลายแบบ
            search_input = None
            search_selectors = [
                'input[placeholder*="ค้นหาข้อมูลหลักสูตร"]',
                'input[placeholder*="ค้นหา"]',
                'input[placeholder*="search"]', 
                'input[type="search"]',
                'input.search-input',
                'input#search',
                'input[name="search"]',
                'input[class*="search"]',
                '.search-box input',
                '#search-input',
                'input'  # สุดท้ายลอง input ทั่วไป
            ]
            
            for selector in search_selectors:
                try:
                    print(f"   🔍 ลองหา selector: {selector}")
                    search_input = await page.wait_for_selector(selector, timeout=3000)
                    if search_input:
                        # ตรวจสอบว่า input นี้สามารถพิมพ์ได้หรือไม่
                        is_visible = await search_input.is_visible()
                        is_enabled = await search_input.is_enabled()
                        if is_visible and is_enabled:
                            print(f"   ✅ พบช่องค้นหา: {selector}")
                            break
                        else:
                            search_input = None
                except:
                    continue
            
            if not search_input:
                print(f"   ❌ ไม่พบช่องค้นหาที่ใช้งานได้")
                # ลองดูหน้าเว็บและหา element ที่เป็นไปได้
                page_content = await page.content()
                print("   🔍 ลองตรวจสอบหน้าเว็บ...")
                
                # ลองคลิกปุ่มค้นหาหรือเมนูก่อน
                search_buttons = [
                    'button[class*="search"]',
                    'a[href*="search"]',
                    '.search-btn',
                    '[data-search]',
                    'button:has-text("ค้นหา")',
                    'a:has-text("ค้นหา")'
                ]
                
                for btn_selector in search_buttons:
                    try:
                        btn = await page.wait_for_selector(btn_selector, timeout=2000)
                        if btn:
                            await btn.click()
                            await page.wait_for_timeout(2000)
                            # ลองหา input อีกครั้ง
                            search_input = await page.wait_for_selector('input[type="search"], input[placeholder*="ค้นหา"]', timeout=3000)
                            if search_input:
                                print(f"   ✅ พบช่องค้นหาหลังคลิกปุ่ม: {btn_selector}")
                                break
                    except:
                        continue
            
            if not search_input:
                print(f"   ❌ ไม่สามารถหาช่องค้นหาได้ กำลังข้าม...")
                return []
            
            # พิมพ์คำค้นหา
            await search_input.click()
            await page.wait_for_timeout(500)
            await page.keyboard.press('Control+a')
            await page.keyboard.type(search_term)
            await page.wait_for_timeout(500)
            await page.keyboard.press('Enter')
            
            # รอผลการค้นหา
            await page.wait_for_timeout(4000)
            
            # ดึงลิงก์ทั้งหมด
            programs = await self._extract_filtered_program_links(page, search_term, exclude_keywords)
            print(f"   พบ {len(programs)} หลักสูตร")
            
            return programs
            
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการค้นหา {search_term}: {str(e)}")
            return []

    async def _extract_filtered_program_links(self, page, search_term, exclude_keywords):
        """ดึงลิงก์หลักสูตรพร้อมกรองคำที่ไม่ต้องการ"""
        programs = []
        
        try:
            # รอให้โหลดเสร็จ
            await page.wait_for_timeout(2000)
            
            # หาลิงก์ทั้งหมดที่เป็น programs
            links = await page.query_selector_all('a[href*="/programs/"]')
            
            for link in links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    
                    if href and text and len(text.strip()) > 10:
                        text_lower = text.lower()
                        should_exclude = False
                        
                        # กรองสำหรับ "วิศวกรรม คอมพิวเตอร์"
                        if search_term == "วิศวกรรม คอมพิวเตอร์":
                            # รวมหลักสูตรทั้งหมดที่ไม่ใช่ปัญญาประดิษฐ์
                            if any(ai_word in text_lower for ai_word in ["ปัญญาประดิษฐ์", "artificial intelligence"]):
                                should_exclude = True
                                print(f"      ❌ ตัดออก (AI): {text.strip()[:60]}...")
                            else:
                                # รวมหลักสูตรทั้งหมดที่ไม่ใช่ AI
                                pass
                        
                        # กรองสำหรับ "วิศวกรรมปัญญาประดิษฐ์"  
                        elif search_term == "วิศวกรรมปัญญาประดิษฐ์":
                            # เอาเฉพาะที่มีคำเกี่ยวกับ AI
                            if not any(ai_word in text_lower for ai_word in ["ปัญญาประดิษฐ์", "artificial intelligence", "ai", "intelligent"]):
                                should_exclude = True
                        
                        # กรองคำที่ไม่ต้องการเพิ่มเติม
                        for exclude_word in exclude_keywords:
                            if exclude_word.lower() in text_lower:
                                should_exclude = True
                                break
                        
                        if not should_exclude:
                            full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                            programs.append({
                                'url': full_url,
                                'title': text.strip(),
                                'search_term': search_term
                            })
                            print(f"      ✅ รวม: {text.strip()[:60]}...")
                        else:
                            print(f"      ❌ ตัดออก: {text.strip()[:60]}...")
                            
                except:
                    continue
                    
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการดึงลิงก์: {str(e)}")
        
        return programs

    async def scrape_program_basic_info(self, page, program_info):
        """ดึงข้อมูลพื้นฐานเท่านั้น: ชื่อ มหาลัย ค่าใช้จ่าย"""
        url = program_info['url']
        
        try:
            print(f"📄 กำลังดึง: {program_info['title'][:50]}...")
            
            # เข้าหน้าหลักสูตร
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)
            
            # ดึงข้อความทั้งหมด
            page_text = await page.inner_text('body')
            
            # สร้างข้อมูลพื้นฐาน
            data = {
                'ชื่อหลักสูตร': program_info['title'],
                'มหาวิทยาลัย': '',
                'วิทยาเขต': '',
                'ค่าใช้จ่าย (บาท/ภาค)': 0,
                'ค่าใช้จ่าย (ข้อความเต็ม)': '',
                'URL': url,
                'ประเภทหลักสูตร': program_info['search_term']
            }
            
            # ดึงชื่อมหาวิทยาลัย
            data['มหาวิทยาลัย'] = self._find_university_name(page_text)
            
            # ดึงวิทยาเขต
            data['วิทยาเขต'] = self._find_campus_name(page_text)
            
            # ดึงค่าใช้จ่าย
            tuition_info = self._find_tuition_cost(page_text)
            data['ค่าใช้จ่าย (บาท/ภาค)'] = tuition_info['amount']
            data['ค่าใช้จ่าย (ข้อความเต็ม)'] = tuition_info['text']
            
            # แสดงประเภทหลักสูตร
            course_type = "💻" if "คอมพิวเตอร์" in program_info['search_term'] else "🤖"
            
            if data['ค่าใช้จ่าย (บาท/ภาค)'] > 0:
                campus_info = f" ({data['วิทยาเขต']})" if data['วิทยาเขต'] and data['วิทยาเขต'] != 'ไม่ระบุ' else ""
                print(f"   ✅ {course_type} {data['มหาวิทยาลัย'][:25]}{campus_info} - {data['ค่าใช้จ่าย (บาท/ภาค)']:,} บาท")
                return data
            else:
                campus_info = f" ({data['วิทยาเขต']})" if data['วิทยาเขต'] and data['วิทยาเขต'] != 'ไม่ระบุ' else ""
                print(f"   ⚠️ {course_type} {data['มหาวิทยาลัย'][:25]}{campus_info} - ไม่พบค่าใช้จ่าย")
                return data  # ส่งคืนข้อมูลแม้ไม่มีค่าใช้จ่าย
                
        except Exception as e:
            print(f"   ❌ ข้อผิดพลาด: {str(e)}")
            return None

    def _find_university_name(self, text):
        """หาชื่อมหาวิทยาลัย"""
        patterns = [
            r'มหาวิทยาลัย[^\n\r]{1,80}',
            r'สถาบัน[^\n\r]{1,50}มหาวิทยาลัย',
            r'สถาบันเทคโนโลยี[^\n\r]{1,50}',
            r'จุฬาลงกรณ์มหาวิทยาลัย',
            r'มหาวิทยาลัยเกษตรศาสตร์[^\n\r]{0,20}',
            r'มหาวิทยาลัยเทคโนโลยีพระจอมเกล้า[^\n\r]{1,50}',
            r'มหาวิทยาลัยสงขลานครินทร์[^\n\r]{0,20}',
            r'มหาวิทยาลัยมหิดล[^\n\r]{0,20}',
            r'มหาวิทยาลัยธรรมศาสตร์[^\n\r]{0,20}',
            r'มหาวิทยาลัยเชียงใหม่[^\n\r]{0,20}',
            r'มหาวิทยาลัยขอนแก่น[^\n\r]{0,20}'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(0).strip()
                if len(name) < 100:
                    return name
        
    def _find_campus_name(self, text):
        """หาชื่อวิทยาเขต"""
        patterns = [
            # แพทเทิร์นเฉพาะสำหรับวิทยาเขต
            r'วิทยาเขต[^\n\r]{1,50}',
            r'campus[^\n\r]{1,30}',
            
            # แพทเทิร์นเฉพาะของแต่ละมหาวิทยาลัย
            r'วิทยาเขตรังสิต',
            r'วิทยาเขตศาลายา', 
            r'วิทยาเขตหาดใหญ่',
            r'วิทยาเขตปัตตานี',
            r'วิทยาเขตสุราษฎร์ธานี',
            r'วิทยาเขตภูเก็ต',
            r'วิทยาเขตกรุงเทพฯ',
            r'วิทยาเขตเชียงใหม่',
            r'วิทยาเขตขอนแก่น',
            r'วิทยาเขตอุบลราชธานี',
            r'วิทยาเขตนครราชสีมา',
            r'วิทยาเขตสกลนคร',
            r'วิทยาเขตกำแพงแสน',
            r'วิทยาเขตจันทบุรี',
            r'วิทยาเขตปราจีนบุรี',
            r'วิทยาเขตสระแก้ว',
            r'วิทยาเขตราชบุรี',
            r'วิทยาเขตเพชรบุรี',
            r'วิทยาเขตนครปฐม',
            r'วิทยาเขตลำปาง',
            r'วิทยาเขตพิษณุโลก',
            r'วิทยาเขตอุดรธานี',
            r'วิทยาเขตยะลา',
            r'วิทยาเขตสงขลา',
            r'วิทยาเขตตรัง',
            r'วิทยาเขตชุมพร',
            
            # ชื่อเมืองหลังคำว่า "ที่ตั้ง" หรือ "สถานที่"
            r'ที่ตั้ง[^\n\r]*?([ก-๙]+)[^\n\r]{0,20}',
            r'สถานที่[^\n\r]*?([ก-๙]+)[^\n\r]{0,20}',
            
            # แพทเทิร์นทั่วไป
            r'(ตั้งอยู่ที่|อยู่ที่|ณ\s+)([ก-๙\s]{3,30})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                campus = match.group(0).strip()
                # ทำความสะอาดข้อความ
                campus = re.sub(r'^(วิทยาเขต|campus|ที่ตั้ง|สถานที่|ตั้งอยู่ที่|อยู่ที่|ณ\s*)', '', campus, flags=re.IGNORECASE)
                campus = campus.strip()
                
                # กรองข้อความที่เหมาะสม
                if len(campus) > 2 and len(campus) < 50:
                    # ตัดคำที่ไม่จำเป็นออก
                    campus = re.sub(r'(จังหวัด|อำเภอ|ตำบล|แขวง|เขต)', '', campus)
                    campus = campus.strip()
                    if campus:
                        return campus
        
        # ถ้าไม่เจอ ลองหาจากชื่อมหาวิทยาลัยเอง
        uni_campus_patterns = [
            r'มหาวิทยาลัยเทคโนโลยีพระจอมเกล้า[^\n\r]*?(พระนคร|ธนบุรี|พระนครเหนือ|เจ้าคุณทหารลาดกระบัง)',
            r'มหาวิทยาลัยราชภัฏ[^\n\r]*?([ก-๙]{3,20})',
            r'มหาวิทยาลัยเทคโนโลยีราชมงคล[^\n\r]*?([ก-๙]{3,20})',
        ]
        
        for pattern in uni_campus_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) > 0:
                    campus = match.group(1).strip()
                    if len(campus) > 2 and len(campus) < 30:
                        return campus
        
        return 'ไม่ระบุ'

    def _find_tuition_cost(self, text):
        """หาค่าใช้จ่าย - หลายแพทเทิร์น"""
        
        # แพทเทิร์นการค้นหาค่าใช้จ่าย
        patterns = [
            # แพทเทิร์นที่เฉพาะเจาะจง
            r'ค่าใช้จ่าย[^\d]*([0-9,]+)[^\d]*บาท',
            r'อัตราค่าเล่าเรียน[^\d]*([0-9,]+)[^\d]*บาท',
            r'ค่าเล่าเรียน[^\d]*([0-9,]+)[^\d]*บาท',
            r'ค่าธรรมเนียมการศึกษา[^\d]*([0-9,]+)[^\d]*บาท',
            
            # แพทเทิร์นตามรูปแบบในภาพ
            r'อัตราค่าเล่าเรียน\s*([0-9,]+)\s*บาท[^\d]*ภาค',
            r'([0-9,]+)\s*บาท[^\d]*ภาคการศึกษา',
            r'([0-9,]+)\s*บาท[^\d]*ต่อภาค',
            r'([0-9,]+)\.-[^\d]*ภาค',
            
            # แพทเทิร์นกว้างๆ
            r'([0-9,]{4,})\s*บาท',  # ตัวเลข 4 หลักขึ้นไป + บาท
            r'([1-9][0-9]{3,5})\s*บาท',  # 4-6 หลัก
            
            # สำหรับกรณีพิเศษ
            r'เรียน\s*([0-9,]+)\s*บาท',
            r'ค่า[^\d]*([0-9,]+)\s*บาท',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # ทำความสะอาดตัวเลข
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1] if len(match) > 1 else ''
                
                clean_number = str(match).replace(',', '')
                if clean_number.isdigit():
                    amount = int(clean_number)
                    # กรองเฉพาะค่าที่สมเหตุสมผล
                    if 3000 <= amount <= 200000:
                        return {
                            'amount': amount,
                            'text': f"{amount:,} บาท/ภาค"
                        }
        
        # ถ้าไม่เจอ ลองหาจาก URL ที่มี TUITION
        url_pattern = r'(https?://[^\s]+(?:tuition|fee)[^\s]*)'
        url_match = re.search(url_pattern, text, re.IGNORECASE)
        if url_match:
            return {
                'amount': 0,
                'text': f"ดูที่: {url_match.group(1)}"
            }
        
        return {'amount': 0, 'text': 'ไม่ระบุ'}

    async def run_simple_scraping(self):
        """เรียกใช้การ scraping แบบง่าย"""
        print("🚀 เริ่ม TCAS Simple Scraper - แยกวิศวกรรมคอมพิวเตอร์และปัญญาประดิษฐ์")
        print("="*70)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                locale='th-TH',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            try:
                # ขั้นตอนที่ 1: รวบรวมลิงก์ทั้งหมด
                all_programs = await self.search_and_collect_all_programs(page)
                
                if not all_programs:
                    print("❌ ไม่พบหลักสูตรใดๆ")
                    return
                
                # ขั้นตอนที่ 2: ดึงข้อมูลแต่ละหลักสูตร
                print(f"\n📋 เริ่มดึงข้อมูล {len(all_programs)} หลักสูตร...")
                
                for i, program_info in enumerate(all_programs, 1):
                    print(f"\n[{i:2d}/{len(all_programs)}]", end=" ")
                    
                    data = await self.scrape_program_basic_info(page, program_info)
                    if data:
                        self.programs_data.append(data)
                    
                    # หน่วงเวลา
                    await asyncio.sleep(1.5)
                
            finally:
                await browser.close()
        
        return len(self.programs_data)

    def save_to_excel(self, filename='TCAS_วิศวกรรม_แยกประเภท'):
        """บันทึกเป็น Excel แยกตามประเภทหลักสูตร"""
        if not self.programs_data:
            print("❌ ไม่มีข้อมูลที่จะบันทึก")
            return
        
        # สร้าง DataFrame
        df = pd.DataFrame(self.programs_data)
        
        print(f"\n🔍 Debug: ข้อมูลทั้งหมดใน DataFrame = {len(df)} รายการ")
        print(f"🔍 Debug: ประเภทหลักสูตรที่มี = {df['ประเภทหลักสูตร'].value_counts().to_dict()}")
        
        # แยกข้อมูลตามประเภท
        df_computer = df[df['ประเภทหลักสูตร'] == 'วิศวกรรม คอมพิวเตอร์'].copy()
        df_ai = df[df['ประเภทหลักสูตร'] == 'วิศวกรรมปัญญาประดิษฐ์'].copy()
        
        print(f"🔍 Debug: หลักสูตรคอมพิวเตอร์ = {len(df_computer)} รายการ")
        print(f"🔍 Debug: หลักสูตรปัญญาประดิษฐ์ = {len(df_ai)} รายการ")
        
        # รวมและเรียงลำดับ (คอมก่อน แล้วปัญญาประดิษฐ์)
        df_final = pd.concat([df_computer, df_ai], ignore_index=True)
        
        # เรียงตามค่าใช้จ่าย
        df_final = df_final.sort_values(['ประเภทหลักสูตร', 'ค่าใช้จ่าย (บาท/ภาค)'], ascending=[True, True])
        
        # สร้างชื่อไฟล์
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_filename = f"{filename}_{timestamp}.xlsx"
        
        # บันทึกเป็น Excel
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            # Sheet รวม
            df_final.to_excel(writer, sheet_name='รวมทั้งหมด', index=False)
            
            # Sheet แยก
            if len(df_computer) > 0:
                df_computer.to_excel(writer, sheet_name='💻 วิศวกรรมคอมพิวเตอร์', index=False)
                print(f"✅ สร้าง Sheet วิศวกรรมคอมพิวเตอร์: {len(df_computer)} รายการ")
            else:
                print("⚠️ ไม่มีข้อมูลวิศวกรรมคอมพิวเตอร์")
            
            if len(df_ai) > 0:
                df_ai.to_excel(writer, sheet_name='🤖 วิศวกรรมปัญญาประดิษฐ์', index=False)
                print(f"✅ สร้าง Sheet วิศวกรรมปัญญาประดิษฐ์: {len(df_ai)} รายการ")
            else:
                print("⚠️ ไม่มีข้อมูลวิศวกรรมปัญญาประดิษฐ์")
            
            # ปรับความกว้างคอลัมน์
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                worksheet.column_dimensions['A'].width = 50  # ชื่อหลักสูตร
                worksheet.column_dimensions['B'].width = 35  # มหาวิทยาลัย
                worksheet.column_dimensions['C'].width = 20  # วิทยาเขต
                worksheet.column_dimensions['D'].width = 15  # ค่าใช้จ่าย (ตัวเลข)
                worksheet.column_dimensions['E'].width = 25  # ค่าใช้จ่าย (ข้อความ)
                worksheet.column_dimensions['F'].width = 60  # URL
                worksheet.column_dimensions['G'].width = 25  # ประเภทหลักสูตร
        
        print(f"\n💾 บันทึกเรียบร้อย: {excel_filename}")
        self._show_summary(df_final)
        
        return df_final

    def _show_summary(self, df):
        """แสดงสรุปผลลัพธ์"""
        print("\n" + "="*70)
        print("📊 สรุปผลการดึงข้อมูล")
        print("="*70)
        
        total = len(df)
        with_tuition = len(df[df['ค่าใช้จ่าย (บาท/ภาค)'] > 0])
        
        print(f"🎓 จำนวนหลักสูตรทั้งหมด: {total}")
        print(f"💰 มีข้อมูลค่าใช้จ่าย: {with_tuition}")
        print(f"❓ ไม่มีข้อมูลค่าใช้จ่าย: {total - with_tuition}")
        
        if with_tuition > 0:
            valid_costs = df[df['ค่าใช้จ่าย (บาท/ภาค)'] > 0]['ค่าใช้จ่าย (บาท/ภาค)']
            print(f"\n💰 สถิติค่าใช้จ่าย:")
            print(f"   ต่ำสุด: {valid_costs.min():,} บาท")
            print(f"   สูงสุด: {valid_costs.max():,} บาท")
            print(f"   เฉลี่ย: {valid_costs.mean():,.0f} บาท")
        
        # แสดงตามประเภทหลักสูตร
        type_summary = df['ประเภทหลักสูตร'].value_counts()
        print(f"\n🔍 แยกตามประเภทหลักสูตร:")
        for course_type, count in type_summary.items():
            emoji = "💻" if "คอมพิวเตอร์" in course_type else "🤖"
            print(f"   {emoji} {course_type}: {count} หลักสูตร")
            
            # แสดงสถิติย่อยของแต่ละประเภท
            subset = df[df['ประเภทหลักสูตร'] == course_type]
            with_cost = subset[subset['ค่าใช้จ่าย (บาท/ภาค)'] > 0]
            if len(with_cost) > 0:
                print(f"      💰 มีค่าใช้จ่าย: {len(with_cost)} หลักสูตร")
                print(f"      📊 ช่วงค่าใช้จ่าย: {with_cost['ค่าใช้จ่าย (บาท/ภาค)'].min():,} - {with_cost['ค่าใช้จ่าย (บาท/ภาค)'].max():,} บาท")

async def main():
    """ฟังก์ชันหลัก"""
    print("🎯 TCAS Simple Scraper - แยกประเภทหลักสูตรชัดเจน")
    print("📋 เป้าหมาย: ชื่อหลักสูตร + มหาวิทยาลัย + วิทยาเขต + ค่าใช้จ่าย")
    print("🔍 ค้นหา:")
    print("   💻 วิศวกรรม คอมพิวเตอร์ (ไม่รวมปัญญาประดิษฐ์)")
    print("   🤖 วิศวกรรมปัญญาประดิษฐ์ (เฉพาะ AI)")
    print("="*70)
    
    scraper = TCASSimpleScraper()
    
    try:
        # เริ่มการ scraping
        found_count = await scraper.run_simple_scraping()
        
        if found_count > 0:
            print(f"\n🎉 เสร็จสิ้น! ดึงข้อมูลได้ {found_count} หลักสูตร")
            
            # บันทึกเป็น Excel
            scraper.save_to_excel()
            
            print("\n✅ ไฟล์ Excel พร้อมใช้งาน!")
            print("📁 ไฟล์จะแยก Sheet เป็น:")
            print("   📄 รวมทั้งหมด")
            print("   💻 วิศวกรรมคอมพิวเตอร์")
            print("   🤖 วิศวกรรมปัญญาประดิษฐ์")
            
        else:
            print("\n❌ ไม่มีข้อมูลที่ดึงได้")
    
    except KeyboardInterrupt:
        print("\n⏹️ หยุดการทำงานโดยผู้ใช้")
    
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())