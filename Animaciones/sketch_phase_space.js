/**
 * Phase Space 3D — Trayectoria (T, R, P) interactiva
 * ===================================================
 *
 * Precomputa la trayectoria 3D del sistema de EDOs y la
 * recorre con un punto animado.  Arrastrá el mouse para
 * rotar la vista.  Ajustá k₂ para ver cómo cambia la
 * órbita.
 *
 * Paste en https://editor.p5js.org/ → Play.
 */

// =====================================================================
// 1.  CONSTANTS
// =====================================================================
const P_MIN = 5;

const DEFAULTS = {
  k1: 0.052, k2: 0.10, gamma: 1.0, delta: 0.105,
  alpha: 1.6, beta: 12.0, k_sig: 0.5,
  T_amb: 25, T_crit: 90, R_obj: 1000, dt: 0.05, t_end: 300,
};

// =====================================================================
// 2.  STATE
// =====================================================================
let p = {};
let traj = [];              // [{T,R,P}, …]
let idx = 0;                // animation position
let slider_k2;
let paused = false;

// Mapping ranges
const R_T = { lo: 25, hi: 100 };
const R_R = { lo: 0,  hi: 2000 };
const R_P = { lo: 0,  hi: 200 };
const S = 2.1;              // global scale factor

// =====================================================================
// 3.  ODE (same as core)
// =====================================================================
function deriv(st) {
  let sig = p.beta / (1 + Math.exp(-p.k_sig * (st.T - p.T_crit)));
  return {
    dT: p.k1 * st.P - p.k2 * (st.T - p.T_amb),
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

function computeTrajectory() {
  traj = [];
  let st = { T: 45, R: 0, P: 15 };
  let n = Math.floor(p.t_end / p.dt);
  for (let i = 0; i < n; i++) {
    traj.push({ ...st });
    st = rk4(st, p.dt);
  }
  idx = 0;
}

// =====================================================================
// 4.  MAPPING
// =====================================================================
function m3(v, rng) {
  return ((v - rng.lo) / (rng.hi - rng.lo) - 0.5) * 500 * S;
}

function eqCoords() {
  let R = p.R_obj;
  let P = (p.delta * R) / p.gamma;
  let T = p.T_amb + (p.k1 * p.delta * R) / (p.k2 * p.gamma);
  return { T, R, P };
}

// =====================================================================
// 5.  SETUP
// =====================================================================
function setup() {
  createCanvas(850, 650, WEBGL);
  Object.assign(p, DEFAULTS);
  computeTrajectory();

  // Label DOM para que persista (no se borra con background)
  let lbl = createDiv('k₂ — DISIPACIÓN TÉRMICA  (↑ = más refrigeración)');
  lbl.position(20, height - 72);
  lbl.style('width', '220px');
  lbl.style('text-align', 'center');
  lbl.style('font-size', '11px');
  lbl.style('font-weight', 'bold');
  lbl.style('color', '#222');
  lbl.style('font-family', 'Helvetica, Arial, sans-serif');

  slider_k2 = createSlider(0.01, 0.3, p.k2, 0.005);
  slider_k2.position(20, height - 45);
  slider_k2.style('width', '220px');
  slider_k2.input(() => {
    p.k2 = slider_k2.value();
    computeTrajectory();
  });
}

// =====================================================================
// 6.  DRAW
// =====================================================================
function draw() {
  background('#F0F0F0');

  // 3D scene
  orbitControl();
  ambientLight(200);
  directionalLight(220, 220, 220, 0.5, 1, -0.5);

  // --- axes ---
  let L = 260 * S;
  stroke('#555'); strokeWeight(2);
  line(-L, 0, 0, L, 0, 0);   // T (x)
  line(0, -L, 0, 0, L, 0);   // R (y)
  line(0, 0, -L, 0, 0, L);   // P (z)

  strokeWeight(1);
  let tick = 40 * S;
  for (let v = 40; v <= 90; v += 10) {
    let x = m3(v, R_T); stroke(180); line(x, -tick, 0, x, tick, 0);
  }
  for (let v = 500; v <= 2000; v += 500) {
    let y = m3(v, R_R); stroke(180); line(-tick, y, 0, tick, y, 0);
  }
  for (let v = 50; v <= 200; v += 50) {
    let z = m3(v, R_P); stroke(180); line(0, -tick, z, 0, tick, z);
  }

  fill('#C0392B'); noStroke(); textSize(15); textStyle(BOLD);
  text('T', L + 15, 0, 0);
  fill('#27AE60');
  text('R', 0, -L - 18, 0);
  fill('#2980B9');
  text('P', 0, 0, L + 15);

  // --- equilibrium ---
  let eq = eqCoords();
  let ex = m3(eq.T, R_T), ey = m3(eq.R, R_R), ez = m3(eq.P, R_P);
  push();
  translate(ex, ey, ez);
  fill(255, 200, 0); noStroke(); sphere(7);
  pop();
  fill(255, 200, 0); textSize(12); textStyle(NORMAL);
  text('Equilibrio', ex + 14, ey - 6, ez);

  // --- trajectory ---
  if (traj.length < 2) return;

  noFill();
  // Full path (faded)
  stroke(100, 200, 200, 50); strokeWeight(1);
  beginShape(LINE_STRIP);
  for (let pt of traj) vertex(m3(pt.T, R_T), m3(pt.R, R_R), m3(pt.P, R_P));
  endShape();

  // Advance
  if (!paused && idx < traj.length - 1) {
    idx += 2;
    if (idx >= traj.length) idx = traj.length - 1;
  }

  // Trail
  let trailStart = Math.max(0, idx - 300);
  stroke(0, 180, 180); strokeWeight(3);
  beginShape(LINE_STRIP);
  for (let i = trailStart; i <= idx; i++) {
    let pt = traj[i];
    vertex(m3(pt.T, R_T), m3(pt.R, R_R), m3(pt.P, R_P));
  }
  endShape();

  // Dot
  let cur = traj[idx];
  let dx = m3(cur.T, R_T), dy = m3(cur.R, R_R), dz = m3(cur.P, R_P);
  push();
  translate(dx, dy, dz);
  fill(0, 200, 200); noStroke(); sphere(8);
  pop();

  // --- 2D overlay ---
  noLights();
  push();
  ortho(-width / 2, width / 2, -height / 2, height / 2, -1000, 1000);
  camera(0, 0, 0, 0, 0, -1, 0, 1, 0);

  fill('#222'); noStroke(); textAlign(CENTER, TOP);
  textSize(18); textStyle(BOLD);
  text('Espacio de Fases (T, R, P)', 0, -height / 2 + 12);

  textStyle(NORMAL); textSize(12); fill('#555');
  text('Arrastrá con mouse para rotar · rueda para zoom', 0, -height / 2 + 36);

  // (Label de k₂ es DOM createDiv en setup — no se borra con background)

  textAlign(RIGHT, CENTER); textSize(11); fill('#555');
  let info = 'T=' + nf(cur.T, 0, 1) + '°C  ' +
             'R=' + nf(cur.R, 0, 1) + 'op/s  ' +
             'P=' + nf(cur.P, 0, 1) + 'W  ' +
             't=' + nf(idx * p.dt, 0, 1) + 's';
  text(info, width / 2 - 15, -height / 2 + 55);

  pop();
}
