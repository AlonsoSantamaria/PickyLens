"use strict";
let state = JSON.parse(document.getElementById("initial-state").textContent);
let panel = document.getElementById("request-review");
const request = document.getElementById("request");
let busy = false, editingRequest=false, beginningCase=false;
const demo=JSON.parse(document.getElementById("canonical-demo").textContent);
let canonical=true, replayRejected=false;
const mode=document.getElementById("mode");
if(state)mode.value=state.mode;
mode.onchange=()=>{if(state){const ok=!state.answer||confirm("Switch mode? Current answer and downstream reviews become superseded in History.");if(ok)call("mode",{mode:mode.value,confirmed_switch:true});else mode.value=state.mode;}};
const labels = {complete:"Complete",partial:"Partial",missing:"Missing",needs_review:"Needs review"};
function node(tag, text, cls) { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; if(cls)n.className=cls; return n; }
function button(text, fn, secondary=false) { const b=node("button",text,secondary?"secondary":""); b.onclick=fn; b.disabled=busy; return b; }
async function call(action, extra={}) {
  if(busy) return;
  const previousAnswer=state?.answer?.response_id, previousFollowup=state?.followup_answer?.response_id;
  let succeeded=false;
  busy=true; mode.disabled=true; document.getElementById("error").hidden=true;
  document.querySelectorAll("button").forEach(b=>b.disabled=true);
  const payload={operation_id:crypto.randomUUID(), ...extra};
  if(state)payload.expected_revision=state.revision;
  beginningCase=!state;
  syncOrientation();
  const url=state?`/api/interactions/${state.interaction_id}/${action}`:"/api/interactions/pre";
  try {
    const response=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    const result=await response.json();
    if(result.snapshot){state=result.snapshot;history.replaceState(null,"",`/?interaction=${state.interaction_id}`);}
    if(!response.ok)throw new Error(typeof result.detail==="string"?result.detail:"This action could not be completed.");
    state=await (await fetch(`/api/interactions/${result.interaction_id}`)).json();
    succeeded=true;
    editingRequest=false;
    replayRejected=false;
    history.replaceState(null,"",`/?interaction=${state.interaction_id}`);
    document.getElementById("saved").textContent="Saved to Interactions";
  } catch(e) { if(action==="mode"&&extra.mode==="replay")replayRejected=true; const box=document.getElementById("error");box.textContent=e.message;box.hidden=false; }
  finally {
    beginningCase=false; busy=false; render();
    if(succeeded){
      if(state.followup_answer?.response_id && state.followup_answer.response_id!==previousFollowup)focusContent("followup-heading");
      else if(state.answer?.response_id && state.answer.response_id!==previousAnswer)focusContent("answer-heading");
      else if(["pre","request","reset-scenario"].includes(action))focusContent("request-review");
      else if(action==="next")focusContent("repair-heading");
      else if(["post","verify","resolve"].includes(action))focusContent(state.verification?"verification-panel":"answer-review");
    }
  }
}
function focusContent(id){
  const target=document.getElementById(id);
  target.setAttribute("tabindex","-1");target.focus({preventScroll:true});
  target.scrollIntoView({behavior:"auto",block:"start"});
}
function counts(review, prefix="") {
  const c={complete:0,partial:0,missing:0,needs_review:0};
  review.assessments.forEach(a=>c[a.status]++);
  const box=node("div",undefined,"counts");
  Object.entries(c).forEach(([k,v])=>box.append(node("span",`${v} ${labels[k]}`,k)));
  if(prefix)panel.append(node("p",prefix,"muted small"));
  panel.append(box);
}
function assessments(review) {
  for(const a of review.assessments) {
    const row=node("details",undefined,"requirement"), summary=node("summary");
    summary.append(node("strong",labels[a.status]+" \xb7 ",a.status),document.createTextNode(a.requirement_text));row.append(summary);
    const before=state.post?.assessments.find(x=>x.requirement_id===a.requirement_id);
    if(review.phase==="verify"&&before&&before.status!==a.status)row.append(node("span",`${labels[before.status]} \u2192 ${labels[a.status]}`,"resolved"));
    row.append(node("p",a.explanation));
    if(a.uncertainty_reason)row.append(node("p",a.uncertainty_reason));
    a.evidence.forEach(e=>{row.append(node("blockquote",e.excerpt),node("small",`${e.location} \xb7 ${e.response_id===state.followup_answer?.response_id?"Follow-up response":"First response"}`));});
    panel.append(row);
  }
}
function showPRE() {
  const p=state.pre;
  if(!p) { panel.append(node("p",state.failure||"Review not completed."));return; }
  const meanings={green:"Ready to send.",amber:"Usable, but worth improving.",red:"Important issue before sending."};
  panel.append(node("h3","PickyLens reviewed your request"));
  panel.append(node("span",meanings[p.readiness],"readiness "+p.readiness));
  p.findings.forEach(f=>{const item=node("div",undefined,"finding");item.append(node("strong",f.title),node("p",f.explanation));panel.append(item);});
  const controls={};
  p.clarifications.forEach(c=>{
    const label=node("label",c.question), select=node(c.options.length?"select":"input");select.id="clarification-"+c.key;label.htmlFor=select.id;
    const blank=node("option","Choose an answer\u2026");blank.value="";if(c.options.length)select.append(blank);
    c.options.forEach(v=>{const o=node("option",v);o.value=v;select.append(o);});
    select.value=state.accepted_clarifications[c.key]||"";controls[c.key]=select;panel.append(label,select);
  });
  if(p.clarifications.length)panel.append(button("Save my clarification",()=>{
    const clarifications={};Object.entries(controls).forEach(([k,v])=>{if(v.value)clarifications[k]=v.value;});call("clarifications",{clarifications});
  },true));
  panel.append(node("h2","Improved request"));
  const improved=node("pre",p.improved_prompt+Object.entries(state.accepted_clarifications).map(([k,v])=>`\nAccepted ${k}: ${v}`).join(""));panel.append(improved);
  if(mode.value==="replay"){
    const details=node("details");details.append(node("summary","Demo request and approved requirements"),node("pre",demo.prompt));
    const canonicalList=node("ul");demo.requirements.forEach(t=>canonicalList.append(node("li",t)));details.append(canonicalList);panel.append(details);
    panel.append(node("p","Replay requires approval of this unchanged canonical intent. Approving this preset uses the original request with no accepted clarifications, replacing any clarification choices above. Use Live Model to keep a changed intent."));
    if(state.canonical_ready)panel.append(button("Use demo request",()=>call("approve-canonical",{confirmed_red:p.readiness!=="red"||confirm("Send canonical original despite the PRE warning?")})));
    panel.append(button("Reset to canonical scenario and review",()=>call("reset-scenario"),true));
  }
  panel.append(node("h2","Requirements you are approving"));
  const list=node("ul",undefined,"intent-list");p.requirements.forEach(r=>list.append(node("li",r.text)));
  Object.entries(state.accepted_clarifications).forEach(([k,v])=>list.append(node("li",`Improved prompt only \u2014 Accepted ${k}: ${v}`)));
  panel.append(list,node("p","Using a prompt approves these requirements for checking the answer and verifying repairs. Sending the original excludes unaccepted PRE suggestions.","muted small"));
  const improvedAction=button("Use improved request",()=>call("approve-intent",{choice:"improved"}),mode.value==="replay");
  improvedAction.disabled=p.clarifications.some(c=>c.required&&!state.accepted_clarifications[c.key]);
  panel.append(improvedAction);
  panel.append(button(p.readiness==="red"?"Send original anyway":"Send original",()=>{
    const confirmed=p.readiness!=="red"||confirm("Send the original despite the important issue?");
    if(confirmed)call("approve-intent",{choice:"original",confirmed_red:p.readiness==="red"});
  },true));
  panel.append(button("Edit improved request",()=>{editingRequest=true;request.readOnly=false;request.value=improved.textContent;request.focus();render();},true));
}
function syncOrientation(){
  const active=!!state||beginningCase;
  document.body.classList.toggle("active-case",active);
  const control=document.querySelector(".mode-control");
  const destination=document.getElementById(active?"active-mode-slot":"new-mode-slot");
  if(control.parentElement!==destination)destination.append(control);
  measureOrientation();
}
function measureOrientation(){
  const header=document.getElementById("global-header"), orientation=document.getElementById("case-orientation");
  document.documentElement.style.setProperty("--header-height",`${header.getBoundingClientRect().height}px`);
  document.documentElement.style.setProperty("--orientation-height",`${orientation.getBoundingClientRect().height}px`);
}
const orientationObserver=new ResizeObserver(measureOrientation);
orientationObserver.observe(document.getElementById("global-header"));
orientationObserver.observe(document.getElementById("case-orientation"));
function render() {
  for(const id of ["request-review","answer-review","repair-panel","verification-panel","recovery","request-tools"])document.getElementById(id).replaceChildren();
  const stage=state?.stage||"pre", paused=state?.lifecycle_status==="Paused";
  const terminal=stage==="done";
  const active={pre:"pre",ai:"ai",post:"ai",post_reviewed:"post",next:"next",verify:"verify",verified:"verify",done:"verify"}[stage];
  const completed={pre:!!state?.intent,ai:!!state?.answer,post:!!state?.post,next:!!state?.followup_answer,verify:!!state?.verification};
  document.querySelectorAll("#progress li").forEach(li=>{
    const key=li.dataset.stage, current=key===active;
    li.classList.toggle("active",current);li.classList.toggle("completed",completed[key]);
    if(current)li.setAttribute("aria-current","step");else li.removeAttribute("aria-current");
    const name=li.querySelector("strong").textContent;
    li.setAttribute("aria-label",`${name}: ${current?(completed[key]?"current, completed":"current"):completed[key]?"completed":"upcoming"}`);
  });
  syncOrientation();
  document.getElementById("start").hidden=!!state;
  document.getElementById("start").disabled=!request.value.trim()||busy;
  request.readOnly=!!state&&!editingRequest;
  mode.disabled=busy||mode.options.length===1||terminal||paused;
  if(state){mode.value=state.mode;if(!editingRequest)request.value=state.current_request;}
  document.getElementById("first-answer").hidden=!state?.answer;
  document.getElementById("answer-placeholder").hidden=!!state?.answer;
  document.getElementById("repair-side").hidden=!state?.next;
  document.getElementById("followup-side").hidden=!state?.followup_answer;
  document.getElementById("followup-answer").hidden=!state?.followup_answer;
  document.getElementById("answer-heading").textContent=stage==="post"?"AI answer ready":"AI answer";
  document.getElementById("answer-side").classList.toggle("reading-active",stage==="post");
  if(!state){panel=document.getElementById("request-review");panel.append(node("p",request.value.trim()?"PickyLens checks your request. You choose which suggestions to accept.":"Enter a request to begin.","muted small"));return;}
  if(state.answer){document.getElementById("answer").textContent=state.answer.text;document.querySelector(".answer-label").textContent=state.answer.metadata.acquisition==="replay"?"Genuine captured response · replayed unchanged":state.test_stub?"Synthetic test response":"Live model response";}
  if(state.followup_answer)document.getElementById("followup").textContent=state.followup_answer.text;
  const recovery=document.getElementById("recovery"), tools=document.getElementById("request-tools");
  if(paused){recovery.append(node("p","This interaction is paused. Completed work is saved."),button("Resume interaction",()=>call("resume")));}
  else if(!terminal){
    recovery.append(button("Pause interaction",()=>call("pause"),true));
    tools.append(button(editingRequest?"Save and review request":"Edit request",()=>{
      if(editingRequest){if(request.value.trim())call("request",{request_text:request.value});}
      else{editingRequest=true;render();request.focus();}
    },true));
    if(editingRequest)tools.append(node("p","Changing your request starts a new review. Earlier results stay in History as superseded evidence.","muted small"));
  }
  if(state.intent){const approved=node("details",undefined,"approved-request");approved.append(node("summary","Approved request and requirements"),node("pre",state.selected_prompt));const list=node("ul");state.intent.requirements.forEach(r=>list.append(node("li",r.text)));approved.append(list);document.getElementById("request-review").append(approved);}
  if(state.pending_operation)recovery.append(node("p","Work is in progress. Your completed steps are saved."),button("Refresh saved state",async()=>{state=await(await fetch(`/api/interactions/${state.interaction_id}`)).json();render();},true));
  if(state.failure)recovery.append(node("p",state.failure),button("Retry failed step",()=>call("retry")));
  if(replayRejected)recovery.append(button("Reset to demo request and review",()=>call("reset-scenario")),button("Remain in Live Model",()=>{replayRejected=false;render();},true));
  const blocked=paused||state.pending_operation||state.failure;
  panel=document.getElementById("request-review");
  if(stage==="pre"&&!blocked)showPRE();
  if(stage==="ai"&&!blocked){
    if(state.mode==="replay"&&!state.intent.replay_scenario)panel.append(node("p","This request is not compatible with the captured demo answer."),button("Reset to demo request and review",()=>call("reset-scenario")),button("Continue in Live Model",()=>call("mode",{mode:"live",confirmed_switch:true}),true));
    else panel.append(node("p","Your request is approved. The answer will appear on the right."),button(state.mode==="replay"?"Load captured response":"Send request to AI",()=>call("answer")));
  }
  panel=document.getElementById("answer-review");
  if(stage==="post"&&!blocked)panel.append(button("Check this answer",()=>call("post")));
  if(state.post){
    panel.append(node("h3","PickyLens checked the answer"));counts(state.post);assessments(state.post);
    if(stage==="post_reviewed"&&!blocked&&state.post.assessments.some(a=>["partial","missing"].includes(a.status)))panel.append(button("Fix only what's missing",()=>call("next")));
  }
  if(state.next){
    panel=document.getElementById("repair-panel");
    panel.append(node("p","Ask only for the missing or incomplete work. Review or edit this before sending.","muted small"));
    const draft=node("textarea");draft.id="followup-draft";draft.rows=6;draft.value=state.followup_draft;draft.setAttribute("aria-label","Follow-up prompt");draft.readOnly=stage!=="next"||paused||!!state.pending_operation;panel.append(draft);
    if(stage==="next"&&!paused&&!state.pending_operation){
      draft.onblur=()=>setTimeout(()=>{if(!busy&&document.activeElement?.tagName!=="BUTTON"&&draft.value.trim()&&draft.value!==state.followup_draft)call("followup-draft",{prompt:draft.value});},0);
      if(!state.failure)panel.append(button("Send follow-up",async()=>{if(draft.value!==state.followup_draft){await call("followup-draft",{prompt:draft.value});if(state.followup_draft!==draft.value)return;}await call("followup");}));
      panel.append(button("Save follow-up edits",()=>call("followup-draft",{prompt:draft.value}),true));
    }
  }
  panel=document.getElementById("verification-panel");
  if(stage==="verify"&&!blocked)panel.append(node("p","Read the follow-up answer, then check both responses against your approved request."),button("Verify result",()=>call("verify")));
  if(state.verification){panel.append(node("h3","PickyLens verified the result"));counts(state.post,"Before");counts(state.verification,"After");assessments(state.verification);}
  const review=state.verification||state.post;
  panel=document.getElementById(state.verification?"verification-panel":"answer-review");
  if(review&&["post_reviewed","verified"].includes(stage)&&!blocked){
    const uncertain=review.assessments.filter(a=>a.status==="needs_review");
    if(uncertain.length){
      panel.append(node("p","Some requirements need review. Uncertainty is not treated as a missing requirement."),button("Resolve uncertainty from existing evidence",()=>call("resolve"),true));
      for(const item of uncertain)if(stage==="post_reviewed"&&state.uncertainty_checked.includes(item.requirement_id)&&!state.approved_uncertainty.includes(item.requirement_id))panel.append(button(`Approve a targeted AI question: ${item.requirement_text}`,()=>call("approve-uncertainty",{requirement_ids:[item.requirement_id]}),true));
      if(stage==="post_reviewed"&&state.approved_uncertainty.length&&!review.assessments.some(a=>["partial","missing"].includes(a.status)))panel.append(button("Prepare approved clarification follow-up",()=>call("next")));
      if(!review.assessments.some(a=>["partial","missing"].includes(a.status)))panel.append(button("Leave unresolved and finish with review items",()=>call("finish-review"),true));
    }
  }
  if(review&&["done","verified"].includes(stage)){
    const complete=review.assessments.filter(a=>a.status==="complete").length,total=review.assessments.length;
    panel.append(node("h3",state.lifecycle_status==="Completed with review items"?"Completed with review items":stage==="done"?"Verified completion":"Unresolved requirements remain"),node("p",`${complete} of ${total} requirements are fulfilled. ${total-complete} remain incomplete or need review.`));
    const link=node("a","Inspect saved interaction");link.href=`/interactions/${state.interaction_id}`;panel.append(link);
  }
}

document.getElementById("start").onclick=()=>call("pre",{request_text:request.value,mode:mode.value,canonical_scenario:canonical&&!mode.disabled});
request.oninput=()=>{canonical=false;if(!state)render();};
render();
