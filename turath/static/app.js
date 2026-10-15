/* «تراث» — لوحة التحكم. JavaScript خالص بلا مكتبات خارجية. */
"use strict";
const S = { token: null, user: null, info: null, schema: null, projects: [], cache: {} };
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const ic = (n, cls = "") => `<svg class="i ${cls}" aria-hidden="true"><use href="img/icons.svg#i-${n}"/></svg>`;
const fmtDate = (s) => (s ? String(s).replace("T", " ").slice(0, 16) : "—");

const C = { blue: "#1F4E79", gold: "#B8860B", teal: "#0E7C86", clay: "#A0522D", palm: "#3E7C3A", sky: "#5BA4CF", night: "#12263F", crimson: "#8B1E3F", plum: "#5B3A7A", brown: "#6B4E2E", sand: "#D9B26F" };
const NAV = [
  { grp: "المؤسسة" },
  { id: "home", label: "الرئيسية", icon: "home", c: C.blue },
  { id: "projects", label: "المشاريع البحثية", icon: "folder", c: C.gold },
  { id: "kpis", label: "لوحة القيادة", icon: "kpi", c: C.sky },
  { grp: "الأرشيف المعرفي" },
  { id: "archive", label: "السجلات", icon: "database", c: C.clay },
  { id: "vault", label: "الخزنة والوسائط", icon: "archive", c: C.brown },
  { id: "lab", label: "المختبر الشفهي واللغوي", icon: "mic", c: C.teal },
  { id: "evidence", label: "الأدلة والتثليث", icon: "shield", c: C.crimson },
  { grp: "المنظومة" },
  { id: "agents", label: "الوكلاء العشرون", icon: "people", c: C.plum },
  { id: "skills", label: "المهارات والأوامر", icon: "star", c: C.palm },
  { id: "docs", label: "الوثائق والاستمارات", icon: "book", c: C.night },
  { id: "settings", label: "الإعدادات والتشغيل", icon: "settings", c: "#56657A" },
];
const DOMAIN_ART = { history_society: "history", material: "material", intangible: "intangible", crafts_economy: "crafts", natural: "natural", legal: "legal" };
// صور الواجهة من مجموعة صاحب الإدارة؛ وما كان منها مولَّداً يوسم «إعادة بناء تصورية» ولا يُقدَّم صورة تاريخية
const PH = (k) => `img/photos/${k}.jpg`;
const CONCEPT = new Set(["hero", "intangible", "legal", "evidence", "aerial"]);
const cx = (k) => (CONCEPT.has(k) ? `<span class="concept" title="صورة مولَّدة لا وثيقة تاريخية">إعادة بناء تصورية</span>` : "");
const DOMAIN_COLOR = { history_society: C.clay, material: C.gold, intangible: C.teal, crafts_economy: C.brown, natural: C.palm, legal: C.plum };
const REGION_ART = { coastal: "coastal", desert: "desert", oasis: "oasis", mountain: "mountain", urban: "urban", contact: "contact" };
const STAGE_COLORS = [C.blue, C.blue, C.blue, C.clay, C.clay, C.crimson, C.palm, C.teal, C.crimson, C.sky, C.gold, C.plum, C.plum, C.night, C.gold, C.brown];

const L = {
  private: "خاص", project: "ضمن المشروع", shared: "مشارَك", public: "عام",
  abu_dhabi: "أبوظبي", dubai: "دبي", sharjah: "الشارقة", ajman: "عجمان", umm_al_quwain: "أم القيوين", ras_al_khaimah: "رأس الخيمة", fujairah: "الفجيرة", multi: "أكثر من إمارة",
  active: "نشط", paused: "متوقف", closed: "مغلق",
  book: "كتاب", article: "مقالة محكّمة", thesis: "رسالة جامعية", manuscript: "مخطوط", archival: "وثيقة أرشيفية", oral: "تسجيل شفهي", photo: "صورة", film: "فيلم",
  map: "خريطة", poem: "قصيدة", object: "قطعة تراثية", field_note: "ملاحظة ميدانية", legal: "نص قانوني", web: "موقع عام", report: "تقرير رسمي",
  m: "ذكر", f: "أنثى", none: "لا تفريغ", draft: "مسودة", native_reviewed: "روجع لهجياً", approved: "معتمد",
  documentary: "وثائقي", analytical: "تحليلي", conceptual: "تصوري — إعادة بناء",
  letter: "رسالة", deed: "صك أو وثيقة ملكية", court: "حكم أو صلح", treaty: "اتفاقية", register: "سجل", other: "أخرى",
  nabati: "شعر نبطي", hazij: "هزج", song: "أغنية شعبية", chant: "أهزوجة عمل",
  high: "عالية", medium: "متوسطة", low: "منخفضة", critical: "حرجة",
  sea: "بحرية", agri: "زراعية", pastoral: "رعوية", textile: "نسيجية", wood_metal: "نجارة وحدادة", trade: "تجارة",
  living: "حية", endangered: "مهددة", dormant: "خاملة", revived: "مُحياة",
  town: "مدينة", village: "قرية", oasis: "واحة", port: "ميناء", souq: "سوق", fort: "حصن", well: "بئر", falaj: "فلج", mountain: "جبل", desert: "صحراء", site: "موقع أثري",
  exact: "مؤكد", approximate: "تقريبي", disputed: "متنازع", unknown: "مجهول",
  direct: "مباشرة", participant: "بالمشاركة", design: "تصميم", pilot: "تجريبي", fielding: "قيد الجمع",
  federal: "اتحادي", local: "محلي", gcc: "خليجي", international: "دولي",
  in_force: "نافذ", amended: "معدّل", repealed: "ملغى", unverified: "لم يُتحقق", apa7: "APA 7", chicago_nb: "Chicago N-B",
  measured: "بيانات مقاسة", narrative: "رواية", inference: "استنتاج", hypothesis: "فرضية", model: "نموذج تفسيري",
  established: "مثبت", probable: "مرجّح", pending_field: "معلّق ميدانياً", rejected: "مردود",
  supports: "يؤيد", contradicts: "يعارض", context: "سياق", explained: "مفسَّر", resolved_by_evidence: "حُسم بالدليل", open: "مفتوح",
  approve: "اعتماد", approve_with_changes: "اعتماد مع تعديلات", revise: "مراجعة", reject: "رفض", escalate: "تصعيد",
  peer_review: "قيد التحكيم", legal_review: "قيد التدقيق القانوني", published: "منشور", pending: "قيد الانتظار", passed: "اجتاز", failed: "لم يجتز",
};
const STATUS_C = { established: C.palm, probable: C.sky, disputed: C.crimson, hypothesis: C.plum, pending_field: C.gold, rejected: "#777",
  ok: C.palm, missing: C.crimson, altered: C.crimson };
const lab = (v) => L[v] ?? S.info?.domains?.[v] ?? S.info?.regions?.[v] ?? S.info?.narrative_types?.[v] ?? S.info?.evidence_types?.[v] ?? v ?? "—";

/* ------------------------------------------------------------ أدوات عامة */
async function api(path, opt = {}) {
  const o = { method: opt.method || "GET", headers: { Authorization: "Bearer " + (S.token || "") } };
  if (opt.body !== undefined) {
    if (opt.raw) { o.body = opt.body; Object.assign(o.headers, opt.headers || {}); }
    else { o.body = JSON.stringify(opt.body); o.headers["Content-Type"] = "application/json"; }
  }
  const r = await fetch("/api/" + path, o);
  if (r.status === 401) { logout(true); throw new Error("انتهت الجلسة"); }
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.error || "تعذر الطلب");
  return d;
}
function toast(m, bad = false) {
  const t = $("#toast"); t.textContent = m; t.className = "toast" + (bad ? " bad" : ""); t.hidden = false;
  clearTimeout(toast._t); toast._t = setTimeout(() => (t.hidden = true), 4200);
}
const busy = (on) => ($("#busy").hidden = !on);
async function run(fn, ok) {
  busy(true);
  try { const r = await fn(); if (ok) toast(ok); return r; } catch (e) { toast(e.message, true); } finally { busy(false); }
}
function modal(title, body, c = C.blue, iconName = "layers") {
  const m = $("#modal");
  m.innerHTML = `<div class="box" style="--c:${c}"><div class="head"><div class="row">${ic(iconName, "lg")}<h2>${esc(title)}</h2></div>
    <button class="iconbtn" data-close style="background:rgba(255,255,255,.15);border:0;color:#fff">✕</button></div><div class="body">${body}</div></div>`;
  m.hidden = false;
  m.onclick = (e) => { if (e.target === m || e.target.closest("[data-close]")) closeModal(); };
  return $(".body", m);
}
const closeModal = () => { $("#modal").hidden = true; $("#modal").innerHTML = ""; };
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); });
const fileUrl = (aid, inline = true) => `/api/assets/${encodeURIComponent(aid)}/file?${inline ? "inline=1&" : ""}t=${encodeURIComponent(S.token)}`;
const download = (path) => { const a = document.createElement("a"); a.href = `/api/${path}${path.includes("?") ? "&" : "?"}t=${encodeURIComponent(S.token)}`; a.click(); };
const sec = (title, icon, c = C.blue, extra = "") => `<div class="sec" style="--c:${c}"><div class="ic">${ic(icon)}</div><h2>${title}</h2><div class="bar"></div>${extra}</div>`;
const badge = (txt, c = C.blue) => `<span class="badge" style="--c:${c}">${esc(txt)}</span>`;
const stageLabel = (id) => (S.info.stages.find((s) => s.id === id) || {}).label || id;
const stageIdx = (id) => Math.max(0, S.info.stages.findIndex((s) => s.id === id));

/* ------------------------------------------------------------ الدخول */
function readHashToken() {
  const m = location.hash.match(/[#&]t=([\w-]+)/);
  if (m) {
    S.token = m[1];
    try { sessionStorage.setItem("turath_t", S.token); } catch {}
    const rest = location.hash.replace(/[#&]?t=[\w-]+/, "").replace(/^#?&?/, "");
    history.replaceState(null, "", "#" + (rest.startsWith("/") ? rest : "/home"));
  }
  if (!S.token) { try { S.token = sessionStorage.getItem("turath_t") || localStorage.getItem("turath_t"); } catch {} }
}
function logout(silent) {
  if (!silent && S.token) api("logout", { method: "POST" }).catch(() => {});
  try { sessionStorage.removeItem("turath_t"); localStorage.removeItem("turath_t"); } catch {}
  S.token = null; S.user = null; showLogin();
}
async function showLogin() {
  const p = await fetch("/api/public").then((r) => r.json()).catch(() => ({}));
  $("#root").innerHTML = `<div class="login"><div class="art"><div class="cap"><img src="img/app-icon.png" width="84" alt="" class="appicon">
    <h1>تراث</h1><p>${esc(p.institution || "")}</p></div></div>
    <div class="pane"><form class="box card stack" id="lf"><div class="accent" style="--c:${C.gold}"></div>
      <h2 style="color:var(--blue);margin:0">تسجيل الدخول</h2><div class="chip blue">${esc(p.mode_label || "")}</div>
      ${p.mode === "solo" ? `<p class="note">النمط الفردي: افتح اللوحة من الأيقونة أو بالأمر <code>turath serve</code>؛ فالدخول برمز يتولد عند كل تشغيل.</p>` : ""}
      <label class="stack"><span class="muted small">اسم المستخدم</span><input name="username" autocomplete="username" required></label>
      <label class="stack"><span class="muted small">كلمة المرور</span><input name="password" type="password" autocomplete="current-password" required></label>
      <label class="row small"><input type="checkbox" name="remember"> تذكّرني على هذا الجهاز</label>
      <button class="btn gold" style="width:100%;justify-content:center">${ic("lock")} دخول</button></form></div></div>`;
  $("#lf").onsubmit = async (e) => {
    e.preventDefault();
    const f = new FormData(e.target);
    const r = await run(() => api("login", { method: "POST", body: { username: f.get("username"), password: f.get("password") } }));
    if (!r) return;
    S.token = r.token;
    try { (f.get("remember") ? localStorage : sessionStorage).setItem("turath_t", r.token); } catch {}
    boot();
  };
}

/* ------------------------------------------------------------ الإطار */
function shell() {
  const navHtml = NAV.map((n) => (n.grp ? `<div class="grp">${n.grp}</div>` :
    `<button data-nav="${n.id}" style="--c:${n.c}"><span class="dot">${ic(n.icon)}</span><span>${n.label}</span></button>`)).join("");
  const init = (S.user.display_name || S.user.username || "؟").trim()[0];
  const eng = S.info.engines[S.info.engine];
  $("#root").innerHTML = `<div class="app"><aside class="side" id="side">
      <div class="brand"><img src="img/app-icon.png" alt=""><div><b>تراث</b><small>إدارة الدراسات والبحوث<br>التراثية الإماراتية</small></div></div>
      <div class="sadu"></div><nav class="nav">${navHtml}</nav>
      <div class="foot"><span class="mode">${ic("users")} ${esc(S.info.mode_label)}</span><div style="margin-top:6px">الإصدار ${esc(S.info.version)}</div></div></aside>
    <div class="col"><header class="top">
      <button class="iconbtn menu-btn" id="menu">${ic("layers")}</button>
      <form class="search" id="sf">${ic("search")}<input id="q" placeholder="ابحث في الأرشيف: المصادر، التفريغات، المفردات، الروايات…"></form>
      <div class="chips"><span class="chip ${eng && eng.available ? "ok" : "warn"}" title="محرك الوكلاء">${ic("play")} ${esc(eng ? eng.label : S.info.engine)}</span>
      <button class="iconbtn" id="theme" title="الوضع الليلي">${ic("eye")}</button>
      <div class="avatar" title="${esc(S.user.display_name)} — ${esc(S.info.roles[S.user.role] || S.user.role)}">${esc(init)}</div>
      ${S.info.mode !== "solo" ? `<button class="iconbtn" id="lo" title="خروج">${ic("lock")}</button>` : ""}</div></header>
      <main id="main"></main></div></div>`;
  $$("[data-nav]").forEach((b) => (b.onclick = () => { location.hash = "#/" + b.dataset.nav; $("#side").classList.remove("open"); }));
  $("#menu").onclick = () => $("#side").classList.toggle("open");
  $("#sf").onsubmit = (e) => { e.preventDefault(); doSearch($("#q").value); };
  $("#theme").onclick = () => { const d = document.documentElement; d.dataset.theme = d.dataset.theme === "dark" ? "light" : "dark"; try { localStorage.setItem("turath_theme", d.dataset.theme); } catch {} };
  if ($("#lo")) $("#lo").onclick = () => logout();
}
async function route() {
  const [, view = "home", ...rest] = (location.hash || "#/home").replace(/^#/, "").split("/");
  $$("[data-nav]").forEach((b) => b.classList.toggle("on", b.dataset.nav === view || (view === "project" && b.dataset.nav === "projects")));
  const main = $("#main");
  main.innerHTML = `<div class="empty"><div class="spin" style="margin:auto"></div></div>`;
  const V = { home, projects, project, kpis: kpiView, archive, vault, lab: labView, evidence, agents: agentsView, skills: skillsView, docs: docsView, settings };
  try { await (V[view] || home)(main, ...rest.map(decodeURIComponent)); } catch (e) { main.innerHTML = `<div class="note">${esc(e.message)}</div>`; }
  window.scrollTo(0, 0);
}
window.addEventListener("hashchange", route);

async function boot() {
  readHashToken();
  try { const t = localStorage.getItem("turath_theme"); if (t) document.documentElement.dataset.theme = t; } catch {}
  if (!S.token) return showLogin();
  try {
    const me = await api("me");
    S.user = me.user; S.info = me.info; S.schema = await api("schema");
  } catch { return; }
  shell(); route();
  let toured = false;
  try { toured = localStorage.getItem("turath_toured") === "1"; } catch {}
  if (!toured) setTimeout(() => showTour(0), 600);
}

/* ------------------------------------------------------------ مكونات */
function ringCard(k) {
  const pct = k.unit === "%";
  const v = k.value;
  const color = { provenance: C.brown, metadata: C.clay, transcripts: C.teal, witnesses: C.plum, consents: C.palm, dialect_err: C.teal,
    claims_linked: C.crimson, conflicts_open: C.crimson, integrity: C.blue, peer_passed: C.gold, elements: C.gold, diversity: C.sky }[k.key] || C.blue;
  const base = k.baseline === undefined || k.baseline === null ? "" : `<div class="base">خط الأساس: ${esc(k.baseline)}${esc(k.unit)}</div>`;
  const body = pct ? `<div class="ring ${v === null ? "na" : ""}" style="--v:${v ?? 0};--c:${color}"><span>${v === null ? "لا بيانات" : v + "%"}</span></div>`
    : `<div class="ring" style="--v:${k.unit === "/6" ? ((v || 0) / 6) * 100 : 100};--c:${color}"><span>${v === null ? "—" : esc(v)}${k.unit === "/6" ? "<small>/6</small>" : ""}</span></div>`;
  return `<div class="card kpi" style="--c:${color}"><div class="accent"></div>${body}<div><div class="lbl">${esc(k.label)}</div>${base}</div></div>`;
}
function statCard(label, n, icon, c, nav) {
  return `<div class="card click stat" style="--c:${c}" ${nav ? `data-go="${nav}"` : ""}><div class="ico">${ic(icon, "lg")}</div><div><b>${n ?? 0}</b><span class="muted small">${label}</span></div></div>`;
}
const bindGo = (el) => $$("[data-go]", el).forEach((x) => (x.onclick = () => (location.hash = "#/" + x.dataset.go)));
function pipeline(counts, current) {
  return `<div class="pipeline">${S.info.stages.map((s, i) => {
    const cls = current ? (s.id === current ? "cur" : stageIdx(current) > i ? "done" : "") : (counts && counts[s.id] ? "cur" : "");
    return `<div class="stg ${cls}" style="--c:${STAGE_COLORS[i]}"><span class="n">${s.id}</span><div class="t">${esc(s.label)}</div>
      ${counts ? `<span class="cnt">${counts[s.id] || ""}</span>` : `<span class="tiny muted">${esc(s.agent)}</span>`}</div>`; }).join("")}</div>`;
}
function projectCard(p) {
  const i = stageIdx(p.stage), c = DOMAIN_COLOR[p.domain] || C.blue;
  return `<div class="card click" style="--c:${c};padding:0" data-go="project/${esc(p.id)}">
    <div style="height:110px;position:relative;background:url(${PH(DOMAIN_ART[p.domain] || "history")}) center/cover">${cx(DOMAIN_ART[p.domain] || "history")}</div>
    <div style="padding:14px 16px"><div class="spread"><span class="tiny muted" dir="ltr">${esc(p.id)}</span>${badge(lab(p.domain), c)}</div>
    <h3 style="margin-top:6px">${esc(p.title)}</h3>
    <div class="spread small"><span>${esc(p.stage)} · ${esc(stageLabel(p.stage))}</span><span class="muted">${i + 1}/16</span></div>
    <div class="progress" style="--c:${c};margin-top:6px"><i style="width:${((i + 1) / 16) * 100}%"></i></div>
    <div class="row small muted" style="margin-top:8px">${p.emirate ? ic("map-pin") + esc(lab(p.emirate)) : ""} ${p.owner_id !== S.user.id ? badge("مشترك", C.plum) : ""}</div></div></div>`;
}

/* ------------------------------------------------------------ الرئيسية */
async function home(main) {
  const d = await api("dashboard");
  S.projects = d.projects;
  const k = d.kpis, c = d.counts;
  const elements = (c.heritage_practices || 0) + (c.crafts || 0);
  const domCount = {};
  d.projects.forEach((p) => (domCount[p.domain] = (domCount[p.domain] || 0) + 1));
  const regionsOn = new Set(k.regions);
  const engines = Object.entries(S.info.engines).map(([n, e]) => `<li>${e.available ? "✅" : "⏳"} ${esc(e.label)}</li>`).join("");
  main.innerHTML = `
  <section class="hero">${cx("hero")}<div class="in">
    <div class="kicker">${ic("pearl")} مرجعية رقمية متخصصة في تراث الإمارات</div>
    <h1>إدارة الدراسات والبحوث<br>التراثية الإماراتية</h1>
    <p>مؤسسة معرفية رقمية للبحث والتحقيق والجمع الميداني والتوثيق والتحليل والنشر؛ تحفظ الأدلة الأولية وتربطها بالاستنتاجات العلمية، بانضباط صفر تلفيق.</p>
    <div class="acts"><button class="btn gold" id="np">${ic("plus")} مشروع بحثي جديد</button>
      <button class="btn glass" data-go="vault">${ic("upload")} أرشف مادة</button>
      <button class="btn glass" data-go="lab">${ic("mic")} المختبر الشفهي</button>
      ${d.projects.length ? "" : `<button class="btn glass" id="pilot">${ic("star")} النموذج التطبيقي: التلي</button>`}</div>
  </div><div class="sadu"></div></section>

  <div class="grid" style="--min:170px;margin-top:22px">
    ${statCard("مشروع بحثي", d.projects.length, "folder", C.gold, "projects")}
    ${statCard("مصدر موثق", c.sources, "book", C.clay, "archive/sources")}
    ${statCard("مقابلة شفهية", c.interviews, "mic", C.teal, "lab")}
    ${statCard("أصل رقمي محفوظ", d.assets.n, "archive", C.brown, "vault")}
    ${statCard("ادعاء علمي", c.claims, "check", C.crimson, "evidence")}
    ${statCard("عنصر تراثي موثق", elements, "star", C.palm, "archive/heritage_practices")}
  </div>

  ${sec("مؤشرات الأداء", "kpi", C.sky, `<span class="chip ${k.baseline_set ? "ok" : "gold"}">${k.baseline_set ? "خط الأساس مثبت " + fmtDate(k.baseline_at) : "لا مستهدفات قبل خط الأساس التجريبي"}</span>`)}
  <div class="grid" style="--min:270px">${k.indicators.map(ringCard).join("")}</div>

  ${sec("دورة المشروع: من التكليف إلى النشر", "gate", C.gold)}
  ${pipeline(d.stages)}
  <p class="muted small">ست عشرة مرحلة، وبوابة جودة ملزمة عند كل انتقال لا يجوز تجاوزها قبل اكتمال متطلباتها. الأرقام: عدد المشاريع في كل مرحلة.</p>

  ${sec("المجالات البحثية الإلزامية", "layers", C.clay)}
  <div class="grid" style="--min:300px">${Object.entries(S.info.domains).map(([key, label]) => `
    <div class="card click domain" style="background-image:url(${PH(DOMAIN_ART[key])})" data-go="projects">${cx(DOMAIN_ART[key])}<div class="shade">
      <h3>${esc(label)}</h3><span class="cnt">${domCount[key] || 0} مشروع</span></div></div>`).join("")}</div>

  ${sec("الخصوصية الإماراتية: النطاقات الجغرافية الثقافية", "map", C.teal, `<span class="chip blue">الممثَّل: ${regionsOn.size}/6</span>`)}
  <div class="grid" style="--min:170px">${Object.entries(S.info.regions).map(([key, label]) => `
    <div class="card" style="padding:0;${regionsOn.has(label) ? "outline:3px solid var(--gold)" : "filter:saturate(.75)"}">
      <div style="height:96px;background:url(${PH(REGION_ART[key])}) center/cover"></div>
      <div style="padding:10px 12px" class="small"><b>${esc(label)}</b><br><span class="muted tiny">${regionsOn.has(label) ? "ممثَّل في البحوث" : "غير ممثَّل بعد"}</span></div></div>`).join("")}</div>
  <p class="muted small">عناية خاصة بالشارقة ومدنها ومناطقها: الذيد، وكلباء، وخورفكان، ودبا الحصن، ومليحة — دون تعميم خصائص منطقة على المجتمع الإماراتي كله.</p>

  <div class="grid" style="--min:420px;margin-top:10px">
    <div>${sec("المشاريع الجارية", "folder", C.gold)}<div class="grid" style="--min:260px">${d.projects.slice(0, 4).map(projectCard).join("") ||
      `<div class="card empty"><img src="${PH("archive")}" alt=""><p>لا مشاريع بعد. ابدأ بمشروع جديد أو استورد النموذج التطبيقي.</p></div>`}</div></div>
    <div>${sec("آخر النشاط", "clock", C.night)}<div class="card"><ul class="timeline">${d.recent.map((r) => `<li><span class="dt">${fmtDate(r.at)}</span>
      <span>${esc(actionLabel(r.action))} · <b>${esc(S.schema[r.item_table]?.one || r.item_table)}</b> <span class="tiny muted" dir="ltr">${esc(r.item_id)}</span></span></li>`).join("") || `<li class="muted">لا نشاط بعد</li>`}</ul></div></div>
  </div>

  ${sec("ما صُمِّم وما نُفِّذ", "check", C.palm)}
  <div class="grid" style="--min:300px">
    <div class="card"><h3>${ic("check")} منفَّذ ومختبَر في هذا النظام</h3><ul class="small">
      <li>قاعدة بيانات علائقية بتسعة وثلاثين جدولاً وسجل تغييرات لكل تعديل</li><li>خزنة أصول ببصمة SHA-256 ونسخ أصلية للقراءة فقط، وفحص سلامة ونسخ احتياطي</li>
      <li>بحث نصي كامل متتبَّع إلى السجل الأصلي</li><li>دورة المشروع ببوابات جودة ملزمة، والتثليث وسجل التعارضات</li>
      <li>الموافقات الأربع المنفصلة، ومؤشرات الأداء الاثنا عشر</li><li>ثلاثة أنماط تشغيل وحسابات خاصة ومشاركة</li></ul></div>
    <div class="card"><h3>${ic("play")} المحركات والأدوات المشروطة</h3><ul class="small" style="list-style:none;padding:0">${engines}
      <li>${S.info.asr.available ? "✅" : "⏳"} التفريغ الآلي (faster-whisper)</li><li>${S.info.ffmpeg ? "✅" : "⏳"} البيانات الفنية للوسائط (ffmpeg)</li>
      <li>📐 البحث الدلالي بالمتجهات وربط Drive وZotero: مواصفات قابلة للتنفيذ</li></ul></div>
  </div>`;
  bindGo(main);
  $("#np").onclick = () => newProject();
  if ($("#pilot")) $("#pilot").onclick = importPilot;
}
const actionLabel = (a) => ({ create: "إنشاء", update: "تعديل", delete: "حذف", ingest: "إيداع أصل", verify: "فحص السلامة", backup: "نسخ احتياطي", advance: "انتقال مرحلة",
  transcript: "تفريغ", lab_step: "خطوة مختبر", agent_run: "تكليف وكيل", share: "مشاركة", member: "ضم شريك", baseline: "خط الأساس" }[a] || a);
async function importPilot() {
  const r = await run(() => api("pilot", { method: "POST" }), "استُورد النموذج التطبيقي");
  if (r) location.hash = "#/project/" + r.project;
}

/* ------------------------------------------------------------ النماذج المولدة من المخطط */
async function refOptions(table) {
  if (table === "assets") return (await api("assets")).map((a) => [a.id, `${a.id} — ${a.filename}`]);
  const R = await api("rows/" + table);
  return R.map((r) => [r.id, `${r.id} — ${r.title || r.name || r.term || r.code || r.display_name || r.topic || (r.text || "").slice(0, 60) || ""}`]);
}
async function formHtml(table, row = {}, preset = {}) {
  const sc = S.schema[table];
  const common = [["project_id", "المشروع", "ref:projects"], ["access_level", "مستوى الإتاحة", "enum:private|project|shared|public"],
    ["rights", "الحقوق وشروط الاستخدام", "long"], ["source_ref", "المصدر المرجعي", "text"]];
  const fields = [...sc.fields.map((f) => [f.name, f.label, f.type]), ...(table === "projects" ? common.slice(1) : common)];
  const out = [];
  for (const [n, label, t] of fields) {
    if (table === "projects" && n === "stage") continue;
    const v = row[n] ?? preset[n] ?? "";
    let input;
    if (t === "long" || t === "json") input = `<textarea name="${n}">${esc(v)}</textarea>`;
    else if (t === "bool") { out.push(`<label class="check"><input type="checkbox" name="${n}" ${v ? "checked" : ""}> ${esc(label)}</label>`); continue; }
    else if (t.startsWith("enum:")) input = `<select name="${n}"><option value="">—</option>${t.slice(5).split("|").map((o) => `<option value="${o}" ${o === v ? "selected" : ""}>${esc(lab(o))}</option>`).join("")}</select>`;
    else if (t.startsWith("ref:")) {
      const opts = await refOptions(t.slice(4)).catch(() => []);
      input = `<select name="${n}"><option value="">—</option>${opts.map(([id, l]) => `<option value="${esc(id)}" ${id === v ? "selected" : ""}>${esc(l)}</option>`).join("")}</select>`;
    } else if (n === "lead_agent") {
      const ag = S.cache.agents || (S.cache.agents = await api("agents"));
      input = `<select name="${n}"><option value="">—</option>${ag.map((a) => `<option value="${a.id}" ${a.id === v ? "selected" : ""}>${a.id} — ${esc(a.name_ar)}</option>`).join("")}</select>`;
    } else input = `<input name="${n}" type="${t === "int" || t === "real" ? "number" : t === "date" ? "date" : "text"}" ${t === "real" ? 'step="any"' : ""} value="${esc(v)}">`;
    out.push(`<label class="${t === "long" || t === "json" ? "wide" : ""}">${esc(label)}${input}</label>`);
  }
  return `<form class="form" id="ef">${out.join("")}<div class="wide row"><button class="btn gold">${ic("check")} حفظ</button>
    ${row.id ? `<button type="button" class="btn ghost" id="hist">${ic("clock")} سجل التغييرات</button><button type="button" class="btn ghost" id="shr">${ic("share")} مشاركة</button>
    <button type="button" class="btn danger sm" id="del">${ic("alert")} حذف</button>` : ""}</div></form>`;
}
function formData(form) {
  const o = {};
  $$("input,select,textarea", form).forEach((el) => { if (!el.name) return; o[el.name] = el.type === "checkbox" ? el.checked : el.value; });
  return o;
}
async function editRecord(table, row = null, preset = {}, after) {
  const sc = S.schema[table];
  const body = modal(row ? `${sc.one}: ${row.id}` : `${sc.one} جديد`, `<div class="empty"><div class="spin" style="margin:auto"></div></div>`, C.clay, sc.icon);
  body.innerHTML = await formHtml(table, row || {}, preset);
  $("#ef", body).onsubmit = async (e) => {
    e.preventDefault();
    const d = formData(e.target);
    const r = await run(() => api(row ? `rows/${table}/${row.id}` : `rows/${table}`, { method: row ? "PUT" : "POST", body: d }), "حُفظ السجل");
    if (r) { closeModal(); after ? after(r) : route(); }
  };
  if (row) {
    $("#hist", body).onclick = async () => {
      const H = await api(`history/${table}/${row.id}`);
      body.insertAdjacentHTML("beforeend", `<h3>سجل التغييرات</h3><ul class="timeline">${H.map((h) => `<li><span class="dt">${fmtDate(h.at)}</span><span>${esc(actionLabel(h.action))}<br><span class="tiny muted">${esc((h.after || "").slice(0, 300))}</span></span></li>`).join("")}</ul>`);
    };
    $("#shr", body).onclick = async () => {
      const g = prompt("اسم المستخدم المشارَك معه (أو * للجميع):");
      if (!g) return;
      const mode = confirm("هل تمنحه صلاحية التعديل؟ (إلغاء = اطلاع فقط)") ? "write" : "read";
      await run(() => api("share", { method: "POST", body: { table, id: row.id, grantee: g, mode } }), "تمت المشاركة");
    };
    $("#del", body).onclick = async () => {
      if (!confirm("حذف السجل نهائياً؟ يبقى أثره في سجل التغييرات.")) return;
      if (await run(() => api(`rows/${table}/${row.id}`, { method: "DELETE" }), "حُذف")) { closeModal(); route(); }
    };
  }
}
async function newProject() { await editRecord("projects", null, { status: "active" }, (r) => (location.hash = "#/project/" + r.id)); }

function rowsTable(table, R, cols) {
  const sc = S.schema[table];
  cols = cols || sc.fields.slice(0, 4).map((f) => f.name);
  const lbl = Object.fromEntries(sc.fields.map((f) => [f.name, f.label]));
  if (!R.length) return `<div class="card empty"><img src="${PH("archive")}" alt=""><p>لا سجلات في «${esc(sc.label)}» بعد.</p></div>`;
  return `<div class="table-wrap"><table><thead><tr><th>المعرّف</th>${cols.map((c) => `<th>${esc(lbl[c] || c)}</th>`).join("")}<th>الإتاحة</th></tr></thead><tbody>
    ${R.map((r) => `<tr class="click" data-row="${esc(r.id)}"><td class="tiny" dir="ltr">${esc(r.id)}</td>${cols.map((c) => {
      const v = r[c]; const f = sc.fields.find((x) => x.name === c);
      if (f && f.type.startsWith("enum:")) return `<td>${badge(lab(v), STATUS_C[v] || C.blue)}</td>`;
      if (f && f.type === "bool") return `<td>${v ? "✅" : "—"}</td>`;
      return `<td>${esc(String(v ?? "—").slice(0, 140))}</td>`; }).join("")}<td>${badge(lab(r.access_level), C.night)}</td></tr>`).join("")}</tbody></table></div>`;
}
function bindRows(el, table, R, after) {
  $$("[data-row]", el).forEach((tr) => (tr.onclick = () => {
    const r = R.find((x) => x.id === tr.dataset.row);
    if (table === "claims") return claimCard(r.id);
    if (table === "interviews") return (location.hash = "#/lab/" + r.id);
    editRecord(table, r, {}, after);
  }));
}

/* ------------------------------------------------------------ المشاريع */
async function projects(main) {
  const P = await api("rows/projects");
  main.innerHTML = `${sec("المشاريع البحثية", "folder", C.gold, `<button class="btn gold" id="np">${ic("plus")} مشروع جديد</button>`)}
    <div class="grid" style="--min:280px">${P.map(projectCard).join("") || `<div class="card empty"><img src="${PH("urban")}" alt=""><p>لا مشاريع بعد.</p>
      <button class="btn gold" id="pilot">${ic("star")} استورد النموذج التطبيقي: التلي</button></div>`}</div>`;
  bindGo(main);
  $("#np").onclick = newProject;
  if ($("#pilot")) $("#pilot").onclick = importPilot;
}
async function project(main, pid, tab) {
  const o = await api(`projects/${pid}/overview`);
  const p = o.project, c = DOMAIN_COLOR[p.domain] || C.blue;
  const roles = ["AG-ETH", "AG-SRC", "AG-PUB", "AG-LAW", "AG-DIR", "HUM-DIR", "HUM-PEER", "HUM-LEGAL", "HUM-NATIVE"];
  const allOk = o.checks.every((x) => x.ok);
  const tables = Object.keys(S.schema).filter((t) => t !== "projects");
  tab = tab || "claims";
  main.innerHTML = `
  <section class="hero" style="min-height:230px;background-image:url(${PH(DOMAIN_ART[p.domain] || "history")})">${cx(DOMAIN_ART[p.domain] || "history")}<div class="in">
    <div class="kicker">${ic("folder")} <span dir="ltr">${esc(p.id)}</span> · ${esc(lab(p.domain))} ${p.emirate ? "· " + esc(lab(p.emirate)) : ""}</div>
    <h1 style="font-size:1.9rem">${esc(p.title)}</h1><p>${esc(p.question || "لم يُصغ السؤال البحثي بعد")}</p>
    <div class="acts"><button class="btn gold" id="edit">${ic("feather")} تحرير البيانات</button>
      <button class="btn glass" id="docx">${ic("download")} ملف Word</button><button class="btn glass" id="json">${ic("download")} JSON</button>
      <button class="btn glass" id="geo">${ic("map")} GeoJSON</button></div></div><div class="sadu"></div></section>
  ${sec("مسار المشروع", "gate", c, `<span class="chip gold">${esc(p.stage)} · ${esc(stageLabel(p.stage))}</span>`)}
  ${pipeline(null, p.stage)}
  <div class="grid" style="--min:380px;margin-top:16px">
    <div class="card"><div class="accent" style="--c:${allOk ? C.palm : C.crimson}"></div>
      <h3>${ic("gate")} بوابة الجودة الخارجة من «${esc(stageLabel(p.stage))}»</h3>
      <ul class="checks">${o.checks.map((x) => `<li class="${x.ok ? "ok" : "no"}"><span class="b">${x.ok ? "✓" : "✕"}</span><span>${esc(x.text)}</span></li>`).join("")}</ul>
      <div class="row" style="margin-top:12px"><button class="btn ${allOk ? "palm" : "ghost"}" id="adv" ${allOk ? "" : "disabled"}>${ic("play")} الانتقال إلى المرحلة التالية</button>
      <span class="small muted">${allOk ? "اجتازت البوابة كل الفحوص" : "لا انتقال قبل اكتمال المتطلبات"}</span></div></div>
    <div class="card"><h3>${ic("handshake")} تسجيل قرار مراجعة</h3>
      <form class="form" id="dec"><label>البوابة<select name="gate">${S.info.stages.map((s) => `<option value="${s.id}" ${s.id === p.stage ? "selected" : ""}>${s.id} · ${esc(s.label)}</option>`).join("")}</select></label>
      <label>صفة المراجع<select name="reviewer_role">${roles.map((r) => `<option>${r}</option>`).join("")}</select></label>
      <label>القرار<select name="decision">${["approve", "approve_with_changes", "revise", "reject", "escalate"].map((d) => `<option value="${d}">${lab(d)}</option>`).join("")}</select></label>
      <label class="wide">التعليل<textarea name="rationale" style="min-height:70px"></textarea></label>
      <div class="wide"><button class="btn">${ic("check")} سجّل القرار</button> <span class="tiny muted">اعتماد HUM-DIR يقتصر على حساب بصفة مدير.</span></div></form></div>
  </div>
  ${sec("مؤشرات المشروع", "kpi", C.sky)}
  <div class="grid" style="--min:250px">${o.kpis.indicators.filter((k) => k.value !== null).map(ringCard).join("") || `<div class="card muted">لا بيانات كافية بعد</div>`}</div>
  ${sec("سجلات المشروع", "database", C.clay, `<button class="btn ghost sm" id="mem">${ic("users")} الشركاء في التأليف</button>`)}
  <div class="tabs" style="--c:${C.clay}">${tables.map((t) => `<button data-t="${t}" class="${t === tab ? "on" : ""}">${ic(S.schema[t].icon)} ${esc(S.schema[t].label)} <span class="n">${o.counts[t] || 0}</span></button>`).join("")}</div>
  <div id="recs"></div>`;
  const loadTab = async (t) => {
    $$("[data-t]", main).forEach((b) => b.classList.toggle("on", b.dataset.t === t));
    const R = await api(`rows/${t}?project=${pid}`);
    const box = $("#recs");
    box.innerHTML = `<div class="spread" style="margin-bottom:10px"><b>${esc(S.schema[t].label)}</b>
      <div class="row"><button class="btn sm ghost" id="csv">${ic("download")} CSV</button><button class="btn sm gold" id="add">${ic("plus")} ${esc(S.schema[t].one)} جديد</button></div></div>${rowsTable(t, R)}`;
    $("#add").onclick = () => editRecord(t, null, { project_id: pid, access_level: "project" }, () => project(main, pid, t));
    $("#csv").onclick = () => download(`export/csv/${t}?project=${pid}`);
    bindRows(box, t, R, () => project(main, pid, t));
  };
  $$("[data-t]", main).forEach((b) => (b.onclick = () => loadTab(b.dataset.t)));
  loadTab(tab);
  $("#edit").onclick = () => editRecord("projects", p, {}, () => project(main, pid));
  $("#docx").onclick = () => download(`export/docx/${pid}`);
  $("#json").onclick = () => download(`export/json/${pid}`);
  $("#geo").onclick = () => download(`export/geojson?project=${pid}`);
  $("#adv").onclick = async () => {
    const r = await run(() => api(`projects/${pid}/advance`, { method: "POST" }));
    if (r && r.advanced) { toast("انتقل المشروع إلى " + stageLabel(r.stage)); project(main, pid); }
  };
  $("#dec").onsubmit = async (e) => {
    e.preventDefault();
    if (await run(() => api(`projects/${pid}/decision`, { method: "POST", body: formData(e.target) }), "سُجّل القرار")) project(main, pid);
  };
  $("#mem").onclick = async () => {
    const M = await api(`projects/${pid}/members`);
    const b = modal("الشركاء في التأليف المشترك", `<p class="muted small">يرى الشركاء سجلات المشروع غير الخاصة، ويحرر «المؤلف المشارك» منها؛ وتبقى سجلات «خاص» لمالكها وحده.</p>
      <ul class="timeline">${M.map((m) => `<li>${ic("users")} <b>${esc(m.display_name)}</b> <span class="muted">${esc(m.username)}</span> ${badge(m.role === "viewer" ? "مطّلع" : "مؤلف مشارك", C.plum)}</li>`).join("") || "<li class='muted'>لا شركاء بعد</li>"}</ul>
      ${p.owner_id === S.user.id ? `<form class="form" id="mf"><label>اسم المستخدم<input name="username" required></label><label>الصفة<select name="role"><option value="coauthor">مؤلف مشارك</option><option value="viewer">مطّلع</option></select></label>
      <div><button class="btn plum">${ic("plus")} دعوة</button></div></form>` : ""}`, C.plum, "users");
    if ($("#mf", b)) $("#mf", b).onsubmit = async (e) => { e.preventDefault(); if (await run(() => api(`projects/${pid}/members`, { method: "POST", body: formData(e.target) }), "أُضيف الشريك")) closeModal(); };
  };
}

/* ------------------------------------------------------------ السجلات */
const GROUPS = { core: "المشاريع", evidence: "المصادر والأدلة", oral: "التاريخ الشفهي", media: "الوسائط", documents: "الوثائق والتشريعات", heritage: "العناصر والحرف", context: "الأماكن والأشخاص والأحداث", field: "الجمع الميداني", ethics: "الأخلاقيات", quality: "الجودة والنشر" };
async function archive(main, table = "sources") {
  const groups = {};
  Object.entries(S.schema).forEach(([t, v]) => (groups[v.group] = groups[v.group] || []).push(t));
  const R = await api("rows/" + table);
  main.innerHTML = `${sec("السجلات المعرفية", "database", C.clay, `<button class="btn gold" id="add">${ic("plus")} ${esc(S.schema[table].one)} جديد</button>`)}
  <div class="split"><div class="card doclist">${Object.entries(groups).map(([g, ts]) => `<div class="tiny muted" style="margin:8px 4px 2px">${GROUPS[g] || g}</div>
    ${ts.map((t) => `<div class="item ${t === table ? "on" : ""}" data-go="archive/${t}">${ic(S.schema[t].icon)} ${esc(S.schema[t].label)}</div>`).join("")}`).join("")}</div>
  <div><div class="spread" style="margin-bottom:10px"><h3 style="margin:0;color:var(--blue)">${ic(S.schema[table].icon)} ${esc(S.schema[table].label)} <span class="muted small">(${R.length})</span></h3>
    <button class="btn sm ghost" id="csv">${ic("download")} CSV</button></div>${rowsTable(table, R)}</div></div>`;
  bindGo(main);
  bindRows(main, table, R);
  $("#add").onclick = () => editRecord(table);
  $("#csv").onclick = () => download(`export/csv/${table}`);
}

/* ------------------------------------------------------------ الخزنة */
async function vault(main) {
  const [A, P] = await Promise.all([api("assets"), api("rows/projects")]);
  const imgs = A.filter((a) => a.kind === "image"), other = A.filter((a) => a.kind !== "image");
  const size = A.reduce((s, a) => s + (a.size || 0), 0);
  main.innerHTML = `${sec("خزنة الأصول الرقمية", "archive", C.brown, `<button class="btn ghost" id="ver">${ic("shield")} فحص السلامة</button><button class="btn" id="bak">${ic("download")} نسخة احتياطية</button>`)}
  <div class="grid" style="--min:220px">${statCard("أصل محفوظ", A.length, "archive", C.brown)}${statCard("ميغابايت", (size / 1048576).toFixed(1), "database", C.clay)}
    ${statCard("سليم البصمة", A.filter((a) => a.integrity === "ok").length, "shield", C.palm)}${statCard("معروف المصدر والحقوق", A.filter((a) => a.provenance && a.rights).length, "handshake", C.gold)}</div>
  <div class="card" style="margin-top:16px"><div class="accent" style="--c:${C.gold}"></div>
    <div class="drop" id="drop"><img src="${PH("archive")}" alt="" style="width:180px;border-radius:14px"><h3>اسحب الملفات هنا أو اخترها</h3>
    <p class="muted small">MP3 · WAV · FLAC · MP4 · MOV · صور · وثائق ممسوحة · نصوص. تُحسب بصمة SHA-256، وتُحفظ النسخة الأصلية للقراءة فقط ولا تُعدَّل أبداً.</p>
    <input type="file" id="files" multiple></div>
    <form class="form" id="meta" style="margin-top:14px"><label>المشروع<select name="project"><option value="">— دون مشروع —</option>${P.map((p) => `<option value="${esc(p.id)}">${esc(p.id)} — ${esc(p.title)}</option>`).join("")}</select></label>
      <label>المصدر وسلسلة الحيازة<input name="provenance" placeholder="من سجّل المادة، ومتى، وكيف وصلت"></label>
      <label>الحقوق وشروط الاستخدام<input name="rights" placeholder="بحثي فقط، مقيّد، بترخيص…"></label>
      <label>المودِع<input name="depositor"></label>
      <label>مستوى الإتاحة<select name="access"><option value="private">خاص</option><option value="project">ضمن المشروع</option><option value="shared">مشارَك</option></select></label></form></div>
  ${sec("المسار الوثائقي: الصور", "camera", C.sky)}
  ${imgs.length ? `<div class="gallery">${imgs.map((a) => `<div class="thumb"><img loading="lazy" src="${fileUrl(a.id)}" alt="${esc(a.filename)}"><span class="tag">${badge(a.integrity === "ok" ? "سليم" : a.integrity, STATUS_C[a.integrity])} ${hasGps(a) ? badge("يحمل موقعاً", C.crimson) : ""}</span><div class="cap">${esc(a.filename)}</div></div>`).join("")}</div>`
    : `<div class="card empty"><img src="${PH("material")}" alt=""><p>لا صور بعد. الصور المودعة هنا تدخل المسار الوثائقي بعد توثيق مصدرها؛ أما صور الواجهة فللزينة لا دليلاً تاريخياً.</p></div>`}
  ${sec("الملفات الصوتية والمرئية والوثائق", "wave", C.teal)}
  ${other.length ? `<div class="table-wrap"><table><thead><tr><th>المعرّف</th><th>الملف</th><th>النوع</th><th>الحجم</th><th>البصمة</th><th>المصدر</th><th>السلامة</th><th></th></tr></thead><tbody>
    ${other.map((a) => `<tr><td class="tiny" dir="ltr">${esc(a.id)}</td><td>${esc(a.filename)}</td><td>${esc(a.kind)}</td><td>${((a.size || 0) / 1024).toFixed(0)} ك.ب</td>
    <td class="tiny" dir="ltr" title="${esc(a.sha256)}">${esc(a.sha256.slice(0, 12))}…</td><td class="small">${esc(a.provenance || "—")}</td>
    <td>${badge(a.integrity === "ok" ? "سليم" : a.integrity, STATUS_C[a.integrity])}</td><td><a href="${fileUrl(a.id, false)}">${ic("download")}</a></td></tr>`).join("")}</tbody></table></div>`
    : `<div class="card empty muted">لا ملفات بعد.</div>`}`;
  const drop = $("#drop"), inp = $("#files");
  const send = async (files) => {
    const m = formData($("#meta"));
    if (!m.provenance || !m.rights) { if (!confirm("لم يُسجَّل المصدر أو الحقوق؛ سيُحسب الملف ناقص البيانات في المؤشرات ولن تجتاز بوابة الجمع. المتابعة؟")) return; }
    busy(true);
    try {
      for (const f of files) {
        const q = new URLSearchParams({ project: m.project, provenance: m.provenance, rights: m.rights, depositor: m.depositor, access: m.access });
        const r = await api("upload?" + q, { method: "POST", raw: true, body: f, headers: { "X-Filename": encodeURIComponent(f.name) } });
        toast(r.duplicate ? `الملف ${f.name} محفوظ من قبل (${r.id})` : `أُودع ${f.name} — ${r.id}`);
      }
    } catch (e) { toast(e.message, true); } finally { busy(false); vault(main); }
  };
  inp.onchange = () => send([...inp.files]);
  drop.ondragover = (e) => { e.preventDefault(); drop.classList.add("over"); };
  drop.ondragleave = () => drop.classList.remove("over");
  drop.ondrop = (e) => { e.preventDefault(); drop.classList.remove("over"); send([...e.dataTransfer.files]); };
  $("#ver").onclick = async () => { const r = await run(() => api("vault/verify", { method: "POST" })); if (r) { toast(`سليم: ${r.ok} · مفقود: ${r.missing.length} · معدَّل: ${r.altered.length}`, !!(r.missing.length || r.altered.length)); vault(main); } };
  $("#bak").onclick = async () => { const r = await run(() => api("vault/backup", { method: "POST" })); if (r) toast("حُفظت النسخة الاحتياطية: " + r.file); };
}

const hasGps = (a) => { try { return !!JSON.parse(a.technical || "{}").gps; } catch { return false; } };

/* ------------------------------------------------------------ دليل البدء */
const TOUR = [
  ["hero", "مرحباً بكم في «تراث»", "إدارة بحثية رقمية لتراث الإمارات: أرشيف يحفظ الأدلة الأولية، ويربط كل استنتاج علمي بأصله، بانضباط صفر تلفيق. هذه جولة من خمس خطوات."],
  ["aerial", "١. المشروع أولاً", "كل بحث مشروع يمر بست عشرة مرحلة، من الفكرة إلى النشر. وعند كل انتقال بوابة جودة تُحسب فحوصها من البيانات، فلا يتقدم المشروع قبل استيفائها."],
  ["archive", "٢. الخزنة", "أودعوا التسجيلات والصور والوثائق بالسحب والإفلات، مع مصدرها وحقوقها. يُحفظ الأصل ببصمة رقمية للقراءة فقط، ويُكشف أي عبث به."],
  ["lab", "٣. المختبر الشفهي", "فرّغوا المقابلة حرفياً بطوابع زمنية، واللفظ المحلي كما نطقه الراوي. وما لم يُفهم يُعلَّم «[غير مفهوم]» دون تخمين، ثم يراجعه متحدث محلي مؤهل."],
  ["evidence", "٤. الأدلة والتثليث", "كل ادعاء يُربط بأدلته. والشهادات المنقولة عن أصل واحد تُعدّ شهادة واحدة، ولا يُثبت ادعاء بالصحافة وحدها، وكل تعارض يُحفظ في سجله."],
  ["skills", "٥. الوكلاء والمهارات", "أربعة عشر أمراً، مثل «فرغ مقابلة» و«حقق رواية»، يُكلَّف بها الوكيل المختص. والاعتماد النهائي لكم وحدكم. ابدؤوا بالنموذج التطبيقي «التلي» لتروا المنظومة تعمل."],
];
function showTour(i = 0) {
  const [img, title, text] = TOUR[i];
  const last = i === TOUR.length - 1;
  const body = modal(title, `<div style="height:220px;border-radius:16px;position:relative;overflow:hidden;background:url(${PH(img)}) center/cover;margin-bottom:14px">${cx(img)}</div>
    <p style="font-size:1.08rem">${esc(text)}</p>
    <div class="row" style="justify-content:space-between;margin-top:14px"><span class="muted small">${i + 1} / ${TOUR.length}</span>
    <div class="row">${i ? `<button class="btn ghost" id="tp">السابق</button>` : ""}
      ${last ? `<button class="btn gold" id="tpilot">${ic("star")} النموذج التطبيقي: التلي</button><button class="btn" id="tend">إنهاء الجولة</button>`
             : `<button class="btn gold" id="tn">التالي</button>`}</div></div>`, C.blue, "compass");
  try { localStorage.setItem("turath_toured", "1"); } catch {}
  if ($("#tp", body)) $("#tp", body).onclick = () => showTour(i - 1);
  if ($("#tn", body)) $("#tn", body).onclick = () => showTour(i + 1);
  if ($("#tend", body)) $("#tend", body).onclick = closeModal;
  if ($("#tpilot", body)) $("#tpilot", body).onclick = () => { closeModal(); importPilot(); };
}

/* ------------------------------------------------------------ المختبر الشفهي */
function hl(t) { return esc(t).replace(/\[غير مفهوم\]|\[؟\]/g, (m) => `<span class="unclear">${m}</span>`); }
async function labView(main, iid) {
  const IV = await api("rows/interviews");
  if (!iid) {
    main.innerHTML = `<section class="hero" style="min-height:240px;background-image:url(${PH("lab")})"><div class="in">
      <div class="kicker">${ic("ear")} المختبر السمعي واللغوي للتاريخ الشفهي</div><h1 style="font-size:1.9rem">الكلمة كما نطقها الراوي</h1>
      <p>دورة معالجة من اثنتي عشرة خطوة لكل تسجيل: من البصمة والنسخة الأصلية إلى التفريغ الحرفي والمراجعة البشرية مع متحدث محلي مؤهل.</p>
      <div class="acts"><button class="btn gold" id="ni">${ic("plus")} مقابلة جديدة</button><button class="btn glass" data-go="vault">${ic("upload")} إيداع تسجيل</button><button class="btn glass" data-go="archive/dialect_lexicon">${ic("ear")} المعجم اللهجي</button></div></div><div class="sadu"></div></section>
      <div class="note teal" style="margin-top:16px">${ic("alert")} <b>قاعدة إلزامية:</b> يُمنع استبدال الكلمات المحلية بالفصحى داخل التفريغ الحرفي؛ تُحفظ كما نطقها الراوي ولو كانت قديمة أو نادرة. والمقطع غير المفهوم يُعلَّم «[غير مفهوم]» دون تخمين.</div>
      ${sec("دورة المعالجة", "wave", C.teal)}<div class="lab">${S.info.lab_steps.map((s) => `<div class="step ${s.mode === "human" ? "human" : ""}"><span class="k">${s.step}</span> · ${esc(s.label)}<br><span class="tiny muted">${esc(s.actor)}</span></div>`).join("")}</div>
      ${sec("المقابلات", "mic", C.teal)}${rowsTable("interviews", IV, ["narrator_id", "date", "place", "transcript_status"])}`;
    bindGo(main);
    $("#ni").onclick = () => editRecord("interviews", null, { access_level: "project", transcript_status: "none" }, (r) => (location.hash = "#/lab/" + r.id));
    bindRows(main, "interviews", IV);
    return;
  }
  const iv = IV.find((x) => x.id === iid) || (await api("rows/interviews/" + iid));
  const L2 = await api("lab/" + iid);
  const asset = iv.asset_id ? await api("assets/" + iv.asset_id).catch(() => null) : null;
  const verb = L2.segments.map((s) => `[${s.start}]${s.end ? " - [" + s.end + "]" : ""} ${s.speaker ? s.speaker + ": " : ""}${s.verbatim}`).join("\n");
  const read = L2.segments.filter((s) => s.readable).map((s) => `[${s.start}] ${s.speaker ? s.speaker + ": " : ""}${s.readable}`).join("\n");
  const done = L2.steps.filter((s) => s.done).length;
  main.innerHTML = `${sec(`المقابلة ${esc(iv.archive_code || iv.id)}`, "mic", C.teal, `<button class="btn ghost sm" id="ed">${ic("feather")} بيانات المقابلة</button><button class="btn ghost sm" data-go="lab">${ic("layers")} كل المقابلات</button>`)}
  <div class="grid" style="--min:300px"><div class="card"><h3>${ic("wave")} الأصل</h3>
    ${asset ? `${asset.kind === "audio" ? `<audio controls preload="none" style="width:100%" src="${fileUrl(asset.id)}"></audio>` : asset.kind === "video" ? `<video controls preload="none" style="width:100%;border-radius:12px" src="${fileUrl(asset.id)}"></video>` : ""}
      <div class="small muted">${esc(asset.filename)} · <span dir="ltr">SHA-256 ${esc(asset.sha256.slice(0, 16))}…</span> · ${badge(asset.integrity === "ok" ? "سليم" : asset.integrity, STATUS_C[asset.integrity])}</div>`
      : `<p class="muted">لا ملف مرتبط. أودع التسجيل في الخزنة ثم اربطه من «بيانات المقابلة».</p>`}
    <div class="small" style="margin-top:8px">الباحث: ${esc(iv.researcher || "—")} · التاريخ: ${esc(iv.date || "—")} · المكان: ${esc(iv.place || "—")}</div></div>
   <div class="card"><h3>${ic("check")} التقدم في الدورة</h3><div class="bignum" style="--c:${C.teal}">${done}/12</div>
    <div class="progress" style="--c:${C.teal};margin:8px 0"><i style="width:${(done / 12) * 100}%"></i></div>${badge(lab(iv.transcript_status || "none"), C.teal)}</div></div>
  ${sec("خطوات المعالجة", "wave", C.teal)}<div class="lab">${L2.steps.map((s) => `<div class="step ${s.done ? "done" : ""} ${s.mode === "human" ? "human" : ""}" data-step="${s.step}" data-done="${s.done ? 1 : 0}" title="${s.mode === "auto" ? "تتم آلياً عند الإيداع" : "انقر للتبديل"}">
    <span class="k">${s.done ? "✓" : s.step}</span> · ${esc(s.label)}<br><span class="tiny muted">${esc(s.actor)}${s.at ? " · " + fmtDate(s.at) : ""}</span></div>`).join("")}</div>
  ${sec("التفريغ", "quote", C.teal, `<button class="btn sm ghost" id="srt">${ic("download")} SRT</button><button class="btn sm teal" id="asr" ${S.info.asr.available ? "" : "disabled"} title="${esc(S.info.asr.hint || "")}">${ic("play")} تفريغ أولي آلي</button>`)}
  ${S.info.asr.available ? "" : `<p class="tiny muted">التفريغ الآلي غير مثبت على هذا الجهاز (${esc(S.info.asr.hint)}). التفريغ اليدوي متاح دائماً.</p>`}
  <div class="grid" style="--min:420px"><div class="card"><h3>النسخة الحرفية</h3><p class="tiny muted">سطر لكل مقطع: <span dir="ltr">[00:01:12] ر1: النص</span></p>
    <textarea id="verb" style="min-height:300px">${esc(verb)}</textarea></div>
    <div class="card"><h3>النسخة اللغوية المقروءة</h3><p class="tiny muted">بالطوابع نفسها؛ لا تحل محل الحرفية.</p><textarea id="read" style="min-height:300px">${esc(read)}</textarea></div></div>
  <div class="row" style="margin:12px 0"><button class="btn teal" id="sv">${ic("check")} حفظ التفريغ</button></div>
  ${L2.segments.length ? `<div class="card">${L2.segments.map((s) => `<div class="seg"><span class="ts">${esc(s.start)}${s.end ? "–" + esc(s.end) : ""}</span><span class="sp">${esc(s.speaker || "")}</span><span>${hl(s.verbatim)}</span></div>`).join("")}</div>` : ""}`;
  bindGo(main);
  $("#ed").onclick = () => editRecord("interviews", iv, {}, () => labView(main, iid));
  $$("[data-step]", main).forEach((el) => (el.onclick = async () => {
    const st = S.info.lab_steps.find((x) => x.step == el.dataset.step);
    if (st.mode === "auto") return toast("هذه الخطوة تتم آلياً عند إيداع الأصل وربطه بالمقابلة");
    const note = el.dataset.done === "1" ? "" : prompt("ملاحظة على الخطوة (اختياري):") ?? "";
    if (await run(() => api(`lab/${iid}/step`, { method: "POST", body: { step: +el.dataset.step, done: el.dataset.done !== "1", note } }))) labView(main, iid);
  }));
  $("#sv").onclick = async () => { const r = await run(() => api(`lab/${iid}/transcript`, { method: "POST", body: { text: $("#verb").value, readable: $("#read").value } })); if (r) { toast(`حُفظ: ${r.segments} مقطعاً، منها ${r.unclear} غير مفهوم`); labView(main, iid); } };
  $("#srt").onclick = () => download(`lab/${iid}/srt`);
  $("#asr").onclick = async () => { if (await run(() => api(`lab/${iid}/asr`, { method: "POST" }), "اكتملت المسودة الآلية — تلزم المراجعة البشرية")) labView(main, iid); };
}

/* ------------------------------------------------------------ الأدلة */
async function evidence(main, tab = "claims") {
  const [CL, CF] = await Promise.all([api("rows/claims"), api("rows/conflicts")]);
  const by = {};
  CL.forEach((c) => (by[c.status] = (by[c.status] || 0) + 1));
  main.innerHTML = `<section class="hero" style="min-height:220px;background-image:url(${PH("evidence")})">${cx("evidence")}<div class="in">
    <div class="kicker">${ic("shield")} هرم المصادر والتثليث المنهجي</div><h1 style="font-size:1.9rem">لا ادعاء بلا دليل</h1>
    <p>عدد الرواة وحده لا يثبت الواقعة: تُعدّ الأصول المستقلة وأصناف الأدلة الستة، ويُحفظ كل تعارض بأسانيده دون حذف أو تسوية مصطنعة.</p>
    <div class="acts"><button class="btn gold" id="nc">${ic("plus")} ادعاء جديد</button><button class="btn glass" id="nf">${ic("alert")} تعارض جديد</button></div></div><div class="sadu"></div></section>
  <div class="grid" style="--min:170px;margin-top:16px">${["established", "probable", "disputed", "hypothesis", "pending_field"].map((s) => statCard(lab(s), by[s] || 0, "check", STATUS_C[s])).join("")}
    ${statCard("تعارض مفتوح", CF.filter((c) => c.status === "open").length, "alert", C.crimson)}</div>
  ${sec("هرم المصادر", "layers", C.crimson)}
  <div class="grid" style="--min:180px">${Object.entries(S.info.levels).map(([n, l]) => `<div class="card" style="--c:${[C.night, C.blue, C.teal, C.gold, "#8A8A8A"][n - 1]}"><div class="accent"></div><div class="bignum">${n}</div><div class="small">${esc(l)}</div></div>`).join("")}</div>
  <p class="tiny muted">ترتيب إرشادي بحسب طبيعة المصدر، لا ترتيب آلي لصدق المعلومات؛ والمستوى الخامس لا يُثبت وحده واقعة جوهرية.</p>
  <div class="tabs" style="--c:${C.crimson}"><button data-tab="claims" class="${tab === "claims" ? "on" : ""}">${ic("check")} الادعاءات <span class="n">${CL.length}</span></button>
    <button data-tab="conflicts" class="${tab === "conflicts" ? "on" : ""}">${ic("alert")} سجل التعارضات <span class="n">${CF.length}</span></button></div>
  <div id="ev"></div>`;
  const box = $("#ev");
  if (tab === "claims") { box.innerHTML = rowsTable("claims", CL, ["text", "kind", "status"]); bindRows(box, "claims", CL); }
  else {
    box.innerHTML = CF.length ? `<div class="grid" style="--min:360px">${CF.map((c) => {
      let pos = []; try { pos = JSON.parse(c.positions || "[]"); } catch {}
      return `<div class="card click" data-cf="${esc(c.id)}" style="--c:${c.status === "open" ? C.crimson : C.palm}"><div class="accent"></div>
        <div class="spread"><span class="tiny muted" dir="ltr">${esc(c.id)}</span>${badge(lab(c.status), c.status === "open" ? C.crimson : C.palm)}</div><h3>${esc(c.topic)}</h3>
        <ul class="small">${pos.map((p) => `<li><b>${esc(p.source || "")}</b>: ${esc(p.position || "")}</li>`).join("")}</ul></div>`; }).join("")}</div>` : `<div class="card empty muted">لا تعارضات مسجلة.</div>`;
    $$("[data-cf]", box).forEach((el) => (el.onclick = () => editRecord("conflicts", CF.find((c) => c.id === el.dataset.cf))));
  }
  $$("[data-tab]", main).forEach((b) => (b.onclick = () => evidence(main, b.dataset.tab)));
  $("#nc").onclick = () => editRecord("claims", null, { status: "pending_field" });
  $("#nf").onclick = () => editRecord("conflicts", null, { status: "open", positions: '[{"source":"SRC-…","position":"…"}]' });
}
async function claimCard(cid) {
  const d = await api("claims/" + cid);
  const t = d.triangulation, c = d.claim;
  const body = modal(`الادعاء ${c.id}`, `<p style="font-size:1.1rem">${esc(c.text)}</p>
    <div class="row">${badge("الحالة: " + lab(c.status), STATUS_C[c.status])} ${badge("الطبيعة: " + lab(c.kind), C.plum)}
      ${badge("الحالة المقترحة من الأدلة: " + lab(d.suggested_status), STATUS_C[d.suggested_status])}
      ${d.suggested_status !== c.status ? `<button class="btn sm ghost" id="apply">اعتمد المقترحة</button>` : ""} <button class="btn sm ghost" id="edc">${ic("feather")} تحرير</button></div>
    <h3>${ic("layers")} التثليث: أصناف الأدلة الستة</h3>
    <div class="tri">${Object.entries(S.info.evidence_types).map(([k, l]) => `<div class="${t.evidence_types.includes(k) ? "on" : ""}">${esc(l)}</div>`).join("")}</div>
    <div class="grid" style="--min:150px;margin:12px 0">${[["أدلة مؤيدة", t.supports, C.palm], ["أدلة معارضة", t.contradicts, C.crimson], ["أصول مستقلة", t.independent_origins, C.blue], ["روابط غير مستقلة", t.dependent_links, C.gold], ["أعلى مستوى", t.best_level ?? "—", C.night]]
      .map(([l, v, cc]) => `<div class="card" style="--c:${cc};padding:12px"><div class="bignum">${v}</div><div class="small">${l}</div></div>`).join("")}</div>
    ${t.press_only ? `<div class="note">${ic("alert")} الأدلة كلها من المستوى الخامس: لا يُثبت الادعاء الجوهري بها وحدها.</div>` : ""}
    <h3>${ic("link")} روابط الأدلة</h3>
    <div class="table-wrap"><table><thead><tr><th>الدليل</th><th>العلاقة</th><th>الصنف</th><th>المستوى</th><th>الموضع والشاهد</th></tr></thead><tbody>
      ${d.links.map((l) => `<tr><td><span class="tiny" dir="ltr">${esc(l.target_id)}</span><br>${esc(l.target_title || "")}</td><td>${badge(lab(l.relation), l.relation === "supports" ? C.palm : l.relation === "contradicts" ? C.crimson : C.sky)}</td>
        <td>${esc(lab(l.evidence_type))}</td><td>${l.level ?? "—"}</td><td class="small">${esc(l.locator || "")} ${l.excerpt ? "«" + esc(l.excerpt) + "»" : ""}</td></tr>`).join("") || `<tr><td colspan="5" class="muted">لا أدلة بعد</td></tr>`}</tbody></table></div>
    <h3>${ic("plus")} ربط دليل جديد</h3>
    <form class="form" id="lk"><label>نوع السجل<select name="target_table" id="tt">${["sources", "historical_documents", "manuscripts", "interviews", "oral_narratives", "images", "poems", "observations"].map((x) => `<option value="${x}">${esc(S.schema[x].label)}</option>`).join("")}</select></label>
      <label>السجل<select name="target_id" id="tid"></select></label>
      <label>صنف التثليث<select name="evidence_type">${Object.entries(S.info.evidence_types).map(([k, l]) => `<option value="${k}">${esc(l)}</option>`).join("")}</select></label>
      <label>العلاقة<select name="relation"><option value="supports">يؤيد</option><option value="contradicts">يعارض</option><option value="context">سياق</option></select></label>
      <label>الموضع (صفحة/توقيت)<input name="locator"></label><label>أصل الشهادة (لفحص الاستقلال)<input name="origin_group" placeholder="مثلاً: رواية الأسرة الفلانية"></label>
      <label class="wide">الشاهد<textarea name="excerpt" style="min-height:60px"></textarea></label><div><button class="btn crimson">${ic("link")} اربط</button></div></form>`, C.crimson, "shield");
  const loadT = async () => { const o = await refOptions($("#tt", body).value); $("#tid", body).innerHTML = o.map(([id, l]) => `<option value="${esc(id)}">${esc(l)}</option>`).join(""); };
  $("#tt", body).onchange = loadT; loadT();
  $("#lk", body).onsubmit = async (e) => { e.preventDefault(); if (await run(() => api(`claims/${cid}/link`, { method: "POST", body: formData(e.target) }), "رُبط الدليل")) claimCard(cid); };
  $("#edc", body).onclick = () => editRecord("claims", c);
  if ($("#apply", body)) $("#apply", body).onclick = async () => { if (await run(() => api(`rows/claims/${cid}`, { method: "PUT", body: { status: d.suggested_status } }), "حُدّثت الحالة")) claimCard(cid); };
}

/* ------------------------------------------------------------ الوكلاء */
const AG_ORDER = ["AG-DIR", "AG-PLN", "AG-HIS", "AG-ANT", "AG-FLD", "AG-ORL", "AG-TRN", "AG-DIA", "AG-PTR", "AG-ARC", "AG-MAT", "AG-CRF", "AG-ENV", "AG-LAW", "AG-GIS", "AG-DAT", "AG-VIS", "AG-SRC", "AG-ETH", "AG-PUB"];
async function agentsView(main) {
  const A = (S.cache.agents || (S.cache.agents = await api("agents"))).slice().sort((x, y) => AG_ORDER.indexOf(x.id) - AG_ORDER.indexOf(y.id));
  const units = {};
  A.forEach((a) => (units[a.unit] = units[a.unit] || { c: a.color, list: [] }).list.push(a));
  const SKN = Object.fromEntries((await skillsList()).map((s) => [s.id, s.command]));
  const R = await api("runs");
  main.innerHTML = `${sec("الهيكل التنظيمي", "director", C.plum)}
  <div class="card"><div class="orgchart"><div class="top-node"><b>المراجع البشري المخوّل</b><br><small>HUM-DIR — صاحب الاعتماد النهائي</small></div><div class="stem"></div>
    <div class="top-node" style="background:linear-gradient(135deg,var(--gold),#8B6508)"><b>المدير التنفيذي للإدارة</b><br><small>AG-DIR — توزيع المهام، ومتابعة التقدم، وتنسيق التخصصات</small></div><div class="stem"></div>
    <div class="units">${Object.entries(units).map(([u, v]) => `<div class="u" style="--c:${v.c}">${esc(u)}<small>${v.list.length} وكيل</small></div>`).join("")}</div></div></div>
  <div class="note" style="margin-top:12px">${ic("alert")} الوكلاء مواصفات تشغيلية كاملة (موجه نظام مستقل، وصلاحيات، وإجراءات، وتسليم). يُشغَّل الوكيل فعلاً بالمحرك المتاح: Claude Code أو مفتاح API؛ وإلا تُنتَج حزمة تكليف جاهزة للصق. لا يُدّعى تشغيل لم يحدث.</div>
  ${Object.entries(units).map(([u, v]) => `${sec(esc(u), "people", v.c)}<div class="grid" style="--min:300px">${v.list.map((a) => `
    <div class="card click" data-ag="${a.id}" style="--c:${a.color}"><div class="accent"></div><div class="agent"><div class="av">${ic(a.icon, "lg")}</div>
    <div><span class="id">${a.id}</span><h3>${esc(a.name_ar)}</h3><div class="tiny muted" dir="ltr" style="text-align:right">${esc(a.name_en)}</div></div></div>
    <p class="small" style="margin:8px 0 0">${esc(a.mission)}</p>
    <div class="row" style="margin-top:8px">${(a.skills || []).map((s) => badge("«" + (SKN[s] || s) + "»", a.color)).join("")}</div></div>`).join("")}</div>`).join("")}
  ${sec("سجل التكليفات", "clock", C.night)}
  ${R.length ? `<div class="table-wrap"><table><thead><tr><th>المعرّف</th><th>الوكيل</th><th>المهارة</th><th>التكليف</th><th>المحرك</th><th>الحالة</th><th>التاريخ</th></tr></thead><tbody>
    ${R.map((r) => `<tr class="click" data-run="${esc(r.id)}"><td class="tiny" dir="ltr">${esc(r.id)}</td><td>${esc(r.agent_id)}</td><td>${esc(r.skill_id || "—")}</td><td>${esc((r.task || "").slice(0, 80))}</td><td>${esc(r.engine)}</td>
    <td>${badge({ package: "حزمة جاهزة", draft: "مسودة للمراجعة", failed: "تعذر" }[r.status] || r.status, r.status === "failed" ? C.crimson : r.status === "draft" ? C.palm : C.gold)}</td><td class="tiny">${fmtDate(r.created_at)}</td></tr>`).join("")}</tbody></table></div>` : `<div class="card muted">لا تكليفات بعد.</div>`}`;
  $$("[data-ag]", main).forEach((el) => (el.onclick = () => agentCard(A.find((a) => a.id === el.dataset.ag))));
  $$("[data-run]", main).forEach((el) => (el.onclick = async () => showRun(await api("runs/" + el.dataset.run))));
}
const list = (arr) => `<ul class="small">${(arr || []).map((x) => `<li>${esc(typeof x === "string" ? x : `${x.tool} — ${x.use}`)}</li>`).join("")}</ul>`;
async function agentCard(a, skillId) {
  const P = await api("rows/projects");
  const tabs = [["sys", "موجه النظام"], ["scope", "الاختصاص والصلاحيات"], ["tools", "الأدوات والبيانات"], ["sop", "الإجراءات والتسليم"], ["kpi", "المخرجات والجودة"], ["run", "كلّف الوكيل"]];
  const body = modal(`${a.name_ar} — ${a.id}`, `<div class="agent"><div class="av" style="--c:${a.color}">${ic(a.icon, "lg")}</div><div><b>${esc(a.name_en)}</b> · ${esc(a.unit)}<p class="small" style="margin:4px 0">${esc(a.mission)}</p>
    <div class="row">${(a.stages || []).map((s) => badge(s, C.gold)).join("")}</div></div></div>
    <div class="tabs" style="--c:${a.color}">${tabs.map(([k, l], i) => `<button data-at="${k}" class="${(skillId ? k === "run" : i === 0) ? "on" : ""}">${l}</button>`).join("")}</div>
    <div data-ap="sys"><pre class="out">${esc(a.system_prompt)}</pre><button class="btn sm ghost" id="cp">${ic("download")} نسخ الموجه</button></div>
    <div data-ap="scope" hidden><div class="grid" style="--min:260px"><div><h3>الاختصاص</h3>${list(a.competence)}</div><div><h3>الصلاحيات</h3>${list(a.permissions)}</div><div><h3>المحظورات</h3>${list(a.prohibitions)}</div><div><h3>المدخلات المقبولة</h3>${list(a.inputs)}</div></div></div>
    <div data-ap="tools" hidden><h3>الأدوات المسموح بها</h3>${list(a.tools_allowed)}<div class="grid" style="--min:260px"><div><h3>قراءة البيانات</h3><div class="row">${(a.data_store?.read || []).map((t) => badge(S.schema[t]?.label || t, C.sky)).join("")}</div></div>
      <div><h3>كتابة البيانات</h3><div class="row">${(a.data_store?.write || []).map((t) => badge(S.schema[t]?.label || t, C.clay)).join("") || "—"}</div></div></div><h3>المهارات</h3><div class="row">${(a.skills || []).map((s) => badge(s, a.color)).join("")}</div></div>
    <div data-ap="sop" hidden><h3>إجراءات العمل</h3><ol class="small">${(a.sop || []).map((s) => `<li>${esc(s)}</li>`).join("")}</ol>
      <h3>التسليم</h3><p class="small">يستلم من: ${(a.handoff?.receives_from || []).map((x) => badge(x, C.blue)).join(" ")}<br>يسلّم إلى: ${(a.handoff?.delivers_to || []).map((x) => badge(x, C.palm)).join(" ")}</p>
      ${list(a.handoff?.package)}<p class="small"><b>معيار القبول:</b> ${esc(a.handoff?.acceptance || "")}</p><h3>التنسيق</h3>${list(a.coordination)}</div>
    <div data-ap="kpi" hidden><div class="grid" style="--min:260px"><div><h3>المخرجات الإلزامية</h3>${list(a.outputs)}</div><div><h3>مقاييس الأداء والجودة</h3>${list(a.kpis)}</div><div><h3>حالات التدخل البشري</h3>${list(a.human_intervention)}</div></div></div>
    <div data-ap="run" hidden><form class="form" id="rf"><label>المشروع<select name="project"><option value="">— دون مشروع —</option>${P.map((p) => `<option value="${esc(p.id)}">${esc(p.id)} — ${esc(p.title)}</option>`).join("")}</select></label>
      <label>المهارة<select name="skill"><option value="">—</option>${(await skillsList()).map((s) => `<option value="${s.id}" ${s.id === skillId ? "selected" : ""}>«${esc(s.command)}»</option>`).join("")}</select></label>
      <label>المحرك<select name="engine">${Object.entries(S.info.engines).map(([k, e]) => `<option value="${k}" ${k === S.info.engine ? "selected" : ""} ${e.available ? "" : "disabled"}>${esc(e.label)}${e.available ? "" : " (غير متاح)"}</option>`).join("")}</select></label>
      <label class="wide">التكليف<textarea name="task" required placeholder="صف المهمة بدقة: المطلوب، والمدخلات، وحدود العمل"></textarea></label>
      <div><button class="btn plum">${ic("play")} كلّف</button></div></form></div>`, a.color, a.icon);
  $$("[data-at]", body).forEach((b) => (b.onclick = () => { $$("[data-at]", body).forEach((x) => x.classList.toggle("on", x === b)); $$("[data-ap]", body).forEach((p) => (p.hidden = p.dataset.ap !== b.dataset.at)); }));
  if (skillId) $$("[data-ap]", body).forEach((p) => (p.hidden = p.dataset.ap !== "run"));
  $("#cp", body).onclick = () => navigator.clipboard.writeText(a.system_prompt).then(() => toast("نُسخ الموجه"));
  $("#rf", body).onsubmit = async (e) => {
    e.preventDefault();
    const f = formData(e.target);
    const r = await run(() => api("agents/run", { method: "POST", body: { agent: a.id, ...f } }));
    if (r) showRun(r);
  };
}
function showRun(r) {
  const out = r.output_clean || r.output || r.prompt;
  const hl = r.humanlang;
  const body = modal(`التكليف ${r.id}`, `<div class="row">${badge("المحرك: " + r.engine, C.plum)} ${badge({ package: "حزمة تكليف جاهزة للصق في Claude", draft: "مسودة — تلزم المراجعة البشرية", failed: "تعذر التشغيل" }[r.status] || r.status, r.status === "failed" ? C.crimson : C.gold)}</div>
    ${hl ? `<div class="note small" style="margin-top:10px">${ic(hl.ok ? "check" : "alert")} اللغة البشرية: ${hl.ok ? "ضمن الحدود" : "تجاوز في: " + hl.flags.map((f) => ({ stock_phrases: "لوازم الصياغة الآلية", em_dash: "الشَّرطة الطويلة", latin_notes: "ملاحظات إنجليزية" }[f] || f)).join("، ")}
      · نسخة القراءة منقّاة (${r.clean_report.translated} وسماً عُرّب، ${r.clean_report.hidden_chars} محرفاً خفياً أزيل)، والأصل محفوظ كما ورد.</div>` : ""}
    <pre class="out" style="margin-top:12px">${esc(out)}</pre><div class="row"><button class="btn sm" id="cp">${ic("download")} نسخ</button>${r.output && r.prompt ? `<button class="btn sm ghost" id="pp">عرض الحزمة</button>` : ""}</div>`, C.plum, "play");
  $("#cp", body).onclick = () => navigator.clipboard.writeText(out).then(() => toast("نُسخ"));
  if ($("#pp", body)) $("#pp", body).onclick = () => ($("pre", body).textContent = r.prompt);
}

/* ------------------------------------------------------------ المهارات */
const skillsList = async () => S.cache.skills || (S.cache.skills = await api("skills"));
async function skillsView(main) {
  const SK = await skillsList();
  const A = S.cache.agents || (S.cache.agents = await api("agents"));
  main.innerHTML = `<section class="hero" style="min-height:220px;background-image:url(${PH("skills")})"><div class="in">
    <div class="kicker">${ic("star")} أربع عشرة مهارة قابلة للاستدعاء</div><h1 style="font-size:1.9rem">الأوامر المؤسسية</h1>
    <p>كل أمر يستدعي وكيله القائد بإجراءات ومخرجات إلزامية. وهي متاحة أيضاً مهاراتٍ في Claude Code داخل هذا المستودع (.claude/skills).</p></div><div class="sadu"></div></section>
  <div class="grid" style="--min:280px;margin-top:18px">${SK.map((s) => `<div class="card click skill" data-sk="${s.id}" style="--c:${s.color}">
    <div class="ghost-ic">${ic(s.icon)}</div><div class="row">${ic(s.icon, "lg")}<span class="tiny" dir="ltr">${s.id}</span></div>
    <div class="cmd">«${esc(s.command)}»</div><p class="small" style="opacity:.92;margin:6px 0">${esc(s.purpose.slice(0, 120))}…</p>
    <div class="row">${s.agents.map((x) => `<span class="chip" style="background:rgba(255,255,255,.18);color:#fff;border-color:transparent">${x}</span>`).join("")}</div></div>`).join("")}</div>`;
  $$("[data-sk]", main).forEach((el) => (el.onclick = () => {
    const s = SK.find((x) => x.id === el.dataset.sk);
    const body = modal(`«${s.command}»`, `<p>${esc(s.purpose)}</p><div class="grid" style="--min:260px"><div><h3>المدخلات</h3>${list(s.inputs)}</div><div><h3>المخرجات الإلزامية</h3>${list(s.outputs)}</div></div>
      <h3>الإجراءات</h3><ol class="small">${s.steps.map((x) => `<li>${esc(x)}</li>`).join("")}</ol>
      <p class="small">المرحلة: ${badge(s.stage + " · " + stageLabel(s.stage), C.gold)} · الوكلاء: ${s.agents.map((x) => badge(x, s.color)).join(" ")}</p>
      <div class="row"><button class="btn" id="go" style="background:${s.color}">${ic("play")} نفّذ الأمر مع ${esc(s.agents[0])}</button>
      ${s.opens ? `<button class="btn ghost" id="op">${ic("database")} افتح السجلات المعنية</button>` : ""}</div>`, s.color, s.icon);
    $("#go", body).onclick = () => agentCard(A.find((a) => a.id === s.agents[0]), s.id);
    if ($("#op", body)) $("#op", body).onclick = () => { closeModal(); location.hash = s.opens === "assets" ? "#/vault" : s.opens === "projects" ? "#/projects" : "#/archive/" + s.opens; };
  }));
}

/* ------------------------------------------------------------ لوحة القيادة */
async function kpiView(main, pid) {
  const [k, P] = await Promise.all([api("kpis" + (pid ? "?project=" + pid : "")), api("rows/projects")]);
  main.innerHTML = `${sec("لوحة القيادة", "kpi", C.sky, `<select id="pp"><option value="">كل المشاريع</option>${P.map((p) => `<option value="${esc(p.id)}" ${p.id === pid ? "selected" : ""}>${esc(p.title)}</option>`).join("")}</select>
    ${["director", "admin"].includes(S.user.role) ? `<button class="btn gold" id="bl">${ic("check")} تثبيت خط الأساس</button>` : ""}`)}
  <div class="note">${ic("alert")} لا تُعتمد مستهدفات رقمية نهائية قبل تأسيس خط أساس تجريبي. ${k.baseline_set ? `خط الأساس مثبت في ${fmtDate(k.baseline_at)}، وتظهر قيمته تحت كل مؤشر.` : "لم يُثبَّت خط الأساس بعد: يُثبته المدير بعد أشهر التشغيل الأولى."}</div>
  <div class="grid" style="--min:280px;margin-top:14px">${k.indicators.map(ringCard).join("")}</div>
  ${sec("النطاقات الممثلة", "map", C.teal)}<div class="row">${Object.values(S.info.regions).map((r) => badge(r, k.regions.includes(r) ? C.palm : "#8A8A8A")).join("")}</div>
  ${sec("طريقة الحساب", "layers", C.night)}<div class="card small"><ul>
    <li>المصدر المعروف: أصول سُجّل مصدرها وحقوقها ÷ كل الأصول.</li><li>اكتمال البيانات الوصفية: أصول مرتبطة بسجل وصفي ومكتملة المصدر والحقوق والمودِع.</li>
    <li>التفريغات المعتمدة: مقابلات روجعت لهجياً أو اعتُمدت ÷ المقابلات المفرغة.</li><li>الشهادات المستقلة: متوسط الأصول المستقلة المؤيدة لكل ادعاء (الشهادات المشتركة الأصل تُعد واحدة).</li>
    <li>الموافقات: مقابلات وصور لها موافقة قائمة غير مسحوبة.</li><li>أخطاء التفريغ اللهجي: المقاطع المصححة بعد التدقيق ÷ مقاطع المقابلات المراجَعة.</li>
    <li>سلامة الأصول: أصول طابقت بصمتها في آخر فحص.</li><li>تنوع النطاقات: النطاقات الستة الممثلة في الرواة والعناصر والحرف والأماكن والمعجم.</li></ul></div>`;
  $("#pp").onchange = (e) => (location.hash = "#/kpis" + (e.target.value ? "/" + e.target.value : ""));
  if ($("#bl")) $("#bl").onclick = async () => { if (confirm("تثبيت القيم الحالية خط أساس؟ قرار بشري يُسجَّل.") && (await run(() => api("kpis/baseline", { method: "POST" }), "ثُبّت خط الأساس"))) kpiView(main, pid); };
}

/* ------------------------------------------------------------ الوثائق */
function md(src) {
  const lines = src.replace(/\r/g, "").split("\n");
  let out = "", i = 0, inList = null;
  const inline = (t) => esc(t).replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>").replace(/\*([^*]+)\*/g, "<i>$1</i>")
    .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>').replace(/\[([^\]]+)\]\(([^)\s]+\.md)\)/g, '<a href="#/docs/$2">$1</a>');
  const close = () => { if (inList) { out += `</${inList}>`; inList = null; } };
  while (i < lines.length) {
    const l = lines[i];
    if (/^```/.test(l)) { close(); let b = ""; i++; while (i < lines.length && !/^```/.test(lines[i])) b += lines[i++] + "\n"; out += `<pre>${esc(b)}</pre>`; i++; continue; }
    if (/^\|/.test(l) && /^\|?\s*:?-{2,}/.test(lines[i + 1] || "")) {
      close(); const row = (s) => s.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
      out += `<table><thead><tr>${row(l).map((c) => `<th>${inline(c)}</th>`).join("")}</tr></thead><tbody>`; i += 2;
      while (i < lines.length && /^\|/.test(lines[i])) out += `<tr>${row(lines[i++]).map((c) => `<td>${inline(c)}</td>`).join("")}</tr>`;
      out += "</tbody></table>"; continue;
    }
    let m;
    if ((m = l.match(/^(#{1,4})\s+(.*)/))) { close(); out += `<h${m[1].length}>${inline(m[2])}</h${m[1].length}>`; }
    else if ((m = l.match(/^\s*[-*]\s+(.*)/))) { if (inList !== "ul") { close(); out += "<ul>"; inList = "ul"; } out += `<li>${inline(m[1])}</li>`; }
    else if ((m = l.match(/^\s*\d+[.)]\s+(.*)/))) { if (inList !== "ol") { close(); out += "<ol>"; inList = "ol"; } out += `<li>${inline(m[1])}</li>`; }
    else if ((m = l.match(/^>\s?(.*)/))) { close(); out += `<blockquote>${inline(m[1])}</blockquote>`; }
    else if (/^---+$/.test(l.trim())) { close(); out += "<hr>"; }
    else if (!l.trim()) close();
    else { close(); out += `<p>${inline(l)}</p>`; }
    i++;
  }
  close();
  return out;
}
async function docsView(main, ...name) {
  const D = await api("docs");
  const cur = name.join("/") || (D[0] && D[0].name);
  const doc = cur ? await api("docs/" + cur).catch(() => null) : null;
  main.innerHTML = `${sec("الوثائق المؤسسية والاستمارات", "book", C.night)}<div class="split"><div class="card doclist">
    ${D.map((d) => `<div class="item ${d.name === cur ? "on" : ""}" data-go="docs/${esc(d.name)}">${ic(d.name.startsWith("pilot") ? "star" : "scroll")}<span class="small">${esc(d.title)}</span></div>`).join("")}</div>
    <div>${doc ? `<div class="row" style="margin-bottom:10px"><button class="btn sm ghost" id="pr">${ic("download")} طباعة / PDF</button></div><article class="doc">${md(doc.text)}</article>` : `<div class="card muted">لا وثيقة</div>`}</div></div>`;
  bindGo(main);
  if ($("#pr")) $("#pr").onclick = () => window.print();
}

/* ------------------------------------------------------------ الإعدادات */
async function settings(main) {
  const U = await api("users");
  const canAdmin = ["admin", "director"].includes(S.user.role);
  const modes = Object.entries(S.info.modes).map(([k, m], i) => `<div class="card" style="--c:${[C.blue, C.teal, C.plum][i]};${k === S.info.mode ? "outline:3px solid var(--gold)" : ""}"><div class="accent"></div>
    <div class="row">${ic(["home", "layers", "users"][i], "lg")}<h3 style="margin:0">${esc(m.label)}</h3>${k === S.info.mode ? badge("النمط الحالي", C.gold) : ""}</div>
    <p class="small">${["الخادم على هذا الجهاز وحده (127.0.0.1)، والدخول برمز يتولد عند كل تشغيل. أبسط الأنماط وأكثرها عزلاً.",
      "خادم محلي على حاسوب في البيت أو المكتب، تصله أجهزتك عبر الشبكة المحلية بكلمة مرور، مع TLS اختياري.",
      "حساب لكل باحث، وبحوثه خاصة لا يطلع عليها غيره، مع مشاركة المصادر بالاختيار والتأليف المشترك بدعوة الشركاء."][i]}</p>
    <pre class="out" dir="ltr" style="text-align:left;font-family:Consolas,monospace;font-size:.8rem">turath setup ${k}${k === "lan" ? " --cert cert.pem --key key.pem" : ""}\nturath serve</pre></div>`).join("");
  main.innerHTML = `${sec("أنماط التشغيل الثلاثة", "settings", "#56657A")}<div class="grid" style="--min:300px">${modes}</div>
  ${sec("المحركات والأدوات", "play", C.plum)}
  <div class="card"><form class="row" id="eng"><label>محرك الوكلاء الافتراضي <select name="engine" ${canAdmin ? "" : "disabled"}>${Object.entries(S.info.engines).map(([k, e]) => `<option value="${k}" ${k === S.info.engine ? "selected" : ""}>${esc(e.label)} — ${e.available ? "متاح" : "غير متاح"}</option>`).join("")}</select></label>
    ${canAdmin ? `<button class="btn plum sm">حفظ</button>` : ""}</form>
    <ul class="small"><li>التفريغ الآلي: ${S.info.asr.available ? "متاح (" + esc(S.info.asr.engine) + ")" : "غير مثبت — " + esc(S.info.asr.hint)}</li>
    <li>البيانات الفنية للوسائط (ffprobe): ${S.info.ffmpeg ? "متاحة" : "غير مثبتة"}</li><li>مجلد البيانات: <code dir="ltr">${esc(S.info.home)}</code></li></ul></div>
  ${sec("الحسابات", "users", C.blue)}
  <div class="table-wrap"><table><thead><tr><th>المستخدم</th><th>الاسم</th><th>الصفة</th></tr></thead><tbody>${U.map((u) => `<tr><td dir="ltr">${esc(u.username)}</td><td>${esc(u.display_name)}</td><td>${badge(S.info.roles[u.role] || u.role, C.blue)}</td></tr>`).join("")}</tbody></table></div>
  ${canAdmin && S.info.mode !== "solo" ? `<div class="card" style="margin-top:12px"><h3>${ic("plus")} حساب جديد</h3><form class="form" id="uf">
    <label>اسم المستخدم<input name="username" required></label><label>الاسم الظاهر<input name="display_name"></label><label>كلمة المرور<input name="password" type="password" minlength="8" required></label>
    <label>الصفة<select name="role">${Object.entries(S.info.roles).map(([k, l]) => `<option value="${k}" ${k === "researcher" ? "selected" : ""}>${esc(l)}</option>`).join("")}</select></label>
    <div><button class="btn">${ic("check")} إنشاء</button></div></form></div>` : ""}
  ${sec("خط الهوية «أضواء السلف»", "feather", C.gold)}
  <div class="card" id="fontcard"><p class="muted small">جارٍ الفحص…</p></div>
  ${sec("أيقونة البرنامج", "star", C.clay)}
  <div class="card" id="iconcard"><p class="muted small">جارٍ الفحص…</p></div>
  ${sec("صور الواجهة ومصادرها", "camera", C.sky)}<div id="credits" class="table-wrap"></div>
  <p class="tiny muted">صور الواجهة للزينة لا دليلاً تاريخياً. والمولَّد منها موسوم «إعادة بناء تصورية» حيثما ظهر.</p>
  ${sec("الحماية والاستمرارية", "shield", C.palm)}<div class="row"><button class="btn ghost" data-go="vault">${ic("shield")} فحص السلامة والنسخ الاحتياطي</button>
    <button class="btn ghost" id="tour">${ic("compass")} دليل البدء</button></div>`;
  $("#tour").onclick = () => showTour(0);
  const loadFont = async () => {
    const f = await api("fonts");
    const ok = f.regular && f.bold;
    $("#fontcard").innerHTML = `<div class="spread"><div>
      <h3 style="margin:0">${ok ? ic("check") + " الخط مثبت" : ic("alert") + " الخط غير مثبت بعد"}</h3>
      <p class="small" style="margin:.4em 0">العادي: ${f.regular ? badge("مثبت", C.palm) : badge("غير مثبت", C.crimson)} · العريض: ${f.bold ? badge("مثبت", C.palm) : badge("غير مثبت", C.crimson)}</p>
      <p class="tiny muted">يُحفظ الملفان في مجلد البيانات على هذا الجهاز (<span dir="ltr">${esc(f.folder)}</span>)، ولا يُرفعان إلى المستودع لأن الخط مرخَّص.
      وبدونه تعمل الواجهة بخط Noto Naskh Arabic.</p>
      <p class="small" style="margin:.4em 0">في نظام التشغيل (لـWord وPowerPoint والدليل المصوَّر): ${f.system && f.system.regular && f.system.bold ? badge("مثبت", C.palm) : badge("غير مثبت", C.crimson)}</p>
      <p style="font-family:'Adwa Assalaf';font-size:1.5rem;margin:.2em 0">إدارة الدراسات والبحوث التراثية الإماراتية <b>· تراث</b></p></div>
      ${canAdmin ? `<div class="row" style="flex-direction:column;align-items:stretch"><label class="btn gold" style="cursor:pointer">${ic("upload")} اختيار ملفّي الخط<input type="file" id="fontfiles" accept=".ttf,.otf" multiple hidden></label>
        ${f.local && ok ? `<button class="btn ghost" id="fontsys">${ic("check")} تثبيته في نظام التشغيل</button>` : ""}</div>` : ""}</div>`;
    if ($("#fontsys")) $("#fontsys").onclick = async () => { if (await run(() => api("fonts/system", { method: "POST" }), "ثُبّت الخط في النظام؛ أعيدوا فتح PowerPoint وWord")) loadFont(); };
    if ($("#fontfiles")) $("#fontfiles").onchange = async (e) => {
      for (const file of e.target.files) {
        await run(() => api("fonts", { method: "POST", raw: true, body: file, headers: { "X-Filename": encodeURIComponent(file.name) } }), "ثُبّت " + file.name);
      }
      location.reload();
    };
  };
  loadFont().catch(() => {});
  const loadIcon = async () => {
    const st = await api("icon");
    $("#iconcard").innerHTML = `<div class="spread"><div style="display:flex;gap:1rem;align-items:center">
      <img src="img/app-icon.png?${Date.now()}" alt="" style="width:96px;height:96px;border-radius:20px;box-shadow:0 6px 18px rgba(0,0,0,.25)">
      <div><h3 style="margin:0">${st.custom ? "الأيقونة التي اعتمدتموها" : "الأيقونة المضمَّنة في البرنامج"}</h3>
      <p class="tiny muted" style="margin:.4em 0">تظهر على سطح المكتب وفي قائمة البرامج وفي هذه اللوحة. ويُفضَّل ملف PNG مربع بمقاس 512 بكسل فأكثر.
      ${st.custom ? `<br>محفوظة في <span dir="ltr">${esc(st.folder)}</span> فتبقى بعد التحديثات.` : ""}</p></div></div>
      ${canAdmin && st.local ? `<label class="btn gold" style="cursor:pointer">${ic("upload")} اعتماد صورة أيقونة<input type="file" id="iconfile" accept=".png,.jpg,.jpeg,.webp" hidden></label>` : ""}</div>`;
    if ($("#iconfile")) $("#iconfile").onchange = async (e) => {
      const file = e.target.files[0];
      const r = file && await run(() => api("icon", { method: "POST", raw: true, body: file }), "اعتُمدت الأيقونة وحُدّث اختصار سطح المكتب");
      if (r) location.reload();
    };
  };
  loadIcon().catch(() => {});
  fetch("img/photos/credits.json").then((r) => r.json()).then((L) => {
    $("#credits").innerHTML = `<table><thead><tr><th>الصورة</th><th>موضعها</th><th>النوع</th><th>الملف الأصلي</th><th>الحقوق</th></tr></thead><tbody>${L.map((c) => `<tr>
      <td><img src="img/photos/${esc(c.file)}" alt="" style="width:96px;height:60px;object-fit:cover;border-radius:8px"></td><td>${esc(c.used_for)}</td>
      <td>${c.kind === "conceptual" ? badge("إعادة بناء تصورية", C.crimson) : badge("صورة فوتوغرافية", C.palm)}</td>
      <td class="tiny" dir="ltr">${esc(c.original)}</td><td class="small muted">${esc(c.rights)}</td></tr>`).join("")}</tbody></table>`;
  }).catch(() => {});
  bindGo(main);
  if (canAdmin) $("#eng").onsubmit = async (e) => { e.preventDefault(); const r = await run(() => api("settings", { method: "POST", body: formData(e.target) }), "حُفظ"); if (r) { S.info = r; shell(); route(); } };
  if ($("#uf")) $("#uf").onsubmit = async (e) => { e.preventDefault(); if (await run(() => api("users", { method: "POST", body: formData(e.target) }), "أُنشئ الحساب")) settings(main); };
}

/* ------------------------------------------------------------ البحث */
async function doSearch(q) {
  if (!q.trim()) return;
  const R = await run(() => api("search?q=" + encodeURIComponent(q)));
  if (!R) return;
  const body = modal(`نتائج البحث: «${q}»`, R.length ? `<ul class="timeline">${R.map((r, i) => `<li class="click" data-i="${i}" style="cursor:pointer">
      ${badge(r.item_table === "transcript" ? "تفريغ" : S.schema[r.item_table]?.one || r.item_table, C.clay)}<div><b>${esc(r.title)}</b><br>
      <span class="small muted">${esc(r.snip).replace(/\[([^\]]+)\]/g, "<mark>$1</mark>")}</span><br><span class="tiny" dir="ltr">${esc(r.item_id)}</span></div></li>`).join("")}</ul>`
    : `<div class="empty">لا نتائج في الأرشيف. تذكير: الأرشيف هو المرجع، لا ذاكرة النموذج.</div>`, C.clay, "search");
  $$("[data-i]", body).forEach((li) => (li.onclick = async () => {
    const r = R[+li.dataset.i];
    closeModal();
    if (r.item_table === "transcript" || r.item_table === "interviews") return (location.hash = "#/lab/" + r.item_id);
    if (r.item_table === "projects") return (location.hash = "#/project/" + r.item_id);
    if (r.item_table === "claims") return claimCard(r.item_id);
    editRecord(r.item_table, await api(`rows/${r.item_table}/${r.item_id}`));
  }));
}

boot();
