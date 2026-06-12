import logging
from datetime import datetime
import os

log_folder = "logs"
os.makedirs(log_folder, exist_ok=True) 


current_date = datetime.now().strftime("%Y-%m-%d")  # รูปแบบวันที่ เช่น 2025-04-11
log_filename = os.path.join(log_folder, f"ai_resume_{current_date}.log")


logging.basicConfig(
    filename=log_filename, 
    level=logging.INFO,  
    format="%(asctime)s - %(levelname)s - %(message)s",  #
    datefmt="%Y-%m-%d %H:%M:%S",  # รูปแบบวันที่
    encoding="utf-8"  
)

# สร้าง Logger สำหรับใช้งานในไฟล์อื่น
logger = logging.getLogger("AiResumeLogger")