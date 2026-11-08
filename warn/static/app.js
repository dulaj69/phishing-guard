// Phishing Guard inbox app (Rathnayake's part).
// Demo mode: shows everything, good for the viva.
// Study mode: asks the participant first, hides the answers, logs decisions.

const $ = (id) => document.getElementById(id);
const state = { scenarios: [], current: null, done: new Set() };

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function api(path, body) {
  const res = await fetch(path, body ? {
    method: "POST", headers: { "Content-Type": "application/json", "X-Research-Request": "1" }, body: JSON.stringify(body),
  } : {});
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
  return res.json();
}

const mode = () => $("mode").value;
const pid = () => $("pid").value.trim();

// ---------------- Inbox ----------------
async function loadInbox() {
  state.scenarios = await api("/scenarios");
  const list = $("threads");
  list.innerHTML = state.scenarios.map((s) => `
    <li data-id="${esc(s.id)}">
      ${state.done.has(s.id) ? '<span class="done">done</span>' : ""}
      <div class="from">${esc(s.sender)}</div>
      <div class="preview">${esc(s.text)}</div>
    </li>`).join("");
  list.querySelectorAll("li").forEach((li) =>
    li.addEventListener("click", () => openMessage(state.scenarios.find((s) => s.id === li.dataset.id))));
}

function show(screen) {
  $("inbox").hidden = screen !== "inbox";
  $("thread").hidden = screen !== "thread";
}

function openMessage(msg) {
  if (mode() === "study" && !pid()) { alert("Enter the participant ID first."); return; }
  if (mode() === "study" && !$("consent").checked) { alert("Read and accept the pilot consent before starting."); return; }
  state.current = { msg, start: performance.now(), initial: null, result: null,
    adviceRevealed: false, condition: $("condition").value, study: mode() === "study", user: pid(), finished: false };
  ["mode", "pid", "condition", "lang"].forEach(id => $(id).disabled = true);
  $("t-sender").textContent = msg.sender || "Unknown sender";
  $("t-text").textContent = msg.text;
  ["tricks", "warning", "actions", "after", "loading"].forEach((id) => ($(id).hidden = true));
  $("hood-body").innerHTML = "";
  show("thread");
  if (mode() === "study") {
    $("initial").hidden = false;
  } else {
    $("initial").hidden = true;
    runAnalysis();
  }
}

document.querySelectorAll("[data-initial]").forEach((b) =>
  b.addEventListener("click", () => {
    state.current.initial = b.dataset.initial;
    $("initial").hidden = true;
    runAnalysis();
  }));

async function runAnalysis() {
  const { msg } = state.current;
  $("loading").hidden = false;
  try {
    const result = await api("/analyze", {
      text: msg.text, sender: msg.sender || null, language: $("lang").value || null,
      user_id: state.current.study ? state.current.user : null, scenario_id: msg.id && !msg.custom ? msg.id : null,
      study_mode: state.current.study, initial_choice: state.current.initial,
      condition: state.current.condition, session: 1,
    });
    state.current.result = result;
    renderMessage(result);
    renderHood(result);
    if (result.warning.verification_prompt && result.warning.show) {
      $("warning").hidden = false;
      $("warning").innerHTML = `<div class="warn Medium"><p>${esc(result.warning.verification_prompt)}</p><button class="btn" id="checked-fact">I checked independently</button> <button class="btn" id="cannot-check">I cannot check now</button></div>`;
      const reveal = (answer) => { state.current.adviceRevealed = true; state.current.verificationResponse = answer; renderWarning(result.warning); renderActions(result); };
      $("checked-fact").onclick = () => reveal("checked");
      $("cannot-check").onclick = () => reveal("unable");
    } else {
      state.current.adviceRevealed = true;
      renderWarning(result.warning);
      renderActions(result);
    }
  } catch (e) {
    $("warning").hidden = false;
    $("warning").innerHTML = `<div class="feedback">Error: ${esc(e.message)}</div>`;
  } finally {
    $("loading").hidden = true;
  }
}

// ---------------- Message + highlights ----------------
function renderMessage(r) {
  const d = r.detection;
  const original = state.current.msg.text;
  if (d.normalized_text === original.trim()) {
    let html = "", pos = 0;
    const spans = r.warning.highlights.slice().sort((a, b) => a.start - b.start);
    for (const s of spans) {
      if (s.start < pos) continue;
      html += esc(original.slice(pos, s.start));
      const cls = s.type === "CONTACT" ? "contact" : "";
      html += `<mark class="${cls}" title="${esc(s.type)}">${esc(original.slice(s.start, s.end))}</mark>`;
      pos = s.end;
    }
    $("t-text").innerHTML = html + esc(original.slice(pos));
    $("t-text").querySelectorAll("mark.contact").forEach((m) =>
      m.addEventListener("click", () => act("call_sms_number")));
  }
  if (d.tricks_found.length) {
    $("tricks").hidden = false;
    $("tricks").textContent = "Hidden tricks found: " + d.tricks_found.join(", ").replaceAll("_", " ");
  }
}

// ---------------- Warning ----------------
function renderWarning(w) {
  const box = $("warning");
  box.hidden = false;
  if (!w.show) {
    box.innerHTML = `<div class="warn Low"><h3>${esc(w.title)}</h3></div>`;
    return;
  }
  const lines = w.lines.map((l) => `<li>${esc(l.text)}${
    w.show_sources && l.evidence ? `<span class="src">Source: ${esc(l.evidence.url)} (checked ${esc(l.evidence.checked)})</span>` : ""
  }</li>`).join("");
  const safe = w.safe_action
    ? `<button class="btn primary" id="safe-btn">${esc(w.safe_action.text)}</button>` : "";
  box.innerHTML = `
    <div class="warn ${esc(w.level)}">
      <h3>${esc(w.title)}</h3>
      <ul>${lines}</ul>
      <div class="advice">${esc(w.advice)}</div>
      ${safe}
      ${w.demo_evidence ? '<div class="review">Fictional bank evidence for demonstration only.</div>' : ""}
      ${w.needs_language_review ? '<div class="review">Draft wording, awaiting native-speaker review.</div>' : ""}
    </div>`;
  if (w.safe_action) $("safe-btn").addEventListener("click", () => chooseAfterOfficial());
}

function chooseAfterOfficial() {
  modal(`<h3>You chose the independently verified contact.</h3><p>How do you classify the original SMS?</p><button class="btn" id="official-scam">Scam</button> <button class="btn" id="official-safe">Safe</button>`);
  ["scam", "safe"].forEach(choice => $("official-" + choice).onclick = () => { closeModal(); finish("call_official", choice); });
}

function renderActions(r) {
  const contacts = r.detection.anatomy.contacts;
  $("btn-call").hidden = !contacts.some((c) => c.type === "phone" || c.type === "short_code");
  $("btn-link").hidden = !contacts.some((c) => c.type === "url");
  $("actions").hidden = false;
}

document.querySelectorAll("[data-act]").forEach((b) => b.addEventListener("click", () => act(b.dataset.act)));

function act(action) {
  const w = state.current.result?.warning;
  if (!w || !state.current.adviceRevealed || state.current.finished) return;
  if (action === "call_sms_number" && w.verify_question) return verifyFirst(w.verify_question);
  if (action === "trust" && w.show) return contest();
  if (action === "report") return finish("report", "scam");
  if (action === "trust") return finish("trust", "safe");
  return finish(action, "safe");  // calling the SMS number or opening the link = trusting it
}

// Cognitive forcing: pick the bank's real number before calling.
function verifyFirst(q) {
  modal(`
    <h3>${esc(q.text)}</h3>
    <div class="opts">${q.options.map((o) => `<button class="btn" data-pick="${esc(o)}">${esc(o)}</button>`).join("")}</div>
    <p class="muted">Tip: the real number is on the back of your card and on the bank's website.</p>`);
  document.querySelectorAll("[data-pick]").forEach((b) => b.addEventListener("click", () => {
    const right = b.dataset.pick === q.answer;
    closeModal();
    finish(right ? "verify_first_correct" : "verify_first_wrong", right ? "scam" : "safe",
      right ? "Correct. That is the bank's real number. The number in the SMS is not." :
              "That number came from the SMS, not from the bank. Scammers use their own numbers.");
  }));
}

// Contest: the user disagrees, so show the evidence and let them decide.
function contest() {
  const v = state.current.result.verification;
  const checks = v.fact_checks.map((c) =>
    `<div class="check"><b class="${c.result}">${c.result.toUpperCase()}</b> ${esc(c.detail)}${
      c.source ? `<span class="src muted"> (${esc(c.source.url)}, ${esc(c.source.checked)})</span>` : ""}</div>`).join("")
    || '<p class="muted">No facts could be checked for this message.</p>';
  modal(`
    <h3>Here is what we checked</h3>
    ${checks}
    <p>${v.risk.reasons.slice(0, 2).map(esc).join(". ")}.</p>
    <div class="opts">
      <button class="btn danger" id="c-scam">OK, treat it as a scam</button>
      <button class="btn" id="c-real">I still think it is real</button>
    </div>`);
  $("c-scam").addEventListener("click", () => { closeModal(); finish("contest_changed", "scam"); });
  $("c-real").addEventListener("click", () => { closeModal(); finish("contest_kept", "safe"); });
}

async function finish(action, finalChoice, message) {
  const cur = state.current;
  if (cur.finished) return;
  cur.finished = true;
  const r = cur.result;
  $("actions").hidden = true;
  let html = "";
  if (message) html += `<div class="feedback">${esc(message)}</div>`;

  if (mode() === "study" && !cur.msg.custom) {
    try {
      const profile = await api("/decision", {
        analysis_id: r.analysis_id, user_id: cur.user, message_id: cur.msg.id, ai_advice: r.ai_advice, final_choice: finalChoice,
        initial_choice: cur.initial, action: cur.verificationResponse ? `${action}:verification_${cur.verificationResponse}` : action, intervention: r.warning.intervention,
        seconds: Math.round((performance.now() - cur.start) / 100) / 10,
      });
      html += `<div class="feedback">Saved. Next message, please.</div>`;
      renderProfile(profile);
    } catch (e) {
      cur.finished = false;
      $("actions").hidden = false;
      html += `<div class="feedback">Could not save: ${esc(e.message)}</div>`;
    }
    if (cur.finished) state.done.add(cur.msg.id);
  } else {
    html += `<div class="feedback">You chose: <b>${finalChoice === "scam" ? "treat as scam" : "trust it"}</b> (${esc(action.replaceAll("_", " "))}).</div>`;
  }
  if (r.warning.lesson) html += `<div class="lesson">${esc(r.warning.lesson)}</div>`;
  $("after").innerHTML = html;
  $("after").hidden = false;
}

// ---------------- Under the hood (for the viva demo) ----------------
function renderHood(r) {
  if (mode() === "study") { $("hood-body").innerHTML = '<p class="muted">Hidden in study mode.</p>'; return; }
  const d = r.detection, v = r.verification, w = r.warning, a = d.anatomy, risk = v.risk;
  const pct = Math.round(d.scam_score * 100);
  const contacts = a.contacts.map((c) => `<span class="chip">${esc(c.type)}: ${esc(c.normalized)}</span>`).join("") || "none";
  const tactics = a.tactics.map((t) => `<span class="chip">${esc(t)}</span>`).join("") || "none";
  const checks = v.fact_checks.map((c) =>
    `<div class="check"><b class="${c.result}">${c.result.toUpperCase()}</b> ${esc(c.detail)}</div>`).join("")
    || '<p class="muted">Nothing to check (no bank, number or link found).</p>';
  const words = v.explanation.map((e) => `<span class="chip">${esc(e.word)} +${e.weight.toFixed(2)}</span>`).join("") || "none";
  $("hood-body").innerHTML = `
    <div class="who">1 · Detection (Sanmith)</div>
    <dl class="kv">
      <dt>Label</dt><dd>${esc(d.label)} <span class="muted">(${esc(d.model_version)})</span></dd>
      <dt>Model score (not probability)</dt><dd>${d.scam_score.toFixed(2)}<div class="bar"><span style="width:${pct}%"></span></div></dd>
      <dt>Language</dt><dd>${esc(d.language)}</dd>
      <dt>Tricks undone</dt><dd>${d.tricks_found.map(esc).join(", ") || "none"}</dd>
      ${d.normalized_text !== state.current.msg.text.trim() ? `<dt>Cleaned text</dt><dd>${esc(d.normalized_text)}</dd>` : ""}
      <dt>Claims to be</dt><dd>${a.claimed_bank ? esc(a.claimed_bank.name) : "no bank found"}</dd>
      <dt>Wants you to</dt><dd><b>${esc(a.primary_action.replaceAll("_", " "))}</b> <span class="muted">(harm ${a.harm})</span></dd>
      <dt>Contacts</dt><dd class="chips">${contacts}</dd>
      <dt>Tactics</dt><dd class="chips">${tactics}</dd>
      <dt>Zero-link</dt><dd>${a.zero_link ? "yes" : "no"}</dd>
    </dl>

    <h4><span class="who">2 · Verify (Perera)</span></h4>
    <div><b>Fact checks</b>${checks}</div>
    <p><b>Words that raised the score</b></p><div class="chips">${words}</div>
    <p><b>Risk tier</b></p>
    <div class="steps">
      <span>likelihood ${esc(risk.likelihood)}</span> × <span>harm ${risk.harm}</span>
      → <span>matrix ${esc(risk.matrix_tier)}</span>
      → <span>fact checks: ${esc(risk.adjustment)}</span>
      → <b>${esc(risk.tier)}</b>${risk.planted_error ? ' <span class="chip">planted error</span>' : ""}
    </div>

    <h4><span class="who">3 · Warn (Rathnayake)</span></h4>
    <dl class="kv">
      <dt>Warning language</dt><dd>${esc(w.language)}</dd>
      <dt>Intervention</dt><dd>${esc(w.intervention)}</dd>
      <dt>AI advice</dt><dd>${esc(r.ai_advice)}</dd>
    </dl>`;
}

function renderProfile(p) {
  if (mode() === "study") return;
  $("hood-body").insertAdjacentHTML("beforeend", `<pre>${esc(JSON.stringify(p, null, 2))}</pre>`);
}

// ---------------- Modal + misc ----------------
function modal(html) { $("modal-body").innerHTML = html; $("modal").hidden = false; }
function closeModal() { $("modal").hidden = true; }
$("modal").addEventListener("click", (e) => { if (e.target.id === "modal") closeModal(); });

$("back").addEventListener("click", () => { ["mode", "pid", "condition", "lang"].forEach(id => $(id).disabled = false); show("inbox"); loadInbox(); });
$("mode").addEventListener("change", () => {
  $("pid-wrap").hidden = mode() !== "study";
  $("consent-wrap").hidden = mode() !== "study";
  $("custom").hidden = mode() === "study";
  $("hood").hidden = mode() === "study";
});
$("custom").addEventListener("submit", (e) => {
  e.preventDefault();
  const text = $("custom-text").value.trim();
  if (!text) return;
  openMessage({ id: "custom-" + Date.now(), custom: true, text, sender: $("custom-sender").value.trim() || null });
});
setInterval(() => {
  const d = new Date();
  $("clock").textContent = `${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`;
}, 10000);

loadInbox();
