// All Gemini DOM assumptions belong here. No PickyLens Core dependencies.
window.PickyLensGemini = {
 editor:()=>[...document.querySelectorAll('[contenteditable="true"][role="textbox"]')].find(e=>e.getClientRects().length),
 action:(name,scope=document)=>scope.querySelector(`mat-icon[data-mat-icon-name="${name}"]`)?.closest('button'),
 send(){return this.action('arrow_upward',document.querySelector('input-container')||document);},
 turns(){return [...document.querySelectorAll('model-response')].map(answer=>{
 const turn=answer.parentElement,body=answer.querySelector('[id^="model-response-message-content"]'),request=turn.querySelector('user-query');
 return {turn,answer,id:turn.id,request:request?.innerText||'',text:body?.innerText||'',busy:body?.getAttribute('aria-busy'),actions:!!this.action('refresh',answer)&&!!this.action('copy',answer)};
 }).filter(t=>t.id&&t.request);}
};
