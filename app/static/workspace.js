"use strict";
let state = JSON.parse(document.getElementById("initial-state").textContent);
const panel = document.getElementById("panel"), request = document.getElementById("request");
let busy = false, editingRequest=false;
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
  busy=true; document.getElementById("error").hidden=true;
  document.querySelectorAll("button").forEach(b=>b.disabled=true);
  const payload={operation_id:crypto.randomUUID(), ...extra};
  if(state)payload.expected_revision=state.revision;
  const url=state?`/api/interactions/${state.interaction_id}/${action}`:"/api/interactions/pre";
  try {
    const response=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    const result=await response.json();
    if(result.snapshot){state=result.snapshot;history.replaceState(null,"",`/?interaction=${state.interaction_id}`);}
    if(!response.ok)throw new Error(typeof result.detail==="string"?result.detail:"This action could not be completed.");
    state=await (await fetch(`/api/interactions/${result.interaction_id}`)).json();
    editingRequest=false;
    replayRejected=false;
    history.replaceState(null,"",`/?interaction=${state.interaction_id}`);
    document.getElementById("saved").textContent="Saved to Interactions";
  } catch(e) { if(action==="mode"&&extra.mode==="replay")replayRejected=true; const box=document.getElementById("error");box.textContent=e.message;box.hidden=false; }
  finally { busy=false; render(); }
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
  panel.append(node("span",meanings[p.readiness],"readiness "+p.readiness));
  p.findings.forEach(f=>{const item=node("div",undefined,"finding");item.append(node("strong",f.title),node("p",f.explanation));panel.append(item);});
  const controls={};
  p.clarifications.forEach(c=>{
    const label=node("label",c.question), select=node(c.options.length?"select":"input");select.id="clarification-"+c.key;label.htmlFor=select.id;
    const blank=node("option","Choose a priority\u2026");blank.value="";if(c.options.length)select.append(blank);
    c.options.forEach(v=>{const o=node("option",v);o.value=v;select.append(o);});
    select.value=state.accepted_clarifications[c.key]||"";controls[c.key]=select;panel.append(label,select);
  });
  if(p.clarifications.length)panel.append(button("Save my clarification",()=>{
    const clarifications={};Object.entries(controls).forEach(([k,v])=>{if(v.value)clarifications[k]=v.value;});call("clarifications",{clarifications});
  },true));
  panel.append(node("h2","Improved prompt"));
  const improved=node("pre",p.improved_prompt+Object.entries(state.accepted_clarifications).map(([k,v])=>`\nAccepted ${k}: ${v}`).join(""));panel.append(improved);
  if(mode.value==="replay"){
    const details=node("details");details.append(node("summary","Canonical Replay request and requirements"),node("pre",demo.prompt));
    const canonicalList=node("ul");demo.requirements.forEach(t=>canonicalList.append(node("li",t)));details.append(canonicalList);panel.append(details);
    panel.append(node("p","Replay requires approval of this unchanged canonical intent. Approving this preset uses the original request with no accepted clarifications, replacing any clarification choices above. Use Live Model to keep a changed intent."));
    if(state.canonical_ready)panel.append(button("Approve canonical Replay request",()=>call("approve-canonical",{confirmed_red:p.readiness!=="red"||confirm("Send canonical original despite the PRE warning?")})));
    panel.append(button("Reset to canonical scenario and review",()=>call("reset-scenario"),true));
  }
  panel.append(node("h2","Requirements you are approving"));
  const list=node("ul",undefined,"intent-list");p.requirements.forEach(r=>list.append(node("li",r.text)));
  Object.entries(state.accepted_clarifications).forEach(([k,v])=>list.append(node("li",`Improved prompt only \u2014 Accepted ${k}: ${v}`)));
  panel.append(list,node("p","Using a prompt approves these requirements for POST and VERIFY. Sending the original excludes unaccepted PRE suggestions.","muted small"));
  const improvedAction=button("Use improved prompt",()=>call("approve-intent",{choice:"improved"}));
  improvedAction.disabled=p.clarifications.some(c=>c.required&&!state.accepted_clarifications[c.key]);
  panel.append(improvedAction);
  panel.append(button(p.readiness==="red"?"Send original anyway":"Send original",()=>{
    const confirmed=p.readiness!=="red"||confirm("Send the original despite the important issue?");
    if(confirmed)call("approve-intent",{choice:"original",confirmed_red:p.readiness==="red"});
  },true));
  panel.append(button("Edit improved prompt",()=>{editingRequest=true;request.readOnly=false;request.value=improved.textContent;request.focus();render();},true));
}
function render() {
  panel.replaceChildren();
  document.getElementById("start").hidden=!!state;
  document.getElementById("start").disabled=!request.value.trim()||busy;
  request.readOnly=!!state&&!editingRequest;
  if(state){mode.value=state.mode;if(!editingRequest)request.value=state.current_request;}
  const stage=state?.stage||"pre";
  document.querySelectorAll("#progress li").forEach(li=>li.classList.toggle("active",li.textContent.toLowerCase()===(stage==="post_reviewed"?"post":stage==="done"||stage==="verified"?"verify":stage)));
  if(!state){panel.append(node("h2","Ready to review your request."),node("p",request.value.trim()?"Start with a deliberate review. You choose what is sent.":"Enter a request to begin."));return;}
  document.getElementById("first-answer").hidden=!state.answer;
  document.getElementById("followup-answer").hidden=!state.followup_answer;
  if(state.answer){document.getElementById("first-answer").hidden=false;document.getElementById("answer").textContent=state.answer.text;document.querySelector(".answer-label").textContent=state.answer.metadata.acquisition==="replay"?"Captured genuine response - replayed unchanged":state.test_stub?"Synthetic development response":"Live model response";}
  if(state.followup_answer){document.getElementById("followup-answer").hidden=false;document.getElementById("followup").textContent=state.followup_answer.text;}
  if(state.lifecycle_status==="Paused") {panel.append(node("p","This interaction is paused. Completed work is saved."),button("Resume interaction",()=>call("resume")));return;}
  if(!state.terminal && stage!=="done") {
    panel.append(button("Pause interaction",()=>call("pause"),true));
    panel.append(button(editingRequest?"Save request and run PRE again":"Edit request",()=>{
      if(editingRequest){if(request.value.trim())call("request",{request_text:request.value});}
      else {editingRequest=true;request.readOnly=false;request.focus();render();}
    },true));
    if(editingRequest)panel.append(node("p","Your request changed. Previous results will be preserved as superseded evidence; PRE and intent approval must run again."));
  }
  if(state.pending_operation){panel.append(node("p","Operation in progress. Saved work is preserved."),button("Refresh saved state",async()=>{state=await(await fetch(`/api/interactions/${state.interaction_id}`)).json();render();},true));return;}
  if(state.failure){panel.append(node("p",state.failure),button("Retry failed step",()=>call("retry")));if(state.stage!=="next")return;}
  if(replayRejected)panel.append(button("Reset to canonical scenario and review",()=>call("reset-scenario")),button("Remain in Live Model",()=>{replayRejected=false;render();},true));
  if(stage==="pre"){showPRE();return;}
  if(stage==="ai"&&state.mode==="replay"&&!state.intent.replay_scenario){panel.append(button("Reset to canonical scenario and review",()=>call("reset-scenario")),button("Continue in Live Model",()=>call("mode",{mode:"live",confirmed_switch:true})));return;}
  if(stage==="ai"){panel.append(node("h2","Intent approved"),node("p","The requirement set is frozen for POST and VERIFY."),button("Generate AI response",()=>call("answer")));return;}
  if(stage==="post"){panel.append(node("h2","Ready for POST"),node("p","Compare the answer with your approved intent."),button("Run POST review",()=>call("post")));return;}
  const review=state.verification||state.post;
  if(review){
    panel.append(node("h2",state.verification?"VERIFY \xb7 evidence of improvement":"POST \xb7 requirement review"));
    if(state.verification)counts(state.post,"Before follow-up");
    counts(review,state.verification?"After follow-up and re-check":"");assessments(review);
  }
  if(stage==="post_reviewed"||stage==="verified") {
    if(stage==="post_reviewed"&&review.assessments.some(a=>["partial","missing"].includes(a.status)))panel.append(button("Fix only what's missing",()=>call("next")));
    const uncertain=review.assessments.filter(a=>a.status==="needs_review");
    if(uncertain.length){
      panel.append(button("Resolve uncertainty from existing evidence",()=>call("resolve"),true));
      for(const item of uncertain){
        if(stage==="post_reviewed"&&state.uncertainty_checked.includes(item.requirement_id)&&!state.approved_uncertainty.includes(item.requirement_id))panel.append(button(`Approve a targeted AI question: ${item.requirement_text}`,()=>call("approve-uncertainty",{requirement_ids:[item.requirement_id]}),true));
      }
      if(stage==="post_reviewed"&&state.approved_uncertainty.length)panel.append(button("Prepare approved clarification follow-up",()=>call("next")));
      if(!review.assessments.some(a=>["partial","missing"].includes(a.status)))panel.append(button("Leave unresolved and finish with review items",()=>call("finish-review"),true));
    }
  }
  if(stage==="next") {
    panel.append(node("h2","Targeted follow-up"),node("p","Review or edit this before sending. The memo will not be repeated."));
    const draft=node("textarea");draft.id="followup-draft";draft.rows=5;draft.value=state.followup_draft;draft.setAttribute("aria-label","Follow-up prompt");panel.append(draft);
    draft.onblur=()=>setTimeout(()=>{if(!busy&&document.activeElement?.tagName!=="BUTTON"&&draft.value.trim()&&draft.value!==state.followup_draft)call("followup-draft",{prompt:draft.value});},0);
    panel.append(button("Save follow-up edits",()=>call("followup-draft",{prompt:draft.value}),true));
    if(!state.failure)panel.append(button("Send follow-up to AI",async()=>{
      if(draft.value!==state.followup_draft){await call("followup-draft",{prompt:draft.value});if(state.followup_draft!==draft.value)return;}
      await call("followup");
    }));
  }
  if(stage==="verify")panel.append(button("Verify combined responses",()=>call("verify")));
  if(stage==="done"||stage==="verified"){
    const complete=review.assessments.filter(a=>a.status==="complete").length,total=review.assessments.length;
    panel.append(node("h2",state.lifecycle_status==="Completed with review items"?"Completed with review items":stage==="done"?"Verified completion":"Unresolved requirements remain"));
    panel.append(node("p",`${complete} of ${total} requirements are fulfilled. ${total-complete} remain incomplete or need review.`));
    const link=node("a","Inspect saved Interaction \u2192");link.href=`/interactions/${state.interaction_id}`;panel.append(link);
  }
}
document.getElementById("start").onclick=()=>call("pre",{request_text:request.value,mode:mode.value,canonical_scenario:canonical&&!mode.disabled});
request.oninput=()=>{canonical=false;if(!state)render();};
render();
