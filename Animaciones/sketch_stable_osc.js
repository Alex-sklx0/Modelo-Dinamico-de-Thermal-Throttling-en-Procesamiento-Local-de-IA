/**
 * Stable vs Oscillatory — Comparación lado a lado
 * ===============================================
 *
 * Dos simulaciones RK4 paralelas: izquierda con k₂
 * nominal (estable), derecha con k₂ × multiplicador
 * (oscilatorio cuando el factor es bajo).
 *
 * Paste en https://editor.p5js.org/ → Play.
 */

// =====================================================================
// 1.  CONSTANTS
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
let sL = { T: 45, R: 0, P: 15 };   // left (stable)
let sR = { T: 45, R: 0, P: 15 };   // right (oscillatory)
let simTime = 0;
let running = true;
const STEPS_FRAME = 2;

let histTime = [], histTL = [], histTR = [];
let k2mult = 0.5;           // default multiplier for right panel
const TIME_WINDOW = 250;
const MAX_PTS = 8000;

let slider_mult;
let paused = false;

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

function rk4(st, h, k2val) {
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

function stepSim() {
  sL = rk4(sL, p.dt, p.k2);
  sR = rk4(sR, p.dt, p.k2 * k2mult);
  simTime += p.dt;
  histTime.push(simTime);
  histTL.push(sL.T);
  histTR.push(sR.T);
  if (histTime.length > MAX_PTS) {
    let trim = 2000;
    histTime.splice(0, trim); histTL.splice(0, trim); histTR.splice(0, trim);
  }
}

function resetSim() {
  Object.assign(p, DEFAULTS);
  sL = { T: 45, R: 0, P: 15 };
  sR = { T: 45, R: 0, P: 15 };
  simTime = 0;
  histTime = []; histTL = []; histTR = [];
  k2mult = 0.5; slider_mult.value(0.5);
  running = true;
}

// =====================================================================
// 4.  LAYOUT
// =====================================================================
const MG = { top: 48, bottom: 60 };
let GRAPH_W, GRAPH_H;

function calcLayout() {
  GRAPH_W = (width - MG.top - 20) / 2;
  GRAPH_H = height - MG.top - MG.bottom;
}

const R_T = { lo: 25, hi: 110, color: '#27AE60', minSpan: 30 };

// =====================================================================
// 5.  SETUP
// =====================================================================
function setup() {
  createCanvas(900, 550);
  pixelDensity(1);
  Object.assign(p, DEFAULTS);
  calcLayout();

  let cx = 20, cy = height - 30;

  let lbl = createDiv('Multiplicador de k₂ (derecha) — ↓ oscila / ↑ estable');
  lbl.position(cx, cy - 32);
  lbl.style('font-size', '11px');
  lbl.style('font-weight', 'bold');
  lbl.style('color', '#333');
  lbl.style('font-family', 'Helvetica, Arial, sans-serif');

  slider_mult = createSlider(0.1, 1.8, k2mult, 0.05);
  slider_mult.position(cx + 340, cy - 1);
  slider_mult.style('width', '180px');
  slider_mult.input(() => {
    k2mult = slider_mult.value();
  });

  let cx2 = cx + 450;
  let btn = createButton(running ? '⏸ Pause' : '▶ Play');
  btn.position(cx2, cy - 4); btn.size(75, 26);
  btn.mousePressed(() => { running = !running; btn.html(running ? '⏸ Pause' : '▶ Play'); });

  let rst = createButton('↺ Reset');
  rst.position(cx2 + 85, cy - 4); rst.size(65, 26);
  rst.mousePressed(resetSim);
}

// =====================================================================
// 6.  GRAPH
// =====================================================================
function drawGraph(gx, gy, gw, gh, data, label, color) {
  let lo = R_T.lo, hi = R_T.hi;

  // auto-scale
  let tMin = Math.max(0, simTime - TIME_WINDOW);
  let tMax = Math.max(TIME_WINDOW, simTime);
  let start = 0;
  while (start < histTime.length - 1 && histTime[start] < tMin) start++;

  if (data.length > 1 && start < data.length - 1) {
    let vis = data.slice(start);
    let dMin = Math.min(...vis);
    let dMax = Math.max(...vis);
    let dSpan = Math.max(dMax - dMin, R_T.minSpan);
    let pad = dSpan * 0.12;
    let nlo = dMin - pad;
    let nhi = dMax + pad;
    if (isFinite(nlo) && isFinite(nhi) && nhi > nlo) { lo = nlo; hi = nhi; }
  }

  fill(255); stroke(200); strokeWeight(1); rect(gx, gy, gw, gh);

  let nG = 5;
  stroke(225); strokeWeight(0.5);
  for (let i = 0; i <= nG; i++) { let y = gy + gh - (i / nG) * gh; line(gx, y, gx + gw, y); }
  for (let i = 0; i <= 6; i++) { let x = gx + (i / 6) * gw; line(x, gy, x, gy + gh); }

  // T_crit
  let yc = gy + gh - map(p.T_crit, lo, hi, 0, gh);
  stroke(120); strokeWeight(1);
  drawingContext.setLineDash([5, 4]);
  line(gx, yc, gx + gw, yc);
  drawingContext.setLineDash([]);
  if (yc > gy - 20 && yc < gy + gh + 10) {
    fill('#666'); noStroke(); textSize(9); textAlign(RIGHT, BOTTOM);
    text('T_crit=' + nf(p.T_crit, 0, 0) + '°C', gx + gw - 4, yc - 2);
  }

  // curve (clipped)
  if (data.length < 2 || start >= data.length - 1) return;
  drawingContext.save();
  drawingContext.beginPath();
  drawingContext.rect(gx, gy, gw, gh);
  drawingContext.clip();

  stroke(color); strokeWeight(3); noFill();
  beginShape();
  for (let i = start; i < data.length; i++) {
    vertex(gx + map(histTime[i], tMin, tMax, 0, gw), gy + gh - map(data[i], lo, hi, 0, gh));
  }
  endShape();

  // end dot
  if (data.length > 0) {
    let px = gx + map(histTime[histTime.length - 1], tMin, tMax, 0, gw);
    let py = gy + gh - map(data[data.length - 1], lo, hi, 0, gh);
    fill(color); noStroke(); circle(px, py, 6);
  }
  drawingContext.restore();

  // Axis labels
  fill(80); noStroke(); textSize(10); textAlign(CENTER, TOP);
  text('t [s]', gx + gw / 2, gy + gh + 6);
  push(); translate(gx - 36, gy + gh / 2); rotate(-HALF_PI);
  textAlign(CENTER, CENTER); textSize(10); fill(80); text('T [°C]', 0, 0);
  pop();

  textSize(9); fill(100); textAlign(RIGHT, CENTER);
  for (let i = 0; i <= nG; i++) {
    let val = lo + (i / nG) * (hi - lo);
    text(nf(val, 0, 0), gx - 5, gy + gh - (i / nG) * gh);
  }

  // Value label
  if (data.length > 0) {
    let lv = data[data.length - 1];
    let px = gx + map(histTime[histTime.length - 1], tMin, tMax, 0, gw);
    let py = gy + gh - map(lv, lo, hi, 0, gh);
    fill(color); noStroke(); textSize(12); textStyle(BOLD);
    textAlign(LEFT, BOTTOM); text(nf(lv, 0, 1), px + 6, py);
    textStyle(NORMAL);
  }

  // Panel title
  fill(color); noStroke(); textAlign(CENTER, TOP); textSize(13); textStyle(BOLD);
  text(label, gx + gw / 2, gy + 6);
  textStyle(NORMAL);
}

// =====================================================================
// 7.  DRAW
// =====================================================================
function draw() {
  background('#F0F0F0');

  if (running) {
    for (let i = 0; i < STEPS_FRAME; i++) stepSim();
  }

  // Title
  fill('#222'); noStroke(); textAlign(CENTER, TOP);
  textSize(17); textStyle(BOLD);
  text('Estable vs Oscilatorio — T(t) con distintos k₂', width / 2, 10);
  textStyle(NORMAL); textSize(11); fill('#555');
  text('k₂ nominal = ' + nf(p.k2, 0, 3) + '  ·  k₂ (der.) = ' + nf(p.k2 * k2mult, 0, 4) + '  ·  multiplicador = ' + nf(k2mult, 0, 2), width / 2, 32);

  let gxL = MG.top;
  let gxR = width / 2 + 6;
  let gy = MG.top + 20;
  let gw = GRAPH_W;
  let gh = GRAPH_H - 20;

  drawGraph(gxL, gy, gw, gh, histTL, 'Base — estable (k₂ nominal)', '#27AE60');
  drawGraph(gxR, gy, gw, gh, histTR, 'k₂ × ' + nf(k2mult, 0, 2) + ' — ' + (k2mult < 0.7 ? 'oscilatorio' : 'estable'), '#E74C3C');

  // Footer info
  fill('#444'); textSize(11); textAlign(LEFT, TOP);
  text('t = ' + nf(simTime, 0, 1) + ' s  |  T* ≈ ' + nf(p.T_amb + (p.k1 * p.delta * p.R_obj) / (p.k2 * p.gamma), 0, 1) + ' °C', 20, height - 58);
}
