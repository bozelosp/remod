"use strict";

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const state = {
  files: [], activeId: null, groups: {}, selectedSegments: new Set(),
  region: "all", shollMetric: "length", view: "workspace", busy: false,
  camera: { yaw: -0.55, pitch: 0.28, zoom: 1, dragging: false, auto: true, lastX: 0, lastY: 0 },
};
let toastTimer;
let idCounter = 0;

function uid() { idCounter += 1; return `morphology-${Date.now()}-${idCounter}`; }
function uniqueFileName(name, pending = []) {
  const occupied = new Set([...state.files, ...pending].map((file) => file.name.toLowerCase()));
  if (!occupied.has(name.toLowerCase())) return name;
  const stem = name.replace(/\.swc$/i, ""); let index = 2;
  while (occupied.has(`${stem} (${index}).swc`.toLowerCase())) index += 1;
  return `${stem} (${index}).swc`;
}
function activeFile() { return state.files.find((file) => file.id === state.activeId) || null; }
function finite(value) { return typeof value === "number" && Number.isFinite(value); }
function numeric(value) { const number = Number(value); return Number.isFinite(number) ? number : 0; }
function formatNumber(value, digits = 1) {
  if (!finite(Number(value))) return "—";
  const number = Number(value);
  if (Math.abs(number) >= 10000) return number.toExponential(2);
  if (Math.abs(number) >= 1000) return number.toLocaleString(undefined, { maximumFractionDigits: digits });
  if (Math.abs(number) > 0 && Math.abs(number) < .01) return number.toExponential(2);
  return number.toLocaleString(undefined, { maximumFractionDigits: digits });
}
function humanMetric(name) {
  return name.replace(/^all_/, "").replaceAll("_", " ").replace(/\bbo\b/g, "branch order").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
function showToast(message, error = false) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.toggle("error", error);
  toast.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("visible"), error ? 5200 : 2600);
}
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    method: options.method || "GET",
    headers: options.body ? { "content-type": "application/json" } : {},
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const type = response.headers.get("content-type") || "";
  const data = type.includes("json") ? await response.json() : await response.text();
  if (!response.ok) throw new Error(data.error || data || `Request failed (${response.status})`);
  return data;
}

async function readFiles(fileList) {
  const additions = [];
  for (const file of [...fileList]) {
    if (!file.name.toLowerCase().endsWith(".swc")) {
      showToast(`${file.name} is not an SWC file`, true);
      continue;
    }
    const content = await file.text(); const name = uniqueFileName(file.name, additions);
    additions.push({ id: uid(), name, content, originalContent: content, group: "A", analysis: null, elapsed: 0, history: [] });
  }
  if (!additions.length) return;
  state.files.push(...additions);
  state.activeId = additions[0].id;
  state.selectedSegments.clear();
  await analyzeWorkspace();
}

async function loadExample() {
  try {
    setBusy(true);
    const listing = await api("/api/examples");
    if (!listing.files.length) throw new Error("No bundled examples are available");
    const name = listing.files[0];
    const content = await api(`/api/examples/${encodeURIComponent(name)}`);
    const file = { id: uid(), name: uniqueFileName(name), content, originalContent: content, group: "A", analysis: null, elapsed: 0, history: [] };
    state.files.push(file); state.activeId = file.id;
    await analyzeWorkspace();
  } catch (error) { showToast(error.message, true); setBusy(false); }
}

function setBusy(busy) {
  state.busy = busy;
  $("#canvasLoading").classList.toggle("hidden", !busy || !state.files.length);
  $("#applyEdit").disabled = busy;
  $("#addFiles").disabled = busy;
}

async function analyzeWorkspace() {
  if (!state.files.length) return;
  try {
    setBusy(true);
    const payload = {
      sholl_step: numeric($("#shollStep").value) || 20,
      files: state.files.map((file) => ({ name: file.name, content: file.content, group: file.group })),
    };
    const result = await api("/api/workspace", { method: "POST", body: payload });
    result.files.forEach((analysis, index) => {
      state.files[index].analysis = { morphology: analysis.morphology, statistics: analysis.statistics };
      state.files[index].elapsed = analysis.elapsed_ms;
    });
    state.groups = result.groups;
    setBusy(false);
    renderAll();
    showToast(`${state.files.length} ${state.files.length === 1 ? "morphology" : "morphologies"} analyzed in ${formatNumber(result.elapsed_ms, 0)} ms`);
  } catch (error) {
    setBusy(false);
    renderAll();
    showToast(error.message, true);
  }
}

function renderAll() {
  const hasFiles = state.files.length > 0;
  $("#emptyState").classList.toggle("hidden", hasFiles);
  if (!hasFiles) return;
  switchView(state.view);
  renderFileList();
  renderActive();
  renderAssignments();
  renderComparison();
  updateCounts();
}

function switchView(view) {
  state.view = view;
  $$(".mode-button").forEach((button) => button.classList.toggle("active", button.dataset.view === view));
  $("#workspaceView").classList.toggle("hidden", view !== "workspace" || !state.files.length);
  $("#compareView").classList.toggle("hidden", view !== "compare" || !state.files.length);
  if (view === "compare") requestAnimationFrame(drawComparisonChart);
}

function updateCounts() {
  const countA = state.files.filter((file) => file.group === "A").length;
  const countB = state.files.length - countA;
  $("#fileCount").textContent = state.files.length;
  $("#compareCount").textContent = `${countA} + ${countB}`;
}

function renderFileList() {
  const list = $("#fileList"); list.replaceChildren();
  for (const file of state.files) {
    const button = element("div", `file-item${file.id === state.activeId ? " active" : ""}`);
    button.tabIndex = 0; button.setAttribute("role", "button");
    const icon = element("span", "file-icon", "SWC");
    const info = element("span", "file-info");
    info.append(element("b", "", file.name));
    const count = file.analysis?.morphology?.counts?.samples;
    info.append(element("span", "", count ? `${count.toLocaleString()} samples` : "Awaiting analysis"));
    const group = element("button", `group-pill ${file.group.toLowerCase()}`, file.group);
    group.type = "button"; group.title = "Toggle comparison group";
    group.addEventListener("click", async (event) => { event.stopPropagation(); file.group = file.group === "A" ? "B" : "A"; await analyzeWorkspace(); });
    button.append(icon, info, group);
    const activate = () => { state.activeId = file.id; state.selectedSegments.clear(); resetCamera(); renderAll(); };
    button.addEventListener("click", activate);
    button.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); activate(); } });
    list.append(button);
  }
}

function renderActive() {
  const file = activeFile();
  if (!file || !file.analysis) return;
  $("#activeName").textContent = file.name;
  $("#activeLabel").textContent = `Group ${file.group} · active morphology`;
  $("#analysisTime").textContent = `${formatNumber(file.elapsed, 0)} ms`;
  $("#undoEdit").disabled = file.history.length === 0;
  renderQuickMetrics(file);
  renderStatCards(file.analysis.statistics);
  renderMetricsTable();
  renderSelection();
  drawShollChart();
}

function metricBlock(label, value, unit = "") {
  const card = element("div", "quick-metric");
  card.append(element("span", "", label));
  const bold = element("b", "", formatNumber(value));
  if (unit) bold.append(element("small", "", unit));
  card.append(bold); return card;
}
function renderQuickMetrics(file) {
  const root = $("#quickMetrics"); root.replaceChildren();
  const counts = file.analysis.morphology.counts;
  const stats = file.analysis.statistics;
  root.append(metricBlock("Samples", counts.samples), metricBlock("Dendritic segments", counts.segments), metricBlock("Branch points", counts.branchpoints), metricBlock("Total length", stats.all_total_length, "µm"));
}
function renderStatCards(stats) {
  const root = $("#statCards"); root.replaceChildren();
  const cards = [
    ["Total length", stats.all_total_length, "µm"], ["Surface area", stats.all_total_area, "µm²"],
    ["Volume", stats.all_total_volume, "µm³"], ["Mean path", stats.all_mean_path_length, "µm"],
    ["Terminal segments", stats.number_of_all_terminal_dendrites, ""], ["Max path", stats.all_max_path_length, "µm"],
  ];
  for (const [label, value, unit] of cards) {
    const card = element("div", "stat-card"); card.append(element("span", "", label));
    const bold = element("b", "", formatNumber(value)); if (unit) bold.append(element("small", "", unit)); card.append(bold); root.append(card);
  }
}

function flattenedMetrics(stats) {
  return Object.entries(stats).sort(([a], [b]) => a.localeCompare(b)).map(([name, value]) => {
    let display;
    if (finite(value)) display = formatNumber(value, 4);
    else if (value && typeof value === "object") display = `${Object.keys(value).length} values`;
    else display = String(value);
    return { name, display };
  });
}
function renderMetricsTable() {
  const file = activeFile(); if (!file?.analysis) return;
  const query = $("#metricSearch").value.trim().toLowerCase();
  const root = $("#metricsTable"); root.replaceChildren();
  for (const metric of flattenedMetrics(file.analysis.statistics).filter((item) => item.name.toLowerCase().includes(query))) {
    const row = element("div", "metric-row"); row.append(element("span", "", humanMetric(metric.name)), element("b", "", metric.display)); root.append(row);
  }
}

function fitCanvas(canvas, cssHeight) {
  const rect = canvas.getBoundingClientRect(); const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const width = Math.max(1, Math.round(rect.width * dpr)); const height = Math.max(1, Math.round((cssHeight || rect.height) * dpr));
  if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; }
  return { ctx: canvas.getContext("2d"), width, height, dpr };
}
function chartFrame(canvas, cssHeight = 190) {
  const frame = fitCanvas(canvas, cssHeight); const { ctx, width, height, dpr } = frame;
  ctx.clearRect(0, 0, width, height); ctx.lineCap = "round"; ctx.lineJoin = "round";
  return { ...frame, left: 36 * dpr, right: width - 10 * dpr, top: 12 * dpr, bottom: height - 27 * dpr };
}
function drawAxes(frame, xLabels, maxValue, unit = "") {
  const { ctx, left, right, top, bottom, dpr } = frame;
  ctx.strokeStyle = "#dfe3dd"; ctx.lineWidth = dpr;
  ctx.fillStyle = "#85908c"; ctx.font = `${8 * dpr}px system-ui`; ctx.textBaseline = "middle";
  for (let i = 0; i <= 4; i += 1) {
    const y = bottom - (bottom - top) * i / 4; ctx.beginPath(); ctx.moveTo(left, y); ctx.lineTo(right, y); ctx.stroke();
    ctx.textAlign = "right"; ctx.fillText(formatNumber(maxValue * i / 4, 0), left - 6 * dpr, y);
  }
  const labelCount = Math.min(6, xLabels.length);
  for (let i = 0; i < labelCount; i += 1) {
    const index = labelCount === 1 ? 0 : Math.round(i * (xLabels.length - 1) / (labelCount - 1));
    const x = xLabels.length === 1 ? (left + right) / 2 : left + (right - left) * index / (xLabels.length - 1);
    ctx.textAlign = "center"; ctx.textBaseline = "top"; ctx.fillText(formatNumber(Number(xLabels[index]), 0), x, bottom + 7 * dpr);
  }
  if (unit) { ctx.save(); ctx.translate(9 * dpr, (top + bottom) / 2); ctx.rotate(-Math.PI / 2); ctx.textAlign = "center"; ctx.fillText(unit, 0, 0); ctx.restore(); }
}
function drawLine(ctx, points, color, width) {
  if (!points.length) return; ctx.strokeStyle = color; ctx.lineWidth = width; ctx.beginPath();
  points.forEach(([x, y], index) => index ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke();
  ctx.fillStyle = color; for (const [x, y] of points) { ctx.beginPath(); ctx.arc(x, y, width * 1.45, 0, Math.PI * 2); ctx.fill(); }
}
function drawShollChart() {
  const file = activeFile(); if (!file?.analysis) return;
  const key = `sholl_${state.region}_${state.shollMetric}`; const values = file.analysis.statistics[key] || {};
  const entries = Object.entries(values).sort(([a], [b]) => Number(a) - Number(b));
  const frame = chartFrame($("#shollCanvas")); const maxValue = Math.max(...entries.map(([, value]) => numeric(value)), 1);
  drawAxes(frame, entries.map(([x]) => x), maxValue, state.shollMetric === "length" ? "µm" : "count");
  const { left, right, top, bottom, dpr, ctx } = frame;
  const points = entries.map(([, value], index) => [entries.length === 1 ? (left + right) / 2 : left + (right - left) * index / (entries.length - 1), bottom - (bottom - top) * numeric(value) / maxValue]);
  drawLine(ctx, points, state.region === "apical" ? "#ef795f" : state.region === "basal" ? "#159479" : "#183f3b", 1.7 * dpr);
}

function resetCamera() { Object.assign(state.camera, { yaw: -.55, pitch: .28, zoom: 1, auto: true }); }
function projectedSamples() {
  const file = activeFile(); if (!file?.analysis) return [];
  const canvas = $("#morphologyCanvas"); const { width, height } = canvas; const morphology = file.analysis.morphology;
  const min = morphology.bounds.min, max = morphology.bounds.max;
  const center = [(min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2];
  const extent = Math.max(max[0] - min[0], max[1] - min[1], max[2] - min[2], 1);
  const scale = Math.min(width, height) * .78 / extent * state.camera.zoom;
  const cy = Math.cos(state.camera.yaw), sy = Math.sin(state.camera.yaw), cp = Math.cos(state.camera.pitch), sp = Math.sin(state.camera.pitch);
  return morphology.samples.map((sample) => {
    const dx = sample.x - center[0], dy = sample.y - center[1], dz = sample.z - center[2];
    const x1 = dx * cy - dz * sy, z1 = dx * sy + dz * cy;
    const y1 = dy * cp - z1 * sp, depth = dy * sp + z1 * cp;
    return { ...sample, sx: width / 2 + x1 * scale, sy: height / 2 - y1 * scale, depth, scale };
  });
}
function drawMorphology() {
  const canvas = $("#morphologyCanvas"); if (!canvas || state.view !== "workspace") return;
  const rect = canvas.getBoundingClientRect(); const fitted = fitCanvas(canvas, rect.height || 500); const ctx = fitted.ctx;
  if (state.camera.auto && !state.camera.dragging && activeFile()?.analysis) state.camera.yaw += .00115;
  const samples = projectedSamples(); if (!samples.length) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const byId = new Map(samples.map((sample) => [sample.id, sample]));
  const edges = samples.filter((sample) => byId.has(sample.parent)).map((sample) => ({ distal: sample, proximal: byId.get(sample.parent), depth: (sample.depth + byId.get(sample.parent).depth) / 2 })).sort((a, b) => a.depth - b.depth);
  for (const edge of edges) {
    const selected = edge.distal.segment && state.selectedSegments.has(edge.distal.segment);
    const color = selected ? "#ffffff" : edge.distal.type === 3 ? "#72d9be" : edge.distal.type === 4 ? "#ef8068" : edge.distal.type === 1 ? "#d6ad53" : "#82a8bd";
    const fade = Math.max(.28, Math.min(.95, .61 + edge.depth / 900));
    ctx.globalAlpha = selected ? 1 : fade; ctx.strokeStyle = color; ctx.lineWidth = selected ? 3.2 * fitted.dpr : Math.max(.7 * fitted.dpr, Math.min(2.2 * fitted.dpr, edge.distal.radius * edge.distal.scale * .035));
    ctx.beginPath(); ctx.moveTo(edge.proximal.sx, edge.proximal.sy); ctx.lineTo(edge.distal.sx, edge.distal.sy); ctx.stroke();
  }
  ctx.globalAlpha = 1;
  for (const sample of samples.filter((item) => item.type === 1)) { ctx.fillStyle = "#d6ad53"; ctx.beginPath(); ctx.arc(sample.sx, sample.sy, Math.max(3 * fitted.dpr, sample.radius * sample.scale * .18), 0, Math.PI * 2); ctx.fill(); }
}
function animationLoop() { drawMorphology(); requestAnimationFrame(animationLoop); }

function distanceToSegment(px, py, x1, y1, x2, y2) {
  const dx = x2 - x1, dy = y2 - y1; const length2 = dx * dx + dy * dy;
  const t = length2 ? Math.max(0, Math.min(1, ((px - x1) * dx + (py - y1) * dy) / length2)) : 0;
  return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
}
function selectAt(clientX, clientY) {
  const canvas = $("#morphologyCanvas"); const rect = canvas.getBoundingClientRect(); const sx = canvas.width / rect.width, sy = canvas.height / rect.height;
  const x = (clientX - rect.left) * sx, y = (clientY - rect.top) * sy; const samples = projectedSamples(); const byId = new Map(samples.map((sample) => [sample.id, sample]));
  let best = null;
  for (const distal of samples) { const proximal = byId.get(distal.parent); if (!proximal || !distal.segment) continue; const distance = distanceToSegment(x, y, proximal.sx, proximal.sy, distal.sx, distal.sy); if (!best || distance < best.distance) best = { distance, segment: distal.segment }; }
  if (best && best.distance < 11 * (window.devicePixelRatio || 1)) {
    if (state.selectedSegments.has(best.segment)) state.selectedSegments.delete(best.segment); else state.selectedSegments.add(best.segment);
    $("#who").value = "manual"; updateRemodelFields(); renderSelection(); showInspector("remodel");
  }
}
function renderSelection() {
  const manual = $("#who").value === "manual"; $("#manualSelection").classList.toggle("hidden", !manual);
  const root = $("#selectionChips"); root.replaceChildren();
  [...state.selectedSegments].sort((a, b) => a - b).forEach((id) => root.append(element("i", "", String(id))));
  if (!state.selectedSegments.size) root.append(element("span", "", "Click segments in the 3D view"));
}

function showInspector(panel) {
  $$(".inspector-tab").forEach((button) => button.classList.toggle("active", button.dataset.panel === panel));
  $$(".inspector-panel").forEach((node) => node.classList.toggle("active", node.id === `${panel}Panel`));
}
const actionNotes = {
  shrink: "Shrinks the distal end while preserving downstream attachment and geometry.",
  remove: "Removes every selected segment and its complete distal subtree.",
  extend: "Adds an outward, quasi-directed path and preserves downstream geometry.",
  branch: "Adds exactly two outward daughter segments at every selected tip.",
  scale: "Scales selected coordinates and radii around each proximal attachment.",
  none: "Keeps topology fixed and changes only the selected segment radii.",
};
function updateRemodelFields() {
  const who = $("#who").value, action = $("#action").value;
  $("#ratioField").classList.toggle("hidden", !who.startsWith("random_"));
  $("#manualSelection").classList.toggle("hidden", who !== "manual");
  $("#amountFields").classList.toggle("hidden", action === "remove" || action === "none");
  $("#extentUnit").disabled = action === "scale"; if (action === "scale") $("#extentUnit").value = "percent";
  $("#editNote").textContent = actionNotes[action]; renderSelection();
}
function resetRemodelControls() {
  $("#who").value = "all_terminal"; $("#action").value = "shrink";
  $("#randomRatio").value = "10"; $("#amount").value = "20";
  $("#extentUnit").value = "percent"; $("#radiusChange").value = "";
  $("#radiusUnit").value = "percent"; $("#seed").value = "";
}

async function applyEdit(event) {
  event.preventDefault(); const file = activeFile(); if (!file?.analysis) return;
  const who = $("#who").value, action = $("#action").value;
  if (who === "manual" && !state.selectedSegments.size) { showToast("Select at least one segment in the 3D view", true); return; }
  const amount = action === "remove" || action === "none" ? null : numeric($("#amount").value);
  const radiusRaw = $("#radiusChange").value.trim();
  const body = {
    name: file.name, content: file.content, sholl_step: numeric($("#shollStep").value) || 20,
    options: {
      who, action, amount, random_ratio: numeric($("#randomRatio").value), manual_dendrites: [...state.selectedSegments].join(","),
      extent_unit: $("#extentUnit").value, radius_change: radiusRaw === "" ? null : Number(radiusRaw), radius_unit: $("#radiusUnit").value,
      seed: $("#seed").value.trim() === "" ? null : Number($("#seed").value),
    },
  };
  try {
    setBusy(true); const prior = { name: file.name, content: file.content, analysis: file.analysis, elapsed: file.elapsed };
    const result = await api("/api/remodel", { method: "POST", body });
    file.history.push(prior); file.name = result.name; file.content = result.content; file.analysis = { morphology: result.morphology, statistics: result.statistics }; file.elapsed = result.elapsed_ms;
    state.selectedSegments.clear(); setBusy(false); renderAll();
    showToast(`${humanMetric(action)} applied to ${result.targets.length} segment${result.targets.length === 1 ? "" : "s"}`);
    await refreshSummaries();
  } catch (error) { setBusy(false); showToast(error.message, true); }
}
async function refreshSummaries() {
  const payload = { sholl_step: numeric($("#shollStep").value) || 20, files: state.files.map((file) => ({ name: file.name, content: file.content, group: file.group })) };
  try { const result = await api("/api/workspace", { method: "POST", body: payload }); state.groups = result.groups; renderComparison(); } catch (_) { /* the edit itself remains valid */ }
}
function undoEdit() {
  const file = activeFile(); if (!file?.history.length) return;
  const prior = file.history.pop(); Object.assign(file, prior); state.selectedSegments.clear(); renderAll(); refreshSummaries(); showToast("Last edit undone");
}

function download(name, content, type) {
  const blob = new Blob([content], { type }); const url = URL.createObjectURL(blob); const anchor = document.createElement("a"); anchor.href = url; anchor.download = name; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function downloadActiveSwc() { const file = activeFile(); if (file) download(file.name, file.content, "text/plain"); }
function downloadActiveJson() { const file = activeFile(); if (file?.analysis) download(`${file.name.replace(/\.swc$/i, "")}_statistics.json`, `${JSON.stringify(file.analysis.statistics, null, 2)}\n`, "application/json"); }

function renderAssignments() {
  const root = $("#groupAssignments"); root.replaceChildren();
  for (const file of state.files) {
    const row = element("div", "assignment"); const info = element("div"); info.append(element("b", "", file.name), element("small", "", `${file.analysis?.morphology?.counts?.segments || 0} dendritic segments`));
    const toggle = element("div", "ab-toggle");
    for (const group of ["A", "B"]) { const button = element("button", `${file.group === group ? "active " : ""}${group.toLowerCase()}`, group); button.type = "button"; button.addEventListener("click", async () => { if (file.group === group) return; file.group = group; await analyzeWorkspace(); }); toggle.append(button); }
    row.append(info, toggle); root.append(row);
  }
}
function scalar(summary, name) { return summary?.scalar_metrics?.[name] || null; }
function percentChange(a, b) { return a === 0 ? null : ((b - a) / Math.abs(a)) * 100; }
function renderComparison() {
  const groupA = state.groups.A, groupB = state.groups.B, ready = groupA && groupB;
  $("#compareEmpty").classList.toggle("hidden", Boolean(ready)); $("#compareContent").classList.toggle("hidden", !ready);
  if (!ready) return;
  $("#compareTitle").textContent = `Group A (${groupA.file_count}) vs Group B (${groupB.file_count})`;
  const cardMetrics = [["Total length", "all_total_length", "µm"], ["Surface area", "all_total_area", "µm²"], ["Volume", "all_total_volume", "µm³"], ["Branch points", "number_of_all_branchpoints", ""]];
  const cards = $("#compareCards"); cards.replaceChildren();
  for (const [label, key, unit] of cardMetrics) {
    const a = scalar(groupA, key)?.mean || 0, b = scalar(groupB, key)?.mean || 0, change = percentChange(a, b);
    const card = element("div", "compare-card"); card.append(element("span", "", label)); const values = element("div", "compare-values");
    const av = element("b", "", formatNumber(a)); av.append(element("small", "", `A ${unit}`)); const bv = element("b", "", formatNumber(b)); bv.append(element("small", "", `B ${unit}`)); values.append(av, bv); card.append(values);
    const delta = element("em", change === null ? "" : change >= 0 ? "positive" : "negative", change === null ? "No baseline" : `${change >= 0 ? "+" : ""}${formatNumber(change)}% B vs A`); card.append(delta); cards.append(card);
  }
  renderComparisonTable(); requestAnimationFrame(drawComparisonChart); updateCounts();
}
function renderComparisonTable() {
  const a = state.groups.A, b = state.groups.B; if (!a || !b) return;
  const common = Object.keys(a.scalar_metrics).filter((key) => b.scalar_metrics[key] && key !== "sholl_step").sort();
  const root = $("#comparisonTable"); root.replaceChildren();
  const header = element("div", "comparison-row header"); ["Measurement", "Group A", "Group B", "Difference"].forEach((value) => header.append(element("span", "", value))); root.append(header);
  for (const key of common) {
    const av = a.scalar_metrics[key].mean, bv = b.scalar_metrics[key].mean, change = percentChange(av, bv); const row = element("div", "comparison-row");
    row.append(element("span", "", humanMetric(key)), element("span", "", formatNumber(av, 2)), element("span", "", formatNumber(bv, 2)));
    const delta = element("span", `delta ${change === null ? "" : change >= 0 ? "positive" : "negative"}`, change === null ? "—" : `${change >= 0 ? "+" : ""}${formatNumber(change)}%`); row.append(delta); root.append(row);
  }
}
function drawComparisonChart() {
  const a = state.groups.A, b = state.groups.B; if (!a || !b || state.view !== "compare") return;
  const metric = $("#comparisonMetric").value; const adata = a.distribution_metrics[metric] || {}, bdata = b.distribution_metrics[metric] || {};
  const keys = [...new Set([...Object.keys(adata), ...Object.keys(bdata)])].sort((x, y) => Number(x) - Number(y));
  const canvas = $("#comparisonCanvas"), frame = chartFrame(canvas, 350); const all = keys.flatMap((key) => [numeric(adata[key]?.mean), numeric(bdata[key]?.mean), numeric(adata[key]?.mean) + numeric(adata[key]?.standard_deviation), numeric(bdata[key]?.mean) + numeric(bdata[key]?.standard_deviation)]);
  const maxValue = Math.max(...all, 1); drawAxes(frame, keys, maxValue, metric.includes("length") ? "µm" : "count");
  const { left, right, top, bottom, dpr, ctx } = frame; const xAt = (index) => keys.length === 1 ? (left + right) / 2 : left + (right - left) * index / (keys.length - 1); const yAt = (value) => bottom - (bottom - top) * value / maxValue;
  const series = [[adata, "#168d76"], [bdata, "#ef795f"]];
  for (const [data, color] of series) {
    const points = keys.map((key, index) => [xAt(index), yAt(numeric(data[key]?.mean))]); ctx.strokeStyle = color; ctx.globalAlpha = .45; ctx.lineWidth = dpr;
    keys.forEach((key, index) => { const mean = numeric(data[key]?.mean), sd = numeric(data[key]?.standard_deviation); if (!sd) return; const x = xAt(index), high = yAt(Math.min(maxValue, mean + sd)), low = yAt(Math.max(0, mean - sd)); ctx.beginPath(); ctx.moveTo(x, high); ctx.lineTo(x, low); ctx.moveTo(x - 3 * dpr, high); ctx.lineTo(x + 3 * dpr, high); ctx.moveTo(x - 3 * dpr, low); ctx.lineTo(x + 3 * dpr, low); ctx.stroke(); });
    ctx.globalAlpha = 1; drawLine(ctx, points, color, 1.6 * dpr);
  }
  $("#comparisonChartTitle").textContent = humanMetric(metric);
}

function makeHeroNeuron() {
  const group = $("#heroNeuron"); let counter = 0; const paths = [];
  function branch(x, y, angle, length, depth) {
    counter += 1; const bend = Math.sin(counter * 2.31) * .22; const nx = x + Math.cos(angle + bend) * length, ny = y + Math.sin(angle + bend) * length;
    paths.push(`M ${x.toFixed(1)} ${y.toFixed(1)} Q ${((x + nx) / 2 + Math.sin(counter) * 5).toFixed(1)} ${((y + ny) / 2 + Math.cos(counter) * 5).toFixed(1)} ${nx.toFixed(1)} ${ny.toFixed(1)}`);
    if (depth <= 0) return; const spread = .31 + (counter % 3) * .09; branch(nx, ny, angle - spread, length * (.71 + (counter % 2) * .06), depth - 1); branch(nx, ny, angle + spread, length * (.67 + (counter % 3) * .035), depth - 1);
  }
  for (const angle of [-2.75, -2.2, -1.55, -.7, -.1, .5, 1.2, 2.25]) branch(260, 265, angle, 74, 4);
  paths.forEach((data) => { const path = document.createElementNS("http://www.w3.org/2000/svg", "path"); path.setAttribute("d", data); group.append(path); });
}

function bindEvents() {
  const openPicker = () => $("#fileInput").click();
  $("#chooseFiles").addEventListener("click", openPicker); $("#addFiles").addEventListener("click", openPicker); $("#railAdd").addEventListener("click", openPicker); $("#compareAddFiles").addEventListener("click", openPicker);
  $("#fileInput").addEventListener("change", async (event) => { await readFiles(event.target.files); event.target.value = ""; });
  $("#loadExample").addEventListener("click", loadExample);
  const drop = $("#dropZone"); drop.addEventListener("click", (event) => { if (event.target === drop) openPicker(); }); drop.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") openPicker(); });
  ["dragenter", "dragover"].forEach((name) => drop.addEventListener(name, (event) => { event.preventDefault(); drop.classList.add("dragging"); }));
  ["dragleave", "drop"].forEach((name) => drop.addEventListener(name, (event) => { event.preventDefault(); drop.classList.remove("dragging"); })); drop.addEventListener("drop", (event) => readFiles(event.dataTransfer.files));
  $$(".mode-button").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.view)));
  $$(".inspector-tab").forEach((button) => button.addEventListener("click", () => showInspector(button.dataset.panel)));
  $$(".region-toggle button").forEach((button) => button.addEventListener("click", () => { state.region = button.dataset.region; $$(".region-toggle button").forEach((node) => node.classList.toggle("active", node === button)); drawShollChart(); }));
  $("#shollMetric").addEventListener("change", (event) => { state.shollMetric = event.target.value; drawShollChart(); });
  $("#shollStep").addEventListener("change", analyzeWorkspace); $("#metricSearch").addEventListener("input", renderMetricsTable);
  $("#who").addEventListener("change", updateRemodelFields); $("#action").addEventListener("change", updateRemodelFields); $("#clearSelection").addEventListener("click", () => { state.selectedSegments.clear(); renderSelection(); });
  $("#remodelForm").addEventListener("submit", applyEdit); $("#undoEdit").addEventListener("click", undoEdit); $("#resetView").addEventListener("click", resetCamera);
  $("#downloadSwc").addEventListener("click", downloadActiveSwc); $("#downloadJson").addEventListener("click", downloadActiveJson);
  $("#downloadComparison").addEventListener("click", () => download("remod-group-comparison.json", `${JSON.stringify(state.groups, null, 2)}\n`, "application/json"));
  $("#comparisonMetric").addEventListener("change", drawComparisonChart);
  const canvas = $("#morphologyCanvas"), wrap = canvas.parentElement; let moved = false, resumeTimer;
  canvas.addEventListener("pointerdown", (event) => { moved = false; state.camera.dragging = true; state.camera.auto = false; state.camera.lastX = event.clientX; state.camera.lastY = event.clientY; canvas.setPointerCapture(event.pointerId); wrap.classList.add("dragging"); });
  canvas.addEventListener("pointermove", (event) => { if (!state.camera.dragging) return; const dx = event.clientX - state.camera.lastX, dy = event.clientY - state.camera.lastY; if (Math.abs(dx) + Math.abs(dy) > 2) moved = true; state.camera.yaw += dx * .008; state.camera.pitch = Math.max(-1.45, Math.min(1.45, state.camera.pitch + dy * .008)); state.camera.lastX = event.clientX; state.camera.lastY = event.clientY; });
  canvas.addEventListener("pointerup", (event) => { state.camera.dragging = false; wrap.classList.remove("dragging"); if (!moved) selectAt(event.clientX, event.clientY); clearTimeout(resumeTimer); resumeTimer = setTimeout(() => { state.camera.auto = true; }, 3500); });
  canvas.addEventListener("wheel", (event) => { event.preventDefault(); state.camera.zoom = Math.max(.25, Math.min(6, state.camera.zoom * Math.exp(-event.deltaY * .001))); state.camera.auto = false; clearTimeout(resumeTimer); resumeTimer = setTimeout(() => { state.camera.auto = true; }, 3500); }, { passive: false });
  window.addEventListener("resize", () => { drawShollChart(); drawComparisonChart(); });
}

makeHeroNeuron(); bindEvents(); resetRemodelControls(); updateRemodelFields(); showInspector("overview"); requestAnimationFrame(animationLoop);
