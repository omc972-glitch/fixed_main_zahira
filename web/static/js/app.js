import { ZahiraController } from "./zahira.js";
import { renderFrame } from "./plotter.js";

const viewMenu = document.getElementById("view-menu");
const viewExp = document.getElementById("view-experiment");
const btnBack = document.getElementById("btn-back");
const btnTheme = document.getElementById("btn-theme");
const btnStart = document.getElementById("btn-start");
const btnPause = document.getElementById("btn-pause");
const btnReset = document.getElementById("btn-reset");
const speedSelect = document.getElementById("speed-select");
const progressBar = document.getElementById("progress-bar");
const progressText = document.getElementById("progress-text");
const toast = document.getElementById("error-toast");

const zahira = new ZahiraController(document.getElementById("zahira-panel"));

let currentExp = null;
let currentParams = {};
let simData = null;
let frameIdx = 0;
let animTimer = null;
let isPaused = false;

function isDark() {
  return document.documentElement.getAttribute("data-theme") === "dark";
}

function showToast(msg) {
  toast.textContent = msg;
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 4000);
}

btnTheme.addEventListener("click", () => {
  const next = isDark() ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  btnTheme.textContent = next === "dark" ? "☀️ Açık Tema" : "🌙 Koyu Tema";
  if (simData && simData.frames[frameIdx]) {
    renderFrame("plot-container", simData.frames[frameIdx], isDark());
  }
});

btnBack.addEventListener("click", () => {
  stopAnim();
  zahira.clear();
  viewExp.classList.add("hidden");
  viewMenu.classList.remove("hidden");
  btnBack.classList.add("hidden");
});

async function loadMenu() {
  const res = await fetch("/api/experiments");
  const list = await res.json();
  viewMenu.innerHTML = "";
  for (const item of list) {
    const card = document.createElement("div");
    card.className = "exp-card";
    card.style.background = item.accent;
    card.innerHTML = `
      <div class="exp-card-icon">${item.icon}</div>
      <div class="exp-card-title">${item.title}</div>
      <div class="exp-card-sub">${item.subtitle}</div>
    `;
    card.addEventListener("click", () => openExperiment(item.id));
    viewMenu.appendChild(card);
  }
}

async function openExperiment(expId) {
  stopAnim();
  const res = await fetch(`/api/experiments/${expId}`);
  currentExp = await res.json();
  currentParams = {};

  document.documentElement.style.setProperty("--accent", currentExp.accent);
  document.getElementById("exp-header").style.background = currentExp.accent;
  document.getElementById("exp-title").textContent = `${currentExp.icon} ${currentExp.title}`;
  document.getElementById("exp-subtitle").textContent = currentExp.subtitle;
  document.getElementById("results-content").innerHTML =
    "<p><i>Parametreleri ayarlayın ve <b>Simülasyonu Başlat</b> düğmesine basın.</i></p>";

  buildParams(currentExp.parameters);
  zahira.configure(currentExp.zahira.sprites);
  zahira.say(currentExp.zahira.intro, true);

  viewMenu.classList.add("hidden");
  viewExp.classList.remove("hidden");
  btnBack.classList.remove("hidden");
  Plotly.purge("plot-container");
  setProgress(0);
}

function buildParams(params) {
  const grid = document.getElementById("params-grid");
  grid.innerHTML = "";
  for (const p of params) {
    currentParams[p.key] = p.value;
    const wrap = document.createElement("div");
    wrap.className = "param-item";

    if (p.type === "select") {
      wrap.innerHTML = `<label class="param-header"><span>${p.label}</span></label>`;
      const sel = document.createElement("select");
      for (const opt of p.options) {
        const o = document.createElement("option");
        o.value = opt.value ?? opt;
        o.textContent = opt.label ?? opt;
        if (o.value == p.value) o.selected = true;
        sel.appendChild(o);
      }
      sel.addEventListener("change", () => (currentParams[p.key] = sel.value));
      wrap.appendChild(sel);
    } else if (p.type === "checkbox") {
      wrap.innerHTML = `<label><input type="checkbox" ${p.value ? "checked" : ""}/> ${p.label}</label>`;
      const cb = wrap.querySelector("input");
      cb.addEventListener("change", () => (currentParams[p.key] = cb.checked));
    } else {
      const unit = p.unit ? ` ${p.unit}` : "";
      wrap.innerHTML = `
        <div class="param-header"><span>${p.label}</span><span id="val-${p.key}">${p.value}${unit}</span></div>
        <input type="range" min="${p.min}" max="${p.max}" step="${p.step || 1}" value="${p.value}" />
      `;
      const inp = wrap.querySelector("input");
      const valEl = wrap.querySelector(`#val-${p.key}`);
      inp.addEventListener("input", () => {
        const v = p.type === "int" ? parseInt(inp.value, 10) : parseFloat(inp.value);
        currentParams[p.key] = v;
        valEl.textContent = `${v}${unit}`;
      });
    }
    grid.appendChild(wrap);
  }
}

function setProgress(pct) {
  const p = Math.max(0, Math.min(100, Math.round(pct)));
  progressBar.style.width = `${p}%`;
  progressText.textContent = `${p}%`;
}

function stopAnim() {
  clearInterval(animTimer);
  animTimer = null;
  isPaused = false;
  btnPause.disabled = true;
  btnPause.textContent = "⏸ Duraklat";
}

btnStart.addEventListener("click", async () => {
  if (!currentExp) return;
  stopAnim();
  try {
    const res = await fetch(`/api/experiments/${currentExp.id}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ params: currentParams }),
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.detail || "Parametre hatası");
      return;
    }
    simData = data;
    frameIdx = 0;
    btnPause.disabled = false;
    if (simData.start_lines) zahira.say(simData.start_lines, true);
    startLoop();
  } catch (err) {
    showToast("Sunucuya bağlanılamadı.");
  }
});

function startLoop() {
  const delay = parseInt(speedSelect.value, 10);
  clearInterval(animTimer);
  animTimer = setInterval(() => {
    if (!simData || frameIdx >= simData.frames.length) {
      stopAnim();
      if (simData) {
        document.getElementById("results-content").innerHTML = simData.results_html;
        if (simData.finish_lines) zahira.say(simData.finish_lines, false);
      }
      return;
    }
    renderFrame("plot-container", simData.frames[frameIdx], isDark());
    const evs = (simData.events || []).filter((e) => e.frame === frameIdx);
    for (const ev of evs) zahira.say(ev.lines, false);
    setProgress(((frameIdx + 1) / simData.frames.length) * 100);
    frameIdx++;
  }, delay);
}

speedSelect.addEventListener("change", () => {
  if (animTimer && !isPaused) startLoop();
});

btnPause.addEventListener("click", () => {
  if (!simData) return;
  if (!isPaused) {
    clearInterval(animTimer);
    isPaused = true;
    btnPause.textContent = "▶ Devam Et";
  } else {
    isPaused = false;
    btnPause.textContent = "⏸ Duraklat";
    startLoop();
  }
});

btnReset.addEventListener("click", () => {
  stopAnim();
  simData = null;
  frameIdx = 0;
  setProgress(0);
  Plotly.purge("plot-container");
  document.getElementById("results-content").innerHTML =
    "<p><i>Parametreleri ayarlayın ve <b>Simülasyonu Başlat</b> düğmesine basın.</i></p>";
  if (currentExp) zahira.say(currentExp.zahira.intro, true);
});

loadMenu();
