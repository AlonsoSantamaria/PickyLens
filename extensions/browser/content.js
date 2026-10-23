(()=>{
 const labels={complete:'Complete',partial:'Partial',missing:'Missing',needs_review:'Needs review'};
 const host=window.PickyLensHost;let bypass=false,busy=false,approvedPrompt=null;const views=new Map();
 const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
 const action=(label,fn)=>{const b=el('button',label);b.type='button';b.onclick=fn;return b;};
 function panel(){const shell=el('div');shell.dataset.pickylens='';const shadow=shell.attachShadow({mode:'open'});const style=el('style',':host{display:block;margin:8px 0}section{background:#f6f7fc;color:#17243b;padding:10px;border:1px solid #aeb6cc;border-radius:10px;font:13px system-ui}button{margin:4px;padding:7px;border:1px solid #8e9bb9;border-radius:7px;background:#fff;color:#243d72;cursor:pointer}textarea{box-sizing:border-box;width:100%;min-height:100px}p{margin:6px 0}summary{cursor:pointer}');shadow.append(style);const box=el('section');shadow.append(box);return {shell,box};}
 const composer=panel();composer.box.append(el('strong','◉—◉ PickyLens'),action('Review my request',()=>review(false)));
 async function api(action,body){const r=await chrome.runtime.sendMessage({action,body});if(!r?.ok)throw Error(r?.error||'Review unavailable.');return r.data;}
 function send(){const b=host.send();if(!b)throw Error('Gemini Send is unavailable.');bypass=true;try{b.click();}finally{bypass=false;}}
 async function review(intercepted){if(busy)return;const original=host.editor()?.innerText;if(!original?.trim())return;busy=true;composer.box.replaceChildren(el('strong','PickyLens · Reviewing your request…'));
 try{const pre=await api('pre',{request:original});composer.box.replaceChildren(el('strong',`PickyLens · ${pre.readiness==='green'?'Ready':pre.readiness==='red'?'Important issue before sending':'Worth improving'}`));
 for(const f of pre.findings)composer.box.append(el('p',`${f.title}: ${f.explanation}`));
 for(const c of pre.clarifications)composer.box.append(el('p',c.question+' — answer this in your request if relevant.'));
 const edit=el('textarea');edit.value=pre.improved_prompt;edit.setAttribute('aria-label','Suggested request; review before accepting');composer.box.append(edit,action('Use edited improvement',()=>{if(host.editor()?.innerText!==original){composer.box.append(el('p','Your request changed. Review it again.'));return;}host.replace(edit.value);approvedPrompt=host.editor().innerText;composer.box.append(el('p','Updated by your choice. Review and send from Gemini.'));}));
 }catch(e){composer.box.replaceChildren(el('p',e.message));}
 finally{busy=false;composer.box.append(action('Review again',()=>review(false)),action('Send original anyway',()=>{if(host.editor()?.innerText!==original){composer.box.append(el('p','Your request changed. Review it again.'));return;}send();}));}}
 function intercept(e){if(bypass||!host.editor()?.innerText.trim())return;const enter=e.type==='keydown'&&e.key==='Enter'&&!e.shiftKey&&!e.isComposing&&host.editor().contains(e.target);const click=e.type==='click'&&e.target.closest?.('button')===host.send();if((enter||click)&&approvedPrompt===host.editor().innerText){approvedPrompt=null;return;}if(enter||click){e.preventDefault();e.stopImmediatePropagation();review(true);}}
 document.addEventListener('keydown',intercept,true);document.addEventListener('click',intercept,true);
 function mount(){const editor=host.editor();if(editor&&!composer.shell.isConnected)editor.parentElement.append(composer.shell);
 for(const turn of host.turns()){let view=views.get(turn.id);if(!view){view=panel();views.set(turn.id,view);}if(!view.shell.isConnected)turn.answer.after(view.shell);
 if(view.version===turn.request+'\n'+turn.text)continue;view.version=turn.request+'\n'+turn.text;view.box.replaceChildren(el('strong','◉—◉ PickyLens'),action('Check this answer',async()=>{
 if(host.generating()){view.box.append(el('p','Wait until Gemini has finished, then check this answer.'));return;}
 const current=host.turns().find(t=>t.id===turn.id);if(!current?.text.trim())return;const version=current.request+'\n'+current.text;if(view.pending)return;view.pending=true;view.box.replaceChildren(el('p','Checking this answer…'));
 try{const result=await api('post',{request:current.request,answer:current.text});if(view.version!==version)return;view.box.replaceChildren(el('strong','PickyLens · Answer review'));
 for(const a of result.assessment.assessments){const d=el('details');d.append(el('summary',`${labels[a.status]||'Needs review'} · ${a.requirement_text}`),el('p',a.explanation));for(const evidence of a.evidence)d.append(el('blockquote',evidence.excerpt));if(a.uncertainty_reason)d.append(el('p',a.uncertainty_reason));view.box.append(d);}
 if(result.assessment.assessments.every(a=>a.status==='complete'))view.box.append(el('p','All requested requirements are fulfilled.'));
 if(result.assessment.assessments.some(a=>['partial','missing'].includes(a.status)))view.box.append(action('Fix only what’s missing',async()=>{if(view.repairPending)return;view.repairPending=true;try{const next=await api('next',result);if(view.version!==version)return;const draft=el('textarea');draft.value=next.text;view.box.append(draft,action('Place follow-up in composer',()=>{if(host.editor()?.innerText.trim()&&!confirm('Replace the current composer draft?'))return;host.replace(draft.value);}));}catch(e){view.box.append(el('p',e.message));}finally{view.repairPending=false;}}));
 }catch(e){if(view.version===version){view.box.replaceChildren(el('p',e.message));view.version=null;}}
 finally{view.pending=false;}
 }));}}
 new MutationObserver(mount).observe(document.documentElement,{childList:true,subtree:true});mount();
})();
