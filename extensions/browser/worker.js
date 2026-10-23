// Packaging replaces this with the exact HTTPS deployment origin; never arbitrary URLs.
const BACKEND = 'http://127.0.0.1:8000';
chrome.storage.local.setAccessLevel({accessLevel:'TRUSTED_CONTEXTS'});
chrome.action.onClicked.addListener(()=>chrome.runtime.openOptionsPage());
chrome.runtime.onMessage.addListener((m,s,reply)=>{
 if(s.id!==chrome.runtime.id||!s.url?.startsWith('https://gemini.google.com/')||!['pre','post','next'].includes(m?.action)||!m.body||JSON.stringify(m.body).length>65000)return false;
 (async()=>{
  const {judgePass}=await chrome.storage.local.get('judgePass');
  if(!judgePass)throw Error('Open PickyLens extension settings and enter your Judge Pass.');
  const response=await fetch(`${BACKEND}/api/browser/${m.action}`,{method:'POST',credentials:'omit',headers:{'Content-Type':'application/json','Authorization':`Bearer ${judgePass}`},body:JSON.stringify(m.body),signal:AbortSignal.timeout(180000)});
  const data=await response.json();
  if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'Review unavailable. Try again manually.');
  if(!data||typeof data!=='object'||(m.action==='pre'&&(!['green','amber','red'].includes(data.readiness)||!Array.isArray(data.findings)||!Array.isArray(data.clarifications)||typeof data.improved_prompt!=='string'))||(m.action==='post'&&(!data.intent||!data.answer||!Array.isArray(data.assessment?.assessments)))||(m.action==='next'&&typeof data.text!=='string'))throw Error('Invalid review response.');
  reply({ok:true,data});
 })().catch(e=>reply({ok:false,error:e.name==='TimeoutError'?'Review timed out. Your work is unchanged.':e.message}));return true;
});
