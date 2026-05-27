# Casos de Prueba — Modelo Térmico

**Parámetros base (defaults):**
- k₁ = 0.052 | k₂ = 0.10 | γ = 1.0 | δ = 0.105 | α = 1.6 | β = 12 | k_sig = 0.5 | R_obj = 1000
- T_amb = 25 | T_crit = 90 | R_min = 50 | P_min = 10
- T(0) = 45 | R(0) = 0 | P(0) = 15
- Frecuencia de throttling: σ = β / (1 + exp(-k_sig·(T − T_crit)))

---

## 1 — Base estable
| k₁ | k₂ | γ | δ | α | β | k_sig | R_obj |
|----|----|----|----|----|----|----|----|
| 0.052 | 0.10 | 1.0 | 0.105 | 1.6 | 12 | 0.5 | 1000 |
T* ≈ 80 °C, P* = 105 W, R* = 1000 GFLOPS → **estable**

---

## 2 — Alta carga (oscilatorio)
| k₁ | k₂ | γ | δ | α | β | k_sig | R_obj |
|----|----|----|----|----|----|----|----|
| 0.052 | 0.10 | 1.0 | 0.105 | 1.6 | 12 | 0.5 | **1500** |
T* ≈ 107 °C > T_crit → **oscilatorio** (throttling cíclico)

---

## 3 — Undervolting (lento pero estable)
| k₁ | k₂ | γ | δ | α | β | k_sig | R_obj |
|----|----|----|----|----|----|----|----|
| 0.052 | 0.10 | 1.0 | 0.105 | **0.4** | 12 | 0.5 | 1000 |
T* ≈ 80 °C, pero α bajo → convergencia **lenta**

---

## 4 — Sobrevoltaje (agresivo, overshoot)
| k₁ | k₂ | γ | δ | α | β | k_sig | R_obj |
|----|----|----|----|----|----|----|----|
| 0.052 | 0.10 | 1.0 | 0.105 | **3.2** | 12 | 0.5 | 1000 |
T* ≈ 80 °C, pero α alto → alcanza T_crit temporalmente, **overshoot**

---

## 5 — Mejor disipación (muy estable)
| k₁ | k₂ | γ | δ | α | β | k_sig | R_obj |
|----|----|----|----|----|----|----|----|
| 0.052 | **0.20** | 1.0 | 0.105 | 1.6 | 12 | 0.5 | 1000 |
T* ≈ 52 °C, muy lejos de T_crit → **muy estable**

---

## 6 — Mala disipación (oscilatorio fuerte)
| k₁ | k₂ | γ | δ | α | β | k_sig | R_obj |
|----|----|----|----|----|----|----|----|
| 0.052 | **0.04** | 1.0 | 0.105 | 1.6 | 12 | 0.5 | 1000 |
T* ≈ 162 °C muy por encima de T_crit → **oscilaciones severas**

---

## 7 — CPU eficiente (bajo consumo)
| k₁ | k₂ | γ | δ | α | β | k_sig | R_obj |
|----|----|----|----|----|----|----|----|
| 0.052 | 0.10 | **2.0** | 0.105 | 1.6 | 12 | 0.5 | 1000 |
P* = 52.5 W, T* ≈ 52 °C → **estable, eficiente**

---

## 8 — CPU ineficiente (alta potencia)
| k₁ | k₂ | γ | δ | α | β | k_sig | R_obj |
|----|----|----|----|----|----|----|----|
| 0.052 | 0.10 | **0.5** | 0.105 | 1.6 | 12 | 0.5 | 1000 |
P* = 210 W, T* ≈ 134 °C > T_crit → **oscilatorio**

---

## 9 — Throttling suave (oscilación leve)
| k₁ | k₂ | γ | δ | α | β | k_sig | R_obj |
|----|----|----|----|----|----|----|----|
| 0.052 | 0.10 | 1.0 | 0.105 | 1.6 | **5** | **0.2** | **1300** |
apenas sobrepasa T_crit, throttling suave → **oscilación leve**

---

## 10 — Throttling agresivo (cortes bruscos)
| k₁ | k₂ | γ | δ | α | β | k_sig | R_obj |
|----|----|----|----|----|----|----|----|
| 0.052 | 0.10 | 1.0 | 0.105 | 1.6 | **25** | **2.0** | **1300** |
supera T_crit con throttling muy brusco → **cortes de potencia abruptos**
