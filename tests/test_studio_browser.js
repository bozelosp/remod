"use strict";

// Exercise the actual UI state transitions with small DOM/network stubs.
// Real rendering, controls, and downloads are also checked in the local browser.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

const source = fs.readFileSync(path.join(__dirname, "../ui/app.js"), "utf8");
const bootstrap = /^makeHeroNeuron\(\); bindEvents\(\);[^\n]*$/m;
assert.match(source, bootstrap);

function runtime() {
  const fields = new Map();
  const document = {
    querySelector(selector) {
      if (!fields.has(selector)) fields.set(selector, { value: "", textContent: "", classList: { add() {}, remove() {}, toggle() {} } });
      return fields.get(selector);
    },
    querySelectorAll() { return []; },
  };
  const context = vm.createContext({ document, TextEncoder, TextDecoder, console });
  const run = (code) => vm.runInContext(code, context);
  run(source.replace(bootstrap, ""));
  run(`
    setBusy = (busy) => { state.busy = busy; };
    showToast = (message) => { globalThis.lastToast = message; };
    renderAll = renderFileList = renderPreview = renderComparison = updateCounts = () => {};
    updateDisplayBounds = markViewerDirty = setWorkflowStage = resetCamera = () => {};
    validateRemodelForm = () => "";
    refreshGroups = async () => {};
    analysisFromResponse = (result) => ({ morphology: result.morphology, statistics: result.statistics });
    $("#shollStep").value = "20";
    $("#who").value = "all_terminal"; $("#action").value = "none";
    $("#extentUnit").value = $("#radiusUnit").value = "percent";
    function fixture(name = "cell.swc", samples = 4) {
      const file = createFile(name, "original " + name);
      Object.assign(file, { analysis: { morphology: { counts: { samples } }, statistics: {} }, analysisId: name, analysisStep: 20, status: "ready" });
      return file;
    }
    function previewFor(file, samples = 4) {
      return { fileId: file.id, sourceContent: file.content, name: "cell_remodeled.swc", content: "exact preview bytes\\n", analysis: { morphology: { counts: { samples } }, statistics: {} }, analysisId: "preview-id", elapsed: 1, label: "Edit", targets: [2], options: { seed: "17" } };
    }
  `);
  return { run, fields };
}

test("CSV formulas are quoted as text without changing numeric measurements", () => {
  const { run } = runtime();
  assert.equal(run('csvCell("=1+1")'), "'=1+1");
  assert.equal(run('csvCell("  @SUM(A1)")'), "'  @SUM(A1)");
  assert.equal(run('csvCell("-12")'), "'-12");
  assert.equal(run("csvCell(-12)"), "-12");
  assert.equal(run('csvCell(\'a,"b"\')'), '"a,""b"""');
});

test("duplicate and export suffixes preserve valid Unicode filenames", () => {
  const { run } = runtime();
  run('const longName = "é".repeat(118) + ".swc"; state.files = [fixture(longName)];');
  assert.ok(run('new TextEncoder().encode(uniqueFileName(longName)).length <= 240'));
  assert.ok(run('uniqueFileName(longName).endsWith(" (2).swc")'));
  assert.ok(run('new TextEncoder().encode(exportFileName(longName, "_statistics.json")).length <= 240'));
  assert.equal(run('state.files[0].name'), "é".repeat(118) + ".swc");
  for (const name of ["../cell.swc", "x\ny.swc", "x\u2028y.swc", "a".repeat(241)]) {
    assert.throws(() => run(`safeFileName(${JSON.stringify(name)})`), /plain filename/);
  }
});

test("numeric form values reach the server without binary64 coercion", () => {
  const { run } = runtime();
  run('$("#radiusChange").value = "1e-999"; $("#seed").value = "1.0000000000000001";');
  assert.equal(run("remodelOptions().radius_change"), "1e-999");
  assert.equal(run("remodelOptions().seed"), "1.0000000000000001");
});

test("apply uses the exact preview and undo restores the exact prior state", async () => {
  const { run } = runtime();
  run('const file = fixture(); state.files = [file]; state.activeId = file.id; const originalAnalysis = file.analysis; state.preview = previewFor(file); const previewAnalysis = state.preview.analysis;');
  await run("applyPreview()");
  assert.equal(run("file.content"), "exact preview bytes\n");
  assert.equal(run("file.analysis === previewAnalysis"), true);
  assert.equal(run("file.history.length"), 1);
  await run("undoEdit()");
  assert.equal(run("file.content"), "original cell.swc");
  assert.equal(run("file.name"), "cell.swc");
  assert.equal(run("file.analysis === originalAnalysis"), true);
  assert.equal(run("file.history.length"), 0);
});

test("capacity refusal cannot mutate the file, discard preview, or consume undo", async () => {
  const { run } = runtime();
  run('state.files = Array.from({length: 5}, (_, i) => fixture(i + ".swc", 50000)); const file = state.files[0]; state.activeId = file.id; state.preview = previewFor(file, 50000);');
  assert.throws(() => run("checkWorkspaceCapacity()"), /250,000/);
  await run("applyPreview()");
  assert.equal(run("file.history.length"), 0);
  assert.equal(run("file.content === file.originalContent"), true);
  assert.equal(run("state.preview !== null"), true);
  assert.match(run("lastToast"), /250,000/);
});

test("an invalid preview filename fails before any history or file mutation", async () => {
  const { run } = runtime();
  run('const file = fixture(); state.files = [file]; state.activeId = file.id; state.preview = previewFor(file); state.preview.name = "a".repeat(250);');
  await run("applyPreview()");
  await run("applyPreview()");
  assert.equal(run("file.history.length"), 0);
  assert.equal(run("file.content === file.originalContent"), true);
});

test("atomic reanalysis capacity failure retains every old result and resets busy", async () => {
  const { run } = runtime();
  run(`
    state.files = Array.from({length: 5}, (_, i) => fixture(i + ".swc", 50000));
    const originals = state.files.map(file => file.analysis);
    $("#shollStep").value = "10";
    api = async () => ({ files: [{ morphology: { counts: { samples: 60000 } }, statistics: {}, analysis_id: "new" }] });
  `);
  assert.equal(await run("analyzeFiles(state.files, { atomic: true })"), false);
  assert.equal(run("state.busy"), false);
  assert.equal(run("state.shollStep"), 20);
  assert.equal(run('$("#shollStep").value'), "20");
  assert.equal(run("state.files.every((file, i) => file.analysis === originals[i] && file.status === 'ready')"), true);
});

test("a stale asynchronous preview never replaces the active morphology", async () => {
  const { run } = runtime();
  run('const file = fixture(); state.files = [file]; state.activeId = file.id; api = () => new Promise(resolve => { globalThis.resolvePreview = resolve; });');
  const pending = run("generatePreview({ preventDefault() {} })");
  run('file.content = "changed while awaiting response"; resolvePreview({ name: "cell_remodeled.swc" });');
  await pending;
  assert.equal(run("state.preview"), null);
  assert.equal(run("state.busy"), false);
  assert.equal(run("file.content"), "changed while awaiting response");
});
