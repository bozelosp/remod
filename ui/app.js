"use strict";

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const REGION_LABELS = { all: "All dendrites", basal: "Basal dendrites", apical: "Apical dendrites" };
const TYPE_LABELS = { 1: "Soma", 2: "Axon", 3: "Basal dendrite", 4: "Apical dendrite" };
const TYPE_COLORS = { 1: "#e2b957", 2: "#86aaba", 3: "#6ed4b8", 4: "#ef856f" };
const COMPARISON_CARD_KEYS = ["all_total_length", "all_total_area", "all_total_volume", "number_of_all_branchpoints"];
const COMPARISON_SCALAR_KEYS = [
  "all_total_length", "basal_total_length", "apical_total_length",
  "all_total_area", "basal_total_area", "apical_total_area",
  "all_total_volume", "basal_total_volume", "apical_total_volume",
  "number_of_all_dendrites", "number_of_basal_dendrites", "number_of_apical_dendrites",
  "number_of_all_terminal_dendrites", "number_of_basal_terminal_dendrites", "number_of_apical_terminal_dendrites",
  "number_of_all_branchpoints", "number_of_basal_branchpoints", "number_of_apical_branchpoints",
  "all_mean_path_length", "basal_mean_path_length", "apical_mean_path_length",
  "all_max_path_length", "basal_max_path_length", "apical_max_path_length",
  "all_mean_median_diameter", "basal_mean_median_diameter", "apical_mean_median_diameter",
  "all_mean_diameter_taper_fraction", "basal_mean_diameter_taper_fraction", "apical_mean_diameter_taper_fraction",
  "all_mean_diameter_taper_per_length", "basal_mean_diameter_taper_per_length", "apical_mean_diameter_taper_per_length",
];

const state = {
  files: [], activeId: null, groups: {}, selectedSegments: new Set(), hoveredSegment: null,
  view: "workspace", analysisView: "overview", busy: false, preview: null, previewView: "overlay", shollStep: 20,
  groupNames: { A: "Cohort A", B: "Cohort B" }, analysisGeneration: 0, groupGeneration: 0, shollGeneration: 0, previewGeneration: 0, previewRequest: null,
  visibility: { 1: true, 2: true, 3: true, 4: true }, chartHits: {}, comparisonSeries: null,
  camera: {
    yaw: -.55, pitch: .28, zoom: 1, panX: 0, panY: 0, auto: true, dragging: false,
    panMode: false, lastX: 0, lastY: 0, target: null, extent: null, dirty: true, lastFrame: 0,
  },
  displayBounds: { center: [0, 0, 0], extent: 1 },
};

let idCounter = 0;
let toastTimer;
let hoverFrame;

function uid() { idCounter += 1; return `morphology-${Date.now()}-${idCounter}`; }
function activeFile() { return state.files.find((file) => file.id === state.activeId) || null; }
function finite(value) { return typeof value === "number" && Number.isFinite(value); }
function numeric(value) { const number = Number(value); return Number.isFinite(number) ? number : 0; }
function formatNumber(value, digits = 1) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  if (Math.abs(number) >= 10000) return number.toExponential(2);
  if (Math.abs(number) >= 1000) return number.toLocaleString(undefined, { maximumFractionDigits: digits });
  if (Math.abs(number) > 0 && Math.abs(number) < .01) return number.toExponential(2);
  return number.toLocaleString(undefined, { maximumFractionDigits: digits });
}
function signedNumber(value, digits = 1) {
  const number = Number(value); if (!Number.isFinite(number)) return "—";
  return `${number > 0 ? "+" : ""}${formatNumber(number, digits)}`;
}
function humanize(name) { return name.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()); }
function showToast(message, error = false) {
  const toast = $("#toast"); toast.textContent = message; toast.classList.toggle("error", error); toast.classList.add("visible");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => toast.classList.remove("visible"), error ? 5200 : 2800);
}
function element(tag, className, text) {
  const node = document.createElement(tag); if (className) node.className = className; if (text !== undefined) node.textContent = text; return node;
}
function uniqueFileName(name, pending = [], excludeId = null) {
  const occupied = new Set([...state.files.filter((file) => file.id !== excludeId), ...pending].map((file) => file.name.toLowerCase()));
  if (!occupied.has(name.toLowerCase())) return name;
  const stem = name.replace(/\.swc$/i, ""); let index = 2;
  while (occupied.has(`${stem} (${index}).swc`.toLowerCase())) index += 1;
  return `${stem} (${index}).swc`;
}
function currentStep() { const value = Number($("#shollStep").value); return Number.isFinite(value) ? value : NaN; }
function groupName(group) { return state.groupNames[group] || `Cohort ${group}`; }

function metricInfo(key) {
  if (key === "sholl_step") return { label: "Sholl shell width", unit: "µm", digits: 2, definition: "Radial shell width measured from the root soma coordinate.", delta: "absolute" };
  const regionMatch = key.match(/^(all|basal|apical)_(.+)$/);
  if (regionMatch) {
    const [, region, suffix] = regionMatch; const prefix = REGION_LABELS[region];
    const known = {
      total_length: ["Total centerline length", "µm", "Sum of dendritic centerline edge lengths."],
      total_area: ["Lateral dendritic area", "µm²", "Open-cylinder lateral area using each edge's distal SWC radius."],
      total_volume: ["Dendritic volume", "µm³", "Cylindrical volume using each edge's distal SWC radius."],
      mean_path_length: ["Mean soma-path length across segments", "µm", "Unweighted mean of segment-tip path lengths to the soma."],
      max_path_length: ["Maximum soma-path length", "µm", "Largest segment-tip path length to the soma."],
      mean_median_diameter: ["Mean median segment diameter", "µm", "Mean across segments of twice the median SWC sample radius."],
      mean_diameter_taper_fraction: ["Mean fractional diameter taper", "", "Mean segment (proximal − distal) / proximal diameter."],
      mean_diameter_taper_per_length: ["Mean diameter taper per length", "µm/µm", "Mean segment diameter change divided by centerline length."],
    };
    if (known[suffix]) {
      const [label, unit, definition] = known[suffix];
      return { label: `${prefix} · ${label}`, unit, digits: suffix.includes("taper") ? 4 : 2, definition, delta: suffix.includes("taper") ? "absolute" : "percent" };
    }
  }
  const countMatch = key.match(/^number_of_(all|basal|apical)_(terminal_)?(dendrites|branchpoints)$/);
  if (countMatch) {
    const [, region, terminal, kind] = countMatch;
    const noun = kind === "branchpoints" ? "branch points" : terminal ? "terminal segments" : "dendritic segments";
    return { label: `${REGION_LABELS[region]} · Number of ${noun}`, unit: "count", digits: 0, definition: `Count of ${noun} in the selected dendritic region.`, delta: "percent" };
  }
  if (key === "path_length_by_dendrite") return { label: "Soma-path length by segment", unit: "µm", digits: 2, definition: "Segment-tip path length to the soma, indexed by segment ID.", delta: "none" };
  if (key === "median_diameter_by_dendrite") return { label: "Median diameter by segment", unit: "µm", digits: 3, definition: "Twice the median SWC radius within each segment.", delta: "none" };
  if (key === "diameter_taper_by_dendrite") return { label: "Diameter taper by segment", unit: "", digits: 4, definition: "Fractional and length-normalized taper indexed by segment ID.", delta: "none" };
  if (key.startsWith("sholl_")) {
    const [, region, measure] = key.match(/^sholl_(all|basal|apical)_(length|intersections|branchpoints)$/) || [];
    const labels = { length: "Cable length per radial shell", intersections: "Sphere intersections", branchpoints: "Branch points per radial shell" };
    return { label: `${REGION_LABELS[region] || "Dendrites"} · ${labels[measure] || "Sholl profile"}`, unit: measure === "length" ? "µm" : "count", digits: measure === "length" ? 2 : 0, definition: "Radial profile measured from the root soma coordinate.", delta: "none" };
  }
  if (key.includes("per_branch_order")) {
    const isCount = key.startsWith("number_of_"); const isPath = key.includes("path_length");
    return { label: isCount ? "Segments per centrifugal branch order" : isPath ? "Mean soma-path length per branch order" : "Mean segment length per branch order", unit: isCount ? "count" : "µm", digits: isCount ? 0 : 2, definition: "One-based centrifugal branch-order distribution.", delta: "none" };
  }
  return { label: humanize(key), unit: "", digits: 3, definition: "REMOD morphology measurement.", delta: "absolute" };
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

function edgeSignature(morphology, proximal, distal) {
  const value = (number) => Number(number).toPrecision(12);
  const p = proximal * 3, d = distal * 3;
  return `${morphology.types[distal]}|${value(morphology.coords[p])},${value(morphology.coords[p + 1])},${value(morphology.coords[p + 2])}|${value(morphology.coords[d])},${value(morphology.coords[d + 1])},${value(morphology.coords[d + 2])}|${value(morphology.radii[distal])}`;
}

function prepareMorphology(payload) {
  if (payload.schema !== 2) throw new Error("Unsupported morphology geometry schema");
  const rows = payload.samples; const count = rows.length;
  const ids = new Float64Array(count), types = new Float64Array(count), coords = new Float64Array(count * 3), radii = new Float64Array(count), parents = new Float64Array(count), segmentIds = new Float64Array(count);
  const byId = new Map();
  rows.forEach((row, index) => {
    ids[index] = row[0]; types[index] = row[1]; coords[index * 3] = row[2]; coords[index * 3 + 1] = row[3]; coords[index * 3 + 2] = row[4]; radii[index] = row[5]; parents[index] = row[6]; segmentIds[index] = row[7] || 0; byId.set(row[0], index);
  });
  const proximal = [], distal = [], childCounts = new Uint32Array(count), segmentSamples = new Map();
  for (let index = 0; index < count; index += 1) {
    const parent = byId.get(parents[index]);
    if (parent !== undefined) { proximal.push(parent); distal.push(index); childCounts[parent] += 1; }
    const segment = segmentIds[index]; if (segment) { if (!segmentSamples.has(segment)) segmentSamples.set(segment, []); segmentSamples.get(segment).push(index); }
  }
  const segments = new Map(payload.segments.map((row) => [row[0], {
    id: row[0], type: row[1], length: row[2], branchOrder: row[3], terminal: row[4], sampleCount: row[5], parentSegment: row[6], descendantCount: row[7],
  }]));
  const result = {
    ids, types, coords, radii, parents, segmentIds, byId, proximal: Int32Array.from(proximal), distal: Int32Array.from(distal), childCounts,
    segmentSamples, segments, bounds: payload.bounds, counts: payload.counts,
    projectedX: new Float64Array(count), projectedY: new Float64Array(count), projectedDepth: new Float64Array(count), edgeKeys: new Set(), edgeSignatures: new Array(distal.length),
  };
  for (let edge = 0; edge < result.distal.length; edge += 1) {
    const signature = edgeSignature(result, result.proximal[edge], result.distal[edge]);
    result.edgeSignatures[edge] = signature; result.edgeKeys.add(signature);
  }
  return result;
}

function analysisFromResponse(result) {
  return { morphology: prepareMorphology(result.morphology), statistics: result.statistics };
}

function createFile(name, content) {
  return { id: uid(), name, content, originalContent: content, group: "A", analysis: null, analysisId: null, analysisStep: null, elapsed: 0, cached: false, status: "queued", error: null, history: [] };
}

async function readFiles(fileList) {
  if (state.busy) return; setBusy(true, "Reading SWC files"); const additions = [];
  try {
    for (const file of [...fileList]) {
      if (!file.name.toLowerCase().endsWith(".swc")) { showToast(`${file.name} is not an SWC file`, true); continue; }
      const content = await file.text(); additions.push(createFile(uniqueFileName(file.name, additions), content));
    }
  } catch (error) {
    setBusy(false); showToast(error.message, true); return;
  }
  if (!additions.length) { setBusy(false); return; }
  discardPreview(false); state.files.push(...additions); state.activeId = additions[0].id; state.selectedSegments.clear(); resetCamera(); renderAll();
  setBusy(false); await analyzeFiles(additions);
}

async function loadExample() {
  if (state.busy) return; setBusy(true, "Loading example");
  try {
    const listing = await api("/api/examples"); if (!listing.files.length) throw new Error("No bundled morphologies are available");
    const unused = listing.files.find((name) => !state.files.some((file) => file.name.startsWith(name.replace(/\.swc$/i, "")))) || listing.files[0];
    const content = await api(`/api/examples/${encodeURIComponent(unused)}`); const file = createFile(uniqueFileName(unused), content);
    discardPreview(false); state.files.push(file); state.activeId = file.id; state.selectedSegments.clear(); resetCamera(); renderAll(); setBusy(false); await analyzeFiles([file]);
  } catch (error) { showToast(error.message, true); setBusy(false); }
}

function setBusy(busy, label = "Local session") {
  state.busy = busy; const status = $("#workspaceStatus"); status.classList.toggle("busy", busy); status.classList.remove("error"); status.lastChild.textContent = busy ? label : "Local session";
  $("#canvasLoading").classList.toggle("hidden", !busy || !state.files.length); ["#previewEdit", "#addFiles", "#chooseFiles", "#loadExample", "#railAdd", "#railExample", "#compareAddFiles", "#discardPreview", "#confirmEdit"].forEach((selector) => { $(selector).disabled = busy; });
  $("#shollStep").disabled = busy; const hasHistory = Boolean(activeFile()?.history.length); $("#undoEdit").disabled = busy || !hasHistory; $("#undoHistory").disabled = busy || !hasHistory; renderFileList(); renderAssignments();
}

function assignAnalysis(file, prepared) {
  Object.assign(file, prepared, { status: "ready", error: null });
}

async function analyzeFiles(files = state.files, { atomic = false } = {}) {
  if (state.busy) return false;
  const step = currentStep(); if (!(step > 0)) { showToast("Sholl shell width must be positive", true); return; }
  const pending = files.filter((file) => !file.analysis || file.analysisStep !== step);
  if (!pending.length) { if (atomic) state.shollStep = step; await refreshGroups(); return true; }
  const previous = new Map(pending.map((file) => [file, { status: file.status, error: file.error, cached: file.cached }]));
  const generation = ++state.analysisGeneration; setBusy(true, `Analyzing ${pending.length}`); pending.forEach((file) => { file.status = "analyzing"; file.error = null; }); renderFileList();
  let cursor = 0; let completed = 0; const errors = [], staged = [];
  async function worker() {
    while (cursor < pending.length) {
      const file = pending[cursor]; cursor += 1;
      try {
        const result = await api("/api/workspace", { method: "POST", body: { sholl_step: step, files: [{ name: file.name, content: file.content }] } });
        if (generation !== state.analysisGeneration) return;
        const item = result.files[0], prepared = { analysis: analysisFromResponse(item), analysisId: item.analysis_id, analysisStep: step, elapsed: item.elapsed_ms, cached: item.cached };
        if (atomic) staged.push([file, prepared]); else assignAnalysis(file, prepared);
      } catch (error) {
        if (generation !== state.analysisGeneration) return;
        if (!atomic) { file.status = "error"; file.error = error.message; } errors.push(`${file.name}: ${error.message}`);
      }
      completed += 1; $("#canvasLoading b").textContent = `Analyzing morphology ${completed} of ${pending.length}`; renderFileList();
    }
  }
  await Promise.all(Array.from({ length: Math.min(3, pending.length) }, worker));
  if (generation !== state.analysisGeneration) return false;
  if (atomic && errors.length) {
    pending.forEach((file) => Object.assign(file, previous.get(file))); $("#shollStep").value = String(state.shollStep); await refreshGroups(); renderAll(); setBusy(false); showToast(`Sholl reanalysis failed; previous results were retained. ${errors[0]}`, true); return false;
  }
  if (atomic) { staged.forEach(([file, prepared]) => assignAnalysis(file, prepared)); state.shollStep = step; }
  const active = activeFile(); if (!active?.analysis) state.activeId = state.files.find((file) => file.analysis)?.id || active?.id || null;
  await refreshGroups(); renderAll();
  setBusy(false);
  if (errors.length) showToast(`${pending.length - errors.length} analyzed; ${errors.length} rejected. Select a rejected file for details.`, true);
  else showToast(`${pending.length} ${pending.length === 1 ? "morphology" : "morphologies"} ready${pending.every((file) => file.cached) ? " from analysis cache" : ""}`);
  return errors.length === 0;
}

async function refreshGroups() {
  const generation = ++state.groupGeneration;
  const ready = state.files.filter((file) => file.analysisId && file.analysisStep === currentStep());
  if (!ready.length) { state.groups = {}; renderComparison(); return; }
  try {
    const result = await api("/api/groups", { method: "POST", body: { files: ready.map((file) => ({ name: file.name, group: file.group, analysis_id: file.analysisId })) } });
    if (generation !== state.groupGeneration) return; state.groups = result.groups; renderComparison(); updateCounts();
  } catch (error) {
    if (generation !== state.groupGeneration) return; state.groups = {}; renderComparison(); updateCounts(); showToast(error.message, true);
  }
}

function renderAll() {
  const hasFiles = state.files.length > 0; $("#emptyState").classList.toggle("hidden", hasFiles);
  if (!hasFiles) { $("#workspaceView").classList.add("hidden"); $("#compareView").classList.add("hidden"); return; }
  switchView(state.view); renderFileList(); renderActive(); renderAssignments(); renderComparison(); updateCounts();
}

function switchView(view) {
  state.view = view; $$(".mode-button").forEach((button) => button.classList.toggle("active", button.dataset.view === view));
  $("#workspaceView").classList.toggle("hidden", view !== "workspace" || !state.files.length); $("#compareView").classList.toggle("hidden", view !== "compare" || !state.files.length);
  if (view === "compare") requestAnimationFrame(drawComparisonChart); else markViewerDirty();
}

function updateCounts() {
  const countA = state.files.filter((file) => file.group === "A").length; const countB = state.files.length - countA;
  $("#fileCount").textContent = state.files.length; $("#compareCount").textContent = `${countA} / ${countB}`;
}

function renderFileList() {
  const list = $("#fileList"); list.replaceChildren();
  for (const file of state.files) {
    const row = element("div", `file-item${file.id === state.activeId ? " active" : ""}`);
    const activate = element("button", "file-activate"); activate.type = "button"; activate.setAttribute("aria-label", `Open ${file.name}`);
    const icon = element("span", "file-icon", file.status === "error" ? "!" : "SWC"); const info = element("span", "file-info"); info.append(element("b", "", file.name));
    const detail = file.status === "error" ? file.error : file.status === "analyzing" ? "Analyzing…" : file.analysis ? `${file.analysis.morphology.counts.samples.toLocaleString()} samples · ${file.cached ? "cached" : `${formatNumber(file.elapsed, 0)} ms`}` : "Queued";
    info.append(element("span", "", detail)); activate.append(icon, info); activate.disabled = state.busy; activate.addEventListener("click", () => activateFile(file.id));
    const tools = element("span", "file-tools"); const group = element("button", `group-pill ${file.group.toLowerCase()}`, file.group); group.type = "button"; group.title = "Move to other cohort"; group.disabled = state.busy; group.addEventListener("click", () => toggleGroup(file));
    const remove = element("button", "file-remove", "×"); remove.type = "button"; remove.title = "Remove from workspace"; remove.setAttribute("aria-label", `Remove ${file.name}`); remove.disabled = state.busy; remove.addEventListener("click", () => removeFile(file.id)); tools.append(group, remove); row.append(activate, tools); list.append(row);
  }
}

function activateFile(id) {
  if (state.busy) return;
  if (state.activeId === id) return; discardPreview(false); state.activeId = id; state.selectedSegments.clear(); state.hoveredSegment = null; resetCamera(); renderAll();
}
function removeFile(id) {
  if (state.busy) return;
  if (state.preview?.fileId === id) discardPreview(false); const index = state.files.findIndex((file) => file.id === id); if (index < 0) return;
  state.files.splice(index, 1); if (state.activeId === id) state.activeId = state.files[Math.min(index, state.files.length - 1)]?.id || null;
  state.selectedSegments.clear(); state.hoveredSegment = null; resetCamera(); refreshGroups(); renderAll();
}
async function toggleGroup(file) { if (state.busy) return; file.group = file.group === "A" ? "B" : "A"; renderFileList(); renderActive(); renderAssignments(); updateCounts(); await refreshGroups(); }

function renderActive() {
  const file = activeFile(); if (!file) return;
  $("#activeName").textContent = file.name; $("#activeLabel").textContent = `${groupName(file.group)} · active morphology`;
  if (!file.analysis) {
    $("#activeMeta").textContent = file.error || "Awaiting analysis"; $("#quickMetrics").replaceChildren(); $("#statCards").replaceChildren(); $("#analysisTime").textContent = ""; renderHistory(); markViewerDirty(); return;
  }
  const bounds = file.analysis.morphology.bounds; const span = bounds.max.map((value, index) => value - bounds.min[index]);
  $("#activeMeta").textContent = `${span.map((value) => formatNumber(value, 0)).join(" × ")} µm bounding box · coordinate units assumed µm`;
  $("#analysisTime").textContent = file.cached ? `cache · ${formatNumber(file.elapsed, 1)} ms` : `${formatNumber(file.elapsed, 1)} ms`;
  $("#undoEdit").disabled = file.history.length === 0; $("#undoHistory").disabled = file.history.length === 0; $("#historyCount").textContent = file.history.length;
  renderQuickMetrics(file); renderStatCards(file.analysis.statistics); renderTopology(file); renderMetricsTable(); renderSelection(); renderHistory(); renderPreview(); drawActiveAnalysis(); updateDisplayBounds(); markViewerDirty();
}

function metricBlock(label, value, unit = "") {
  const card = element("div", "quick-metric"); card.append(element("span", "", label)); const bold = element("b", "", formatNumber(value)); if (unit) bold.append(element("small", "", unit)); card.append(bold); return card;
}
function renderQuickMetrics(file) {
  const root = $("#quickMetrics"); root.replaceChildren(); const counts = file.analysis.morphology.counts; const stats = file.analysis.statistics;
  root.append(metricBlock("Samples", counts.samples), metricBlock("Dendritic segments", counts.segments), metricBlock("Branch points", counts.branchpoints), metricBlock("Total centerline length", stats.all_total_length, "µm"));
}
function renderStatCards(stats) {
  const cards = [
    ["Total centerline length", stats.all_total_length, "µm"], ["Lateral dendritic area", stats.all_total_area, "µm²"],
    ["Dendritic volume", stats.all_total_volume, "µm³"], ["Mean soma-path length", stats.all_mean_path_length, "µm"],
    ["Terminal segments", stats.number_of_all_terminal_dendrites, ""], ["Maximum soma-path length", stats.all_max_path_length, "µm"],
  ];
  const root = $("#statCards"); root.replaceChildren();
  for (const [label, value, unit] of cards) { const card = element("div", "stat-card"); card.append(element("span", "", label)); const bold = element("b", "", formatNumber(value)); if (unit) bold.append(element("small", "", unit)); card.append(bold); root.append(card); }
}
function renderTopology(file) {
  const counts = file.analysis.morphology.counts; const root = $("#topologySummary"); root.replaceChildren();
  [["All segments", counts.segments, ""], ["Basal", counts.basal, "basal-item"], ["Apical", counts.apical, "apical-item"], ["Terminal", counts.terminals, ""], ["Branch points", counts.branchpoints, ""], ["Max order", maxDistributionKey(file.analysis.statistics.number_of_all_dendrites_per_branch_order), ""]].forEach(([label, value, cls]) => { const node = element("div", `topology-item ${cls}`); node.append(element("span", "", label), element("b", "", String(value))); root.append(node); });
  renderSegmentSummary(state.hoveredSegment || (state.selectedSegments.size === 1 ? [...state.selectedSegments][0] : null));
}
function maxDistributionKey(mapping = {}) { return Math.max(0, ...Object.keys(mapping).map(Number)); }

function segmentMetric(stats, key, id) { const mapping = stats[key] || {}; return mapping[id] ?? mapping[String(id)]; }
function segmentDetails(id) {
  const file = activeFile(); if (!file?.analysis) return null; const segment = file.analysis.morphology.segments.get(id); if (!segment) return null; const stats = file.analysis.statistics; const taper = segmentMetric(stats, "diameter_taper_by_dendrite", id) || {};
  return { ...segment, typeLabel: TYPE_LABELS[segment.type] || `SWC type ${segment.type}`, pathLength: segmentMetric(stats, "path_length_by_dendrite", id), medianDiameter: segmentMetric(stats, "median_diameter_by_dendrite", id), taperFraction: taper.fraction, taperPerLength: taper.per_length };
}
function renderSegmentSummary(id) {
  const root = $("#segmentSummary"); root.replaceChildren(); root.append(element("span", "eyebrow", "Segment inspection")); const details = id ? segmentDetails(id) : null;
  if (!details) { root.append(element("p", "", "Hover a dendritic segment in the 3D view to inspect its branch order, path length, diameter, and terminal status.")); return; }
  root.append(element("p", "", `Segment ${details.id} · ${details.typeLabel}${state.selectedSegments.has(details.id) ? " · selected" : ""}`)); const list = element("dl");
  [["Centrifugal branch order", details.branchOrder], ["Segment centerline length", `${formatNumber(details.length, 2)} µm`], ["Soma-path length", `${formatNumber(details.pathLength, 2)} µm`], ["Median diameter", `${formatNumber(details.medianDiameter, 3)} µm`], ["Fractional taper", formatNumber(details.taperFraction, 4)], ["Terminal / distal segments", `${details.terminal ? "Yes" : "No"} / ${details.descendantCount}`]].forEach(([term, value]) => { list.append(element("dt", "", term), element("dd", "", String(value))); }); root.append(list);
}

function flattenedMetrics(stats) {
  return Object.entries(stats).sort(([a], [b]) => metricInfo(a).label.localeCompare(metricInfo(b).label)).map(([name, value]) => {
    const info = metricInfo(name); let display;
    if (finite(value)) display = `${formatNumber(value, info.digits)}${info.unit ? ` ${info.unit}` : ""}`;
    else if (value && typeof value === "object") display = `${Object.keys(value).length} indexed values`;
    else display = String(value);
    return { name, display, info };
  });
}
function renderMetricsTable() {
  const file = activeFile(); if (!file?.analysis) return; const query = $("#metricSearch").value.trim().toLowerCase(); const root = $("#metricsTable"); root.replaceChildren();
  const matches = flattenedMetrics(file.analysis.statistics).filter((item) => `${item.info.label} ${item.name}`.toLowerCase().includes(query));
  for (const metric of matches) { const row = element("div", "metric-row"); const label = element("span", "", metric.info.label); label.append(element("small", "", metric.info.definition)); row.append(label, element("b", "", metric.display)); root.append(row); }
  if (!matches.length) root.append(element("div", "history-empty", "No measurements match this filter."));
}

function showInspector(panel) {
  $$(".inspector-tab").forEach((button) => { const active = button.dataset.panel === panel; button.classList.toggle("active", active); button.setAttribute("aria-selected", String(active)); });
  $$(".inspector-panel").forEach((node) => node.classList.toggle("active", node.id === `${panel}Panel`)); if (panel === "analyze") requestAnimationFrame(drawActiveAnalysis);
}
function showAnalysis(view) {
  state.analysisView = view; $$("[data-analysis-view]").forEach((button) => button.classList.toggle("active", button.dataset.analysisView === view));
  $$(".analysis-pane").forEach((pane) => pane.classList.toggle("active", pane.id === `analysis${view[0].toUpperCase()}${view.slice(1)}`)); requestAnimationFrame(drawActiveAnalysis);
}

const actionNotes = {
  shrink: "Removes length from the distal end. If the target is nonterminal, its complete distal subtree is translated rigidly to preserve attachment and internal geometry.",
  remove: "Removes each selected segment and its complete distal subtree from the preview.",
  extend: "Adds an outward, quasi-directed path. A nonterminal target's distal subtree is translated and reattached to the new tip.",
  branch: "Adds exactly two outward daughter segments. Generated step lengths use the bundled empirical table, whose biological provenance is not recorded.",
  scale: "Scales selected coordinates and radii about each proximal attachment. Distal subtrees are translated to preserve connectivity.",
  none: "Keeps topology and coordinates fixed while changing SWC radius values on the selected segments.",
};
function updateRemodelFields() {
  discardPreview(false); const who = $("#who").value, action = $("#action").value;
  $("#ratioField").classList.toggle("hidden", !who.startsWith("random_")); $("#manualSelection").classList.toggle("hidden", who !== "manual"); $("#amountFields").classList.toggle("hidden", action === "remove" || action === "none"); $("#radiusFields").classList.toggle("hidden", action === "remove");
  $("#extentUnit").disabled = action === "scale"; if (action === "scale") $("#extentUnit").value = "percent"; if (action === "remove") $("#radiusChange").value = "";
  const amountLabel = action === "shrink" ? "Length removed" : action === "extend" ? "Added length" : action === "branch" ? "Length per daughter" : action === "scale" ? "Scale factor" : "Extent";
  $("#amount").closest("label").firstChild.textContent = amountLabel; $("#editNote").textContent = actionNotes[action]; validateRemodelForm(false); renderSelection(); setWorkflowStage("configure");
}
function setWorkflowStage(stage) {
  const order = ["select", "configure", "preview", "apply"]; const index = order.indexOf(stage); $$(".workflow-ribbon li").forEach((item, itemIndex) => { item.classList.toggle("active", itemIndex === index); item.classList.toggle("complete", itemIndex < index); });
}
function validateRemodelForm(show = true) {
  const who = $("#who").value, action = $("#action").value, amount = Number($("#amount").value), ratio = Number($("#randomRatio").value), radiusRaw = $("#radiusChange").value.trim(), radius = Number(radiusRaw), seedRaw = $("#seed").value.trim(), seed = Number(seedRaw); let message = "";
  if (who === "manual" && !state.selectedSegments.size) message = "Select at least one segment in the 3D view.";
  else if (who.startsWith("random_") && (!Number.isFinite(ratio) || ratio <= 0 || ratio > 100)) message = "Random sampling must be greater than 0% and no more than 100%.";
  else if (!["remove", "none"].includes(action) && (!Number.isFinite(amount) || amount <= 0)) message = "The operation extent must be a positive finite number.";
  else if (action === "shrink" && $("#extentUnit").value === "percent" && amount >= 100) message = "Percentage shrink must be less than 100% so the segment retains positive length.";
  else if (action === "none" && (radiusRaw === "" || !Number.isFinite(radius))) message = "Radius-only editing requires a finite SWC radius change.";
  else if (radiusRaw !== "" && !Number.isFinite(radius)) message = "SWC radius change must be finite.";
  else if (radiusRaw !== "" && $("#radiusUnit").value === "percent" && radius <= -100) message = "Percentage radius change must be greater than −100% so radii remain positive.";
  else if (seedRaw !== "" && !Number.isSafeInteger(seed)) message = "Random seed must be a finite whole number within JavaScript's exact integer range.";
  const box = $("#editValidation"); box.textContent = message; box.classList.toggle("hidden", !message || !show); return message;
}
function explicitSeed() {
  const field = $("#seed"); if (field.value.trim() !== "") return Number(field.value); const values = new Uint32Array(1); crypto.getRandomValues(values); const seed = values[0] & 0x7fffffff; field.value = String(seed); return seed;
}
function remodelOptions() {
  const who = $("#who").value, action = $("#action").value; const stochastic = who.startsWith("random_") || action === "extend" || action === "branch";
  return {
    who, action, amount: ["remove", "none"].includes(action) ? null : Number($("#amount").value),
    random_ratio: who.startsWith("random_") ? Number($("#randomRatio").value) : 0,
    manual_dendrites: who === "manual" ? [...state.selectedSegments].sort((a, b) => a - b).join(",") : "",
    extent_unit: $("#extentUnit").value, radius_change: action === "remove" || $("#radiusChange").value.trim() === "" ? null : Number($("#radiusChange").value),
    radius_unit: $("#radiusUnit").value, seed: stochastic ? explicitSeed() : $("#seed").value.trim() === "" ? null : Number($("#seed").value),
  };
}
function operationLabel(options, count) {
  const names = { shrink: "Shrink", remove: "Remove subtree", extend: "Extend", branch: "Add daughter branches", scale: "Scale", none: "Change SWC radius" };
  return `${names[options.action]} · ${count} segment${count === 1 ? "" : "s"}`;
}

async function generatePreview(event) {
  event.preventDefault(); if (state.busy) return; const file = activeFile(); if (!file?.analysis) return; const message = validateRemodelForm(true); if (message) return;
  const options = remodelOptions(); const generation = ++state.previewGeneration; const sourceContent = file.content; const request = { generation, fileId: file.id }; state.previewRequest = request;
  try {
    setBusy(true, "Generating preview"); const result = await api("/api/remodel", { method: "POST", body: { name: file.name, content: file.content, sholl_step: currentStep(), options } });
    if (state.previewRequest !== request) return;
    if (generation !== state.previewGeneration || activeFile()?.id !== file.id || file.content !== sourceContent) { state.previewRequest = null; setBusy(false); return; }
    state.preview = { fileId: file.id, sourceContent, name: result.name, content: result.content, targets: result.targets, selector: result.selector, analysisId: result.analysis_id, analysis: analysisFromResponse(result), changes: result.changes, warnings: result.warnings, impact: result.impact, elapsed: result.elapsed_ms, options, label: operationLabel(options, result.targets.length) };
    state.previewRequest = null; state.previewView = "overlay"; setBusy(false); renderPreview(); updateDisplayBounds(); markViewerDirty(); setWorkflowStage("preview"); showToast("Preview ready; the active morphology is unchanged");
  } catch (error) { if (state.previewRequest !== request) return; state.previewRequest = null; setBusy(false); validateRemodelForm(false); showToast(error.message, true); }
}
function renderPreview() {
  const preview = state.preview; const active = preview && preview.fileId === state.activeId; $("#previewReview").classList.toggle("hidden", !active); $("#previewMode").classList.toggle("hidden", !active);
  if (!active) return; $("#previewSummary").textContent = preview.label; $("#previewRuntime").textContent = `${formatNumber(preview.elapsed, 1)} ms`; const warnings = $("#previewWarnings"); warnings.replaceChildren();
  const impactDelta = preview.impact.samples_after - preview.impact.samples_before; const impact = `Samples ${impactDelta >= 0 ? "+" : ""}${impactDelta}; segments ${preview.impact.segments_after - preview.impact.segments_before >= 0 ? "+" : ""}${preview.impact.segments_after - preview.impact.segments_before}.`;
  [impact, ...preview.warnings].forEach((message) => warnings.append(element("div", "preview-warning", message))); const changes = $("#previewChanges"); changes.replaceChildren();
  preview.changes.forEach((change) => { const row = element("div", "preview-change"); const unit = change.unit === "count" ? "" : change.unit; row.append(element("span", "", change.label), element("b", "", `${formatNumber(change.after, change.unit === "count" ? 0 : 1)}${unit ? ` ${unit}` : ""}`), element("em", "", `${signedNumber(change.delta, change.unit === "count" ? 0 : 1)}${unit ? ` ${unit}` : ""}`)); changes.append(row); });
  $$("[data-preview-view]").forEach((button) => button.classList.toggle("active", button.dataset.previewView === state.previewView));
}
function discardPreview(notify = true) {
  const hadPreview = Boolean(state.preview), hadRequest = Boolean(state.previewRequest); state.previewGeneration += 1; state.previewRequest = null; state.preview = null; if (hadRequest) setBusy(false); if (!hadPreview) return;
  state.previewView = "overlay"; $("#previewReview").classList.add("hidden"); $("#previewMode").classList.add("hidden"); updateDisplayBounds(); markViewerDirty(); setWorkflowStage("configure"); if (notify) showToast("Preview discarded; no morphology was changed");
}
async function applyPreview() {
  if (state.busy) return;
  const preview = state.preview, file = activeFile(); if (!preview || !file || preview.fileId !== file.id || preview.sourceContent !== file.content) { discardPreview(false); showToast("The preview is stale; generate it again", true); return; }
  file.history.push({ name: file.name, content: file.content, analysis: file.analysis, analysisId: file.analysisId, analysisStep: file.analysisStep, elapsed: file.elapsed, cached: file.cached, operation: preview.label, targets: [...preview.targets], options: preview.options });
  file.name = uniqueFileName(preview.name, [], file.id); file.content = preview.content; file.analysis = preview.analysis; file.analysisId = preview.analysisId; file.analysisStep = currentStep(); file.elapsed = preview.elapsed; file.cached = true; state.preview = null; state.selectedSegments.clear(); state.hoveredSegment = null;
  setWorkflowStage("apply"); await refreshGroups(); renderAll(); showToast(`${preview.label} applied; undo remains available`);
}
async function undoEdit() {
  if (state.busy) return; const file = activeFile(); if (!file?.history.length) return; discardPreview(false); const prior = file.history.pop(); Object.assign(file, { name: prior.name, content: prior.content, analysis: prior.analysis, analysisId: prior.analysisId, analysisStep: prior.analysisStep, elapsed: prior.elapsed, cached: prior.cached }); state.selectedSegments.clear(); state.hoveredSegment = null; resetCamera();
  if (file.analysisStep !== currentStep()) { Object.assign(file, { analysis: null, analysisId: null, analysisStep: null, cached: false, status: "queued", error: null }); await analyzeFiles([file]); }
  else { await refreshGroups(); renderAll(); }
  showToast(`${prior.operation} undone`);
}

function renderSelection() {
  const ids = [...state.selectedSegments].sort((a, b) => a - b); $("#selectionCount").textContent = ids.length; $("#selectionStatus").classList.toggle("hidden", !ids.length); $("#focusSelection").disabled = !ids.length;
  $("#manualSelectionLabel").textContent = ids.length ? `${ids.length} segment${ids.length === 1 ? "" : "s"}` : "No segments selected"; const root = $("#selectionChips"); root.replaceChildren(); ids.forEach((id) => root.append(element("i", "", String(id)))); if (!ids.length) root.append(element("span", "", "Click segments in the viewer; Shift-click adds to the selection."));
  validateRemodelForm(false); if (activeFile()?.analysis) renderSegmentSummary(state.hoveredSegment || (ids.length === 1 ? ids[0] : null)); markViewerDirty();
}
function clearSelection() { discardPreview(false); state.selectedSegments.clear(); state.hoveredSegment = null; renderSelection(); }

function renderHistory() {
  const file = activeFile(); const root = $("#historyList"); root.replaceChildren(); if (!file) return;
  const baseline = element("div", `history-entry${file.history.length ? "" : " current"}`); baseline.append(element("b", "", "Imported morphology"), element("span", "", `${file.originalContent.split(/\r?\n/).filter(Boolean).length.toLocaleString()} source rows and comments`)); root.append(baseline);
  if (!file.history.length) root.append(element("div", "history-empty", "Applied edits will appear here. Previewing never adds a history entry."));
  file.history.forEach((entry, index) => { const item = element("div", `history-entry${index === file.history.length - 1 ? " current" : ""}`); item.append(element("b", "", entry.operation), element("span", "", `${entry.targets.length} target${entry.targets.length === 1 ? "" : "s"} · seed ${entry.options.seed ?? "not used"}`)); root.append(item); });
}

function download(name, content, type) { const blob = new Blob([content], { type }); const url = URL.createObjectURL(blob); const anchor = document.createElement("a"); anchor.href = url; anchor.download = name; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
function csvCell(value) { const text = String(value ?? ""); return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text; }
function csv(rows) { return `${rows.map((row) => row.map(csvCell).join(",")).join("\n")}\n`; }
function downloadActiveSwc() { const file = activeFile(); if (file) download(file.name, file.content, "text/plain"); }
function downloadActiveJson() { const file = activeFile(); if (file?.analysis) download(`${file.name.replace(/\.swc$/i, "")}_statistics.json`, `${JSON.stringify(file.analysis.statistics, null, 2)}\n`, "application/json"); }
function scalarCsvContent() {
  const file = activeFile(); if (!file?.analysis) return ""; const rows = [["metric_key", "measurement", "value", "unit", "definition"]];
  Object.entries(file.analysis.statistics).filter(([, value]) => finite(value)).forEach(([key, value]) => { const info = metricInfo(key); rows.push([key, info.label, value, info.unit, info.definition]); }); return csv(rows);
}
function downloadScalarCsv() { const file = activeFile(); if (file?.analysis) download(`${file.name.replace(/\.swc$/i, "")}_scalar_metrics.csv`, scalarCsvContent(), "text/csv"); }
function distributionCsv(key) {
  const file = activeFile(); if (!file?.analysis) return ""; const info = metricInfo(key); const rows = [["bin", info.label, "unit"]]; Object.entries(file.analysis.statistics[key] || {}).sort(([a], [b]) => Number(a) - Number(b)).forEach(([bin, value]) => rows.push([bin, value, info.unit])); return csv(rows);
}

function renderAssignments() {
  const root = $("#groupAssignments"); root.replaceChildren();
  for (const file of state.files) {
    const row = element("div", "assignment"); const info = element("div"); info.append(element("b", "", file.name), element("small", "", file.analysis ? `${file.analysis.morphology.counts.segments} dendritic segments` : file.status)); const toggle = element("div", "ab-toggle");
    for (const group of ["A", "B"]) { const button = element("button", `${file.group === group ? "active " : ""}${group.toLowerCase()}`, group); button.type = "button"; button.title = `Assign to ${groupName(group)}`; button.disabled = state.busy; button.addEventListener("click", () => { if (file.group !== group) toggleGroup(file); }); toggle.append(button); } row.append(info, toggle); root.append(row);
  }
}
function scalar(summary, name) { return summary?.scalar_metrics?.[name] || null; }
function percentChange(a, b) { return a === 0 ? null : ((b - a) / Math.abs(a)) * 100; }
function renderComparison() {
  const a = state.groups.A, b = state.groups.B, ready = a && b; $("#compareEmpty").classList.toggle("hidden", Boolean(ready)); $("#compareContent").classList.toggle("hidden", !ready); $("#legendA").textContent = groupName("A"); $("#legendB").textContent = groupName("B"); if (!ready) return;
  $("#compareTitle").textContent = `${groupName("A")} vs ${groupName("B")}`; $("#compareSubtitle").textContent = `Descriptive mean ± population SD · n=${a.file_count} and n=${b.file_count}`;
  const notice = $("#compareNotice"); const lowN = a.file_count < 2 || b.file_count < 2; notice.classList.toggle("hidden", !lowN); notice.textContent = lowN ? "At least one cohort has n=1. Its population SD is 0 by definition and should not be interpreted as low biological variability." : "";
  const cards = $("#compareCards"); cards.replaceChildren();
  for (const key of COMPARISON_CARD_KEYS) {
    const info = metricInfo(key), av = scalar(a, key), bv = scalar(b, key); if (!av || !bv) continue; const card = element("div", "compare-card"); card.append(element("span", "", info.label.replace("All dendrites · ", ""))); const values = element("div", "compare-values");
    const left = element("b", "", formatNumber(av.mean, info.digits)); left.append(element("small", "", `${groupName("A")} ± ${formatNumber(av.standard_deviation, info.digits)} ${info.unit}`)); const right = element("b", "", formatNumber(bv.mean, info.digits)); right.append(element("small", "", `${groupName("B")} ± ${formatNumber(bv.standard_deviation, info.digits)} ${info.unit}`)); values.append(left, right); card.append(values);
    const delta = percentChange(av.mean, bv.mean); card.append(element("em", "", delta === null ? `Absolute difference ${signedNumber(bv.mean - av.mean, info.digits)}` : `${signedNumber(delta, 1)}% B relative to A`)); cards.append(card);
  }
  renderComparisonTable(); requestAnimationFrame(drawComparisonChart); updateCounts();
}
function renderComparisonTable() {
  const a = state.groups.A, b = state.groups.B; if (!a || !b) return; const root = $("#comparisonTable"); root.replaceChildren(); const header = element("div", "comparison-row header"); ["Measurement", `${groupName("A")} · mean ± SD`, `${groupName("B")} · mean ± SD`, "B − A"].forEach((value) => header.append(element("span", "", value))); root.append(header);
  for (const key of COMPARISON_SCALAR_KEYS) {
    const av = scalar(a, key), bv = scalar(b, key); if (!av || !bv) continue; const info = metricInfo(key); const row = element("div", "comparison-row"); const label = element("span", "", info.label); label.append(element("small", "", info.unit || "dimensionless")); row.append(label, element("span", "", `${formatNumber(av.mean, info.digits)} ± ${formatNumber(av.standard_deviation, info.digits)} (n=${av.sample_count})`), element("span", "", `${formatNumber(bv.mean, info.digits)} ± ${formatNumber(bv.standard_deviation, info.digits)} (n=${bv.sample_count})`), element("span", "", signedNumber(bv.mean - av.mean, info.digits))); root.append(row);
  }
}

function comparisonCsvContent() {
  const a = state.groups.A, b = state.groups.B; if (!a || !b) return ""; const rows = [["metric_key", "measurement", "unit", "cohort_a_mean", "cohort_a_population_sd", "cohort_a_n", "cohort_b_mean", "cohort_b_population_sd", "cohort_b_n", "absolute_difference"]];
  COMPARISON_SCALAR_KEYS.forEach((key) => { const av = scalar(a, key), bv = scalar(b, key); if (!av || !bv) return; const info = metricInfo(key); rows.push([key, info.label, info.unit, av.mean, av.standard_deviation, av.sample_count, bv.mean, bv.standard_deviation, bv.sample_count, bv.mean - av.mean]); });
  const metric = $("#comparisonMetric").value, adata = a.distribution_metrics[metric] || {}, bdata = b.distribution_metrics[metric] || {}, zeroFill = zeroFillDistribution(metric); rows.push([], ["distribution_metric", metric], ["bin", "cohort_a_mean", "cohort_a_population_sd", "cohort_a_n", "cohort_b_mean", "cohort_b_population_sd", "cohort_b_n"]); const keys = [...new Set([...Object.keys(adata), ...Object.keys(bdata)])].sort((x, y) => Number(x) - Number(y)); const cells = (data, group, key) => data[key] ? [data[key].mean, data[key].standard_deviation, data[key].sample_count] : zeroFill ? [0, 0, group.file_count] : ["", "", ""]; keys.forEach((key) => rows.push([key, ...cells(adata, a, key), ...cells(bdata, b, key)])); return csv(rows);
}

function fitCanvas(canvas) {
  const rect = canvas.getBoundingClientRect(); const dpr = Math.min(window.devicePixelRatio || 1, 2); const width = Math.max(1, Math.round(rect.width * dpr)), height = Math.max(1, Math.round(rect.height * dpr)); const changed = canvas.width !== width || canvas.height !== height; if (changed) { canvas.width = width; canvas.height = height; } return { ctx: canvas.getContext("2d"), width, height, dpr, rect, changed };
}
function niceMaximum(value) { if (!(value > 0)) return 1; const power = 10 ** Math.floor(Math.log10(value)); const scaled = value / power; return (scaled <= 1 ? 1 : scaled <= 2 ? 2 : scaled <= 5 ? 5 : 10) * power; }
function chartFrame(canvas) {
  const frame = fitCanvas(canvas); const { ctx, width, height, dpr } = frame; ctx.clearRect(0, 0, width, height); ctx.lineCap = "round"; ctx.lineJoin = "round"; return { ...frame, left: 48 * dpr, right: width - 14 * dpr, top: 14 * dpr, bottom: height - 42 * dpr };
}
function drawChartAxes(frame, xLabels, maxValue, xTitle, yTitle) {
  const { ctx, left, right, top, bottom, dpr } = frame; ctx.strokeStyle = "#e2e5df"; ctx.lineWidth = dpr; ctx.fillStyle = "#717d78"; ctx.font = `${9 * dpr}px system-ui`; ctx.textBaseline = "middle";
  for (let index = 0; index <= 4; index += 1) { const y = bottom - (bottom - top) * index / 4; ctx.beginPath(); ctx.moveTo(left, y); ctx.lineTo(right, y); ctx.stroke(); ctx.textAlign = "right"; ctx.fillText(formatNumber(maxValue * index / 4, maxValue < 10 ? 1 : 0), left - 7 * dpr, y); }
  const labelCount = Math.min(6, xLabels.length); for (let index = 0; index < labelCount; index += 1) { const item = labelCount === 1 ? 0 : Math.round(index * (xLabels.length - 1) / (labelCount - 1)); const x = xLabels.length === 1 ? (left + right) / 2 : left + (right - left) * item / Math.max(1, xLabels.length - 1); ctx.textAlign = "center"; ctx.textBaseline = "top"; ctx.fillText(formatNumber(Number(xLabels[item]), 0), x, bottom + 7 * dpr); }
  ctx.fillStyle = "#63716c"; ctx.font = `${9 * dpr}px system-ui`; ctx.textAlign = "center"; ctx.fillText(xTitle, (left + right) / 2, bottom + 27 * dpr); ctx.save(); ctx.translate(12 * dpr, (top + bottom) / 2); ctx.rotate(-Math.PI / 2); ctx.fillText(yTitle, 0, 0); ctx.restore();
}
function drawLineSeries(frame, series, maxValue, color, name, connectGaps = false) {
  const { ctx, left, right, top, bottom, dpr } = frame; const xAt = (index) => series.length === 1 ? (left + right) / 2 : left + (right - left) * index / Math.max(1, series.length - 1); const yAt = (value) => bottom - (bottom - top) * value / maxValue; const hits = []; ctx.strokeStyle = color; ctx.lineWidth = 1.7 * dpr; ctx.beginPath(); let started = false;
  series.forEach((item, index) => { if (item.value === null) { if (!connectGaps) started = false; return; } const x = xAt(index), y = yAt(item.value); if (!started) { ctx.moveTo(x, y); started = true; } else ctx.lineTo(x, y); hits.push({ x, y, item, name }); }); ctx.stroke(); ctx.fillStyle = color; hits.forEach(({ x, y }) => { ctx.beginPath(); ctx.arc(x, y, 2.4 * dpr, 0, Math.PI * 2); ctx.fill(); }); return hits;
}
function drawBarSeries(frame, series, maxValue, color, name) {
  const { ctx, left, right, top, bottom, dpr } = frame; const slot = (right - left) / Math.max(1, series.length), width = Math.min(24 * dpr, slot * .55); const hits = []; ctx.fillStyle = color;
  series.forEach((item, index) => { if (item.value === null) return; const x = left + slot * (index + .5), y = bottom - (bottom - top) * item.value / maxValue; ctx.fillRect(x - width / 2, y, width, bottom - y); hits.push({ x, y, width, item, name }); }); return hits;
}
function drawEmptyChart(frame, message) { const { ctx, width, height, dpr } = frame; ctx.fillStyle = "#7a8581"; ctx.font = `${10 * dpr}px system-ui`; ctx.textAlign = "center"; ctx.fillText(message, width / 2, height / 2); }

function drawActiveAnalysis() {
  if (state.analysisView === "sholl") drawShollChart(); else if (state.analysisView === "branch") drawBranchChart();
}
function drawShollChart() {
  const file = activeFile(); if (!file?.analysis || state.analysisView !== "sholl") return; const region = $("#shollRegion").value, measure = $("#shollMetric").value, key = `sholl_${region}_${measure}`, values = file.analysis.statistics[key] || {}; const entries = Object.entries(values).sort(([a], [b]) => Number(a) - Number(b)); const frame = chartFrame($("#shollCanvas"));
  const labels = { length: ["Cable length by radial shell", "Cable length within shell (µm)"], intersections: ["Intersections at Sholl radius", "Intersections (count)"], branchpoints: ["Branch points by radial shell", "Branch points within shell (count)"] }; $("#shollTitle").textContent = `${labels[measure][0]} · ${REGION_LABELS[region].toLowerCase()}`; $("#shollCaption").textContent = `Distance is measured from the root soma coordinate. Shell width: ${formatNumber(currentStep(), 3)} µm; coordinate units are assumed µm.`;
  if (!entries.length) { drawEmptyChart(frame, "No dendritic observations for this profile"); state.chartHits.sholl = []; return; } const maxValue = niceMaximum(Math.max(...entries.map(([, value]) => numeric(value)), 1)); drawChartAxes(frame, entries.map(([bin]) => bin), maxValue, "Radial distance from root soma (µm)", labels[measure][1]); const color = region === "basal" ? "#188c76" : region === "apical" ? "#d86e58" : "#254c47"; state.chartHits.sholl = drawLineSeries(frame, entries.map(([bin, value]) => ({ bin, value: numeric(value), raw: value })), maxValue, color, "Sholl");
}
function branchKey() { const region = $("#branchRegion").value; return $("#branchMetric").value.replace("{region}", region); }
function drawBranchChart() {
  const file = activeFile(); if (!file?.analysis || state.analysisView !== "branch") return; const key = branchKey(), values = file.analysis.statistics[key] || {}, entries = Object.entries(values).sort(([a], [b]) => Number(a) - Number(b)); const frame = chartFrame($("#branchCanvas")); const info = metricInfo(key); $("#branchTitle").textContent = info.label;
  if (!entries.length) { drawEmptyChart(frame, "No branch-order observations for this region"); state.chartHits.branch = []; return; } const maxValue = niceMaximum(Math.max(...entries.map(([, value]) => numeric(value)), 1)); drawChartAxes(frame, entries.map(([bin]) => bin), maxValue, "Centrifugal branch order", info.unit === "count" ? "Dendritic segments (count)" : `${info.label.split(" · ").pop()} (${info.unit})`); state.chartHits.branch = drawBarSeries(frame, entries.map(([bin, value]) => ({ bin, value: numeric(value), raw: value })), maxValue, "#188c76", "Branch order");
}

function zeroFillDistribution(metric) { return metric.startsWith("sholl_") || metric.startsWith("number_of_"); }
function comparisonMetricInfo(metric) {
  const info = metricInfo(metric); const isSholl = metric.startsWith("sholl_"); return { ...info, xTitle: isSholl ? "Radial distance from root soma (µm)" : "Centrifugal branch order", yTitle: info.unit === "count" ? `${info.label.split(" · ").pop()} (count)` : `${info.label.split(" · ").pop()} (${info.unit})` };
}
function drawComparisonChart() {
  const a = state.groups.A, b = state.groups.B; if (!a || !b || state.view !== "compare") return; const metric = $("#comparisonMetric").value, adata = a.distribution_metrics[metric] || {}, bdata = b.distribution_metrics[metric] || {}, zeroFill = zeroFillDistribution(metric); const keys = [...new Set([...Object.keys(adata), ...Object.keys(bdata)])].sort((x, y) => Number(x) - Number(y)); const frame = chartFrame($("#comparisonCanvas")); const info = comparisonMetricInfo(metric); $("#comparisonChartTitle").textContent = info.label;
  if (!keys.length) { drawEmptyChart(frame, "No observations for this comparison profile"); state.chartHits.comparison = []; return; }
  const seriesFor = (data, group) => keys.map((bin) => { const item = data[bin]; return { bin, value: item ? numeric(item.mean) : zeroFill ? 0 : null, mean: item?.mean ?? (zeroFill ? 0 : null), sd: item?.standard_deviation ?? (zeroFill ? 0 : null), n: item?.sample_count ?? (zeroFill ? group.file_count : null) }; }); const aseries = seriesFor(adata, a), bseries = seriesFor(bdata, b); state.comparisonSeries = { keys, A: aseries, B: bseries, metric }; const observed = [...aseries, ...bseries].filter((item) => item.value !== null).map((item) => item.value + numeric(item.sd)); const maxValue = niceMaximum(Math.max(...observed, 1)); drawChartAxes(frame, keys, maxValue, info.xTitle, info.yTitle);
  const { ctx, left, right, top, bottom, dpr } = frame; const xAt = (index) => keys.length === 1 ? (left + right) / 2 : left + (right - left) * index / Math.max(1, keys.length - 1); const yAt = (value) => bottom - (bottom - top) * value / maxValue;
  [[aseries, "#188c76"], [bseries, "#a15bc0"]].forEach(([series, color]) => { ctx.strokeStyle = color; ctx.globalAlpha = .4; ctx.lineWidth = dpr; series.forEach((item, index) => { if (item.value === null || !item.sd) return; const x = xAt(index), high = yAt(Math.min(maxValue, item.value + item.sd)), low = yAt(Math.max(0, item.value - item.sd)); ctx.beginPath(); ctx.moveTo(x, high); ctx.lineTo(x, low); ctx.moveTo(x - 3 * dpr, high); ctx.lineTo(x + 3 * dpr, high); ctx.moveTo(x - 3 * dpr, low); ctx.lineTo(x + 3 * dpr, low); ctx.stroke(); }); ctx.globalAlpha = 1; });
  state.chartHits.comparison = [...drawLineSeries(frame, aseries, maxValue, "#188c76", groupName("A")), ...drawLineSeries(frame, bseries, maxValue, "#a15bc0", groupName("B"))];
}

function showChartTooltip(kind, event) {
  const canvas = event.currentTarget, tooltip = $(`#${kind}Tooltip`), hits = state.chartHits[kind] || []; if (!hits.length) { tooltip.classList.add("hidden"); return; } const rect = canvas.getBoundingClientRect(), dpr = Math.min(window.devicePixelRatio || 1, 2), x = (event.clientX - rect.left) * dpr, y = (event.clientY - rect.top) * dpr; let best = null;
  hits.forEach((hit) => { const distance = Math.hypot(hit.x - x, hit.y - y); if (!best || distance < best.distance) best = { ...hit, distance }; }); if (!best || best.distance > 18 * dpr) { tooltip.classList.add("hidden"); return; }
  const item = best.item; if (kind === "comparison" && state.comparisonSeries) { const index = state.comparisonSeries.keys.indexOf(String(item.bin)), radial = state.comparisonSeries.metric.startsWith("sholl_"); tooltip.replaceChildren(element("b", "", `${radial ? "Radial bin" : "Branch order"} ${item.bin}`)); for (const group of ["A", "B"]) { const observation = state.comparisonSeries[group][index]; tooltip.append(element("span", "", observation?.value === null ? `${groupName(group)} · no observation` : `${groupName(group)} · mean ${formatNumber(observation?.mean, 3)} · SD ${formatNumber(observation?.sd, 3)} · n=${observation?.n ?? "—"}`)); } } else { tooltip.replaceChildren(element("b", "", `${best.name} · ${kind === "branch" ? "order" : "bin"} ${item.bin}`), element("span", "", `Value ${formatNumber(item.value, 3)}`)); } tooltip.classList.remove("hidden"); const left = Math.min(rect.width - tooltip.offsetWidth - 6, Math.max(6, event.clientX - rect.left + 10)), top = Math.min(rect.height - tooltip.offsetHeight - 6, Math.max(6, event.clientY - rect.top + 10)); tooltip.style.left = `${left}px`; tooltip.style.top = `${top}px`;
}

function updateDisplayBounds() {
  const file = activeFile(); const morphologies = []; if (file?.analysis) morphologies.push(file.analysis.morphology); if (state.preview?.fileId === file?.id) morphologies.push(state.preview.analysis.morphology); if (!morphologies.length) { state.displayBounds = { center: [0, 0, 0], extent: 1 }; return; }
  const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity]; morphologies.forEach((morphology) => { for (let axis = 0; axis < 3; axis += 1) { min[axis] = Math.min(min[axis], morphology.bounds.min[axis]); max[axis] = Math.max(max[axis], morphology.bounds.max[axis]); } }); state.displayBounds = { center: min.map((value, axis) => (value + max[axis]) / 2), extent: Math.max(1, ...max.map((value, axis) => value - min[axis])) };
}
function resetCamera() { Object.assign(state.camera, { yaw: -.55, pitch: .28, zoom: 1, panX: 0, panY: 0, auto: true, target: null, extent: null, dirty: true }); syncRotationButton(); }
function fitView() { Object.assign(state.camera, { zoom: 1, panX: 0, panY: 0, target: null, extent: null, dirty: true }); }
function focusSelection() {
  const file = activeFile(); if (!file?.analysis || !state.selectedSegments.size) return; const morphology = file.analysis.morphology; const indices = [...state.selectedSegments].flatMap((id) => morphology.segmentSamples.get(id) || []); if (!indices.length) return; const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity]; indices.forEach((index) => { for (let axis = 0; axis < 3; axis += 1) { const value = morphology.coords[index * 3 + axis]; min[axis] = Math.min(min[axis], value); max[axis] = Math.max(max[axis], value); } }); state.camera.target = min.map((value, axis) => (value + max[axis]) / 2); state.camera.extent = Math.max(1, ...max.map((value, axis) => value - min[axis])) * 1.35; state.camera.zoom = 1; state.camera.panX = 0; state.camera.panY = 0; state.camera.auto = false; state.camera.dirty = true; syncRotationButton();
}
function setOrientation(yaw, pitch) { state.camera.yaw = yaw; state.camera.pitch = pitch; state.camera.auto = false; state.camera.dirty = true; syncRotationButton(); }
function syncRotationButton() { const button = $("#toggleRotation"); button.classList.toggle("active", state.camera.auto); button.textContent = state.camera.auto ? "Pause" : "Rotate"; button.title = state.camera.auto ? "Pause automatic rotation" : "Start automatic rotation"; }
function markViewerDirty() { state.camera.dirty = true; }

function projectMorphology(morphology, fitted) {
  const { width, height, dpr } = fitted, target = state.camera.target || state.displayBounds.center, extent = state.camera.extent || state.displayBounds.extent; const scale = Math.min(width, height) * .76 / Math.max(1, extent) * state.camera.zoom; const cy = Math.cos(state.camera.yaw), sy = Math.sin(state.camera.yaw), cp = Math.cos(state.camera.pitch), sp = Math.sin(state.camera.pitch);
  for (let index = 0; index < morphology.ids.length; index += 1) { const offset = index * 3, dx = morphology.coords[offset] - target[0], dy = morphology.coords[offset + 1] - target[1], dz = morphology.coords[offset + 2] - target[2], x1 = dx * cy - dz * sy, z1 = dx * sy + dz * cy, y1 = dy * cp - z1 * sp; morphology.projectedX[index] = width / 2 + x1 * scale + state.camera.panX * dpr; morphology.projectedY[index] = height / 2 - y1 * scale + state.camera.panY * dpr; morphology.projectedDepth[index] = dy * sp + z1 * cp; }
  return scale;
}
function visibleType(type) { return state.visibility[type] !== false; }
function drawPrepared(ctx, morphology, fitted, options = {}) {
  const dpr = fitted.dpr, otherKeys = options.otherKeys, diffMode = options.diffMode; ctx.lineCap = "round";
  for (let edge = 0; edge < morphology.distal.length; edge += 1) {
    const distal = morphology.distal[edge], proximal = morphology.proximal[edge], type = morphology.types[distal]; if (!visibleType(type)) continue; const segment = morphology.segmentIds[distal], changed = otherKeys ? !otherKeys.has(morphology.edgeSignatures[edge]) : false;
    if (diffMode === "removed" && !changed) { ctx.globalAlpha = .12; ctx.strokeStyle = TYPE_COLORS[type] || "#8ba8ad"; }
    else if (diffMode === "removed" && changed) { ctx.globalAlpha = .92; ctx.strokeStyle = "#ff8a7b"; }
    else if (diffMode === "added" && !changed) { ctx.globalAlpha = .42; ctx.strokeStyle = TYPE_COLORS[type] || "#8ba8ad"; }
    else if (diffMode === "added" && changed) { ctx.globalAlpha = 1; ctx.strokeStyle = "#69b8ff"; }
    else { ctx.globalAlpha = .76; ctx.strokeStyle = TYPE_COLORS[type] || "#8ba8ad"; }
    const selected = segment && state.selectedSegments.has(segment) && options.allowSelection !== false, hovered = segment && state.hoveredSegment === segment && options.allowSelection !== false;
    const x1 = morphology.projectedX[proximal], y1 = morphology.projectedY[proximal], x2 = morphology.projectedX[distal], y2 = morphology.projectedY[distal]; const baseWidth = Math.max(.65 * dpr, Math.min(2.4 * dpr, morphology.radii[distal] * options.scale * .032));
    if (selected || hovered) { ctx.globalAlpha = 1; ctx.strokeStyle = hovered ? "#65c8ff" : "#081c1b"; ctx.lineWidth = (selected ? 5.2 : 4.5) * dpr; ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); ctx.strokeStyle = selected ? "#f7f5df" : "#9addff"; ctx.lineWidth = (selected ? 2.4 : 1.9) * dpr; }
    else ctx.lineWidth = baseWidth;
    if (diffMode === "removed" && changed) ctx.setLineDash([4 * dpr, 3 * dpr]); ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); ctx.setLineDash([]);
  }
  ctx.globalAlpha = 1;
  if (state.visibility[1]) { for (let index = 0; index < morphology.ids.length; index += 1) if (morphology.types[index] === 1) { ctx.fillStyle = TYPE_COLORS[1]; ctx.beginPath(); ctx.arc(morphology.projectedX[index], morphology.projectedY[index], Math.max(2.7 * dpr, morphology.radii[index] * options.scale * .13), 0, Math.PI * 2); ctx.fill(); } }
  for (let index = 0; index < morphology.ids.length; index += 1) { const type = morphology.types[index]; if (!visibleType(type) || ![3, 4].includes(type)) continue; if (morphology.childCounts[index] > 1) { ctx.globalAlpha = .6; ctx.fillStyle = TYPE_COLORS[type]; ctx.beginPath(); ctx.arc(morphology.projectedX[index], morphology.projectedY[index], 1.8 * dpr, 0, Math.PI * 2); ctx.fill(); } else if (morphology.childCounts[index] === 0) { ctx.globalAlpha = .75; ctx.fillStyle = TYPE_COLORS[type]; ctx.beginPath(); ctx.arc(morphology.projectedX[index], morphology.projectedY[index], 1.25 * dpr, 0, Math.PI * 2); ctx.fill(); } } ctx.globalAlpha = 1;
}
function drawOrientation(ctx, fitted) {
  const { width, height, dpr } = fitted, originX = width - 50 * dpr, originY = height - 55 * dpr, length = 24 * dpr, cy = Math.cos(state.camera.yaw), sy = Math.sin(state.camera.yaw), cp = Math.cos(state.camera.pitch), sp = Math.sin(state.camera.pitch); const vectors = [[1, 0, 0, "X", "#f08a78"], [0, 1, 0, "Y", "#7adabf"], [0, 0, 1, "Z", "#79b9ef"]];
  ctx.font = `${8 * dpr}px ui-monospace, monospace`; ctx.lineWidth = 1.2 * dpr; vectors.forEach(([dx, dy, dz, label, color]) => { const x1 = dx * cy - dz * sy, z1 = dx * sy + dz * cy, y1 = dy * cp - z1 * sp, x = originX + x1 * length, y = originY - y1 * length; ctx.strokeStyle = color; ctx.fillStyle = color; ctx.beginPath(); ctx.moveTo(originX, originY); ctx.lineTo(x, y); ctx.stroke(); ctx.fillText(label, x + 3 * dpr, y); });
}
function niceScaleBar(worldLength) { const power = 10 ** Math.floor(Math.log10(Math.max(worldLength, 1e-9))); const scaled = worldLength / power; return (scaled >= 5 ? 5 : scaled >= 2 ? 2 : 1) * power; }
function drawScaleBar(ctx, fitted, scale) {
  const { width, height, dpr } = fitted, desired = 72 * dpr, world = niceScaleBar(desired / scale), pixels = world * scale, x = width - 18 * dpr - pixels, y = height - 18 * dpr; ctx.strokeStyle = "rgba(255,255,255,.68)"; ctx.fillStyle = "rgba(255,255,255,.68)"; ctx.lineWidth = dpr; ctx.beginPath(); ctx.moveTo(x, y - 3 * dpr); ctx.lineTo(x, y); ctx.lineTo(x + pixels, y); ctx.lineTo(x + pixels, y - 3 * dpr); ctx.stroke(); ctx.font = `${8 * dpr}px system-ui`; ctx.textAlign = "center"; ctx.fillText(`${formatNumber(world, world < 1 ? 2 : 0)} µm`, x + pixels / 2, y - 8 * dpr);
}
function drawMorphology() {
  const canvas = $("#morphologyCanvas"), file = activeFile(); if (!canvas || state.view !== "workspace") return; const fitted = fitCanvas(canvas), ctx = fitted.ctx; ctx.clearRect(0, 0, fitted.width, fitted.height); if (!file?.analysis) { ctx.fillStyle = "rgba(255,255,255,.55)"; ctx.font = `${11 * fitted.dpr}px system-ui`; ctx.textAlign = "center"; ctx.fillText(file?.error || "No analyzed morphology", fitted.width / 2, fitted.height / 2); return; }
  const original = file.analysis.morphology, preview = state.preview?.fileId === file.id ? state.preview.analysis.morphology : null; const originalScale = projectMorphology(original, fitted); let previewScale = originalScale; if (preview) previewScale = projectMorphology(preview, fitted);
  if (!preview || state.previewView === "before") drawPrepared(ctx, original, fitted, { scale: originalScale, allowSelection: true });
  else if (state.previewView === "after") drawPrepared(ctx, preview, fitted, { scale: previewScale, otherKeys: original.edgeKeys, diffMode: "added", allowSelection: false });
  else { drawPrepared(ctx, original, fitted, { scale: originalScale, otherKeys: preview.edgeKeys, diffMode: "removed", allowSelection: true }); drawPrepared(ctx, preview, fitted, { scale: previewScale, otherKeys: original.edgeKeys, diffMode: "added", allowSelection: false }); }
  drawOrientation(ctx, fitted); drawScaleBar(ctx, fitted, originalScale); state.camera.dirty = false;
}
function animationLoop(timestamp) {
  const active = state.view === "workspace" && activeFile()?.analysis && !document.hidden; if (active && state.camera.auto && !state.camera.dragging) { const delta = state.camera.lastFrame ? Math.min(32, timestamp - state.camera.lastFrame) : 16; state.camera.yaw += delta * .000075; state.camera.dirty = true; } state.camera.lastFrame = timestamp; if (active && state.camera.dirty) drawMorphology(); requestAnimationFrame(animationLoop);
}
function distanceToSegment(px, py, x1, y1, x2, y2) { const dx = x2 - x1, dy = y2 - y1, length2 = dx * dx + dy * dy, t = length2 ? Math.max(0, Math.min(1, ((px - x1) * dx + (py - y1) * dy) / length2)) : 0; return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy)); }
function hitSegment(clientX, clientY) {
  const canvas = $("#morphologyCanvas"), file = activeFile(); if (!file?.analysis) return null; const rect = canvas.getBoundingClientRect(), sx = canvas.width / rect.width, sy = canvas.height / rect.height, x = (clientX - rect.left) * sx, y = (clientY - rect.top) * sy, morphology = file.analysis.morphology; let best = null;
  for (let edge = 0; edge < morphology.distal.length; edge += 1) { const distal = morphology.distal[edge], proximal = morphology.proximal[edge], segment = morphology.segmentIds[distal], type = morphology.types[distal]; if (!segment || !visibleType(type)) continue; const distance = distanceToSegment(x, y, morphology.projectedX[proximal], morphology.projectedY[proximal], morphology.projectedX[distal], morphology.projectedY[distal]); if (distance > 10 * sx) continue; const depth = (morphology.projectedDepth[proximal] + morphology.projectedDepth[distal]) / 2; if (!best || depth > best.depth + 1e-6 || (Math.abs(depth - best.depth) <= 1e-6 && distance < best.distance)) best = { segment, distance, depth }; }
  return best?.segment || null;
}
function updateHover(event) {
  const segment = hitSegment(event.clientX, event.clientY); if (segment === state.hoveredSegment && segment) { positionSegmentPopover(event); return; } state.hoveredSegment = segment; renderSegmentSummary(segment || (state.selectedSegments.size === 1 ? [...state.selectedSegments][0] : null)); const popover = $("#segmentPopover"); if (!segment) { popover.classList.add("hidden"); markViewerDirty(); return; } const details = segmentDetails(segment); popover.replaceChildren(); const title = element("div", "popover-title"); title.append(element("b", "", `Segment ${segment}`), element("span", "", details.typeLabel)); const list = element("dl"); [["Branch order", details.branchOrder], ["Centerline length", `${formatNumber(details.length, 2)} µm`], ["Soma-path length", `${formatNumber(details.pathLength, 2)} µm`], ["Median diameter", `${formatNumber(details.medianDiameter, 3)} µm`], ["Terminal", details.terminal ? "Yes" : "No"], ["Distal segments", details.descendantCount]].forEach(([term, value]) => list.append(element("dt", "", term), element("dd", "", String(value)))); popover.append(title, list); popover.classList.remove("hidden"); positionSegmentPopover(event); markViewerDirty();
}
function positionSegmentPopover(event) { const wrap = $("#canvasWrap"), popover = $("#segmentPopover"), rect = wrap.getBoundingClientRect(); const left = Math.min(rect.width - popover.offsetWidth - 8, Math.max(8, event.clientX - rect.left + 14)), top = Math.min(rect.height - popover.offsetHeight - 8, Math.max(8, event.clientY - rect.top + 14)); popover.style.left = `${left}px`; popover.style.top = `${top}px`; }
function selectAt(event) {
  const segment = hitSegment(event.clientX, event.clientY); if (!segment) { if (!event.shiftKey && !event.metaKey && !event.ctrlKey) clearSelection(); return; } const additive = event.shiftKey || event.metaKey || event.ctrlKey;
  discardPreview(false);
  if (!additive) { state.selectedSegments.clear(); state.selectedSegments.add(segment); } else if (state.selectedSegments.has(segment)) state.selectedSegments.delete(segment); else state.selectedSegments.add(segment); renderSelection(); setWorkflowStage("select");
}

function bindEvents() {
  const openPicker = () => $("#fileInput").click(); ["#chooseFiles", "#addFiles", "#railAdd", "#compareAddFiles"].forEach((selector) => $(selector).addEventListener("click", openPicker)); $("#fileInput").addEventListener("change", async (event) => { await readFiles(event.target.files); event.target.value = ""; }); $("#loadExample").addEventListener("click", loadExample); $("#railExample").addEventListener("click", loadExample);
  const drop = $("#dropZone"); drop.addEventListener("click", (event) => { if (event.target === drop) openPicker(); }); drop.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); openPicker(); } }); ["dragenter", "dragover"].forEach((name) => drop.addEventListener(name, (event) => { event.preventDefault(); drop.classList.add("dragging"); })); ["dragleave", "drop"].forEach((name) => drop.addEventListener(name, (event) => { event.preventDefault(); drop.classList.remove("dragging"); })); drop.addEventListener("drop", (event) => readFiles(event.dataTransfer.files));
  $$(".mode-button").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.view))); $$(".inspector-tab").forEach((button) => button.addEventListener("click", () => showInspector(button.dataset.panel))); $$("[data-analysis-view]").forEach((button) => button.addEventListener("click", () => showAnalysis(button.dataset.analysisView)));
  $("#shollMetric").addEventListener("change", drawShollChart); $("#shollRegion").addEventListener("change", drawShollChart); $("#branchMetric").addEventListener("change", drawBranchChart); $("#branchRegion").addEventListener("change", drawBranchChart); $("#metricSearch").addEventListener("input", renderMetricsTable);
  $("#shollStep").addEventListener("change", async () => {
    const generation = ++state.shollGeneration, requested = currentStep(); if (!(requested > 0)) { $("#shollStep").value = String(state.shollStep); showToast("Sholl shell width must be positive", true); return; }
    if (requested === state.shollStep) return; discardPreview(false); const succeeded = await analyzeFiles(state.files.filter((file) => file.analysis), { atomic: true });
    if (generation !== state.shollGeneration) return;
    if (!succeeded) $("#shollStep").value = String(state.shollStep);
  });
  $("#who").addEventListener("change", updateRemodelFields); $("#action").addEventListener("change", updateRemodelFields); ["#amount", "#extentUnit", "#radiusChange", "#radiusUnit", "#randomRatio", "#seed"].forEach((selector) => $(selector).addEventListener("input", () => { discardPreview(false); validateRemodelForm(false); })); $("#clearSelection").addEventListener("click", clearSelection); $("#clearViewerSelection").addEventListener("click", clearSelection); $("#remodelForm").addEventListener("submit", generatePreview); $("#discardPreview").addEventListener("click", () => discardPreview(true)); $("#confirmEdit").addEventListener("click", applyPreview); $("#undoEdit").addEventListener("click", undoEdit); $("#undoHistory").addEventListener("click", undoEdit);
  $$("[data-preview-view]").forEach((button) => button.addEventListener("click", () => { state.previewView = button.dataset.previewView; renderPreview(); markViewerDirty(); }));
  $("#toggleRotation").addEventListener("click", () => { state.camera.auto = !state.camera.auto; state.camera.dirty = true; syncRotationButton(); }); $("#fitView").addEventListener("click", fitView); $("#focusSelection").addEventListener("click", focusSelection); $("#viewFront").addEventListener("click", () => setOrientation(0, 0)); $("#viewSide").addEventListener("click", () => setOrientation(Math.PI / 2, 0)); $("#viewTop").addEventListener("click", () => setOrientation(0, Math.PI / 2));
  [["#showBasal", 3], ["#showApical", 4], ["#showSoma", 1]].forEach(([selector, type]) => $(selector).addEventListener("change", (event) => { state.visibility[type] = event.target.checked; markViewerDirty(); }));
  $("#downloadSwc").addEventListener("click", downloadActiveSwc); $("#downloadJson").addEventListener("click", downloadActiveJson); $("#downloadMetricsCsv").addEventListener("click", downloadScalarCsv); $("#downloadShollCsv").addEventListener("click", () => { const file = activeFile(), key = `sholl_${$("#shollRegion").value}_${$("#shollMetric").value}`; if (file) download(`${file.name.replace(/\.swc$/i, "")}_${key}.csv`, distributionCsv(key), "text/csv"); }); $("#downloadBranchCsv").addEventListener("click", () => { const file = activeFile(), key = branchKey(); if (file) download(`${file.name.replace(/\.swc$/i, "")}_${key}.csv`, distributionCsv(key), "text/csv"); });
  $("#historyDownloadSwc").addEventListener("click", downloadActiveSwc); $("#historyDownloadJson").addEventListener("click", downloadActiveJson); $("#historyDownloadCsv").addEventListener("click", downloadScalarCsv);
  $("#downloadComparison").addEventListener("click", () => download("remod-cohort-comparison.json", `${JSON.stringify({ cohort_names: state.groupNames, ...state.groups }, null, 2)}\n`, "application/json")); $("#downloadComparisonCsv").addEventListener("click", () => download("remod-cohort-comparison.csv", comparisonCsvContent(), "text/csv")); $("#comparisonMetric").addEventListener("change", drawComparisonChart);
  [["A", "#groupAName"], ["B", "#groupBName"]].forEach(([group, selector]) => $(selector).addEventListener("input", (event) => { state.groupNames[group] = event.target.value.trim() || `Cohort ${group}`; renderActive(); renderAssignments(); renderComparison(); }));
  [["sholl", "#shollCanvas"], ["branch", "#branchCanvas"], ["comparison", "#comparisonCanvas"]].forEach(([kind, selector]) => { $(selector).addEventListener("pointermove", (event) => showChartTooltip(kind, event)); $(selector).addEventListener("pointerleave", () => $(`#${kind}Tooltip`).classList.add("hidden")); });
  const canvas = $("#morphologyCanvas"), wrap = $("#canvasWrap"); let moved = false;
  canvas.addEventListener("contextmenu", (event) => event.preventDefault()); canvas.addEventListener("pointerdown", (event) => { moved = false; state.camera.dragging = true; state.camera.dragButton = event.button; state.camera.panMode = event.shiftKey || event.button === 1 || event.button === 2; state.camera.auto = false; state.camera.lastX = event.clientX; state.camera.lastY = event.clientY; canvas.setPointerCapture(event.pointerId); wrap.classList.add("dragging"); syncRotationButton(); });
  canvas.addEventListener("pointermove", (event) => { if (state.camera.dragging) { const dx = event.clientX - state.camera.lastX, dy = event.clientY - state.camera.lastY; if (Math.abs(dx) + Math.abs(dy) > 2) moved = true; if (state.camera.panMode) { state.camera.panX += dx; state.camera.panY += dy; } else { state.camera.yaw += dx * .008; state.camera.pitch = Math.max(-1.5, Math.min(1.5, state.camera.pitch + dy * .008)); } state.camera.lastX = event.clientX; state.camera.lastY = event.clientY; state.camera.dirty = true; return; } cancelAnimationFrame(hoverFrame); hoverFrame = requestAnimationFrame(() => updateHover(event)); });
  canvas.addEventListener("pointerleave", () => { if (!state.camera.dragging) { state.hoveredSegment = null; $("#segmentPopover").classList.add("hidden"); renderSegmentSummary(state.selectedSegments.size === 1 ? [...state.selectedSegments][0] : null); markViewerDirty(); } }); canvas.addEventListener("pointerup", (event) => { state.camera.dragging = false; wrap.classList.remove("dragging"); if (!moved && state.camera.dragButton === 0) selectAt(event); state.camera.panMode = false; state.camera.dragButton = null; });
  canvas.addEventListener("wheel", (event) => { event.preventDefault(); state.camera.zoom = Math.max(.15, Math.min(12, state.camera.zoom * Math.exp(-event.deltaY * .001))); state.camera.auto = false; state.camera.dirty = true; syncRotationButton(); }, { passive: false });
  const observer = new ResizeObserver(() => { markViewerDirty(); drawActiveAnalysis(); drawComparisonChart(); }); observer.observe(canvas); observer.observe($("#shollCanvas")); observer.observe($("#branchCanvas")); observer.observe($("#comparisonCanvas")); document.addEventListener("visibilitychange", () => { state.camera.lastFrame = 0; markViewerDirty(); });
}

function makeHeroNeuron() {
  const group = $("#heroNeuron"); let counter = 0; const paths = []; function branch(x, y, angle, length, depth) { counter += 1; const bend = Math.sin(counter * 2.31) * .22, nx = x + Math.cos(angle + bend) * length, ny = y + Math.sin(angle + bend) * length; paths.push(`M ${x.toFixed(1)} ${y.toFixed(1)} Q ${((x + nx) / 2 + Math.sin(counter) * 5).toFixed(1)} ${((y + ny) / 2 + Math.cos(counter) * 5).toFixed(1)} ${nx.toFixed(1)} ${ny.toFixed(1)}`); if (depth <= 0) return; const spread = .31 + (counter % 3) * .09; branch(nx, ny, angle - spread, length * (.71 + (counter % 2) * .06), depth - 1); branch(nx, ny, angle + spread, length * (.67 + (counter % 3) * .035), depth - 1); }
  [-2.75, -2.2, -1.55, -.7, -.1, .5, 1.2, 2.25].forEach((angle) => branch(260, 265, angle, 74, 4)); paths.forEach((data) => { const path = document.createElementNS("http://www.w3.org/2000/svg", "path"); path.setAttribute("d", data); group.append(path); });
}

makeHeroNeuron(); bindEvents(); updateRemodelFields(); showInspector("analyze"); showAnalysis("overview"); syncRotationButton(); requestAnimationFrame(animationLoop);
