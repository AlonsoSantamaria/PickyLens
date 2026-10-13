// Disposable composer probe. No network, model calls, or prompt transmission.
(() => {
  let bypass = false;
  const editor = () => [...document.querySelectorAll('[contenteditable="true"][role="textbox"]')].find(e => e.getClientRects().length);
  const root = document.createElement('div');
  root.id = 'pickylens-feasibility-probe';
  const shadow = root.attachShadow({mode:'open'});
  shadow.innerHTML = `<style>:host{display:block}button{font:13px system-ui;padding:6px 10px;margin:4px;border:1px solid #888;border-radius:8px;background:#f4f5ff;color:#18233b}p{font:13px system-ui;color:#18233b}</style><button>Review with PickyLens · test</button><div></div>`;
  const review = () => {
    const box = shadow.querySelector('div'); box.replaceChildren();
    const text = document.createElement('p');
    text.textContent = 'Deterministic placeholder: request preserved. No AI review performed.';
    box.append(text);
  };
  shadow.querySelector('button').onclick = review;
  const mount = () => {
    const e=editor(); if(e && !root.isConnected) e.parentElement.append(root);
    for(const answer of document.querySelectorAll('model-response')) {
      const turn=answer.parentElement;
      if(!turn.id || !turn.querySelector('user-query')) continue;
      const body=answer.querySelector('[id^="model-response-message-content"][aria-busy="false"]');
      const ready=body && answer.querySelector('button[aria-label="Rehacer"]') && !document.querySelector('button[aria-label="Detener respuesta"]');
      let panel=turn.querySelector('[data-pickylens-post]');
      if(!ready){if(panel)panel.remove();continue;}
      if(panel)continue;
      panel=document.createElement('aside');panel.dataset.pickylensPost=turn.id;
      panel.textContent='PickyLens · Deterministic test: 1 item needs attention. Placeholder only; no answer evaluation performed.';
      panel.style.cssText='padding:10px;border:1px solid #8c93aa;border-radius:8px;font:13px system-ui;margin:8px 0';
      answer.after(panel);
    }
  };
  const intercept = event => {
    const e=editor(); if(!e || bypass || !e.innerText.trim()) return;
    const enter=event.type==='keydown' && event.key==='Enter' && !event.shiftKey && !event.isComposing && e.contains(event.target);
    const send = event.type==='click' && event.target.closest?.('button[aria-label="Enviar mensaje"]');
    if(!enter && !send) return;
    event.preventDefault();event.stopImmediatePropagation();review();
    const note=document.createElement('p'); note.textContent=(enter?'Enter':'Send')+' intercepted. Original request remains unchanged.';
    const release=document.createElement('button');release.textContent='Send original anyway';
    release.onclick=()=>{const button=document.querySelector('button[aria-label="Enviar mensaje"]');if(!button)return;root.dataset.submittedPrompt=e.innerText;root.dataset.submittedAt=new Date().toISOString();bypass=true;try{button.click();}finally{bypass=false;}review();};
    shadow.querySelector('div').append(note,release);
  };
  document.addEventListener('keydown',intercept,true);
  document.addEventListener('click',intercept,true);
  const start=()=>{mount();new MutationObserver(mount).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-busy']});};
  if(document.documentElement) start();else document.addEventListener('DOMContentLoaded',start,{once:true});
})();
