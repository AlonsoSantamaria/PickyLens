// Fixed mock endpoint only; no provider keys, arbitrary URL forwarding or production API.
chrome.runtime.onMessage.addListener((message,sender,respond)=>{
 if(sender.id!==chrome.runtime.id||!sender.url?.startsWith('https://gemini.google.com/')||message?.type!=='probe-review'||typeof message.text!=='string'||message.text.length>20000)return false;
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),2000);
 fetch('http://127.0.0.1:8033/probe/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:message.text}),signal:controller.signal})
 .then(async r=>{if(!r.ok)throw Error('HTTP');const x=await r.json();if(x.kind!=='deterministic-probe'||typeof x.message!=='string'||x.message.length>200)throw Error('schema');respond({ok:true,message:x.message});})
 .catch(()=>respond({ok:false,message:'Local review unavailable. Your request is unchanged; you may send anyway.'})).finally(()=>clearTimeout(timer));return true;
});
