export class ZahiraController {
  constructor(container) {
    this.container = container;
    this.TYPE_MS = 14;        // harf başına yazma süresi
    this.MIN_HOLD = 1400;     // bir satırın en az bekleme süresi
    this.PER_CHAR = 28;       // okuma süresi: karakter başına ms
    this.MAX_HOLD = 5500;
    this.MAX_QUEUE = 30;
    this.MAX_LOG = 40;
    this.sprites = {};
    this.queue = [];
    this.timer = null;
    this.holdTimer = null;
    this.isTyping = false;

    this.container.innerHTML = `
      <div class="zahira-name">🧑‍🔬 Zahira</div>
      <div class="zahira-log" id="zahira-log"></div>
      <div class="zahira-stage"><img class="zahira-sprite" id="zahira-img" alt="Zahira" /></div>
    `;
    this.logEl = this.container.querySelector("#zahira-log");
    this.imgEl = this.container.querySelector("#zahira-img");
  }

  configure(sprites) {
    this.sprites = sprites || {};
    this.setSprite("idle");
  }

  setSprite(key) {
    const file = this.sprites[key] || this.sprites["idle"] || "zahira_idle.png";
    this.imgEl.src = `/assets/zahira/${file}`;
  }

  say(lines, interrupt = false) {
    if (!lines || !lines.length) return;
    if (interrupt) this.clear();
    for (const line of lines) {
      if (this.queue.length >= this.MAX_QUEUE) this.queue.shift();
      this.queue.push(line);
    }
    if (!this.isTyping) this._next();
  }

  clear() {
    clearInterval(this.timer);
    clearTimeout(this.holdTimer);
    this.queue = [];
    this.isTyping = false;
    this.logEl.innerHTML = "";
  }

  _scroll() {
    this.logEl.scrollTop = this.logEl.scrollHeight;
  }

  _next() {
    if (!this.queue.length) {
      this.isTyping = false;
      return;
    }
    this.isTyping = true;
    const { sprite, text } = this.queue.shift();
    this.setSprite(sprite);

    // eski mesajları soluklaştır, yenisini ekle
    for (const old of this.logEl.querySelectorAll(".zahira-msg.current")) old.classList.remove("current");
    const msg = document.createElement("div");
    msg.className = "zahira-msg current";
    this.logEl.appendChild(msg);
    while (this.logEl.children.length > this.MAX_LOG) this.logEl.removeChild(this.logEl.firstChild);

    let idx = 0;
    clearInterval(this.timer);
    this.timer = setInterval(() => {
      idx++;
      msg.textContent = text.slice(0, idx);
      this._scroll();
      if (idx >= text.length) {
        clearInterval(this.timer);
        // sırada çok satır birikmişse beklemeyi kısalt, yoksa rahat okunsun
        let hold = Math.min(this.MAX_HOLD, Math.max(this.MIN_HOLD, text.length * this.PER_CHAR));
        if (this.queue.length > 3) hold = 500;
        this.holdTimer = setTimeout(() => this._next(), hold);
      }
    }, this.TYPE_MS);
  }
}
