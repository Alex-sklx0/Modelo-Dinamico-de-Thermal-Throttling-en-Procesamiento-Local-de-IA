/**
 * Thermal Throttling ODE Model — Interactive p5.js Simulation
 * ===========================================================
 *
 * Paste en https://editor.p5js.org/ → Play.
 *
 * Tres paneles (T, R, P) en tiempo real.  8 deslizadores para
 * controlar todos los parámetros del modelo.
 *
 * Control automático: cuando T > 80 °C el ventilador acelera
 * (k₂ efectivo sube).  Si T ≥ 100 °C → EMERGENCY SHUTDOWN.
 */

// =====================================================================
// 1.  CONSTANTS & DEFAULTS
// =====================================================================
const P_MIN = 10;

const DEFAULTS = {
  k1: 0.052, k2: 0.10, gamma: 1.0, delta: 0.105,
  alpha: 1.6, beta: 12.0, k_sig: 0.5,
  T_amb: 25, T_crit: 90, R_obj: 1000, dt: 0.1,
};

// =====================================================================
// 2.  STATE
// =====================================================================
let p = {};
let s = { T: 45, R: 0, P: 15 };
let simTime = 0;
let running = true;
let shutdown = false;
const STEPS_PER_FRAME = 3;

let histTime = [], histT = [], histR = [], histP = [];
const TIME_WINDOW = 300;
const MAX_PTS = 12000;

// =====================================================================
// 3.  ODE
// =====================================================================
function deriv(st, k2val) {
  let sig = p.beta / (1 + Math.exp(-p.k_sig * (st.T - p.T_crit)));
  return {
    dT: p.k1 * st.P - k2val * (st.T - p.T_amb),
    dR: p.gamma * st.P - p.delta * st.R,
    dP: p.alpha * (p.R_obj - st.R) - sig,
  };
}

function rk4Step(st, h, k2val) {
  let k1 = deriv(st, k2val);
  let a2 = { T: st.T + 0.5 * h * k1.dT, R: st.R + 0.5 * h * k1.dR, P: st.P + 0.5 * h * k1.dP };
  let k2 = deriv(a2, k2val);
  let a3 = { T: st.T + 0.5 * h * k2.dT, R: st.R + 0.5 * h * k2.dR, P: st.P + 0.5 * h * k2.dP };
  let k3 = deriv(a3, k2val);
  let a4 = { T: st.T + h * k3.dT, R: st.R + h * k3.dR, P: st.P + h * k3.dP };
  let k4 = deriv(a4, k2val);
  return {
    T: st.T + (h / 6) * (k1.dT + 2 * k2.dT + 2 * k3.dT + k4.dT),
    R: st.R + (h / 6) * (k1.dR + 2 * k2.dR + 2 * k3.dR + k4.dR),
    P: Math.max(P_MIN, st.P + (h / 6) * (k1.dP + 2 * k2.dP + 2 * k3.dP + k4.dP)),
  };
}

function fanBoost(T) {
  if (T <= 80) return 1.0;
  if (T >= 100) return 4.0;
  return 1.0 + (T - 80) / 20 * 3.0;
}

function runSimulation() {
  if (shutdown) return;
  let eff_k2 = p.k2 * fanBoost(s.T);
  s = rk4Step(s, p.dt, eff_k2);
  simTime += p.dt;
  histTime.push(simTime);
  histT.push(s.T);
  histR.push(s.R);
  histP.push(s.P);
  if (histTime.length > MAX_PTS) {
    let trim = 2000;
    histTime.splice(0, trim); histT.splice(0, trim);
    histR.splice(0, trim); histP.splice(0, trim);
  }
  if (s.T >= 100) {
    shutdown = true;
    s.R = 0;
    s.P = P_MIN;
  }
}

// =====================================================================
// 4.  LAYOUT
// =====================================================================
const GW = 540, GH = 128, GX = 50, GAP = 10;
const INFO_X = 620, INFO_W = 290;
const SROW1_Y = 468, SROW2_Y = 528, BTN_Y = 590;

function graphY(i) { return 48 + i * (GH + GAP); }

const Y_RANGES = [
  { lo: 25, hi: 100, minSpan: 30, label: 'T [°C]',      color: '#E74C3C' },
  { lo: 0,  hi: 2000, minSpan: 300, label: 'R [GFLOPS]', color: '#27AE60' },
  { lo: 0,  hi: 200,  minSpan: 40,  label: 'P [W]',      color: '#2980B9' },
];

// =====================================================================
// 5.  SETUP
// =====================================================================
let sl_k1, sl_k2, sl_gamma, sl_delta, sl_alpha, sl_beta, sl_ksig, sl_Robj;
let pauseBtn, resetBtn;

function mkSlider(col, rowY, txt, min, max, val, step, cb) {
  let x = 10 + col * 230;
  let lbl = createDiv(txt);
  lbl.position(x, rowY - 30);
  lbl.style('width', '220px');
  lbl.style('text-align', 'center');
  lbl.style('font-size', '10px');
  lbl.style('font-weight', 'bold');
  lbl.style('color', '#222');
  lbl.style('font-family', 'Helvetica, Arial, sans-serif');
  lbl.style('line-height', '1.3');
  let sl = createSlider(min, max, val, step);
  sl.position(x, rowY); sl.style('width', '220px');
  sl.input(cb);
  return sl;
}

function setup() {
  createCanvas(960, 700);
  pixelDensity(1);
  Object.assign(p, DEFAULTS);

  // Row 1: k₁, k₂, γ, δ
  sl_k1    = mkSlider(0, SROW1_Y, 'k₁ — CALENTAMIENTO  (↑ = más calor)',          0.01, 0.2,  p.k1,    0.005, () => p.k1    = sl_k1.value());
  sl_k2    = mkSlider(1, SROW1_Y, 'k₂ — DISIPACIÓN  (↑ = más refrigeración)',     0.01, 0.3,  p.k2,    0.005, () => p.k2    = sl_k2.value());
  sl_gamma = mkSlider(2, SROW1_Y, 'γ — EFICIENCIA CPU  (↑ = más rápido)',         0.1,  3.0,  p.gamma, 0.05,  () => p.gamma = sl_gamma.value());
  sl_delta = mkSlider(3, SROW1_Y, 'δ — INERCIA DEL RENDIMIENTO  (↑ = más lento)', 0.1,  5.0,  p.delta, 0.1,   () => p.delta = sl_delta.value());

  // Row 2: α, β, k_sig, R_obj
  sl_alpha = mkSlider(0, SROW2_Y, 'α — AGRESIVIDAD  (↑ = más potencia)',          0.1,  5.0,  p.alpha, 0.1,   () => p.alpha = sl_alpha.value());
  sl_beta  = mkSlider(1, SROW2_Y, 'β — THROTTLING MAX  (↑ = más corte)',          1,    30,   p.beta,  0.5,   () => p.beta  = sl_beta.value());
  sl_ksig  = mkSlider(2, SROW2_Y, 'k_sig — SIGMOIDE  (↑ = más brusco)',           0.05, 3.0,  p.k_sig, 0.05,  () => p.k_sig = sl_ksig.value());
  sl_Robj  = mkSlider(3, SROW2_Y, 'R_obj — CARGA OBJETIVO  (↑ = más calor)',      50,   2000, p.R_obj, 10,    () => p.R_obj = sl_Robj.value());

  pauseBtn = createButton(running ? '⏸ Pausa' : '▶ Play');
  pauseBtn.position(10, BTN_Y); pauseBtn.size(85, 28);
  pauseBtn.mousePressed(() => { running = !running; pauseBtn.html(running ? '⏸ Pausa' : '▶ Play'); });

  resetBtn = createButton('↺ Reiniciar');
  resetBtn.position(110, BTN_Y); resetBtn.size(85, 28);
  resetBtn.mousePressed(resetSim);

  resetSim();
}

function resetSim() {
  Object.assign(p, DEFAULTS);
  s = { T: 45, R: 0, P: 15 }; simTime = 0;
  histTime = []; histT = []; histR = []; histP = [];
  shutdown = false; running = true;
  sl_k1.value(p.k1); sl_k2.value(p.k2); sl_gamma.value(p.gamma); sl_delta.value(p.delta);
  sl_alpha.value(p.alpha); sl_beta.value(p.beta); sl_ksig.value(p.k_sig); sl_Robj.value(p.R_obj);
  if (pauseBtn) pauseBtn.html('⏸ Pausa');
}

// =====================================================================
// 6.  DRAW
// =====================================================================
function draw() {
  background('#F0F0F0');

  if (running) { for (let i = 0; i < STEPS_PER_FRAME; i++) runSimulation(); }

  // Title
  fill('#222'); noStroke(); textAlign(CENTER, TOP);
  textSize(17); textStyle(BOLD);
  text('Evolución Térmica — Throttling Dinámico (RK4)', width / 2, 10);
  textStyle(NORMAL); textSize(11); fill('#555');
  text('Ajustá los 8 deslizadores abajo.  Ventilador automático >80 °C.  Shutdown ≥100 °C.', width / 2, 32);

  // Graphs
  for (let i = 0; i < 3; i++) {
    let data = i === 0 ? histT : i === 1 ? histR : histP;
    drawGraph(GX, graphY(i), GW, GH, Y_RANGES[i], data, i);
  }

  // Info panel
  drawInfo();

  // Shutdown overlay
  if (shutdown) {
    fill(200, 0, 0, 50); noStroke();
    rect(GX, graphY(0), GW, graphY(2) + GH - graphY(0));
    fill(200, 0, 0); noStroke(); textAlign(CENTER, CENTER);
    textSize(24); textStyle(BOLD);
    text('⚠ EMERGENCIA\nSHUTDOWN TÉRMICO', GX + GW / 2, graphY(0) + (graphY(2) + GH - graphY(0)) / 2);
    textStyle(NORMAL);
  }
}

// =====================================================================
// 7.  GRAPH DRAWING
// =====================================================================
function drawGraph(gx, gy, gw, gh, range, data, idx) {
  let { lo, hi } = range;
  let tMin = Math.max(0, simTime - TIME_WINDOW);
  let tMax = Math.max(TIME_WINDOW, simTime);
  let start = 0;
  while (start < histTime.length - 1 && histTime[start] < tMin) start++;

  if (data.length > 1 && start < data.length - 1) {
    let vis = data.slice(start);
    let dMin = Math.min(...vis);
    let dMax = Math.max(...vis);
    let dSpan = Math.max(dMax - dMin, range.minSpan);
    let pad = dSpan * 0.12;
    let nlo = dMin - pad;
    let nhi = dMax + pad;
    if (idx > 0) nlo = Math.max(0, nlo);
    if (isFinite(nlo) && isFinite(nhi) && nhi > nlo) { lo = nlo; hi = nhi; }
  }

  fill(255); stroke(200); strokeWeight(1); rect(gx, gy, gw, gh);

  // Fan boost badge on T graph
  if (idx === 0) {
    let boost = fanBoost(s.T);
    if (boost > 1.0) {
      let badgeTxt = boost < 2.0 ? 'FAN 🟡 ' + nf(boost, 0, 2) + '×' :
                     boost < 3.0 ? 'FAN 🟠 ' + nf(boost, 0, 2) + '×' :
                                   'FAN 🔴 ' + nf(boost, 0, 2) + '×';
      fill(boost < 2.0 ? color(255, 230, 150) : boost < 3.0 ? color(255, 200, 100) : color(255, 150, 150));
      stroke(boost < 2.0 ? '#D4A000' : boost < 3.0 ? '#C07A00' : '#C0392B');
      strokeWeight(1); rect(gx + 4, gy + 4, 130, 20, 4);
      fill(boost < 2.0 ? '#7A6000' : boost < 3.0 ? '#7A4A00' : '#7A1A1A');
      noStroke(); textAlign(LEFT, CENTER); textSize(11); textStyle(BOLD);
      text(badgeTxt, gx + 10, gy + 14);
      textStyle(NORMAL);
    }
  }

  let nG = 5;
  stroke(225); strokeWeight(0.5);
  for (let i = 0; i <= nG; i++) { line(gx, gy + gh - (i / nG) * gh, gx + gw, gy + gh - (i / nG) * gh); }
  for (let i = 0; i <= 6; i++) { line(gx + (i / 6) * gw, gy, gx + (i / 6) * gw, gy + gh); }

  if (idx === 0) {
    let yc = gy + gh - map(p.T_crit, lo, hi, 0, gh);
    stroke('#C0392B'); strokeWeight(1.2);
    drawingContext.setLineDash([5, 4]);
    line(gx, yc, gx + gw, yc);
    drawingContext.setLineDash([]);
    if (yc > gy - 20 && yc < gy + gh + 10) {
      fill('#C0392B'); noStroke(); textSize(9); textAlign(RIGHT, BOTTOM);
      text('T_crit=' + nf(p.T_crit, 0, 0) + '°C', gx + gw - 4, yc - 2);
    }
  }

  if (data.length < 2 || start >= data.length - 1) return;

  drawingContext.save();
  drawingContext.beginPath();
  drawingContext.rect(gx, gy, gw, gh);
  drawingContext.clip();

  stroke(range.color); strokeWeight(2.5); noFill();
  beginShape();
  for (let i = start; i < data.length; i++) {
    vertex(gx + map(histTime[i], tMin, tMax, 0, gw), gy + gh - map(data[i], lo, hi, 0, gh));
  }
  endShape();

  if (data.length > 0) {
    let lv = data[data.length - 1];
    circle(gx + map(histTime[histTime.length - 1], tMin, tMax, 0, gw), gy + gh - map(lv, lo, hi, 0, gh), 5);
  }
  drawingContext.restore();

  fill(80); noStroke(); textSize(9); textAlign(CENTER, TOP);
  text('t [s]', gx + gw / 2, gy + gh + 5);
  push(); translate(gx - 34, gy + gh / 2); rotate(-HALF_PI);
  textAlign(CENTER, CENTER); textSize(9); fill(80); text(range.label, 0, 0);
  pop();

  textSize(8); fill(100); textAlign(RIGHT, CENTER);
  for (let i = 0; i <= nG; i++) {
    let val = lo + (i / nG) * (hi - lo);
    text(nf(val, 0, val < 10 ? 1 : 0), gx - 4, gy + gh - (i / nG) * gh);
  }

  if (data.length > 0) {
    let lv = data[data.length - 1];
    let px = gx + map(histTime[histTime.length - 1], tMin, tMax, 0, gw);
    let py = gy + gh - map(lv, lo, hi, 0, gh);
    fill(range.color); noStroke(); textSize(10); textStyle(BOLD);
    textAlign(LEFT, BOTTOM); text(nf(lv, 0, 1), px + 5, py);
    textStyle(NORMAL);
  }
}

// =====================================================================
// 8.  INFO PANEL
// =====================================================================
function drawInfo() {
  let cx = INFO_X, cy = 45;
  fill(255, 230); stroke(200); strokeWeight(1);
  rect(cx, cy, INFO_W, graphY(2) + GH - cy, 6);

  let x = cx + 12, y = cy + 12;
  fill('#333'); noStroke(); textSize(13); textStyle(BOLD);
  text('Estado', x, y); y += 20;
  textStyle(NORMAL); textSize(11);

  let vals = [
    { l: 'T', v: s.T, u: '°C', c: '#E74C3C' },
    { l: 'R', v: s.R, u: 'GFLOPS', c: '#27AE60' },
    { l: 'P', v: s.P, u: 'W', c: '#2980B9' },
  ];
  for (let v of vals) {
    fill(v.c); textStyle(BOLD); text(v.l + ':', x + 2, y);
    textStyle(NORMAL); fill('#222');
    text(nf(v.v, 0, 1) + ' ' + v.u, x + 30, y);
    y += 20;
  }

  // All slider values
  y += 2;
  fill('#555'); textStyle(BOLD); textSize(10);
  text('Parámetros:', x, y); y += 14;
  textStyle(NORMAL); fill('#666'); textSize(8.5);
  text('k₁=' + nf(p.k1, 0, 3) + '  k₂=' + nf(p.k2, 0, 3), x + 2, y); y += 11;
  text('γ=' + nf(p.gamma, 0, 3) + '  δ=' + nf(p.delta, 0, 2) + '  α=' + nf(p.alpha, 0, 2), x + 2, y); y += 11;
  text('β=' + nf(p.beta, 0, 1) + '  k_sig=' + nf(p.k_sig, 0, 2) + '  R_obj=' + nf(p.R_obj, 0, 0), x + 2, y); y += 18;

  // Fan boost
  let boost = fanBoost(s.T);
  fill('#333'); textStyle(BOLD); textSize(11);
  text('Ventilador', x, y); y += 16;
  textStyle(NORMAL); fill('#555');
  let boostStr = boost <= 1.0 ? '🟢 Normal (1.0×)' :
                 boost < 2.0 ? '🟡 Acelerado (' + nf(boost, 0, 2) + '×)' :
                 boost < 3.0 ? '🟠 Alto (' + nf(boost, 0, 2) + '×)' :
                               '🔴 Máximo (' + nf(boost, 0, 2) + '×)';
  text(boostStr, x + 2, y); y += 20;

  fill('#555'); textSize(10);
  text('k₂ efectivo = ' + nf(p.k2 * boost, 0, 4) + ' (base=' + nf(p.k2, 0, 3) + ')', x + 2, y); y += 20;

  // Separator
  y += 4; stroke(210); line(cx + 10, y, cx + INFO_W - 10, y); y += 12;

  // Equilibrium
  let eqR = p.R_obj;
  let eqP = (p.delta * eqR) / p.gamma;
  let eqT = p.T_amb + (p.k1 * p.delta * eqR) / (p.k2 * p.gamma);
  fill('#333'); textStyle(BOLD); textSize(12);
  text('Equilibrio teórico', x, y); y += 18;
  textStyle(NORMAL); fill('#555'); textSize(10);
  text('T* = ' + nf(eqT, 0, 1) + ' °C', x + 2, y); y += 14;
  text('R* = ' + nf(eqR, 0, 1) + ' GFLOPS', x + 2, y); y += 14;
  text('P* = ' + nf(eqP, 0, 1) + ' W', x + 2, y); y += 16;

  // Separator
  stroke(210); line(cx + 10, y, cx + INFO_W - 10, y); y += 10;

  // Throttling
  let sig = p.beta / (1 + Math.exp(-p.k_sig * (s.T - p.T_crit)));
  let frac = sig / p.beta;
  fill('#333'); textStyle(BOLD); textSize(12);
  text('Throttling', x, y); y += 18;
  let bx = x + 2, bw = INFO_W - 36, bh = 12;
  noStroke(); fill(220); rect(bx, y, bw, bh, 3);
  let fw = map(frac, 0, 1, 0, bw);
  let bc = frac < 0.3 ? '#27AE60' : frac < 0.7 ? '#F39C12' : '#E74C3C';
  fill(bc); rect(bx, y, fw, bh, 3);
  fill(80); textSize(9); textAlign(CENTER, CENTER); text(nf(sig, 0, 2), bx + bw / 2, y + bh / 2);
  y += 20;
  textAlign(LEFT, TOP); textSize(9); fill('#666');
  text('σ = ' + nf(sig, 0, 3) + '  β=' + nf(p.beta, 0, 1), x + 2, y); y += 14;

  // Time
  y += 4; fill('#333'); textStyle(BOLD); textSize(11);
  text('t = ' + nf(simTime, 0, 1) + ' s', x, y);
}
