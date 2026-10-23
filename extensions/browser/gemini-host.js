// Gemini-only assumptions. Completion is an explicit user action, never inferred.
window.PickyLensHost={
 editor:()=>[...document.querySelectorAll('[contenteditable="true"][role="textbox"]')].find(e=>e.getClientRects().length),
 icon:(name,scope=document)=>scope.querySelector(`mat-icon[data-mat-icon-name="${name}"]`)?.closest('button'),
 send(){return this.icon('arrow_upward',document.querySelector('input-container')||document);},
 generating(){return !!this.icon('stop',document.querySelector('input-container')||document);},
 turns(){return [...document.querySelectorAll('model-response')].flatMap(answer=>{
 const turn=answer.parentElement,request=turn?.querySelector('user-query'),body=answer.querySelector('[id^="model-response-message-content"]');
 if(!turn?.id||!request||!body)return [];
 const text=[...request.querySelectorAll('.query-text-line')].map(e=>e.innerText.trim()).join('\n')||request.innerText.replace(/^Tú dijiste\s*/,'');
 if(!text.trim())return [];
 return [{id:turn.id,turn,answer,request:text,text:body.innerText}];
 });},
 replace(text){const e=this.editor();if(!e)throw Error('Gemini composer unavailable.');e.focus();document.execCommand('selectAll',false);document.execCommand('insertText',false,text);if(e.innerText.trim()!==text.trim())throw Error('Could not update composer. Review your request before sending.');}
};
