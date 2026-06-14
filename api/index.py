import os
import time
import requests
from google import genai
from google.genai import types
from dotenv import load_dotenv # หรือ load_dotenv
from http.server import BaseHTTPRequestHandler
load_dotenv()  # สั่งให้โหลดค่าจากไฟล์ .env เข้าสู่ระบบ

# 🛠️ ตั้งค่าส่วนตัวของคุณตรงนี้
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
RUN_EVERY_X_HOURS = int(os.environ.get("RUN_EVERY_X_HOURS", 1)) # ถ้าไม่ได้ตั้งไว้ จะรันทุกๆ 1 ชม.

if not GEMINI_API_KEY or not DISCORD_WEBHOOK_URL:
    print("❌ เออร์เรอร์: ตรวจไม่พบ GEMINI_API_KEY หรือ DISCORD_WEBHOOK_URL ในระบบ!")
    exit(1)

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)

def run_agent_workflow():
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

    print("⚡ [4/4] ส่งรายงานเข้า Discord...")
    # กำหนดความยาวสูงสุดต่อ 1 ข้อความ (เผื่อความปลอดภัยไว้ที่ 1,900 ตัวอักษร จากโควตา 2,000)
    MAX_LENGTH = 1900
    
    # รวมข้อความทั้งหมดที่จะส่ง
    full_message = f"🔔 **[ระบบอัตโนมัติประจำชั่วโมง] รายงานวิเคราะห์สถานการณ์ลงทุนจริง**\n\n{final_report}"
    
    # 📝 แยกข้อความเป็นบรรทัดๆ ก่อน เพื่อเอามาคำนวณการแบ่งช่อง
    lines = full_message.split('\n')
    chunks = []
    current_chunk = ""
    
    for line in lines:
        # ถ้าข้อความในช่องปัจจุบัน + บรรทัดใหม่ รวมกันแล้วยังไม่เกินโควตา
        if len(current_chunk) + len(line) + 1 <= MAX_LENGTH:
            current_chunk += line + '\n'
        else:
            # ถ้าเกิน ให้เก็บท่อนปัจจุบันไว้ แล้วเริ่มท่อนใหม่ด้วยบรรทัดนี้
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line + '\n'
            
    # เก็บตกท่อนสุดท้ายที่เหลือ
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    try:
        # วนลูปส่งข้อความที่หั่นแบบสวยงามแล้วเข้า Discord
        for index, chunk in enumerate(chunks):
            # เสริมป้ายบอกพาร์ทไว้ด้านบนสุด เพื่อไม่ให้รบกวนเนื้อหาด้านล่าง
            # if len(chunks) > 1:
            #     chunk_content = f"*[Part {index + 1}/{len(chunks)}]*\n{chunk}"
            # else:
            #     chunk_content = chunk
            
            chunk_content = chunk # ไม่ต้องใส่ป้ายพาร์ท เพราะหั่นตามย่อหน้าแล้วน่าจะโอเค
                
            payload = {"content": chunk_content}
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            
            if response.status_code not in [200, 204]:
                print(f"❌ ส่งข้อความชิ้นที่ {index + 1} ไม่สำเร็จ: {response.status_code}")
            
            time.sleep(1.5) # หน่วงเวลาเพิ่มขึ้นอีกนิดเพื่อความชัวร์
            
        print("✅ ทำงานเสร็จสมบูรณ์! หั่นแบ่งข้อความตามย่อหน้าเรียบร้อยแล้ว")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการหั่นส่งข้อความ: {e}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            print("🚀 เว็บโดนปลุก! เริ่มรันระบบ Agent Workflow...")
            run_agent_workflow()
            
            # ส่งสถานะกลับไปบอกเว็บตั้งเวลาว่ารันเสร็จแล้วนะ
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write("บอททำงานและส่ง Discord สำเร็จเรียบร้อยแล้ว!".encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"เกิดข้อผิดพลาด: {e}".encode('utf-8'))

if __name__ == "__main__":
    print(f"🚀 เริ่มเปิดระบบ Agent Workflow (ทำงานอัตโนมัติทุกๆ {RUN_EVERY_X_HOURS} ชั่วโมง)...")
    while True:
        try:
            run_agent_workflow()
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")
            
        print(f"😴 กำลังสแตนด์บาย... จะทำงานครั้งต่อไปในอีก {RUN_EVERY_X_HOURS} ชั่วโมงข้างหน้า")
        time.sleep(RUN_EVERY_X_HOURS * 3600)