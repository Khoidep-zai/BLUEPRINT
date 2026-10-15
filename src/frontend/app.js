/* Photo AI Tool — frontend logic.
   Flow: GET /api/recipes -> pick function -> upload image -> POST /api/jobs
   -> render result + QA report. No login, no build step. */
"use strict";

const API = { recipes: "/api/recipes", jobs: "/api/jobs", health: "/healthz" };

const METRIC_LABELS = {
  ear: "Độ mở mắt (EAR)",
  identity_cosine: "Giữ danh tính",
  outside_mask_ssim: "SSIM ngoài vùng sửa",
  structure_similarity: "Tương đồng cấu trúc",
  clip_ratio: "Tỷ lệ cháy sáng",
  delta_e_skin: "Lệch màu da (ΔE)",
  texture_variance: "Độ chi tiết da",
  ocr_recheck: "Không còn chữ/watermark",
  person_recheck: "Không còn người trong vùng xóa",
};

const state = { recipes: [], selected: null, file: null, running: false, beforeUrl: null };

const $ = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", init);

async function init() {
  bindEvents();
  await Promise.all([loadRecipes(), checkHealth()]);
  loadHistory();
}

function bindEvents() {
  $("file-input").addEventListener("change", (event) => {
    const file = event.target.files && event.target.files[0];
    if (file) setFile(file);
  });

  const dropzone = $("dropzone");
  ["dragenter", "dragover"].forEach((type) =>
    dropzone.addEventListener(type, (event) => {
      event.preventDefault();
      dropzone.classList.add("is-drag");
    })
  );
  ["dragleave", "drop"].forEach((type) =>
    dropzone.addEventListener(type, (event) => {
      event.preventDefault();
      dropzone.classList.remove("is-drag");
    })
  );
  dropzone.addEventListener("drop", (event) => {
    const file = event.dataTransfer && event.dataTransfer.files[0];
    if (file) setFile(file);
  });
  dropzone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") $("file-input").click();
  });

  $("strength-range").addEventListener("input", (event) => {
    $("strength-value").textContent = Number(event.target.value).toFixed(2);
  });
  $("ownership-check").addEventListener("change", updateRunButton);
  $("run-btn").addEventListener("click", run);
}

async function checkHealth() {
  const badge = $("server-status");
  try {
    const res = await fetch(API.health);
    if (!res.ok) throw new Error();
    badge.textContent = "Máy chủ sẵn sàng";
    badge.classList.add("is-ok");
  } catch {
    badge.textContent = "Không kết nối được máy chủ";
    badge.classList.add("is-off");
  }
}

async function loadRecipes() {
  try {
    const res = await fetch(API.recipes);
    if (!res.ok) throw new Error();
    const data = await res.json();
    state.recipes = data.recipes || [];
    renderRecipes();
  } catch {
    setStatus("Không tải được danh sách chức năng.", true);
  }
}

function renderRecipes() {
  const grid = $("function-grid");
  grid.replaceChildren();
  for (const recipe of state.recipes) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "fn-card";
    card.setAttribute("role", "option");
    card.setAttribute("aria-selected", "false");
    card.dataset.id = recipe.id;

    const name = document.createElement("span");
    name.className = "fn-card__name";
    name.textContent = recipe.name_vi || recipe.id;
    const en = document.createElement("span");
    en.className = "fn-card__en";
    en.textContent = recipe.name_en || recipe.id;
    card.append(name, en);

    if (recipe.requires_ownership) {
      const flag = document.createElement("span");
      flag.className = "fn-card__flag";
      flag.textContent = "Cần xác nhận sở hữu";
      card.append(flag);
    }
    card.addEventListener("click", () => selectRecipe(recipe.id));
    grid.append(card);
  }
  if (state.recipes.length) selectRecipe(state.recipes[0].id);
}

function selectRecipe(id) {
  state.selected = state.recipes.find((recipe) => recipe.id === id) || null;
  document.querySelectorAll(".fn-card").forEach((card) => {
    card.setAttribute("aria-selected", String(card.dataset.id === id));
  });
  const needsOwnership = Boolean(state.selected && state.selected.requires_ownership);
  $("ownership-field").hidden = !needsOwnership;
  if (!needsOwnership) $("ownership-check").checked = false;
  updateRunButton();
}

function setFile(file) {
  if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
    setStatus("Chỉ hỗ trợ JPEG, PNG hoặc WebP.", true);
    return;
  }
  if (file.size > 20 * 1024 * 1024) {
    setStatus("Ảnh vượt quá 20 MB.", true);
    return;
  }
  state.file = file;
  if (state.beforeUrl) URL.revokeObjectURL(state.beforeUrl);
  state.beforeUrl = URL.createObjectURL(file);
  const preview = $("input-preview");
  preview.src = state.beforeUrl;
  preview.hidden = false;
  $("dropzone-hint").hidden = true;
  setStatus("");
  updateRunButton();
}

function updateRunButton() {
  const needsOwnership = Boolean(state.selected && state.selected.requires_ownership);
  const ready =
    !state.running &&
    Boolean(state.selected) &&
    Boolean(state.file) &&
    (!needsOwnership || $("ownership-check").checked);
  $("run-btn").disabled = !ready;
}

function setStatus(message, isError = false) {
  const line = $("status-line");
  line.textContent = message || "";
  line.classList.toggle("is-error", Boolean(isError));
}

function setRunning(running) {
  state.running = running;
  $("run-spinner").hidden = !running;
  $("run-label").textContent = running ? "Đang xử lý…" : "Xử lý ảnh";
  updateRunButton();
}

async function run() {
  if (!state.file || !state.selected) return;
  setRunning(true);
  setStatus("Đang xử lý ảnh…");
  try {
    const form = new FormData();
    form.append("file", state.file);
    form.append("recipe_id", state.selected.id);
    form.append("params", JSON.stringify({ strength: Number($("strength-range").value) }));
    form.append("ownership_confirmed", String($("ownership-check").checked));

    const res = await fetch(API.jobs, { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) {
      setStatus(data.error ? `${data.error.message} (${data.error.code})` : "Xử lý thất bại.", true);
      return;
    }
    setStatus("Hoàn tất.");
    renderResult(data);
    loadHistory();
  } catch {
    setStatus("Không kết nối được máy chủ.", true);
  } finally {
    setRunning(false);
  }
}

function renderResult(job) {
  $("result-empty").hidden = true;
  $("result-body").hidden = false;

  const recipe = state.recipes.find((item) => item.id === job.recipe_id);
  $("result-title").textContent = recipe ? `${recipe.name_vi} — ${job.status}` : job.recipe_id;

  if (state.beforeUrl) $("before-img").src = state.beforeUrl;
  else $("before-img").removeAttribute("src");

  const after = $("after-img");
  after.src = job.result_url ? `${job.result_url}?t=${Date.now()}` : "";

  $("download-link").href = job.result_url || "#";

  renderQa(job.qa_report, job);
}

function renderQa(report, job) {
  const badge = $("qa-badge");
  const table = $("qa-table").querySelector("tbody");
  const warnings = $("qa-warnings");
  table.replaceChildren();
  warnings.replaceChildren();

  if (!report) {
    badge.textContent = "Không có báo cáo QA";
    badge.className = "qa-badge is-fail";
    return;
  }

  if (report.passed) {
    badge.textContent = "✓ Đạt mọi kiểm tra chất lượng";
    badge.className = "qa-badge is-pass";
  } else {
    badge.textContent = "⚠ Kết quả tốt nhất có thể — có kiểm tra chưa đạt";
    badge.className = "qa-badge is-warn";
  }

  const thresholds = report.thresholds || {};
  const metricKeys = Object.keys(report.metrics || {});
  const booleanKeys = ["ocr_recheck", "person_recheck"].filter((key) => key in thresholds);

  for (const key of metricKeys) {
    const value = report.metrics[key];
    const minKey = `${key}_min`;
    const maxKey = `${key}_max`;
    let direction = null;
    let threshold = null;
    if (key in thresholds && typeof thresholds[key] === "boolean") {
      direction = "bool";
    } else if (minKey in thresholds) {
      direction = "min";
      threshold = thresholds[minKey];
    } else if (maxKey in thresholds) {
      direction = "max";
      threshold = thresholds[maxKey];
    } else if (booleanKeys.includes(key)) {
      direction = "bool";
    }

    let passed = null;
    if (direction === "min") passed = Number(value) >= Number(threshold);
    else if (direction === "max") passed = Number(value) <= Number(threshold);
    else if (direction === "bool") passed = Boolean(value);

    table.append(qaRow(key, value, direction, threshold, passed));
  }

  for (const key of booleanKeys) {
    if (key in (report.metrics || {})) continue;
    table.append(qaRow(key, "—", "bool", true, null));
  }

  const list = (job.warnings || []).filter(Boolean);
  for (const warning of list) {
    const item = document.createElement("li");
    item.textContent = warning;
    warnings.append(item);
  }
}

function qaRow(key, value, direction, threshold, passed) {
  const row = document.createElement("tr");
  const name = document.createElement("td");
  name.textContent = METRIC_LABELS[key] || key;

  const shown = document.createElement("td");
  shown.className = "num";
  shown.textContent = formatValue(key, value);

  const limit = document.createElement("td");
  limit.className = "num";
  if (direction === "min") limit.textContent = `≥ ${threshold}`;
  else if (direction === "max") limit.textContent = `≤ ${threshold}`;
  else if (direction === "bool") limit.textContent = "bắt buộc";
  else limit.textContent = "—";

  const verdict = document.createElement("td");
  if (passed === null) {
    verdict.textContent = "—";
  } else {
    const chip = document.createElement("span");
    chip.className = passed ? "chip is-pass" : "chip is-fail";
    chip.textContent = passed ? "Đạt" : "Chưa đạt";
    verdict.append(chip);
  }

  row.append(name, shown, limit, verdict);
  return row;
}

function formatValue(key, value) {
  if (typeof value !== "number") return String(value);
  if (key === "clip_ratio") return `${(value * 100).toFixed(2)}%`;
  if (Math.abs(value) < 10) return value.toFixed(4);
  return value.toFixed(2);
}

async function loadHistory() {
  try {
    const res = await fetch(`${API.jobs}?limit=8`);
    if (!res.ok) return;
    const data = await res.json();
    const jobs = data.jobs || [];
    const block = $("history-block");
    const list = $("history-list");
    list.replaceChildren();
    block.hidden = jobs.length === 0;

    for (const job of jobs) {
      const item = document.createElement("li");
      const meta = document.createElement("span");
      meta.className = "hist-meta";
      const recipe = state.recipes.find((entry) => entry.id === job.recipe_id);
      meta.textContent = `${recipe ? recipe.name_vi : job.recipe_id} · ${job.status}${
        job.qa_report && !job.qa_report.passed ? " · QA chưa đạt" : ""
      }`;
      const view = document.createElement("button");
      view.type = "button";
      view.textContent = "Xem lại";
      view.addEventListener("click", () => renderResult(job));
      item.append(meta, view);
      list.append(item);
    }
  } catch {
    /* history is best-effort */
  }
}
