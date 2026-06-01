from googletrans import Translator

# สร้าง object translator
translator = Translator()

# แปลภาษา (ต้นทาง -> ปลายทาง)
result = translator.translate('Hello world', dest='th')

# แสดงผล
print(f"ต้นฉบับ: {result.origin}")
print(f"แปลเป็น: {result.text}")
print(f"ภาษาที่ตรวจพบ: {result.src}")
