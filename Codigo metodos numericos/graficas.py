"""
ANIMACIONES Y VISUALIZACIÓN — Modelo de estabilidad térmica y rendimiento en CPUs
================================================================================
Carga el modelo desde thermal_throttling_core.py y genera:

  1. Trayectorias T, R, P por método y paso de integración (3×3)
  2. Error relativo global vs h (log-log con pendientes)
  3. Comparación de los 4 escenarios de intervención
  4. Mapa de calor del error (método × h)

Además, es el punto de entrada para las animaciones con Manim.
"""

import os
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D

from thermal_throttling_core import ThermalModel


# ── Configuración ─────────────────────────────────────────────────────────────

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

modelo = ThermalModel()
estado0 = modelo.estado0
t_final = modelo.t_final

# ── Parámetros de estilo para las gráficas ────────────────────────────────────

COLORES_H = {
    1.0:  "#e63946",
    0.5:  "#f4a261",
    0.1:  "#2a9d8f",
    0.05: "#457b9d",
    0.01: "#1d3557",
}
ESTILO_METODO = {
    "Euler":          ("solid",   "o"),
    "Euler Mejorado": ("dashed",  "s"),
    "RK4":            ("dashdot", "^"),
}
ETIQUETAS_H  = [f"h = {h}" for h in COLORES_H]
TAMANIOS_PASO = list(COLORES_H.keys())

VAR_LABELS  = ["Temperatura  T  [°C]", "Rendimiento  R  [GFLOPS]", "Potencia  P  [W]"]
METODOS_FNS = [
    ("Euler",          lambda h: modelo.euler(h, estado0, t_final)),
    ("Euler Mejorado", lambda h: modelo.euler_mejorado(h, estado0, t_final)),
    ("RK4",            lambda h: modelo.runge_kutta(h, estado0, t_final)),
]

# =============================================================================
# REFERENCIA RK45 (usada en Fig 1 y Fig 2)
# =============================================================================
print("Obteniendo referencia RK45...")
t_ref45, T_ref45, R_ref45, P_ref45 = modelo.rk45_referencia(estado0, t_final)
REF_VARS = [T_ref45, R_ref45, P_ref45]

# =============================================================================
# FIG 1 — Trayectorias T, R, P para cada método y cada h  (3×3 subplots)
# =============================================================================
print("\n[Gráfica 1] Generando trayectorias por método y paso de integración...")

fig1, axes1 = plt.subplots(3, 3, figsize=(16, 12), sharex=True)
fig1.suptitle("Trayectorias T, R, P — comparación de pasos de integración (h)\npor método numérico",
              fontsize=13, fontweight="bold", y=1.01)

for col, (nombre_m, fn_m) in enumerate(METODOS_FNS):
    for h in TAMANIOS_PASO:
        t_a, T_a, R_a, P_a = fn_m(h)
        vars_aprox = [T_a, R_a, P_a]
        for fila in range(3):
            ax = axes1[fila][col]
            ax.plot(t_a, vars_aprox[fila],
                    color=COLORES_H[h], linewidth=1.3,
                    linestyle=ESTILO_METODO[nombre_m][0],
                    alpha=0.85, label=f"h = {h}")
    for fila in range(3):
        ax = axes1[fila][col]
        ax.plot(t_ref45, REF_VARS[fila],
                color="black", linewidth=1.8, linestyle="dotted",
                label="RK45 ref.")
        ax.set_title(nombre_m, fontsize=11, fontweight="bold")
        if col == 0:
            ax.set_ylabel(VAR_LABELS[fila], fontsize=9)
        if fila == 2:
            ax.set_xlabel("Tiempo [s]", fontsize=9)
        ax.tick_params(labelsize=8)
        ax.grid(True, alpha=0.3)

leyenda_lineas = [Line2D([0], [0], color=c, linewidth=1.8, label=f"h = {h}")
                  for h, c in COLORES_H.items()]
leyenda_lineas.append(Line2D([0], [0], color="black", linewidth=1.8,
                              linestyle="dotted", label="RK45 referencia"))
fig1.legend(handles=leyenda_lineas, loc="lower center", ncol=6,
            fontsize=9, framealpha=0.9, bbox_to_anchor=(0.5, -0.03))
fig1.tight_layout()
fig1.savefig(os.path.join(OUTPUT_DIR, "fig1_trayectorias_por_metodo.png"),
             dpi=150, bbox_inches="tight")
plt.close(fig1)
print("  -> Guardada: fig1_trayectorias_por_metodo.png")

# =============================================================================
# FIG 2 — Error relativo global vs h  (log-log)
# =============================================================================
print("\n[Gráfica 2] Generando análisis log-log de error relativo global...")

errores = {nombre: [] for nombre, _ in METODOS_FNS}
for nombre_m, fn_m in METODOS_FNS:
    for h in TAMANIOS_PASO:
        t_a, T_a, R_a, P_a = fn_m(h)
        e = modelo.error_relativo_global(t_ref45, T_ref45, R_ref45, P_ref45,
                                          t_a, T_a, R_a, P_a)
        errores[nombre_m].append(e)

fig2, ax2 = plt.subplots(figsize=(8, 5))
ax2.set_title("Error relativo global vs paso de integración h\n(escala log-log — pendiente ≈ orden del método)",
              fontsize=12, fontweight="bold")

colores_m = {"Euler": "#e63946", "Euler Mejorado": "#f4a261", "RK4": "#1d3557"}
for nombre_m, vals_error in errores.items():
    ax2.loglog(TAMANIOS_PASO, vals_error,
               marker="o", markersize=7, linewidth=2,
               color=colores_m[nombre_m], label=nombre_m)
    if min(vals_error) > 0:
        coefs = np.polyfit(np.log10(TAMANIOS_PASO), np.log10(vals_error), 1)
        ax2.annotate(f"pendiente ≈ {coefs[0]:.2f}",
                     xy=(TAMANIOS_PASO[2], vals_error[2]),
                     xytext=(TAMANIOS_PASO[2]*1.15, vals_error[2]*2.5),
                     fontsize=8, color=colores_m[nombre_m],
                     arrowprops=dict(arrowstyle="->", color=colores_m[nombre_m], lw=1))

ax2.invert_xaxis()
ax2.set_xlabel("Paso de integración  h  [s]  ←  más refinado", fontsize=11)
ax2.set_ylabel("Error relativo global máximo", fontsize=11)
ax2.grid(True, which="both", alpha=0.35, linestyle="--")
ax2.legend(fontsize=10, framealpha=0.9)
fig2.tight_layout()
fig2.savefig(os.path.join(OUTPUT_DIR, "fig2_error_relativo_loglog.png"),
             dpi=150, bbox_inches="tight")
plt.close(fig2)
print("  -> Guardada: fig2_error_relativo_loglog.png")

# =============================================================================
# FIG 3 — Comparación de los cuatro escenarios de intervención (RK4, h=0.05)
# =============================================================================
print("\n[Gráfica 3] Generando comparación de escenarios de intervención...")

resultados_esc = modelo.correr_todos_escenarios(estado0, t_final)

NOMBRES_ESC  = list(resultados_esc.keys())
COLORES_ESC  = {"Base": "#6c757d", "Undervolting": "#e63946",
                "Refrigerante": "#2a9d8f", "MetalLiquido": "#457b9d"}
LABELS_ESC   = {
    "Base":          "Base (control)",
    "Undervolting":  "Undervolting (α×0.5)",
    "Refrigerante":  "Base refrigerante (Φ×2)",
    "MetalLiquido":  "Metal líquido (Hd×3)",
}

fig3, axes3 = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
fig3.suptitle("Comparación de escenarios de intervención térmica\n(RK4, h = 0.05 s)",
              fontsize=13, fontweight="bold")

YLABELS3 = ["Temperatura  T  [°C]", "Rendimiento  R  [GFLOPS]", "Potencia  P  [W]"]
HMBRALES  = [modelo.T_crit, modelo.R_min, modelo.P_min]
HLABELS   = [f"T_crit = {modelo.T_crit} °C", f"R_min = {modelo.R_min} GFLOPS", f"P_min = {modelo.P_min} W"]

for nombre_esc, (r_e, r_em, r_rk) in resultados_esc.items():
    t_rk, T_rk, R_rk, P_rk = r_rk
    datos = [T_rk, R_rk, P_rk]
    for i, ax in enumerate(axes3):
        ax.plot(t_rk, datos[i],
                color=COLORES_ESC[nombre_esc], linewidth=2,
                label=LABELS_ESC[nombre_esc])

for i, ax in enumerate(axes3):
    ax.axhline(HMBRALES[i], color="crimson", linewidth=1.2,
               linestyle="--", alpha=0.7, label=HLABELS[i])
    ax.set_ylabel(YLABELS3[i], fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=9)

axes3[-1].set_xlabel("Tiempo [s]", fontsize=11)

handles3, labels3 = axes3[0].get_legend_handles_labels()
fig3.legend(handles3, labels3, loc="lower center", ncol=3,
            fontsize=9, framealpha=0.9, bbox_to_anchor=(0.5, -0.04))
fig3.tight_layout()
fig3.savefig(os.path.join(OUTPUT_DIR, "fig3_escenarios_intervencion.png"),
             dpi=150, bbox_inches="tight")
plt.close(fig3)
print("  -> Guardada: fig3_escenarios_intervencion.png")

# =============================================================================
# FIG 4 — Mapa de calor: error relativo global (método × h)
# =============================================================================
print("\n[Gráfica 4] Generando mapa de calor de errores...")

matriz_error = np.array([errores[m] for m in ["Euler", "Euler Mejorado", "RK4"]])

fig4, ax4 = plt.subplots(figsize=(8, 4))
ax4.set_title("Mapa de calor — Error relativo global\n(escala logarítmica)",
              fontsize=12, fontweight="bold")

im = ax4.imshow(np.log10(matriz_error + 1e-15),
                cmap="RdYlGn_r", aspect="auto", interpolation="nearest")
cbar = fig4.colorbar(im, ax=ax4, pad=0.02)
cbar.set_label("log₁₀(error relativo global)", fontsize=9)

ax4.set_xticks(range(len(TAMANIOS_PASO)))
ax4.set_xticklabels([f"h = {h}" for h in TAMANIOS_PASO], fontsize=9)
ax4.set_yticks(range(3))
ax4.set_yticklabels(["Euler", "Euler Mejorado", "RK4"], fontsize=10)

for i in range(3):
    for j in range(len(TAMANIOS_PASO)):
        val = matriz_error[i, j]
        txt = f"{val:.2e}" if val > 0 else "~0"
        ax4.text(j, i, txt, ha="center", va="center",
                 fontsize=8.5, color="black", fontweight="bold")

fig4.tight_layout()
fig4.savefig(os.path.join(OUTPUT_DIR, "fig4_heatmap_errores.png"),
             dpi=150, bbox_inches="tight")
plt.close(fig4)
print("  -> Guardada: fig4_heatmap_errores.png")

print("\n" + "="*60)
print(f"VISUALIZACIÓN COMPLETA — 4 figuras generadas en {OUTPUT_DIR}/")
print("="*60)


# =============================================================================
# ANIMACIONES CON MANIM  (por implementar por el equipo)
# =============================================================================
# Para usar animaciones con Manim, crear una clase como:
#
#   from manim import *
#   from thermal_throttling_core import ThermalModel
#
#   class ThermalThrottlingScene(ThreeDScene):
#       def construct(self):
#           modelo = ThermalModel()
#           t, T, R, P = modelo.runge_kutta(0.05, modelo.estado0, modelo.t_final)
#           # ... animar trayectorias en espacio de fases 3D
#
# Ejemplos de animaciones útiles:
#   1. Evolución temporal de T(t), R(t), P(t) en panels separados
#   2. Espacio de fases 3D (T, R, P) con trayectoria coloreada por tiempo
#   3. Comparación lado a lado: régimen estable vs oscilatorio
#   4. Activación del throttling: resaltar el instante T > T_crit
