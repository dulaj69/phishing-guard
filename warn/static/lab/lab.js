'use strict';
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state = {view:'overview', results:{}, session:null, currentTrial:null};
const names = {overview:'Research overview', actions:'Action contrast & robustness', evidence:'Evidence dependency audit', warnings:'Warning comprehension & transfer'};
const conditionName = c => ({static:'Static',user_only:'User only',evidence_aware:'User + evidence'}[c] || c);
const badge = (text, cls='') => `<span class="pill ${cls}">${esc(text)}</span>`;
const metric = (value, label) => `<div class="metric"><b>${esc(value)}</b><span>${esc(label)}</span></div>`;
function showError(error){$('error').textContent=error.message || String(error);$('error').hidden=false;}
async function api(path, data){const response=await fetch('/research'+path,data === undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-Research-Request':'1'},body:JSON.stringify(data)});const body=await response.json();if(!response.ok)throw Error(typeof body.detail==='string'?body.detail:'The request could not be completed.');return body;}
async function busy(id, fn){const b=$(id), text=b.textContent;b.disabled=true;b.textContent='Running…';$('error').hidden=true;try{await fn();}catch(e){showError(e);}finally{b.disabled=false;b.textContent=text;}}
function saveResult(result, view=state.view){state.results[view]=result;if(state.view===view)$('export').disabled=false;}
function navigate(view){state.view=view;document.querySelectorAll('.view').forEach(e=>e.hidden=e.id!==view);document.querySelectorAll('[data-view]').forEach(e=>e.classList.toggle('active',e.dataset.view===view));$('page-name').textContent=names[view];$('export').disabled=!state.results[view];$('error').hidden=true;window.scrollTo({top:0,behavior:'smooth'});}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>navigate(b.dataset.view));$('start-tour').onclick=()=>navigate('actions');
$('export').onclick=()=>{const result=state.results[state.view];if(!result)return;const blob=new Blob([JSON.stringify({...result,exported_at:new Date().toISOString()},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`verify-then-warn-${state.view}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
function limitation(text){return `<div class="note"><b>Interpretation limit.</b> ${esc(text)}</div>`;}

$('inspect').onclick=()=>busy('inspect',async()=>{
 const r=await api('/robustness',{case_id:$('case').value});saveResult(r,'actions');
 $('action-result').innerHTML=`${badge('Live diagnostic','green')} <span class="small">Model ${esc(r.model_fingerprint)}</span><div class="message">${esc(r.case.text)}</div><p class="small">Authored expected action: <b>${esc(r.case.expected_action)}</b> · Language: ${esc(r.case.language)}</p><div class="metrics">${metric(`${r.summary.correct_actions}/${r.summary.variants}`,'variants with expected action')}${metric(r.summary.raw_label_changes,'raw label changes vs original')}${metric(r.summary.normalized_label_changes,'label changes after normalisation')}</div><div class="table-wrap"><table><thead><tr><th>Test</th><th>Raw classifier</th><th>Normalised classifier</th><th>Requested action</th></tr></thead><tbody>${r.rows.map(row=>`<tr><td class="message-cell"><b>${esc(row.name)}</b><span class="small">${esc(row.text)}</span></td><td>${esc(row.raw_label)}<span class="small">Score ${row.raw_score.toFixed(3)}</span></td><td>${esc(row.label)}<span class="small">Score ${row.score.toFixed(3)} · ${esc(row.tricks.join(', ')||'No normalization changes')}</span></td><td class="${row.action_correct?'ok':'bad'}">${esc(row.action)}<span class="small">${row.action_correct?'Matches fixture':'Mismatch — retain as a finding'}</span></td></tr>`).join('')}</tbody></table></div><h3 style="margin-top:25px">Inspect the action evidence</h3>${r.rows.map(row=>`<details class="detail-box"><summary>${esc(row.name)} · keyword comparator: ${esc(row.keyword_action)}</summary><p>Normalised text: ${esc(row.normalized_text)}</p>${row.evidence.length?row.evidence.map(e=>`<p>${badge(e.status,e.status==='requested'?'green':'amber')} ${esc(e.action)}<br>“${esc(e.text)}” <span class="small">[${e.start}, ${e.end})</span></p>`).join(''):'<p>No explicit action evidence extracted.</p>'}</details>`).join('')}${limitation(r.limitation)}`;
});
$('benchmark').onclick=()=>busy('benchmark',async()=>{
 const r=await api('/benchmark',{});saveResult(r,'actions');
 $('action-result').innerHTML=`${badge('Measured on authored fixtures','green')}<div class="metrics">${metric(r.cases,'diagnostic cases')}${metric(`${r.keyword_correct}/${r.cases}`,'keyword-only action matches')}${metric(`${r.context_correct}/${r.cases}`,'context-rule action matches')}</div><div class="panel"><h3>Action matches by language</h3>${r.per_language.map(g=>`<div class="bar-row"><b>${esc(g.language)}</b><div class="bar"><i style="width:${100*g.context_correct/g.n}%"></i></div><span>${g.context_correct}/${g.n}</span></div>`).join('')}<p class="small">Bars show contextual action matches, not population accuracy. Denominators include every diagnostic case in that language.</p></div><div class="table-wrap subpanel"><table><thead><tr><th>Case</th><th>Expected action</th><th>Keyword-only</th><th>Context rules</th></tr></thead><tbody>${r.rows.map(row=>`<tr><td class="message-cell"><b>${esc(row.id)}</b><span class="small">${esc(row.text)}</span></td><td>${esc(row.expected)}</td><td class="${row.keyword===row.expected?'ok':'bad'}">${esc(row.keyword)}</td><td class="${row.correct?'ok':'bad'}">${esc(row.context)}</td></tr>`).join('')}</tbody></table></div>${limitation(r.limitation)}`;
});

$('score').oninput=()=>{$('score-value').textContent=Number($('score').value).toFixed(2);};
$('audit').onclick=()=>busy('audit',async()=>{
 const r=await api('/evidence',{scenario:$('evidence-scenario').value,score:Number($('score').value),contradiction:$('contradiction').checked,copied_domain:$('copied-domain').checked,stale:$('stale').checked,missing:$('missing').checked,uncertainty:$('uncertain-action').checked});saveResult(r,'evidence');
 $('evidence-result').innerHTML=`<div class="verdict"><div class="eyebrow">EVIDENCE-AWARE POLICY</div><b>${r.risk.abstain?'Abstain · verify independently':esc(r.risk.tier+' risk')}</b><p>Provisional tier: ${esc(r.risk.tier)} · Evidence: ${esc(r.risk.evidence_quality)} · Harm level: ${r.risk.harm}</p></div><div class="message">${esc(r.scenario.text)}</div><div class="metrics">${metric(r.baselines.likelihood_only,'score-band baseline')}${metric(r.baselines.matrix_only,'score × harm matrix')}${metric(r.baselines.evidence_policy,'evidence-aware tier')}</div><div class="panel"><h3>What did we actually check?</h3><ul class="evidence-list">${r.checks.length?r.checks.map(c=>`<li>${badge(c.result,c.result==='fail'?'red':c.result==='pass'?'green':'amber')}${esc(c.detail)}<span class="small">Fictional source · ${esc(c.source.freshness)}</span></li>`).join(''):'<li>No evidence is available in this intervention.</li>'}</ul><h3>Remove one fact</h3>${r.removal_audit.length?r.removal_audit.map(a=>`<p class="small"><b>${esc(a.removed)}</b> removed → ${esc(a.tier)}${a.abstain?' / abstain':''} ${badge(a.decision_changed?'Decision changes':'Decision preserved',a.decision_changed?'amber':'green')}</p>`).join(''):'<p class="small">No facts to remove.</p>'}<h3 style="margin-top:22px">Smallest sufficient evidence sets</h3>${r.minimal_sufficient_sets.map(set=>`<p>${set.length?set.map(s=>badge(s)).join(' '):badge('No external fact required for this policy result','amber')}</p>`).join('')}<p class="small">These sets preserve the current tier and abstention state. They do not establish truth or real-world causality.</p></div><div class="table-wrap subpanel"><table><thead><tr><th>Evidence available</th><th>Tier</th><th>Decision</th></tr></thead><tbody>${r.coverage.map(c=>`<tr><td>${esc(c.evidence)}</td><td>${esc(c.tier)}</td><td>${c.abstain?'Abstain':'Assessed'}</td></tr>`).join('')}</tbody></table></div>${limitation(r.limitation)}`;
});

$('preview').onclick=()=>busy('preview',async()=>{
 const r=await api('/warning-preview',{persona:$('persona').value,case_id:$('preview-case').value});saveResult(r,'warnings');
 $('preview-result').innerHTML=`<div class="message">${esc(r.text)}</div>${badge('Simulated profiles · no participant data','amber')}<div class="cards three">${r.conditions.map(c=>`<div class="preview-card"><b>${esc(conditionName(c.condition))}</b><p>${badge(c.warning.intervention)}</p>${c.warning.verification_prompt?`<div class="prompt"><b>Before advice</b><p>${esc(c.warning.verification_prompt)}</p></div>`:''}<h3>${esc(c.warning.title)}</h3><ul>${c.warning.lines.map(l=>`<li>${esc(l.text)}</li>`).join('')}</ul></div>`).join('')}</div>${limitation(r.limitation)}`;
});
$('session-mode').onchange=()=>{$('pilot-consent-row').hidden=$('session-mode').value!=='pilot';};
$('start-session').onclick=()=>busy('start-session',async()=>{
 const s=await api('/pilot/sessions',{mode:$('session-mode').value,consent:$('pilot-consent').checked});
 state.session=s;state.currentTrial=null;$('pilot-setup').hidden=true;$('pilot-active').hidden=false;$('pilot-report').hidden=true;renderTrial();
});
function choices(name, items){return `<div class="options">${items.map(([v,t])=>`<label><input type="radio" name="${name}" value="${v}" required>${esc(t)}</label>`).join('')}</div>`;}
function confidence(id,label){return `<label class="confidence">${label} <output id="${id}-value">50</output>/100<input id="${id}" type="range" min="0" max="100" value="50"></label>`;}
function bindConfidence(id){$(id).oninput=()=>{$(id+'-value').textContent=$(id).value;};}
function selected(name){return document.querySelector(`input[name="${name}"]:checked`)?.value;}
function trialHeader(){const s=state.session;return `<div class="trial-top"><span>${badge(s.mode==='rehearsal'?'Demo rehearsal':'Consented pilot',s.mode==='rehearsal'?'amber':'blue')} Trial ${s.completed+1} / ${s.total}</span><span>${s.item.phase==='transfer'?'No-advice transfer block':'Advice block'}</span></div><div class="progress"><i style="width:${100*s.completed/s.total}%"></i></div><div class="message">${esc(s.item.text)}</div>`;}
function renderTrial(){
 $('pilot-active').innerHTML=`${trialHeader()}<form id="initial-form"><fieldset><legend>Your judgement before any advice</legend>${choices('initial',[['scam','Scam'],['safe','Safe']])}</fieldset>${confidence('initial-confidence','Confidence')}<div class="trial-actions"><button id="submit-initial" class="primary" type="submit">Lock initial response →</button></div></form><p class="small">Fictional scenario. No number will be called and no link will be opened.</p>`;
 bindConfidence('initial-confidence');
 $('initial-form').onsubmit=e=>{e.preventDefault();busy('submit-initial',async()=>{
  state.currentTrial=await api(`/pilot/${state.session.session_id}/initial`,{index:state.session.completed,choice:selected('initial'),confidence:Number($('initial-confidence').value)});
  renderAdvice();
 });};
}
function renderAdvice(){
 const r=state.currentTrial,w=r.warning;
 if(w?.verification_prompt){
  $('pilot-active').innerHTML=`${trialHeader()}<div class="warning-box"><h3>Check one thing before advice</h3><p>${esc(w.verification_prompt)}</p><p class="small">All details here are fictional. In a real message, consult your own card or independently opened bank app.</p><button id="reveal-advice" class="secondary">I have considered what I would check →</button></div>`;
  $('reveal-advice').onclick=renderFinal;
 }else renderFinal();
}
function renderFinal(){
 const r=state.currentTrial,w=r.warning;
 $('pilot-active').innerHTML=`${trialHeader()}${w?`<div class="warning-box"><div class="eyebrow">APP ADVICE · ${esc(r.ai_advice)}</div><h3>${esc(w.title)}</h3><ul>${w.lines.map(l=>`<li>${esc(l.text)}</li>`).join('')}</ul>${w.advice?`<p>${esc(w.advice)}</p>`:''}</div>`:'<div class="note"><b>No AI advice on this trial.</b> Decide independently from the message.</div>'}<form id="final-form"><fieldset><legend>Your final judgement</legend>${choices('final',[['scam','Scam'],['safe','Safe']])}</fieldset>${confidence('final-confidence','Final confidence')}<fieldset><legend>What would you do?</legend>${choices('action',[['independent_check','Check independently with the bank'],['follow_sms','Follow the SMS instruction'],['ignore_report','Ignore or report']])}</fieldset>${r.question?`<fieldset><legend>${esc(r.question.text)}</legend>${choices('comprehension',r.question.options.map((t,i)=>[i,t]))}</fieldset>`:''}<button id="submit-final" class="primary" type="submit">Save response →</button></form>`;
 bindConfidence('final-confidence');
 $('final-form').onsubmit=e=>{e.preventDefault();busy('submit-final',async()=>{
  const next=await api(`/pilot/${state.session.session_id}/final`,{index:state.session.completed,choice:selected('final'),confidence:Number($('final-confidence').value),action:selected('action'),comprehension:r.question?Number(selected('comprehension')):null});
  state.session=next.next;
  if(!state.session.item){await renderReport();return;}
  $('pilot-active').innerHTML=`<div class="feedback">${esc(next.feedback)}</div><button id="next-trial" class="primary">Next scenario →</button>`;
  $('next-trial').onclick=renderTrial;
 });};
}
async function renderReport(){
 const r=await api(`/pilot/${state.session.session_id}/report`);saveResult(r,'warnings');$('pilot-active').hidden=true;$('pilot-report').hidden=false;
 const ratio=g=>g.n?`${g.correct}/${g.n}`:'Not measured';
 $('pilot-report').innerHTML=`<div class="verdict"><div class="eyebrow">SESSION COMPLETE · ${esc(r.kind)}</div><b>Your observed decisions</b><p>${esc(conditionName(r.condition))} · ${r.completed} trials · one session</p></div><div class="metrics">${metric(ratio(r.phases.advice),'correct decisions with advice')}${metric(ratio(r.phases.transfer),'correct decisions without advice')}${metric(r.reliance.RSR===null?'No opportunities':r.reliance.RSR.toFixed(2),`RSR · n=${r.reliance.RSR_opportunities}`)}</div><div class="note"><b>Debrief.</b> ${esc(state.session.debrief)}</div><div class="table-wrap"><table><thead><tr><th>Trial</th><th>Phase</th><th>Initial → final</th><th>Correct</th><th>Confidence</th><th>Comprehension</th></tr></thead><tbody>${r.rows.map(row=>`<tr><td>${esc(row.item_id)}</td><td>${esc(row.phase)}</td><td>${esc(row.initial)} → ${esc(row.final)}</td><td class="${row.correct?'ok':'bad'}">${row.correct?'Yes':'No'}</td><td>${row.initial_confidence} → ${row.final_confidence}</td><td>${row.comprehension_correct===null?'Not asked':row.comprehension_correct?'Correct':'Incorrect'}</td></tr>`).join('')}</tbody></table></div>${limitation(r.limitation)}<button id="new-session" class="secondary">Prepare another session</button>`;
 $('new-session').onclick=()=>{$('pilot-report').hidden=true;$('pilot-setup').hidden=false;state.session=null;};
}
async function boot(){try{const c=await api('/catalog');$('fixture-count').textContent=c.cases.length;$('fingerprint').textContent='Model fingerprint '+c.model_fingerprint;$('case').innerHTML=c.cases.map(x=>`<option value="${esc(x.id)}">${esc(x.name)} · ${esc(x.language)}</option>`).join('');$('contributions').innerHTML=c.contributions.map((x,i)=>`<article class="card"><div class="owner">0${i+1} / ${esc(x.owner)}</div><h3>${esc(x.title)}</h3><p>${esc(x.question)}</p><div class="built"><b>IMPLEMENTED</b><p>${esc(x.built)}</p></div><div class="next"><b>Next evidence milestone</b><br>${esc(x.remaining)}</div><button class="quiet" data-open="${['actions','evidence','warnings'][i]}">Open experiment ↗</button></article>`).join('');document.querySelectorAll('[data-open]').forEach(b=>b.onclick=()=>navigate(b.dataset.open));}catch(e){showError(e);}}
boot();
// Direct links from the individual workspace keep each member's component visible.
if (['overview','actions','evidence','warnings'].includes(location.hash.slice(1))) navigate(location.hash.slice(1));
