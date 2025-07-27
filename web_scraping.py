import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime

class ImprovedTCASScraper:
    def __init__(self):
        self.programs_data = []
        self.base_url = "https://course.mytcas.com"

    async def search_and_collect_programs(self, page, keyword):
        """ค้นหาและรวบรวมหลักสูตร - ใช้วิธีที่เฉพาะเจาะจง"""
        programs = []
        
        try:
            print(f"\n🔍 ค้นหา: {keyword}")
            
            # ไปหน้าหลัก
            await page.goto(self.base_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)
            
            # หาช่องค้นหาที่เฉพาะเจาะจง ✅
            search_input = await page.wait_for_selector(
                "input[placeholder='พิมพ์ชื่อมหาวิทยาลัย คณะ หรือหลักสูตร']", 
                timeout=10000
            )
            
            if not search_input:
                print("❌ ไม่พบช่องค้นหา")
                return []
            
            # ค้นหา
            await search_input.fill("")
            await page.wait_for_timeout(500)
            await search_input.fill(keyword)
            await search_input.press("Enter")
            await page.wait_for_timeout(3000)
            
            # หาผลลัพธ์ที่เฉพาะเจาะจง ✅
            results = await page.query_selector_all(".t-programs > li")
            print(f"  เจอ {len(results)} รายการ")
            
            for i, li in enumerate(results):
                try:
                    # ดึงข้อมูลพื้นฐาน
                    title_full = await li.inner_text()
                    link_element = await li.query_selector("a")
                    if not link_element:
                        continue
                        
                    link = await link_element.get_attribute("href")
                    full_link = link if link.startswith("http") else f"{self.base_url}{link}"
                    
                    # แยกข้อมูลจาก title
                    lines = title_full.strip().splitlines()
                    faculty = lines[1].strip().replace('›', ' > ') if len(lines) >= 2 else ""
                    university = lines[2].strip() if len(lines) >= 3 else ""
                    
                    programs.append({
                        'keyword': keyword,
                        'university': university,
                        'faculty': faculty,
                        'title_full': title_full,
                        'url': full_link
                    })
                    
                except Exception as e:
                    print(f"  ❌ ข้อผิดพลาดในรายการที่ {i+1}: {str(e)}")
                    continue
            
            return programs
            
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการค้นหา {keyword}: {str(e)}")
            return []

    async def scrape_program_details(self, page, program_info):
        """ดึงข้อมูลรายละเอียดจากหน้าของแต่ละโปรแกรม ✅"""
        url = program_info['url']
        
        try:
            print(f"📄 กำลังดึง: {program_info['title_full'].splitlines()[0][:50]}...")
            
            # เข้าหน้ารายละเอียด
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)
            
            # สร้างข้อมูลพื้นฐาน
            data = {
                'สาขา': ''.join(program_info['keyword'].split()),
                'มหาวิทยาลัย': program_info['university'],
                'คณะ': program_info['faculty'],
                'หลักสูตร': '',
                'ประเภทหลักสูตร': '',
                'ลิงก์': url,
                'ค่าใช้จ่าย': 'ไม่พบข้อมูล'
            }

            
            # ดึงชื่อหลักสูตร ✅
            program_name_element = await page.query_selector("dt:has-text('ชื่อหลักสูตร') + dd")
            if program_name_element:
                data['หลักสูตร'] = await program_name_element.inner_text()
            
            # ดึงประเภทหลักสูตร ✅
            program_type_element = await page.query_selector("dt:has-text('ประเภทหลักสูตร') + dd")
            if program_type_element:
                data['ประเภทหลักสูตร'] = await program_type_element.inner_text()
            
            # ดึงค่าใช้จ่าย ✅
            fee_element = await page.query_selector("dt:has-text('ค่าใช้จ่าย') + dd")
            if fee_element:
                data['ค่าใช้จ่าย'] = await fee_element.inner_text()
            
            print(f"   ✅ {data['มหาวิทยาลัย'][:25]} - {data['ค่าใช้จ่าย'][:30]}...")
            return data
            
        except Exception as e:
            print(f"   ❌ ข้อผิดพลาด: {str(e)}")
            return None

    async def run_scraping(self):
        """เรียกใช้การ scraping"""
        print("🚀 เริ่ม Improved TCAS Scraper")
        print("="*70)
        
        keywords = ["วิศวกรรม ปัญญาประดิษฐ์", "วิศวกรรม คอมพิวเตอร์"]
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                locale='th-TH',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            try:
                all_programs = []
                
                # ขั้นตอนที่ 1: รวบรวมลิงก์ทั้งหมด
                for keyword in keywords:
                    programs = await self.search_and_collect_programs(page, keyword)
                    all_programs.extend(programs)
                    await asyncio.sleep(2)
                
                if not all_programs:
                    print("❌ ไม่พบหลักสูตรใดๆ")
                    return 0
                
                print(f"\n📋 เริ่มดึงข้อมูลรายละเอียด {len(all_programs)} หลักสูตร...")
                
                # ขั้นตอนที่ 2: ดึงข้อมูลรายละเอียดแต่ละหลักสูตร ✅
                for i, program_info in enumerate(all_programs, 1):
                    print(f"\n[{i:2d}/{len(all_programs)}]", end=" ")
                    
                    data = await self.scrape_program_details(page, program_info)
                    if data:
                        self.programs_data.append(data)
                    
                    # หน่วงเวลา
                    await asyncio.sleep(1.5)
                
            finally:
                await browser.close()
        
        return len(self.programs_data)

    def save_to_excel(self, filename='tcas_data'):
        """บันทึกเป็น Excel"""
        if not self.programs_data:
            print("❌ ไม่มีข้อมูลที่จะบันทึก")
            return
        
        df = pd.DataFrame(self.programs_data)
        filename = f"{filename}.xlsx"
        
        # บันทึกเป็น Excel
        df.to_excel(filename, index=False)
        
        print(f"\n💾 บันทึกเรียบร้อย: {filename}")
        print(f"📊 จำนวนข้อมูล: {len(df)} รายการ")
        
        # แสดงสรุป
        if len(df) > 0:
            keyword_counts = df['คำค้น'].value_counts()
            print(f"\n📈 สรุปตามคำค้น:")
            for keyword, count in keyword_counts.items():
                emoji = "🤖" if "ปัญญาประดิษฐ์" in keyword else "💻"
                print(f"   {emoji} {keyword}: {count} รายการ")
            
            # นับที่มีค่าใช้จ่าย
            with_fee = len(df[df['ค่าใช้จ่าย'] != 'ไม่พบข้อมูล'])
            print(f"\n💰 มีข้อมูลค่าใช้จ่าย: {with_fee}/{len(df)} รายการ")
        
        return df

async def main():
    """ฟังก์ชันหลัก"""
    print("🎯 Improved TCAS Scraper")
    print("🔧 ปรับปรุงจากปัญหาของ code เดิม:")
    print("   ✅ ใช้ selector ที่เฉพาะเจาะจง")
    print("   ✅ เข้าไปดึงข้อมูลรายละเอียดจากหน้าแต่ละโปรแกรม")
    print("   ✅ ใช้โครงสร้าง HTML แทน regex")
    print("="*70)
    
    scraper = ImprovedTCASScraper()
    
    try:
        # เริ่มการ scraping
        found_count = await scraper.run_scraping()
        
        if found_count > 0:
            print(f"\n🎉 เสร็จสิ้น! ดึงข้อมูลได้ {found_count} หลักสูตร")
            scraper.save_to_excel()
            print("\n✅ ไฟล์ Excel พร้อมใช้งาน!")
        else:
            print("\n❌ ไม่มีข้อมูลที่ดึงได้")
    
    except KeyboardInterrupt:
        print("\n⏹️ หยุดการทำงานโดยผู้ใช้")
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())