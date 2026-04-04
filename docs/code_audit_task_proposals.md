# ข้อเสนอรายการงานจากการตรวจสอบฐานโค้ด

เอกสารนี้สรุป “งานที่ควรทำต่อ” อย่างละ 1 งานตามที่ร้องขอ: แก้ข้อความพิมพ์ผิด, แก้บั๊ก, แก้คอมเมนต์/เอกสารคลาดเคลื่อน, และปรับปรุงการทดสอบ

## 1) งานแก้ไขข้อความพิมพ์ผิด (Typo/Text Consistency)

**ปัญหาที่พบ**
- ชื่อโปรเจกต์ในบางเอกสารถูกเขียนเป็น `Aetherium LM` (มีช่องว่างและรูปแบบตัวพิมพ์ต่างจากชื่อรีโป `AETHERIUM-LM`) ทำให้เอกสารมีความไม่สม่ำเสมอด้านแบรนด์และการอ้างอิง

**หลักฐาน**
- `docs/architecture_reports/project_structure_report.txt`
- `docs/architecture_reports/data_flow_simulation.md`

**งานที่เสนอ**
- แก้ให้เป็นรูปแบบเดียวกันทั้งโปรเจกต์ (แนะนำ `AETHERIUM-LM`) และตรวจจุดอ้างอิงใน README/Docs ทั้งหมดให้คงที่

---

## 2) งานแก้ไขบั๊ก (Bug Fix)

**ปัญหาที่พบ**
- การเก็บข้อมูล sync ใช้ key เดียวคือ `item_id` (`_sync_records: Dict[str, SyncRecord]`) ทำให้ผู้ใช้คนละคนไม่สามารถมี `item_id` ซ้ำกันได้ และจะชนเงื่อนไข `FORBIDDEN` ทันที
- สำหรับระบบหลายผู้ใช้ พฤติกรรมนี้เสี่ยงเป็นบั๊กเชิงโดเมน เพราะ `item_id` ควรถูกแยก namespace ตามผู้ใช้ (หรือ tenant) โดยปกติ

**หลักฐาน**
- โครงสร้าง `_sync_records` และการอ่าน/เขียนใน `upsert_item()` ภายใน `app/mobile_backend.py`

**งานที่เสนอ**
- เปลี่ยน index ภายในเป็น `(user_id, item_id)` หรือเพิ่ม per-user bucket เพื่อลดการชนกันข้ามผู้ใช้
- คงพฤติกรรม `FORBIDDEN` เฉพาะกรณีที่เป็น access ข้าม owner จริง ไม่ใช่ชน key ตั้งแต่ชั้น storage

---

## 3) งานแก้ไขคอมเมนต์/เอกสารคลาดเคลื่อน

**ปัญหาที่พบ**
- เอกสารสถาปัตยกรรมระบุ flow “Validate & Save Config” และอธิบายว่า `main.py` เรียก `validate_llm_config()`
- แต่โค้ด `main.py` ปัจจุบันเป็นแชตจำลอง/แนบไฟล์ ไม่ได้มีฟอร์ม validate config ตามที่เอกสารอธิบาย

**หลักฐาน**
- เอกสาร: `docs/architecture_reports/data_flow_simulation.md`, `docs/architecture_reports/project_structure_report.txt`
- โค้ดจริง: `main.py`

**งานที่เสนอ**
- ปรับเอกสาร architecture reports ให้สะท้อน behavior ปัจจุบันของ `main.py`
- หรือหากตั้งใจกลับไปใช้ flow เดิม ให้เพิ่มสถานะในเอกสารว่าเป็น “legacy flow / planned flow” เพื่อลดความสับสน

---

## 4) งานปรับปรุงการทดสอบ (Test Improvement)

**ปัญหาที่พบ**
- ชุดทดสอบ `tests/test_mobile_backend.py` ครอบคลุม auth flow พื้นฐาน, idempotency, sync, push และ rate limit แล้ว
- แต่ยังไม่เห็นกรณีทดสอบ token ผิดรูปแบบโดยตรง เช่น token ถูกแก้ไข signature หรือ token หมดอายุ เพื่อยืนยัน error code (`AUTH_INVALID_TOKEN`, `AUTH_EXPIRED`) ตามที่โค้ดรองรับ

**หลักฐาน**
- ฟังก์ชัน `authenticate()` ใน `app/mobile_backend.py`
- ชุดทดสอบปัจจุบันใน `tests/test_mobile_backend.py`

**งานที่เสนอ**
- เพิ่ม unit tests อย่างน้อย 2 เคส:
  1. tampered signature -> ควรได้ 401 + `AUTH_INVALID_TOKEN`
  2. expired token -> ควรได้ 401 + `AUTH_EXPIRED`
- จะช่วย lock พฤติกรรมด้าน security contract ให้ชัดเจนขึ้น
