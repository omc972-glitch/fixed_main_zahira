const KEY = "lab-layout-v2";
const root = document.documentElement;
const DEFAULTS = { "--col-left": 380, "--col-right": 300, "--bottom-h": 190, "--sprite-h": null };
let saved = {};
try { saved = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}

function apply(name, px) {
  if (px == null) { root.style.removeProperty(name); delete saved[name]; return; }
  root.style.setProperty(name, px + "px");
  saved[name] = px;
}
function persist() {
  try { localStorage.setItem(KEY, JSON.stringify(saved)); } catch (e) {}
}
function replot() {
  const el = document.getElementById("plot-container");
  if (el && window.Plotly && el.data) { try { Plotly.Plots.resize(el); } catch (e) {} }
}
let raf = 0;
function replotSoon() {
  if (raf) return;
  raf = requestAnimationFrame(() => { raf = 0; replot(); });
}
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

for (const k of Object.keys(DEFAULTS)) apply(k, saved[k] !== undefined ? saved[k] : DEFAULTS[k]);

// Zahira içindeki konuşma / sprite ayırıcısını ekle
function ensureInnerHandle() {
  const panel = document.getElementById("zahira-panel");
  if (!panel || panel.querySelector(".resizer-inner")) return;
  const stage = panel.querySelector(".zahira-stage");
  if (!stage) return;
  const h = document.createElement("div");
  h.className = "resizer resizer-h resizer-inner";
  h.dataset.var = "--sprite-h";
  h.dataset.edge = "sprite";
  h.title = "Sürükle (çift tık: sıfırla)";
  panel.insertBefore(h, stage);
  bind(h);
}

function limits(edge) {
  const ws = document.querySelector(".exp-workspace");
  const lay = document.getElementById("view-experiment");
  const panel = document.getElementById("zahira-panel");
  const W = ws.getBoundingClientRect(), L = lay.getBoundingClientRect(), P = panel.getBoundingClientRect();
  return { W, L, P };
}

function onMove(edge, e) {
  const { W, L, P } = limits(edge);
  if (edge === "left")   apply("--col-left",  clamp(e.clientX - W.left, 220, W.width * 0.6));
  if (edge === "right")  apply("--col-right", clamp(W.right - e.clientX, 200, W.width * 0.5));
  if (edge === "bottom") apply("--bottom-h",  clamp(L.bottom - 12 - e.clientY, 90, L.height * 0.65));
  if (edge === "sprite") apply("--sprite-h",  clamp(P.bottom - 10 - e.clientY, 90, P.height - 140));
  replotSoon();
}

function bind(h) {
  const edge = h.dataset.edge, name = h.dataset.var;
  h.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    h.setPointerCapture(e.pointerId);
    h.classList.add("active");
    document.body.classList.add("resizing", edge === "left" || edge === "right" ? "rs-col" : "rs-row");
    const move = (ev) => onMove(edge, ev);
    const up = () => {
      h.classList.remove("active");
      document.body.classList.remove("resizing", "rs-col", "rs-row");
      h.removeEventListener("pointermove", move);
      h.removeEventListener("pointerup", up);
      h.removeEventListener("pointercancel", up);
      persist(); replot();
    };
    h.addEventListener("pointermove", move);
    h.addEventListener("pointerup", up);
    h.addEventListener("pointercancel", up);
  });
  h.addEventListener("dblclick", () => { apply(name, DEFAULTS[name]); persist(); replotSoon(); });
}

document.querySelectorAll(".resizer").forEach(bind);
ensureInnerHandle();
new MutationObserver(ensureInnerHandle).observe(document.getElementById("zahira-panel") || document.body, { childList: true });

// Üst çubuğa sıfırlama düğmesi
const top = document.querySelector(".topbar");
if (top && !document.getElementById("btn-layout-reset")) {
  const b = document.createElement("button");
  b.id = "btn-layout-reset"; b.className = "btn-ghost"; b.textContent = "⟲ Düzeni Sıfırla";
  b.addEventListener("click", () => {
    for (const k of Object.keys(DEFAULTS)) apply(k, DEFAULTS[k]);
    persist(); replotSoon();
  });
  const theme = document.getElementById("btn-theme");
  theme ? theme.parentNode.insertBefore(b, theme) : top.appendChild(b);
}
window.addEventListener("resize", replotSoon);
