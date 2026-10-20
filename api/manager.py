"""Read-only adapter for the existing public Drive XLSX, without credentials."""
from http.server import BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from datetime import datetime, timedelta, timezone
from io import BytesIO
import json, posixpath, zipfile
import xml.etree.ElementTree as ET

FILE_ID = '1CT_RqXDYAP-rk2wC2FC2j8KHEWW21cTX'
PROJECT_SHEETS = [('IBL ECS','IBL · ECS'),('IBL TVS FDA FPSG','IBL · TVS / FDA / FPSG'),('BLE','BLE'),('Lotus Makro MA','Lotus / Makro MA'),('Lotus Makro Renovate','Lotus / Makro Renovate'),('GCC','GCC'),('Smart City','Smart City'),('ORL','ORL'),('MA จุฬา','MA จุฬา'),('OCC','OCC'),('IRDN','IRDN')]
NS = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'

def parse_workbook(raw):
    with zipfile.ZipFile(BytesIO(raw)) as z:
        if sum(i.file_size for i in z.infolist()) > 50_000_000:
            raise ValueError('ไฟล์มีขนาดใหญ่เกินรองรับ')
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            shared=[''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',NS)]
        rels={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        book=ET.fromstring(z.read('xl/workbook.xml'))
        prop=book.find('s:workbookPr',NS)
        epoch=datetime(1904,1,1) if prop is not None and prop.get('date1904') in ('1','true') else datetime(1899,12,30)
        sheets={}
        for sheet in book.findall('s:sheets/s:sheet',NS):
            name=sheet.get('name')
            if name not in ('อัปเดตงาน','สรุป KPI') and name not in dict(PROJECT_SHEETS):continue
            target=rels[sheet.get(RID)]
            path=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
            cells={}
            for c in ET.fromstring(z.read(path)).findall('.//s:sheetData/s:row/s:c',NS):
                value=c.find('s:v',NS);typ=c.get('t')
                if typ=='inlineStr':v=''.join(c.find('s:is',NS).itertext())
                elif value is None:v=None
                elif typ=='s':v=shared[int(value.text)]
                elif typ in ('str','e','d'):v=value.text
                else:
                    try:v=float(value.text) if value.text is not None else None
                    except (ValueError,TypeError):v=value.text
                formula=c.find('s:f',NS)
                if name=='สรุป KPI' and c.get('r')=='E4' and formula is not None and 'TODAY' in (formula.text or '').upper():v=None
                cells[c.get('r')]=v
            sheets[name]=cells
        if not all(n in sheets for n in ('อัปเดตงาน','สรุป KPI')):raise ValueError('ไม่พบชีต อัปเดตงาน และ สรุป KPI ในไฟล์หลัก')
        def date(v):
            if isinstance(v,(int,float)):
                try:return (epoch+timedelta(days=v)).date().isoformat()
                except (OverflowError,ValueError):return None
            if isinstance(v,str) and len(v)>=10:
                try:return datetime.fromisoformat(v.replace('Z','+00:00')).date().isoformat()
                except ValueError:return None
            return None
        t=sheets['อัปเดตงาน'];s=sheets['สรุป KPI']
        expected={'A6':'รหัสงาน','B6':'Manager','C6':'งาน / ผลส่งมอบ','G6':'กำหนดส่งเดิม','N6':'วันที่ตรวจรับ'}
        if any(t.get(k)!=v for k,v in expected.items()):raise ValueError('หัวตาราง อัปเดตงาน เปลี่ยนไป กรุณาตรวจรูปแบบข้อมูลก่อนแสดงผล')
        # Read input rows only. Formula/helper columns T:AA are calculated below in the UI.
        rows=sorted({int(k[1:]) for k in t if k.startswith('A') and k[1:].isdigit() and int(k[1:])>=7} | {int(k[1:]) for k in t if k.startswith('C') and k[1:].isdigit() and int(k[1:])>=7})
        tasks=[]
        for r in rows:
            vals=[t.get(f'{c}{r}') for c in 'ABCDEFGHIJKLMNOPQRS']
            if not any(v is not None and v!='' for v in vals):continue
            def text(i):return str(vals[i]).strip() if vals[i] is not None else ''
            tasks.append(dict(row=r,id=text(0),manager=text(1),title=text(2),criteria=text(3),weight=vals[4],started=date(vals[5]),dueOriginal=date(vals[6]),dueApproved=date(vals[7]),rescheduleReason=text(8),status=text(9),submitted=date(vals[10]),reviewed=date(vals[11]),firstPass=text(12),accepted=date(vals[13]),evidence=text(14),blocker=text(15),nextAction=text(16),recovery=date(vals[17]),updated=date(vals[18])))
        targets=[dict(label=s.get(f'A{r}'),target=s.get(f'B{r}'),points=s.get(f'C{r}')) for r in range(7,11)]
        if any(not isinstance(v['target'],(int,float)) or v['target']<=0 or not isinstance(v['points'],(int,float)) or v['points']<0 for v in targets):raise ValueError('เป้าหมายและน้ำหนัก KPI ในชีต สรุป KPI ไม่ถูกต้อง')
        names=[str(s[f'A{r}']).strip() for r in range(14,34) if s.get(f'A{r}')]
        for task in tasks:
            if task['manager'] and task['manager'] not in names:names.append(task['manager'])
        projects=[]
        for sheet_name,label in PROJECT_SHEETS:
            if sheet_name not in sheets:raise ValueError('ไม่พบชีตโครงการ '+sheet_name)
            cells=sheets[sheet_name];items=[]
            for r in range(2,1000):
                step=cells.get(f'A{r}')
                if not isinstance(step,(int,float)) or not 1<=step<=10.4 or not cells.get(f'C{r}'):continue
                items.append(dict(id=f'{sheet_name}:{r}',row=r,step=format(step,'g'),title=cells.get(f'B{r}') or '',role=cells.get(f'C{r}') or '',project=label,manager=cells.get('J2') or '',due=date(cells.get(f'D{r}')),finished=date(cells.get(f'E{r}')),status=cells.get(f'F{r}') or '',note='ชีต '+sheet_name+' แถว '+str(r),sheet=sheet_name))
            projects.append(dict(name=label,sheet=sheet_name,manager=cells.get('J2') or '',tasks=items))
        return dict(tasks=tasks,managers=names,targets=targets,projects=projects,month=(date(s.get('B4')) or datetime.now(timezone(timedelta(hours=7))).date().isoformat())[:7],asOf=date(s.get('E4')) or datetime.now(timezone(timedelta(hours=7))).date().isoformat(),sourceSummary=[dict(manager=s.get(f'A{r}'),values=[s.get(f'{c}{r}') for c in 'BCDEFGHIJK']) for r in range(14,34) if s.get(f'A{r}')])

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            req=Request(f'https://drive.google.com/uc?export=download&id={FILE_ID}',headers={'User-Agent':'Workboard/1.0'})
            with urlopen(req,timeout=20) as response:raw=response.read(8_000_001)
            if len(raw)>8_000_000 or not raw.startswith(b'PK'):raise ValueError('อ่านไฟล์ Excel ไม่สำเร็จ กรุณาตรวจว่าลิงก์ Drive ยังเข้าถึงได้')
            payload=parse_workbook(raw)
            payload.update(fetchedAt=datetime.now(timezone.utc).isoformat(),sourceUrl=f'https://docs.google.com/spreadsheets/d/{FILE_ID}/edit',sourceSheets=['อัปเดตงาน','สรุป KPI'],mode='live-read-only')
            self.respond(200,payload)
        except Exception as exc:
            self.respond(502,{'error':str(exc) if isinstance(exc,ValueError) else 'ไม่สามารถอ่านไฟล์จาก Google Drive ได้ กรุณาลองรีเฟรชอีกครั้ง'})
    def respond(self,code,payload):
        raw=json.dumps(payload,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
