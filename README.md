# Modelo Dinámico de Estabilidad Térmica y Rendimiento en Computadores de Propósito General

Simulación numérica del *thermal throttling* en CPUs usando RK4, Euler y Euler Mejorado,
con análisis de error, 4 escenarios de intervención y visualización.

## Archivos

| Archivo | Propósito |
|---|---|
| `thermal_throttling_core.py` | Clase `ThermalModel`: sistema de EDOs, métodos numéricos, análisis de error, escenarios |
| `main.tex` | Versión LaTeX del informe (artículo 2 columnas) |
| `presentacion.tex` | Versión LaTeX de la presentación |

## Uso

```bash
# Simulación numérica (terminal)
python3 thermal_throttling_core.py

```

