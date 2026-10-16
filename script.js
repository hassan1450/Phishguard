const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const sleep = (ms) => new Promise((res) => setTimeout(res, ms));
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

function countUp(el, to, decimals = 0, ms = 1200) {
  const start = performance.now();
  function tick(now) {
    const t = Math.min((now - start) / ms, 1);
    const eased = 1 - Math.pow(1 - t, 3);
    const v = to * eased;
    el.textContent = decimals ? v.toFixed(decimals) : Math.round(v).toLocaleString();
    if (t < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/* ---------- Tabs ---------- */
$$('.tab').forEach((btn) =>
  btn.addEventListener('click', () => {
    $$('.tab').forEach((b) => b.classList.remove('active'));
    $$('.panel').forEach((p) => p.classList.remove('active'));
    btn.classList.add('active');
    $('#' + btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'models') loadModels();
  })
);

/* ---------- Banner ---------- */
(async function checkStatus() {
  try {
    const m = await (await fetch('/api/metrics')).json();
    const b = $('#banner');
    if (!m.ready) {
      b.innerHTML = 'No trained model found. Run <b>python train.py</b> in your terminal, then restart the app.';
      b.classList.add('show');
    } else if (m.mode !== 'url') {
      b.textContent = 'Your dataset has no URL column, so live URL scanning is disabled. The Model Lab still works.';
      b.classList.add('show');
    }
  } catch (e) { /* ignore */ }
})();

/* ---------- Scanner ---------- */
async function scan(url) {
  const card = $('#scanCard'), btn = $('#scanBtn'), res = $('#result'), err = $('#error');
  err.textContent = '';
  res.classList.remove('show');
  if (!url.trim()) { err.textContent = 'Please enter a URL.'; return; }
  card.classList.add('scanning');
  btn.disabled = true;
  $('span', btn).textContent = 'Scanning…';
  try {
    const [r] = await Promise.all([
      fetch('/api/predict', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }) }),
      sleep(1100),
    ]);
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || 'Request failed');
    showResult(data);
  } catch (e) {
    err.textContent = e.message;
  } finally {
    card.classList.remove('scanning');
    btn.disabled = false;
    $('span', btn).textContent = 'Scan URL';
  }
}

function showResult(d) {
  const res = $('#result'), fg = $('#gFg');
  res.className = 'card result show ' + d.level;
  fg.style.strokeDashoffset = 440;
  void fg.getBoundingClientRect();
  requestAnimationFrame(() => { fg.style.strokeDashoffset = 440 * (1 - d.risk / 100); });
  countUp($('#riskNum'), d.risk, 1, 1500);
  $('#verdict').textContent = d.verdict;
  $('#rUrl').textContent = d.url;
  $('#modelChips').innerHTML = Object.entries(d.models).map(([name, m]) =>
    `<div class="mchip ${esc(m.label)}">${esc(name)}${name === d.best ? ' ★' : ''}<b>${esc(m.label)} · ${m.risk}%</b></div>`).join('');
  $('#signals').innerHTML = d.signals.map((s, i) =>
    `<li class="${esc(s.level)}" style="animation-delay:${0.15 * i + 0.4}s">${esc(s.text)}</li>`).join('');
  res.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

$('#scanBtn').addEventListener('click', () => scan($('#urlInput').value));
$('#urlInput').addEventListener('keydown', (e) => { if (e.key === 'Enter') scan(e.target.value); });
$$('.chip').forEach((c) => c.addEventListener('click', () => { $('#urlInput').value = c.dataset.url; scan(c.dataset.url); }));

/* ---------- Model Lab ---------- */
const pct = (v) => (v * 100).toFixed(2);

function renderModels(m) {
  const stats = `<div class="stats">
    <div class="card stat"><b data-count="${m.rows}">0</b><span>Samples used</span></div>
    <div class="card stat"><b data-count="${m.phishing}">0</b><span>Phishing</span></div>
    <div class="card stat"><b data-count="${m.legitimate}">0</b><span>Legitimate</span></div>
    <div class="card stat"><b data-count="${m.n_features}">0</b><span>Features</span></div></div>`;

  const cards = Object.entries(m.models).map(([name, r], i) => {
    const bars = [['Accuracy', r.accuracy], ['Precision', r.precision], ['Recall', r.recall], ['F1-score', r.f1]].map(([l, v]) =>
      `<div class="bar"><label>${l}<em>${pct(v)}%</em></label><div class="track"><i data-w="${pct(v)}"></i></div></div>`).join('');
    const c = r.confusion;
    return `<div class="card mcard" style="animation-delay:${i * 0.15}s">
      ${name === m.best ? '<span class="best">★ Best (F1)</span>' : ''}
      <h3>${esc(name)}</h3>${bars}
      <div class="cm">
        <div class="c tn">TN<b>${c.tn.toLocaleString()}</b></div><div class="c fp">FP<b>${c.fp.toLocaleString()}</b></div>
        <div class="c fn">FN<b>${c.fn.toLocaleString()}</b></div><div class="c tp">TP<b>${c.tp.toLocaleString()}</b></div>
      </div></div>`;
  }).join('');

  const maxImp = Math.max(...m.importances.map((x) => x.importance), 1e-9);
  const imps = `<h3 class="section-title">Top features (Random Forest importance)</h3><div class="card">` +
    m.importances.map((x) => `<div class="bar"><label>${esc(x.feature)}<em>${(x.importance * 100).toFixed(1)}%</em></label>
      <div class="track"><i data-w="${(x.importance / maxImp * 100).toFixed(1)}"></i></div></div>`).join('') + '</div>';

  let dom = '';
  if (m.domain_split) {
    dom = `<h3 class="section-title">Generalization: random split vs. unseen domains</h3><div class="card"><table>
      <tr><th>Model</th><th>F1 (random)</th><th>F1 (unseen domains)</th><th>Change</th></tr>` +
      Object.keys(m.models).map((n) => {
        const a = m.models[n].f1, b = m.domain_split[n] ? m.domain_split[n].f1 : null;
        if (b === null) return '';
        const d = (b - a) * 100;
        return `<tr><td>${esc(n)}</td><td>${pct(a)}%</td><td>${pct(b)}%</td><td class="${d < 0 ? 'neg' : 'pos'}">${d.toFixed(2)} pts</td></tr>`;
      }).join('') + '</table></div>';
  }
  return stats + `<div class="mgrid">${cards}</div>` + imps + dom +
    `<p class="disclaimer" style="margin-top:18px;text-align:center">Dataset: ${esc(m.dataset)} · TN/FP/FN/TP: phishing is the positive class.</p>`;
}

async function loadModels() {
  const root = $('#modelsRoot');
  if (root.dataset.loaded === '1') return;
  root.innerHTML = '<div class="loader"></div>';
  try {
    const m = await (await fetch('/api/metrics')).json();
    if (!m.ready) {
      root.innerHTML = '<div class="card empty">No trained model yet.<br>Run <code>python train.py</code>, then restart <code>python app.py</code>.</div>';
      return;
    }
    root.innerHTML = renderModels(m);
    root.dataset.loaded = '1';
    $$('[data-count]', root).forEach((el) => countUp(el, Number(el.dataset.count), 0));
    setTimeout(() => $$('.track i', root).forEach((el) => { el.style.width = el.dataset.w + '%'; }), 80);
  } catch (e) {
    root.innerHTML = '<div class="card empty">Could not load metrics.</div>';
  }
}