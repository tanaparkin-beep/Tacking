# RTB Task Tracker

Dashboard ติดตามงานของ Rapid Transit System Business สร้างจาก Google Sheet บันทึกการประชุม

| ไฟล์ | คืออะไร |
|---|---|
| `index.html` | **RTB Task Tracker** – สรุปสถานะงานรายบุคคลจากแท็บ `Task` (เกินกำหนด / ใกล้ครบกำหนด / ไม่ระบุกำหนด / ร่าง / เสร็จแล้ว) |
| `action-tracker.html` | **RTB Action Tracker** – Action Items ที่สรุปจากบันทึกการประชุมแต่ละครั้ง (16 ก.ค. – 20 ก.ย. 69) |
| `build_task_tracker.py` | สคริปต์ดึงแท็บ `Task` จาก Google Sheet แล้วสร้าง `index.html` ใหม่ |
| `task_tracker_template.html` | เทมเพลตหน้า Dashboard ที่สคริปต์ใช้ |

## อัปเดตข้อมูล

ต้องมี Python 3 และ `openpyxl` (`pip install openpyxl`)

```bash
python3 build_task_tracker.py --standalone --strip-email --out index.html
```

- `--today YYYY-MM-DD` กำหนดวันอ้างอิงเอง (ปกติใช้วันนี้)
- `--strip-email` ตัดอีเมลออกจากหน้าเว็บ (ใช้เสมอเมื่อเผยแพร่บน repo สาธารณะ)
- `--standalone` ใส่ `<!doctype html>` ให้เปิดเป็นไฟล์เดี่ยว / GitHub Pages ได้

จากนั้น commit และ push ไฟล์ `index.html` ที่ได้

## เกณฑ์สถานะ (แท็บ Task)

- **เสร็จแล้ว** = มี Finish Date
- **เกินกำหนด** = เลย Due date และยังไม่มี Finish Date
- **ใกล้ครบกำหนด** = Due ภายใน 7 วัน (รวมวันนี้)
- **อยู่ในกำหนด** = Due ยังไม่ถึง
- **ไม่ระบุกำหนด** = ไม่มี Due date
- **ร่าง** = มีแค่ Task Name ยังไม่ระบุโครงการ / ผู้รับผิดชอบ / วันที่

1 แถวในแท็บ Task = 1 งานของ 1 คน งานเดียวกันที่มอบหลายคนจะถูกรวมในมุมมอง "สรุปตามชื่องาน"

## เปิดดูออนไลน์

เปิด GitHub Pages ที่ Settings › Pages › Branch `main` / root แล้วเข้าที่
`https://tanaparkin-beep.github.io/Tacking/` (หน้า Task) และ `https://tanaparkin-beep.github.io/Tacking/action-tracker.html`
