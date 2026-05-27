/**
 * Throttling Activation — T(t) y σ(t) con control de calor
 * =========================================================
 *
 * Dos paneles apilados: T(t) arriba, σ(t) abajo.
 *
 * Usá "Calor externo" para empujar T hacia T_crit y más
 * allá.  Después ajustá k_sig (pendiente de la sigmoide) y
 * β (amplitud) para ver cómo cambia la respuesta del
 * throttling.
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
  heat: 0.0,
};

// =====================================================================
// 2.  STATE
// =====================================================================
let p = {};
let s = { T: 45, R: 0, P: 15 };
let simTime = 0;
let running = true;
const STEPS_FRAME = 2;

let histTime = [], histT = [], histSig = [];
const TIME_WINDOW = 250;
const MAX_PTS = 8000;

let slider_heat, slider_k_sig, slider_beta;

// =====================================================================
// 3.  ODE
// =====================================================================
function deriv(st) {
  let sig = p.beta / (1 + Math.exp(-p.k_sig * (st.T - p.T_crit)));
  return {
    dT: p.k1 * st.P - p.k2 * (st.T - p.T_amb) + p.heat,
    dR: p.gamma * st.P - p.delta * st.R,
    dP: p.alpha * (p.R_obj - st.R) - sig,
  };
}

function rk4(st, h) {
  let k1 = deriv(st);
  let a2 = { T: st.T + 0.5 * h * k1.dT, R: st.R + 0.5 * h * k1.dR, P: st.P + 0.5 * h * k1.dP };
  let k2 = deriv(a2);
  let a3 = { T: st.T + 0.5 * h * k2.dT, R: st.R + 0.5 * h * k2.dR, P: st.P + 0.5 * h * k2.dP };
  let k3 = deriv(a3);
  let a4 = { T: st.T + h * k3.dT, R: st.R + h * k3.dR, P: st.P + h * k3.dP };
  let k4 = deriv(a4);
  return {
    T: st.T + (h / 6) * (k1.dT + 2 * k2.dT + 2 * k3.dT + k4.dT),
    R: st.R + (h / 6) * (k1.dR + 2 * k2.dR + 2 * k3.dR + k4.dR),
    P: Math.max(P_MIN, st.P + (h / 6) * (k1.dP + 2 * k2.dP + 2 * k3.dP + k4.dP)),
  };
}

function stepSim() {
  s = rk4(s, p.dt);
  simTime += p.dt;
  let sig = p.beta / (1 + Math.exp(-p.k_sig * (s.T - p.T_crit)));
  histTime.push(simTime);
  histT.push(s.T);
  histSig.push(sig);
  if (histTime.length > MAX_PTS) {
    let trim = 2000;
    histTime.splice(0, trim); histT.splice(0, trim); histSig.splice(0, trim);
  }
}

function resetSim() {
  Object.assign(p, DEFAULTS);
  s = { T: 45, R: 0, P: 15 }; simTime = 0;
  histTime = []; histT = []; histSig = [];
  slider_heat.value(p.heat);
  slider_k_sig.value(p.k_sig);
  slider_beta.value(p.beta);
  running = true;
}

// =====================================================================
// 4.  LAYOUT
// =====================================================================
const MG = { top: 48, bottom: 80 };
let GRAPH_W, GRAPH_H;

function calcLayout() {
  GRAPH_W = width - 80;
  GRAPH_H = (height - MG.top - MG.bottom - 14) / 2;
}

const R_TEMP = { lo: 25, hi: 100, label: 'T(t) [°C]', color: '#E74C3C', minSpan: 30 };
const R_SIG  = { lo: 0,  hi: 15,  label: 'σ(t) throttling', color: '#E67E22', minSpan: 10 };

// =====================================================================
// 5.  SETUP
// =====================================================================
function setup() {
  createCanvas(880, 680);
  pixelDensity(1);
  Object.assign(p, DEFAULTS);
  calcLayout();

  // Sliders — row below panels (labels DOM para que no se borren con background)
  let sy = height - 70, sw = 210;
  let x0 = 30;

  function mkSlider(x, label, min, max, val, step, cb) {
    let lbl = createDiv(label);
    lbl.position(x, sy - 32);
    lbl.style('width', sw + 'px');
    lbl.style('text-align', 'center');
    lbl.style('font-size', '10px');
    lbl.style('font-weight', 'bold');
    lbl.style('color', '#222');
    lbl.style('font-family', 'Helvetica, Arial, sans-serif');
    lbl.style('line-height', '1.3');
    let sl = createSlider(min, max, val, step);
    sl.position(x, sy); sl.style('width', sw + 'px');
    sl.input(cb);
    return sl;
  }

  slider_heat  = mkSlider(x0,             '🔥 Calor externo  (↑ = empuja T arriba)',     0,    3.0, p.heat,  0.05, () => p.heat   = slider_heat.value());
  slider_k_sig = mkSlider(x0 + 225,       'k_sig — pendiente sigmoide  (↑ = más brusco)', 0.05, 3.0, p.k_sig, 0.05, () => p.k_sig = slider_k_sig.value());
  slider_beta  = mkSlider(x0 + 450,       'β — amplitud de throttling  (↑ = más corte)',  1,    30,  p.beta,  0.5,  () => p.beta  = slider_beta.value());

  let btnX = x0 + 670;
  let btn = createButton(running ? '⏸ Pausa' : '▶ Play');
  btn.position(btnX, sy); btn.size(75, 26);
  btn.mousePressed(() => { running = !running; btn.html(running ? '⏸ Pausa' : '▶ Play'); });

  let rst = createButton('↺ Reinicio');
  rst.position(btnX + 85, sy); rst.size(75, 26);
  rst.mousePressed(resetSim);
}

// =====================================================================
// 6.  GRAPH
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
    if (isFinite(nlo) && isFinite(nhi) && nhi > nlo) { lo = nlo; hi = nhi; }
  }

  fill(255); stroke(200); strokeWeight(1); rect(gx, gy, gw, gh);

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

  // Fill under curve
  if (idx === 0 && data.length > start + 1) {
    let yBot = gy + gh;
    fill(200, 50, 50, 12); noStroke();
    beginShape();
    for (let i = start; i < data.length; i++) {
      vertex(gx + map(histTime[i], tMin, tMax, 0, gw), gy + gh - map(data[i], lo, hi, 0, gh));
    }
    vertex(gx + map(histTime[data.length - 1], tMin, tMax, 0, gw), yBot);
    vertex(gx + map(histTime[start], tMin, tMax, 0, gw), yBot);
    endShape(CLOSE);
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

  // Vertical sync line
  let vx = gx + map(simTime, tMin, tMax, 0, gw);
  if (vx >= gx && vx <= gx + gw) {
    stroke(150, 150, 150, 120); strokeWeight(0.8); drawingContext.setLineDash([3, 4]);
    line(vx, gy, vx, gy + gh);
    drawingContext.setLineDash([]);
  }

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
// 7.  DRAW
// =====================================================================
function draw() {
  background('#F0F0F0');

  if (running) { for (let i = 0; i < STEPS_FRAME; i++) stepSim(); }

  fill('#222'); noStroke(); textAlign(CENTER, TOP);
  textSize(16); textStyle(BOLD);
  text('Activación del Throttling — T(t) y σ(t)', width / 2, 8);
  textStyle(NORMAL); textSize(10); fill('#555');
  text('Subí "Calor externo" para empujar T → T_crit.  Ajustá k_sig y β para ver cómo responde el throttling.', width / 2, 28);

  let gx = 52, gy1 = MG.top, gw = GRAPH_W, gh = GRAPH_H;

  drawGraph(gx, gy1, gw, gh, R_TEMP, histT, 0);
  let gy2 = gy1 + gh + 14;
  drawGraph(gx, gy2, gw, gh, R_SIG, histSig, 1);

  // Connection label
  fill(180, 130, 0, 200); noStroke(); textAlign(CENTER, CENTER); textSize(10);
  text('T ↑  →  σ ↑  →  P ↓', width / 2, (gy1 + gy2) / 2);

  // Bottom info
  let sigNow = p.beta / (1 + Math.exp(-p.k_sig * (s.T - p.T_crit)));
  fill('#333'); textSize(10); textAlign(LEFT, TOP);
  text('t=' + nf(simTime, 0, 1) + 's  |  Calor=' + nf(p.heat, 0, 2) + '  k_sig=' + nf(p.k_sig, 0, 2) + '  β=' + nf(p.beta, 0, 1) + '  σ=' + nf(sigNow, 0, 3), 8, height - 90);
}
