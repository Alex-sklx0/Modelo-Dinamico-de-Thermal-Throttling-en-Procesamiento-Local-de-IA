# Modelo Dinámico de Estabilidad Térmica y Rendimiento en Computadores de Propósito General

Simulación numérica del *thermal throttling* en CPUs usando RK4, Euler y Euler Mejorado,
con análisis de error, 4 escenarios de intervención y visualización.

## Archivos

| Archivo | Propósito |
|---|---|
| `thermal_throttling_core.py` | Clase `ThermalModel`: sistema de EDOs, métodos numéricos, análisis de error, escenarios |
| `simulacion_thermal_throttling.py` | Ejecución en terminal (parámetros, error, escenarios) |
| `animaciones.py` | Generación de gráficas Matplotlib (4 figuras) y punto de entrada para animaciones Manim |
| `modelo.md` | Informe completo del proyecto |
| `main.tex` | Versión LaTeX del informe (artículo 2 columnas) |

## Uso

```bash
# Simulación numérica (terminal)
python3 simulacion_thermal_throttling.py

# Visualización (genera 4 figuras en outputs/)
python3 animaciones.py
```

