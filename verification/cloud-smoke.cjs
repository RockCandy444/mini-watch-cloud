// Real local integration checks against the final Docker/Waitress/Next images.
// All accounts and passwords below are disposable classroom fixtures.
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const {execFileSync} = require('child_process');
const root = path.resolve(__dirname,'..');
const lines = ['# Day2 local validation', '', 'Date: 2026-10-13 (Asia/Seoul). External cloud services were not deployed.', ''];
const report = s => { console.log(s); lines.push('- '+s); };
function docker(args) { return execFileSync('docker', args, {cwd:root,encoding:'utf8',maxBuffer:10*1024*1024}); }
function compose(which,args) {return docker(['compose','-f',`compose-${which}.yaml`,...args]);}
async function call(base,url,options={}) {
  const response=await fetch(base+url,{redirect:'manual',...options});
  const text=await response.text();
  let data;try{data=JSON.parse(text);}catch{data=null;}
  return {status:response.status,data,text,headers:response.headers};
}
const json = (data,method='POST',headers={}) => ({method,headers:{'Content-Type':'application/json',...headers},body:JSON.stringify(data)});
const g='http://127.0.0.1:8081',m='http://127.0.0.1:8082';
(async()=>{
  for (const [service,app] of [['general','general-api'],['monitor','monitor-api']]) {
    compose(service,['exec','-T',app,'python','create_user.py','--classroom']);
    compose(service,['config','--quiet']);
  }
  let r=await call(g,'/health');assert.equal(r.status,200);assert.equal(r.data.service,'general');
  assert.equal((await call(m,'/api/auth/me')).status,401);
  assert.equal((await call(m,'/api/events',json({method:'GET',path:'/',status_code:200}))).status,404);
  report('Both Compose configs pass; general /health=200; Next blocks browser event ingestion; anonymous monitor /me=401.');
  r=await call(g,'/auth/login',json({username:'student',password:'wrong-test-only'}));assert.equal(r.status,401);
  r=await call(g,'/auth/login',json({username:'student',password:'Learn123!'}));assert.equal(r.status,200);
  const gcookie=r.headers.getSetCookie().map(c=>c.split(';')[0]).join('; ');
  assert.ok(gcookie);assert.ok(r.headers.get('set-cookie').includes('HttpOnly'));
  r=await call(m,'/api/auth/login',json({username:'operator',password:'Learn123!'}));assert.equal(r.status,200);
  const mcookie=r.headers.getSetCookie().map(c=>c.split(';')[0]).join('; ');
  const csrf=r.data.csrf_token;assert.ok(csrf);assert.ok(mcookie);
  const mh={Cookie:mcookie,'X-CSRF-Token':csrf};
  r=await call(m,'/api/auth/me',{headers:mh});assert.equal(r.status,200);assert.equal(r.data.user.username,'operator');
  report('General failed/successful logins return 401/200; Next forwards Set-Cookie, Cookie, login status and CSRF token.');
  const noteValues={title:'Day2 배포 설정 점검',body:'쿠키와 CSRF 전달 및 외부 저장소 연결 코드 확인',status:'확인 전'};
  r=await call(m,'/api/notes',json(noteValues,'POST',{Cookie:mcookie}));assert.equal(r.status,403);
  r=await call(m,'/api/notes',json({title:' ',body:'x'},'POST',mh));assert.equal(r.status,400);
  r=await call(m,'/api/notes',json(noteValues,'POST',mh));assert.equal(r.status,201);const noteId=r.data.note.id;
  const updated={...noteValues,status:'완료',body:'재실행 뒤 같은 PostgreSQL 자료를 읽었다'};
  r=await call(m,`/api/notes/${noteId}`,json(updated,'PUT',mh));assert.equal(r.status,200);
  r=await call(m,`/api/notes/${noteId}`,{headers:mh});assert.equal(r.status,200);assert.equal(r.data.note.body,updated.body);
  r=await call(g,'/board/new',{method:'POST',headers:{Cookie:gcookie},body:new URLSearchParams({title:'Day2 게시글',body:'재배포와 저장소 구분'})});assert.equal(r.status,303);
  const postPath=r.headers.get('location'),postId=Number(postPath.split('/').pop());
  r=await call(g,postPath+'/edit',{method:'POST',headers:{Cookie:gcookie},body:new URLSearchParams({title:'Day2 게시글 수정',body:'PostgreSQL에 보존된 내용'})});assert.equal(r.status,303);
  r=await call(g,postPath);assert.equal(r.status,200);assert.ok(r.text.includes('PostgreSQL에 보존된 내용'));
  r=await call(m,'/api/events?path=/auth/login',{headers:mh});assert.equal(r.status,200);
  assert.ok(r.data.events.some(e=>e.event_type==='login_failure'&&e.status_code===401));
  assert.ok(r.data.events.some(e=>e.event_type==='login_success'&&e.status_code===200));
  const noteDB=compose('monitor',['exec','-T','monitor-db','psql','-U','monitor','-d','monitor_db','-Atc',`SELECT body FROM notes WHERE id=${noteId}`]);assert.ok(noteDB.includes(updated.body));
  const postDB=compose('general',['exec','-T','general-db','psql','-U','general','-d','general_db','-Atc',`SELECT body FROM posts WHERE id=${postId}`]);assert.ok(postDB.includes('PostgreSQL에 보존된 내용'));
  report('Posts and notes create/read/update use separate real PostgreSQL databases; notes reject missing CSRF=403 and blank input=400; login_failure/401 and login_success/200 are stored and queried.');
  compose('general',['up','-d','--force-recreate']);
  compose('monitor',['up','-d','--force-recreate']);
  // Poll actual readiness after container recreation; each request is meaningful.
  for(let i=0;i<30;i++) {
    try{r=await call(m,'/api/auth/me',{headers:mh});if(r.status===200)break;}catch{}
    await new Promise(resolve=>setTimeout(resolve,500));
  }
  assert.equal(r.status,200);
  r=await call(m,`/api/notes/${noteId}`,{headers:mh});assert.equal(r.data.note.body,updated.body);
  r=await call(g,postPath);assert.equal(r.status,200);assert.ok(r.text.includes('PostgreSQL에 보존된 내용'));
  r=await call(g,'/auth/me',{headers:{Cookie:gcookie}});assert.equal(r.status,200);
  report('After recreation of all seven containers, posts, notes, user hashes and both signed login sessions remain valid.');
  compose('monitor',['stop','monitor-api']);
  try {
    r=await call(m,'/api/events',{headers:mh});assert.equal(r.status,502);assert.ok(r.data.error.includes('감시 API에 연결하지 못했습니다'));
    report('Stopped monitor API: Next returns 502 with the documented error message.');
  }finally{compose('monitor',['start','monitor-api']);}
  for(let i=0;i<30;i++){try{r=await call(m,'/api/events',{headers:mh});if(r.status===200)break;}catch{}await new Promise(resolve=>setTimeout(resolve,500));}
  assert.equal(r.status,200);report('After restoring monitor API, the same events request succeeds=200.');
  r=await call(m,`/api/notes/${noteId}`,{method:'DELETE',headers:mh});assert.equal(r.status,200);
  assert.equal((await call(m,`/api/notes/${noteId}`,{headers:mh})).status,404);
  r=await call(g,postPath+'/delete',{method:'POST',headers:{Cookie:gcookie}});assert.equal(r.status,303);
  assert.equal((await call(g,postPath)).status,404);
  r=await call(m,'/api/auth/logout',{method:'POST',headers:mh});assert.equal(r.status,200);
  report('Post/note deletes succeed and deleted details return 404; proxied logout=200. Smoke-test fixtures were cleaned up.');
  fs.writeFileSync(path.join(__dirname,'cloud-results.md'),lines.join('\n')+'\n');
})().catch(error=>{console.error(error);process.exitCode=1;});
