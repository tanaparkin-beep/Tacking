#!/usr/bin/env python3
"""Build rtb-task-tracker.html from the 'Task' tab of the RTB meeting-minutes Google Sheet.

Usage: python3 build_task_tracker.py [--today YYYY-MM-DD]
Downloads the workbook (public export), reads the Task tab, injects JSON into the template.
"""
import json, sys, os, datetime as dt, urllib.request, io, re
import openpyxl

SHEET_ID = "1nYQOoOtZRPfxs1iKjQckmWs_QnvS2UdS-49XUeO0Oro"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"
HERE = os.path.dirname(os.path.abspath(__file__))

TH_NAMES = {
    "Manas Phonphai": "มนัส พ้นภัย",
    "Chainarin Thangnu": "ชัยนรินทร์ แตงหนู",
    "Nattapatchr Sinthumpitak": "ณัฐพัชร์ ศีลธรรมพิทักษ์",
    "Kitawit Jitaton": "กฤตวิทย์ จิตราทร",
    "Nattharat Tamungmee": "ณัฐรัตน์ ถามั่งมี",
    "Premsak Preecha": "เปรมศักดิ์ ปรีชา",
    "Paiwadee Inta": "ภัยวดี อินตา",
    "Parkin Tanapongsapak": "ภาคิน ธนาพงศภัค",
}

today = dt.date.today()
if "--today" in sys.argv:
    today = dt.date.fromisoformat(sys.argv[sys.argv.index("--today") + 1])

data = urllib.request.urlopen(URL, timeout=60).read()
wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
ws = wb["Task"]

def iso(v):
    if isinstance(v, (dt.datetime, dt.date)):
        return v.date().isoformat() if isinstance(v, dt.datetime) else v.isoformat()
    if isinstance(v, str):
        m = re.match(r"^\s*(\d{1,2})/(\d{1,2})/(\d{2,4})\s*$", v)
        if m:
            d, mo, y = map(int, m.groups())
            y = y + 2000 if y < 100 else (y - 543 if y > 2400 else y)
            return dt.date(y, mo, d).isoformat()
    return None

rows = []
header_seen = False
for r in ws.iter_rows(values_only=True):
    a = r[0]
    if a is None or str(a).strip() == "":
        continue
    if not header_seen:
        if str(a).strip().lower() == "task name":
            header_seen = True
        continue
    task, project, owner, email, created, due, finish, notes = (list(r) + [None] * 8)[:8]
    owner_en = (owner or "").strip()
    rows.append({
        "task": str(task).strip(),
        "project": (project or "").strip() or "ไม่ระบุ",
        "owner": TH_NAMES.get(owner_en, owner_en) or "ไม่ระบุ",
        "ownerEn": owner_en,
        "email": (email or "").strip(),
        "created": iso(created),
        "due": iso(due),
        "finish": iso(finish),
        "notes": (str(notes).strip() if notes else ""),
        "draft": not any([project, owner, created, due]),
    })

if "--strip-email" in sys.argv:          # for public hosting: keep names, drop addresses
    for r in rows:
        r["email"] = ""

out_path = f"{HERE}/rtb-task-tracker.html"
if "--out" in sys.argv:
    out_path = sys.argv[sys.argv.index("--out") + 1]

payload = {"today": today.isoformat(), "generated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "rows": rows}
tpl = open(f"{HERE}/task_tracker_template.html", encoding="utf-8").read()
out = tpl.replace("/*__DATA__*/null", json.dumps(payload, ensure_ascii=False))
if "--standalone" in sys.argv:            # full document for GitHub Pages / local file
    out = '<!doctype html>\n<html lang="th">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n' + out + "\n</html>\n"
open(out_path, "w", encoding="utf-8").write(out)
print(f"rows={len(rows)} drafts={sum(r['draft'] for r in rows)} today={today} -> {out_path}")
