// Disposable composer probe. Sends request text only to the fixed local mock via worker; no AI calls.
(() => {
  let bypass = false;
  const host=window.PickyLensGemini,states=new Map(),aborted=new Set();
  const editor=()=>host.editor();
  const root = document.createElement('div');
  root.id = 'pickylens-feasibility-probe';
  const shadow = root.attachShadow({mode:'open'});
  shadow.innerHTML = `<style>:host{display:block}button{font:13px system-ui;padding:6px 10px;margin:4px;border:1px solid #888;border-radius:8px;background:#f4f5ff;color:#18233b}p{font:13px system-ui;color:#18233b}</style><button>Review with PickyLens · test</button><div></div>`;
  const review = () => {
    const box = shadow.querySelector('div'); box.replaceChildren();
    const text = document.createElement('p');
    text.textContent = 'Deterministic placeholder: request preserved. No AI review performed.';
    box.append(text);
    chrome.runtime.sendMessage({type:'probe-review',text:editor()?.innerText||''}).then(r=>{if(text.isConnected)text.textContent=r?.message||'Local review unavailable.';}).catch(()=>{if(text.isConnected)text.textContent='Local review unavailable. Request unchanged.';});
  };
  shadow.querySelector('button').onclick = review;
  const mount = () => {
    const e=editor(); if(e && !root.isConnected) e.parentElement.append(root);
    for(const t of host.turns()) {
      const key=location.pathname+':'+t.id;
      const previous=states.get(key);
      const state=window.PickyLensLifecycle.classify(previous?.state,{...t,aborted:aborted.has(key)});
      const version=t.text;
      states.set(key,{state,version});
      let panel=t.turn.querySelector('[data-pickylens-post]');
      if(state!=='complete'){if(panel)panel.remove();continue;}
      if(panel&&previous?.version===version)continue;
      if(panel)panel.remove();
      panel=document.createElement('aside');panel.dataset.pickylensPost=t.id;
      panel.textContent='PickyLens · Deterministic POST placeholder. Completed answer observed; no AI evaluation.';
      panel.style.cssText='padding:10px;border:1px solid #8c93aa;border-radius:8px;font:13px system-ui;margin:8px 0';
      t.answer.after(panel);
    }
  };
  const intercept = event => {
    const e=editor(); if(!e || bypass || !e.innerText.trim()) return;
    const enter=event.type==='keydown' && event.key==='Enter' && !event.shiftKey && !event.isComposing && e.contains(event.target);
    const send = event.type==='click' && event.target.closest?.('button')===host.send();
    if(!enter && !send) return;
    event.preventDefault();event.stopImmediatePropagation();review();
    const note=document.createElement('p'); note.textContent=(enter?'Enter':'Send')+' intercepted. Original request remains unchanged.';
    const release=document.createElement('button');release.textContent='Send original anyway';
    release.onclick=()=>{const button=host.send();if(!button)return;root.dataset.submittedPrompt=e.innerText;root.dataset.submittedAt=new Date().toISOString();bypass=true;try{button.click();}finally{bypass=false;}review();};
    shadow.querySelector('div').append(note,release);
  };
  document.addEventListener('keydown',intercept,true);
  document.addEventListener('click',intercept,true);
  document.addEventListener('click',event=>{const button=event.target.closest?.('button');if(!button)return;for(const t of host.turns()){const key=location.pathname+':'+t.id;if(button===host.action('refresh',t.answer)){states.set(key,{state:'unknown'});aborted.delete(key);}if(button===host.action('stop'))aborted.add(key);}},true);
  const start=()=>{mount();new MutationObserver(mount).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-busy']});};
  if(document.documentElement) start();else document.addEventListener('DOMContentLoaded',start,{once:true});
})();

