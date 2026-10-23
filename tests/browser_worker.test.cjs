const {readFileSync}=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const source=readFileSync('extensions/browser/worker.js','utf8');
async function harness(token,data,ok=true){
 let listener;const requests=[];
 const chrome={storage:{local:{setAccessLevel:()=>Promise.resolve(),get:async()=>({judgePass:token})}},action:{onClicked:{addListener(){}}},runtime:{id:'self',onMessage:{addListener(fn){listener=fn;}},openOptionsPage(){}}};
 vm.runInNewContext(source,{chrome,AbortSignal,fetch:async(url,options)=>{requests.push({url,options});return {ok,json:async()=>data};}});
 return {requests,send:message=>new Promise(resolve=>{const accepted=listener(message,{id:'self',url:'https://gemini.google.com/app/test'},resolve);if(!accepted)resolve(null);}),rejectSender:()=>listener({action:'pre',body:{}},{id:'other',url:'https://evil.test'},()=>{})};
}
(async()=>{
 let h=await harness(null,{});assert.equal((await h.send({action:'pre',body:{request:'x'}})).ok,false);assert.equal(h.requests.length,0);
 h=await harness('bounded-test-token',{readiness:'green',findings:[],clarifications:[],improved_prompt:'x'});
 assert.equal(h.rejectSender(),false);assert.equal((await h.send({action:'pre',body:{request:'x'}})).ok,true);
 assert.equal(h.requests[0].url,'http://127.0.0.1:8000/api/browser/pre');assert.equal(h.requests[0].options.credentials,'omit');assert.equal(h.requests[0].options.headers.Authorization,'Bearer bounded-test-token');
 assert.equal(await h.send({action:'arbitrary-url',body:{}}),null);
 h=await harness('test',{detail:'Your PickyLens evaluation allowance has been reached.'},false);assert.match((await h.send({action:'post',body:{}})).error,/allowance/);
 h=await harness('test',{});assert.equal((await h.send({action:'pre',body:{}})).ok,false);
 console.log('Browser worker protocol checks passed (no network).');
})().catch(e=>{console.error(e);process.exitCode=1;});
