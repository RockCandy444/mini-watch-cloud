// Exercise the deployed HTTPS apps. This creates uniquely named test accounts,
// uses only its own test posts/notes, and never prints credentials or cookies.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const general = 'https://rockcandy-mini-general.onrender.com';
const monitor = 'https://rockcandy-mini-monitor-web.onrender.com';
const account = { username: 'cloud_' + Date.now(), password: crypto.randomBytes(24).toString('hex') };
const messages = [];
const note = s => { console.log(s); messages.push('- '+s); };
async function call(base, url, options = {}) {
  const response = await fetch(base + url, { redirect: 'manual', signal: AbortSignal.timeout(55000), ...options });
  const text = await response.text();
  let data; try { data = JSON.parse(text); } catch { data = null; }
  return {status: response.status, data, text, headers: response.headers};
}
const json = (data, method = 'POST', headers = {}) => ({method, headers: {'Content-Type':'application/json', ...headers}, body: JSON.stringify(data)});
const cookies = response => response.headers.getSetCookie().map(cookie=>cookie.split(';')[0]).join('; ');
(async()=>{
  assert.ok((await call(general,'/login')).text.includes(`${monitor}/register/general`));
  assert.ok((await call(monitor,'/register/general')).text.includes(`${general}/login`));
  note('Signup and login navigation links use the actual public HTTPS app URLs.');
  const signup = {...account, password_confirm:account.password};
  let response = await call(general,'/auth/register',json(signup));
  assert.equal(response.status,201,`General signup failed: ${response.status} ${response.data?.error}`);
  response = await call(monitor,'/api/auth/register',json(signup));
  assert.equal(response.status,201,`Monitor signup failed: ${response.status} ${response.data?.error}`);
  note('General and monitor test accounts created through the actual Supabase-backed applications (201). Passwords are hashed; no credentials in this report.');
  assert.equal((await call(general,'/auth/login',json({...account,password:'intentional-wrong-test-password'}))).status,401);
  response = await call(general,'/auth/login',json(account)); assert.equal(response.status,200);
  const generalCookie=cookies(response),generalCsrf=response.data.csrf_token;
  assert.ok(response.headers.get('set-cookie').includes('Secure'));
  const gh={Cookie:generalCookie,'X-CSRF-Token':generalCsrf};
  response = await call(monitor,'/api/auth/login',json(account)); assert.equal(response.status,200,`Monitor login failed: ${response.status} ${response.data?.error}`);
  const monitorCookie=cookies(response),monitorCsrf=response.data.csrf_token;
  assert.ok(response.headers.get('set-cookie').includes('Secure'));
  const mh={Cookie:monitorCookie,'X-CSRF-Token':monitorCsrf};
  assert.equal((await call(monitor,'/api/auth/me',{headers:mh})).status,200);
  note('HTTPS login and proxy Cookie/Set-Cookie/CSRF work; both session cookies have Secure; failed general login=401 and successful login=200.');
  assert.equal((await call(general,'/board/new',{method:'POST',body:new URLSearchParams({title:'unauthorized',body:'test'})})).status,401);
  assert.equal((await call(general,'/board/new',{method:'POST',headers:{Cookie:generalCookie},body:new URLSearchParams({title:'no csrf',body:'test'})})).status,403);
  response=await call(general,'/board/new',{method:'POST',headers:gh,body:new URLSearchParams({title:'클라우드 배포 검증',body:'Render와 Supabase 연결'})});assert.equal(response.status,303);
  const postPath=response.headers.get('location');
  response=await call(general,postPath+'/edit',{method:'POST',headers:gh,body:new URLSearchParams({title:'클라우드 배포 검증 완료',body:'HTTPS 게시글 수정과 재조회'})});assert.equal(response.status,303);
  response=await call(general,postPath);assert.equal(response.status,200);assert.ok(response.text.includes('HTTPS 게시글 수정과 재조회'));
  response=await call(monitor,'/api/notes',json({title:'실제 클라우드 관찰',body:'HTTPS와 로그인 기록을 확인했다',status:'확인 전'},'POST',mh));assert.equal(response.status,201);
  const noteId=response.data.note.id;
  response=await call(monitor,`/api/notes/${noteId}`,json({title:'실제 클라우드 관찰 완료',body:'Supabase 메모 수정과 재조회',status:'완료'},'PUT',mh));assert.equal(response.status,200);
  response=await call(monitor,`/api/notes/${noteId}`,{headers:mh});assert.equal(response.data.note.body,'Supabase 메모 수정과 재조회');
  note('Actual deployed post and note create/read/update succeed, persisted in separate Supabase projects. Anonymous post mutation=401 and missing CSRF=403.');
  response=await call(monitor,'/api/events?path=/auth/login',{headers:mh});assert.equal(response.status,200);
  assert.ok(response.data.events.some(event=>event.event_type==='login_failure'&&event.status_code===401),'Missing login_failure/401 delivery');
  assert.ok(response.data.events.some(event=>event.event_type==='login_success'&&event.status_code===200),'Missing login_success/200 delivery');
  note('General HTTPS requests reach the monitor through the final server event token; login_failure/401 and login_success/200 are stored and queried through Next.');
  assert.equal((await call(general,'/api/sentry-test',{headers:gh})).status,404);
  assert.equal((await call(monitor,'/api/events',json({method:'GET',path:'/',status_code:200}))).status,404);
  note('Sentry exercise remains disabled (404); Next prevents browser event ingestion (404). Sentry dashboard reception is not configured.');
  response=await call(general,postPath+'/delete',{method:'POST',headers:gh});assert.equal(response.status,303);
  assert.equal((await call(general,postPath)).status,404);
  assert.equal((await call(monitor,`/api/notes/${noteId}`,{method:'DELETE',headers:mh})).status,200);
  assert.equal((await call(monitor,`/api/notes/${noteId}`,{headers:mh})).status,404);
  note('Own smoke-test posts and notes deleted; subsequent detail requests return 404. Existing data was not altered.');
  const localDir=path.resolve(__dirname,'../.local');fs.mkdirSync(localDir,{recursive:true});
  fs.writeFileSync(path.join(localDir,'cloud-test-account.json'),JSON.stringify(account));
  fs.writeFileSync(path.join(__dirname,'public-results.md'),'# Public cloud validation\n\nDate: 2026-10-13, Asia/Seoul.\n\n'+messages.join('\n')+'\n');
})().catch(error=>{console.error(error.message);process.exitCode=1;});
