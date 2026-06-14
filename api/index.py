import os
import requests
from google import genai
from google.genai import types
from http.server import BaseHTTPRequestHandler

# 🔒 ดึงคีย์ความลับ 2 ตัวนี้พอ (ตัวตั้งเวลา RUN_EVERY_X_HOURS ลบออกได้เลย)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

if not GEMINI_API_KEY or not DISCORD_WEBHOOK_URL:
    print("❌ เออร์เรอร์: ตรวจไม่พบ GEMINI_API_KEY หรือ DISCORD_WEBHOOK_URL ในระบบ!")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

def run_agent_workflow():
    # ... (ท่อนด่าน 1, 2, 3 ของคุณเหมือนเดิม) ...
    print("\n⚡ [1/4] กำลังให้ Gemini ค้นหาข่าวจริงล่าสุดจาก Google Search...")
    prompt_search = "จงค้นหาข่าวล่าสุดและสถานการณ์การลงทุนของหุ้นกู้กำลังออกใหม่ ในช่วง 1-2 สัปดาห์ที่ผ่านมา สรุปประเด็นสำคัญและตัวเลขราคาจริงมาเป็นข้อๆ"
    
    # ใช้ gemini-2.5-flash ในการค้นข่าว (ฟรีและได้โควตาเยอะกว่า)
    news_response = client.models.generate_content(
        model='gemini-2.5-flash', 
        contents=prompt_search,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())] 
        )
    )
    real_market_data = news_response.text

    print("⚡ [2/4] ข้อมูลข่าวจริงมาแล้ว กำลังส่งให้ Agent Bull และ Bear ดีเบตกัน...")
    prompt_debate = f"""
    คุณคือทีมวิเคราะห์กลยุทธ์ โปรดวิเคราะห์ข้อมูลข่าวสารจริงต่อไปนี้:
    {real_market_data}

    จงจำลองการโต้เถียง (Debate) ระหว่างผู้เชี่ยวชาญ 2 คนอย่างดุเดือด:
    - [Agent A: The Aggressive Bull] - มองโลกแง่ดี หาเหตุผลสนับสนุนจากข่าวว่าทำไมต้อง 'ซื้อเพิ่มทันที'
    - [Agent B: The Paranoid Bear] - มองโลกแง่ร้าย ระแวงทุกสัญญาณ หาเหตุผลเตือนว่าทำไมควร 'ขายหรืออยู่เฉยๆ'
    ให้ทั้งสองคนผลัดกันโต้ตอบกันคนละ 2 รอบ เพื่อเค้นเอาข้อมูลและจุดเสี่ยงที่ซ่อนอยู่ออกมาให้ได้มากที่สุด
    """
    
    # เปลี่ยนมาใช้ gemini-2.5-flash เพื่อเลี่ยง Error 429 และปลอดภัยเรื่องค่าใช้จ่าย
    debate_response = client.models.generate_content(
        model='gemini-2.5-flash', 
        contents=prompt_debate,
    )
    debate_output = debate_response.text

    print("⚡ [3/4] ดีเบตเสร็จสิ้น ส่งต่อให้ Agent CIO ทำการตัดสินใจขั้นสุดท้าย...")
    prompt_report = f"""
    คุณคือ Chief Investment Officer (CIO) ผู้มีอำนาจตัดสินใจสูงสุด
    นี่คือบทสรุปการโต้เถียงกันจากทีมงานของคุณ:
    {debate_output}

    จงทำหน้าที่สรุปและตัดสินใจขั้นสุดท้าย (Final Decision) โดยมีเงื่อนไขดังนี้:
    1. ชั่งน้ำหนักเหตุผลของทั้งสองฝ่ายอย่างเป็นกลางบนฐานของข้อมูลข่าวจริง
    2. ฟันธงข้อสรุปคำแนะนำ (เช่น ซื้อเพิ่ม 20%, คงพอร์ตไว้, หรือทยอยขาย)
    3. ร่างรายงานสรุปผู้บริหาร (Executive Summary) เป็นภาษาไทยที่กระชับ เป็นข้อๆ

    โครงสร้างรายงาน:
    - 📊 **สรุปสถานการณ์จากข่าวจริงล่าสุด**
    - ⚔️ **ประเด็นขัดแย้งสำคัญ (Bull vs Bear)**
    - 🎯 **การตัดสินใจขั้นสุดท้ายของ CIO**
    - ⚠️ **ความเสี่ยงที่ต้องเฝ้าระวัง**
    """
    
    # ใช้ gemini-2.5-flash ร่างรายงานสรุปฉบับสุดท้าย
    report_response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_report,
    )
    final_report = report_response.text

    # ⚡ [ด่าน 4] หั่นแบ่งข้อความส่งเข้า Discord (รันรอบเดียวจบ ไม่ต้องมี loop ข้างนอก)
    print("⚡ [4/4] กำลังหั่นแบ่งข้อความตามย่อหน้าและส่งรายงานเข้า Discord...")
    MAX_LENGTH = 1900
    full_message = f"🔔 **[ระบบอัตโนมัติประจำชั่วโมง] รายงานวิเคราะห์สถานการณ์ลงทุนจริง**\n\n{final_report}"
    
    lines = full_message.split('\n')
    chunks = []
    current_chunk = ""
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 <= MAX_LENGTH:
            current_chunk += line + '\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line + '\n'
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    for index, chunk in enumerate(chunks):
        # if len(chunks) > 1:
        #     chunk_content = f"*[Part {index + 1}/{len(chunks)}]*\n{chunk}"
        # else:
        #     chunk_content = chunk

        chunk_content = chunk # ไม่ต้องใส่ป้ายพาร์ท เพราะหั่นตามย่อหน้าแล้ว
            
        payload = {"content": chunk_content}
        requests.post(DISCORD_WEBHOOK_URL, json=payload)

# 🌐 ท่อนรับสัญญาณเว็บของ Vercel (เมื่อ Cron-Job.org ยิงมา)
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            print("🚀 เว็บโดนปลุก! เริ่มรันระบบ Agent Workflow...")
            run_agent_workflow()
            
            # ตอบกลับไปหา Cron-Job.org ว่าทำงานเสร็จแล้วนะ
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write("บอททำงานและส่ง Discord สำเร็จเรียบร้อยแล้ว!".encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"เกิดข้อผิดพลาด: {e}".encode('utf-8'))