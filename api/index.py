import os
import requests
from google import genai
from google.genai import types
from http.server import BaseHTTPRequestHandler

# 🔒 ดึงคีย์ความลับ 2 ตัวนี้พอ (ตัวตั้งเวลา RUN_EVERY_X_HOURS ลบออกได้เลย)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

client = genai.Client(api_key=GEMINI_API_KEY)

def run_agent_workflow():
    # ... (ท่อนด่าน 1, 2, 3 ของคุณเหมือนเดิม) ...
    
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