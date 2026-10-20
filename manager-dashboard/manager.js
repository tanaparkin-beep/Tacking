/* Live Manager input data uses its own source and never the project demo tasks. */
const managerLive={data:null,loading:false,error:'',managerOptions:false};
function managerValid(t){return !!(t.id&&t.manager&&Number.isFinite(t.weight)&&t.weight>0&&t.dueOriginal);}
function managerDue(t){return t.dueApproved||t.dueOriginal;}
function managerMissing(t){return [!t.id?'รหัสงาน (A)':'',!t.manager?'Manager (B)':'',!Number.isFinite(t.weight)||t.weight<=0?'น้ำหนัก (E)':'',!t.dueOriginal?'กำหนดส่งเดิม (G)':''].filter(Boolean);}
function managerSummary(tasks,name,month,asOf,targets){
 const start=month+'-01',end=new Date(Date.UTC(Number(month.slice(0,4)),Number(month.slice(5,7)),0)).toISOString().slice(0,10),all=tasks.filter(t=>t.manager===name),valid=all.filter(managerValid),due=valid.filter(t=>managerDue(t)>=start&&managerDue(t)<=end),closed=due.filter(t=>t.accepted&&t.accepted<=end),on=due.filter(t=>t.submitted&&t.submitted<=managerDue(t)&&t.accepted),reviewed=all.filter(t=>t.reviewed&&t.reviewed>=start&&t.reviewed<=end&&Number.isFinite(t.weight)&&t.weight>0),first=reviewed.filter(t=>t.firstPass==='ใช่'),carry=valid.filter(t=>managerDue(t)<start&&(!t.accepted||t.accepted>=start)&&t.recovery&&t.recovery>=start&&t.recovery<=end),recovered=carry.filter(t=>t.accepted&&t.accepted<=t.recovery),sum=a=>a.reduce((v,t)=>v+t.weight,0),ratio=(n,d)=>sum(d)?sum(n)/sum(d):null;
 const rates=[ratio(on,due),ratio(closed,due),ratio(first,reviewed),ratio(recovered,carry)];let points=0,applicable=0;rates.forEach((v,i)=>{if(v!==null){points+=Math.min(v/targets[i].target,1)*targets[i].points;applicable+=targets[i].points;}});
 const overdue=valid.filter(t=>!t.accepted&&managerDue(t)<asOf);
 return {manager:name,due:due.length,closed:closed.length,overdue:overdue.length,waiting:overdue.filter(t=>t.submitted).length,rates,score:applicable?points/applicable*100:null,invalid:all.filter(t=>!managerValid(t)).length,qualityMissing:reviewed.filter(t=>!['ใช่','ไม่ใช่'].includes(t.firstPass)).length};
}
function managerStatus(t,asOf){if(t.accepted)return 'ตรวจรับแล้ว';if(!managerValid(t))return 'ข้อมูลหลักไม่ครบ';if(managerDue(t)<asOf)return t.submitted?'ค้างรอตรวจ / แก้':'ค้างยังไม่ส่ง';return t.status||'ยังไม่ระบุสถานะ';}
function renderLiveManager(){
 const panel=$('managerLive');panel.hidden=false;
 if(!managerLive.data){$('metrics').innerHTML='';$('managerSummaryRows').innerHTML='';$('managerTaskRows').innerHTML='';$('managerEmpty').hidden=false;$('managerEmpty').textContent=managerLive.error||'กำลังอ่านข้อมูลจาก Google Drive…';if(!managerLive.loading&&!managerLive.error)loadManagerData();return;}
 const d=managerLive.data,month=$('month').value||d.month,filter=$('manager').value,query=$('search').value.trim().toLowerCase(),names=d.managers.filter(n=>!filter||n===filter),stats=names.map(n=>managerSummary(d.tasks,n,month,d.asOf,d.targets));
 const scores=stats.map(s=>s.score).filter(v=>v!==null),avg=scores.length?scores.reduce((a,b)=>a+b,0)/scores.length:null;
 const monthTasks=d.tasks.filter(t=>(!filter||t.manager===filter)&&managerDue(t)&&managerDue(t).startsWith(month)),invalid=d.tasks.filter(t=>(!filter||t.manager===filter)&&!managerValid(t));
 $('managerDataIssues').textContent=invalid.length?`${invalid.length} รายการยังไม่พร้อมคำนวณ KPI — กรุณากรอกช่องที่ขาดตามหมายเหตุในตาราง (กำหนดส่งที่อนุมัติ H ไม่แทนช่องกำหนดส่งเดิม G ในสูตรต้นทาง)`:'ข้อมูลหลักพร้อมคำนวณ KPI';
 $('metrics').innerHTML=[['งานในเดือนที่อ่านจากชีต',monthTasks.length,`${stats.reduce((a,s)=>a+s.due,0)} รายการมีข้อมูลพร้อมคำนวณ KPI`],['ตรวจรับตามแผน',stats.reduce((a,s)=>a+s.closed,0),'ตรวจรับภายในสิ้นเดือนประเมิน'],['งานค้าง ณ วันติดตาม',stats.reduce((a,s)=>a+s.overdue,0),'เฉพาะรายการข้อมูลครบ รวมงานค้างเดือนก่อน'],['คะแนน KPI เฉลี่ย',avg===null?'N/A':avg.toFixed(1),'เฉลี่ยเฉพาะ Manager ที่มี KPI ให้ประเมิน']].map(([label,value,note])=>`<article class="metric"><small>${label}</small><strong>${value}</strong><p>${note}</p></article>`).join('');
 const pct=v=>v===null?'N/A':(v*100).toFixed(1)+'%';
 $('managerSummaryRows').innerHTML=stats.map(s=>`<tr><td><b>${esc(s.manager)}</b></td><td>${s.due}</td><td>${s.closed}</td><td>${s.overdue}</td>${s.rates.map(v=>`<td>${pct(v)}</td>`).join('')}<td><b>${s.score===null?'N/A':s.score.toFixed(1)}</b></td><td>${s.invalid+s.qualityMissing?`ตรวจข้อมูล ${s.invalid+s.qualityMissing} จุด`:'—'}</td></tr>`).join('');
 // Detail uses due month; quality/carry KPI still uses their own populations, as in the workbook.
 const data=d.tasks.filter(t=>(!filter||t.manager===filter)&&(!managerDue(t)||managerDue(t).startsWith(month))&&(!query||`${t.title} ${t.manager} ${t.id}`.toLowerCase().includes(query)));
 $('managerTaskRows').innerHTML=data.map(t=>`<tr><td><b>${esc(t.title||'ยังไม่ระบุชื่องาน')}</b><small>${esc(t.id||'ยังไม่ระบุรหัส')} · แถว ${t.row}</small></td><td>${esc(t.manager||'ยังไม่ระบุ Manager')}</td><td>${t.weight??'—'}</td><td>${dateLabel(managerDue(t))}</td><td>${dateLabel(t.submitted)}</td><td>${dateLabel(t.accepted)}</td><td><span class="badge ${t.accepted?'done':!managerValid(t)?'blocked':'muted'}">${esc(managerStatus(t,d.asOf))}</span></td><td>${!managerValid(t)?`<b class="late-text">ขาด ${esc(managerMissing(t).join(', '))} · แถว ${t.row}</b>`:''}${esc(t.blocker||t.nextAction||'—')}</td></tr>`).join('');
 $('managerEmpty').hidden=!!data.length;$('managerEmpty').textContent=d.tasks.length?'ไม่พบรายการงานในเดือนหรือตัวกรองนี้':'ยังไม่มีรายการงานในชีต “อัปเดตงาน” กรุณากรอกข้อมูลที่ไฟล์หลักแล้วกดรีเฟรช';
 $('managerSourceTime').textContent=`อ่านล่าสุด ${new Date(d.fetchedAt).toLocaleString('th-TH',{timeZone:'Asia/Bangkok'})} · ${d.tasks.length} รายการจากชีต · รีเฟรชอัตโนมัติทุก 1 นาที`;
 $('managerTargets').textContent=d.targets.map(t=>`${t.label}: เป้า ${(t.target*100).toFixed(0)}% / ${t.points} คะแนน`).join(' · ');
 $('managerSourceError').textContent=managerLive.error;
}
async function loadManagerData(){if(managerLive.loading)return;managerLive.loading=true;managerLive.error='';$('refreshManager').disabled=true;$('managerSourceError').textContent='กำลังอ่านไฟล์หลัก…';try{if(location.protocol==='file:')throw Error('เปิดเว็บ Vercel เพื่ออ่านข้อมูลสด หรือเปิดไฟล์หลักจากปุ่มด้านบน');const response=await fetch('/api/manager',{cache:'no-store'});let d;try{d=await response.json();}catch{throw Error('บริการอ่านข้อมูลยังไม่พร้อม กรุณาลองใหม่');}if(!response.ok)throw Error(d.error||'อ่านไฟล์ไม่สำเร็จ');if(!Array.isArray(d.tasks)||!Array.isArray(d.managers)||!Array.isArray(d.targets)||d.targets.length!==4)throw Error('รูปแบบข้อมูลจากชีตไม่ถูกต้อง');const first=!managerLive.data;managerLive.data=d;if(first)$('month').value=d.month;managerLive.managerOptions=false;if(currentView==='manager'){setManagerMode(true);renderLiveManager();}}catch(e){managerLive.error=e.message;if(currentView==='manager')renderLiveManager();}finally{managerLive.loading=false;$('refreshManager').disabled=false;$('managerSourceError').textContent=managerLive.error;}}
function setManagerMode(manager){
 $('metricNote').hidden=manager;$('workspaceMode').textContent='LIVE · GOOGLE DRIVE';$('projectSourcePanel').hidden=manager;$('add').hidden=true;
 $('overview').hidden=manager;$('projectMatrix').hidden=manager;$('projectTasks').hidden=manager;$('managerLive').hidden=!manager;$('project').parentElement.hidden=manager;$('stepFilter').parentElement.hidden=manager;$('restore').hidden=true;$('export').hidden=manager;
 $('sourceNotice').innerHTML=manager?'<span>ข้อมูลจากไฟล์หลัก</span> อ่านเฉพาะชีต “อัปเดตงาน” และ “สรุป KPI” · แก้ข้อมูลที่ไฟล์ต้นทางแล้วกดรีเฟรช':'<span>ข้อมูลโครงการจากไฟล์หลัก</span> อ่านสถานะจากชีตแต่ละโครงการ · Done ที่ไม่มี Finish Date จะแสดง ? และยังไม่นับว่ายืนยันเสร็จ';
 if(manager&&!managerLive.managerOptions){const value=$('manager').value;$('manager').innerHTML='<option value="">Manager ทุกคน</option>';for(const n of managerLive.data?.managers||[])$('manager').add(new Option(n,n));$('manager').value=Array.from($('manager').options||[]).some(o=>o.value===value)?value:'';managerLive.managerOptions=true;}
 if(!manager&&managerLive.managerOptions){$('manager').innerHTML='<option value="">Manager ทุกคน</option>';for(const n of new Set(roster.map(r=>r[1])))$('manager').add(new Option(n,n));managerLive.managerOptions=false;}
}
if(typeof module!=='undefined')module.exports={managerSummary,managerValid,managerStatus};
if(typeof window!=='undefined'&&window.addEventListener){
 window.setInterval(()=>{if(currentView==='manager'&&!document.hidden)loadManagerData();},60000);
 window.addEventListener('focus',()=>{if(currentView==='manager')loadManagerData();});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden&&currentView==='manager')loadManagerData();});
}
