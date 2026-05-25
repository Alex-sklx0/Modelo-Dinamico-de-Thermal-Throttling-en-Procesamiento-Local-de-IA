import math
from scipy.integrate import solve_ivp
import numpy as np


# =============================================================================
# PARÁMETROS DE HARDWARE
# Especificaciones físicas del equipo de referencia
# Las constantes del modelo se calculan directamente desde estas variables,
# sin factores de escala intermedios (ver sección 2.2 del informe)
# =============================================================================

# Variables de hardware (fijas al adquirir el equipo)
Nc    = 8       # Núcleos físicos
Nh    = 16      # Hilos lógicos
fp    = 3.5     # Frecuencia del procesador (GHz)
v_ram = 4800    # Velocidad de la RAM (MT/s)
v_bus = 16      # Velocidad del bus PCIe (GT/s)
Phi   = 2.5     # Flujo de aire de los ventiladores (CFM)
Hd    = 5.0     # Conductancia del disipador (W/°C)

# Factores de escala empíricos (convierten hardware en constantes físicas)
kappa0 = 0.002    # Ineficiencia térmica del silicio (1/C_th)
eta0   = 0.004    # Constante de convección del chasis [1/(R_th * C_th)]
gamma0 = 0.015    # Eficiencia IPC de la arquitectura
delta0 = 16       # Overhead intrínseco del SO (calibrado para P* en 15-45 W)
alpha0 = 0.8      # Ganancia del gobernador del SO

# Constantes del modelo — derivadas del hardware y factores de escala
k1    = kappa0 * (fp * Nc)
k2    = eta0   * (Phi * Hd)
gamma = gamma0 * (Nh * fp)
delta = delta0 / min(v_ram, v_bus)
alpha = alpha0 * (Nh / Nc)

# Parámetros de calibración del firmware (no dependen del hardware)
beta  = 12.0    # Amplitud máxima del corte de potencia (W)
k_sig = 0.5     # Agresividad de la transición logística (1/°C)

# Parámetros del entorno
T_amb  = 25     # Temperatura ambiente (°C)
T_crit = 90     # Umbral de referencia del throttling (°C)
R_obj  = 40     # Throughput objetivo normalizado (ops/s)
R_min  = 5      # Umbral mínimo de viabilidad (ops/s)
P_min  = 5      # Potencia mínima física del procesador (W)

# Condiciones iniciales [T, R, P]
T0 = 45     # Temperatura de reposo con carga base del SO (°C)
R0 = 0      # Procesador sin carga activa (ops/s)
P0 = 15     # Potencia base del SO en inactividad (W)

# Horizonte de simulación
t_inicio = 0
t_final  = 300   # segundos


# =============================================================================
# SISTEMA DE ECUACIONES DIFERENCIALES
# f(estado) -> [dT/dt, dR/dt, dP/dt]
# =============================================================================

def sistema(estado):
    T, R, P = estado

    # Ecuación 1: Temperatura (Lumped Capacitance + Ley de Newton)
    dTdt = k1 * P - k2 * (T - T_amb)

    # Ecuación 2: Rendimiento (Fluid Queueing Model)
    dRdt = gamma * P - delta * R

    # Ecuación 3: Potencia (controlador proporcional + throttling logístico)
    throttling = beta / (1 + math.exp(-k_sig * (T - T_crit)))
    dPdt = alpha * (R_obj - R) - throttling

    return [dTdt, dRdt, dPdt]


def aplicarFrontera(estado):
    # Condición de frontera programática: P no puede caer por debajo de P_min
    # No modifica la ODE — es una regla lógica del integrador
    estado[2] = max(P_min, estado[2])
    return estado


# =============================================================================
# MÉTODO 1: EULER EXPLÍCITO
# =============================================================================

def Euler(h, f, estado0, tFinal):
    t = t_inicio
    estado = list(estado0)

    tSalida = [t]
    TSalida = [estado[0]]
    RSalida = [estado[1]]
    PSalida = [estado[2]]

    while t < tFinal - 1e-10:
        d = f(estado)
        estado = [
            estado[0] + h * d[0],
            estado[1] + h * d[1],
            estado[2] + h * d[2]
        ]
        estado = aplicarFrontera(estado)
        t += h
        tSalida += [t]
        TSalida += [estado[0]]
        RSalida += [estado[1]]
        PSalida += [estado[2]]

    print("Euler con h =", h, "-> T:", round(TSalida[-1], 4),
          "°C | R:", round(RSalida[-1], 4), "ops/s | P:", round(PSalida[-1], 4), "W")
    return tSalida, TSalida, RSalida, PSalida


# =============================================================================
# MÉTODO 2: EULER MEJORADO (HEUN)
# =============================================================================

def EulerMejorado(h, f, estado0, tFinal):
    t = t_inicio
    estado = list(estado0)

    tSalida = [t]
    TSalida = [estado[0]]
    RSalida = [estado[1]]
    PSalida = [estado[2]]

    while t < tFinal - 1e-10:
        d1 = f(estado)

        pred = [
            estado[0] + h * d1[0],
            estado[1] + h * d1[1],
            estado[2] + h * d1[2]
        ]
        pred = aplicarFrontera(pred)

        d2 = f(pred)
        estado = [
            estado[0] + h * (d1[0] + d2[0]) / 2,
            estado[1] + h * (d1[1] + d2[1]) / 2,
            estado[2] + h * (d1[2] + d2[2]) / 2
        ]
        estado = aplicarFrontera(estado)
        t += h
        tSalida += [t]
        TSalida += [estado[0]]
        RSalida += [estado[1]]
        PSalida += [estado[2]]

    print("Euler Mejorado con h =", h, "-> T:", round(TSalida[-1], 4),
          "°C | R:", round(RSalida[-1], 4), "ops/s | P:", round(PSalida[-1], 4), "W")
    return tSalida, TSalida, RSalida, PSalida


# =============================================================================
# MÉTODO 3: RUNGE-KUTTA DE CUARTO ORDEN (RK4)
# =============================================================================

def RungeKutta(h, f, estado0, tFinal):
    numPasos = int(round((tFinal - t_inicio) / h))
    t = t_inicio
    estado = list(estado0)

    tSalida = [t]
    TSalida = [estado[0]]
    RSalida = [estado[1]]
    PSalida = [estado[2]]

    for i in range(numPasos):
        k1v = f(estado)

        eK2 = aplicarFrontera([estado[j] + (h/2) * k1v[j] for j in range(3)])
        k2v = f(eK2)

        eK3 = aplicarFrontera([estado[j] + (h/2) * k2v[j] for j in range(3)])
        k3v = f(eK3)

        eK4 = aplicarFrontera([estado[j] + h * k3v[j] for j in range(3)])
        k4v = f(eK4)

        estado = [
            estado[j] + (h/6) * (k1v[j] + 2*k2v[j] + 2*k3v[j] + k4v[j])
            for j in range(3)
        ]
        estado = aplicarFrontera(estado)
        t += h
        tSalida += [t]
        TSalida += [estado[0]]
        RSalida += [estado[1]]
        PSalida += [estado[2]]

    print("Runge-Kutta con h =", h, "-> T:", round(TSalida[-1], 4),
          "°C | R:", round(RSalida[-1], 4), "ops/s | P:", round(PSalida[-1], 4), "W")
    return tSalida, TSalida, RSalida, PSalida


# =============================================================================
# SOLUCIONADOR DE REFERENCIA: RK45 (SciPy)
# Exclusivamente para validación y cálculo del error relativo
# =============================================================================

def RK45Referencia(estado0, tFinal):
    def sistemaScipY(t, estado):
        return sistema(estado)

    sol = solve_ivp(
        sistemaScipY,
        [t_inicio, tFinal],
        estado0,
        method="RK45",
        max_step=0.01,
        dense_output=True
    )

    tSalida = list(sol.t)
    TSalida = list(sol.y[0])
    RSalida = list(sol.y[1])
    PSalida = [max(P_min, p) for p in sol.y[2]]

    print("RK45 referencia -> T:", round(TSalida[-1], 4),
          "°C | R:", round(RSalida[-1], 4), "ops/s | P:", round(PSalida[-1], 4), "W")
    return tSalida, TSalida, RSalida, PSalida


# =============================================================================
# ANÁLISIS DE ERROR
# Error relativo global de cada método respecto a RK45
# E_rel(h) = max_t || x_aprox(t,h) - x_RK45(t) || / || x_RK45(t) ||
# =============================================================================

def errorRelativoGlobal(tRef, TRef, RRef, PRef, tAprox, TAprox, RAprox, PAprox):
    TRefInterp = np.interp(tAprox, tRef, TRef)
    RRefInterp = np.interp(tAprox, tRef, RRef)
    PRefInterp = np.interp(tAprox, tRef, PRef)

    errorMaximo = 0
    for i in range(len(tAprox)):
        normaRef = math.sqrt(TRefInterp[i]**2 + RRefInterp[i]**2 + PRefInterp[i]**2)
        normaErr = math.sqrt(
            (TAprox[i] - TRefInterp[i])**2 +
            (RAprox[i] - RRefInterp[i])**2 +
            (PAprox[i] - PRefInterp[i])**2
        )
        if normaRef > 1e-10:
            errorLocal = normaErr / normaRef
            if errorLocal > errorMaximo:
                errorMaximo = errorLocal

    return errorMaximo


def analisisError(estado0, tFinal):
    tamaniosPaso = [1.0, 0.5, 0.1, 0.05, 0.01]

    print("\n" + "="*60)
    print("ANÁLISIS DE ERROR RELATIVO GLOBAL vs RK45")
    print("="*60)

    tRef, TRef, RRef, PRef = RK45Referencia(estado0, tFinal)

    print("\n--- Euler ---")
    for h in tamaniosPaso:
        tA, TA, RA, PA = Euler(h, sistema, estado0, tFinal)
        error = errorRelativoGlobal(tRef, TRef, RRef, PRef, tA, TA, RA, PA)
        print("  h =", h, "-> error relativo global:", round(error, 8))

    print("\n--- Euler Mejorado ---")
    for h in tamaniosPaso:
        tA, TA, RA, PA = EulerMejorado(h, sistema, estado0, tFinal)
        error = errorRelativoGlobal(tRef, TRef, RRef, PRef, tA, TA, RA, PA)
        print("  h =", h, "-> error relativo global:", round(error, 8))

    print("\n--- Runge-Kutta RK4 ---")
    for h in tamaniosPaso:
        tA, TA, RA, PA = RungeKutta(h, sistema, estado0, tFinal)
        error = errorRelativoGlobal(tRef, TRef, RRef, PRef, tA, TA, RA, PA)
        print("  h =", h, "-> error relativo global:", round(error, 8))


# =============================================================================
# ESCENARIOS DE INTERVENCIÓN
# Cada escenario modifica los parámetros globales y corre los tres métodos
# =============================================================================

def correrEscenario(nombre, k1v, k2v, gammav, deltav, alphav, betav, k_sigv, estado0, tFinal, h=0.05):
    global k1, k2, gamma, delta, alpha, beta, k_sig

    k1    = k1v
    k2    = k2v
    gamma = gammav
    delta = deltav
    alpha = alphav
    beta  = betav
    k_sig = k_sigv

    print("\n" + "-"*50)
    print("ESCENARIO:", nombre)
    print("-"*50)
    print("k1 =", round(k1, 4), "| k2 =", round(k2, 4),
          "| gamma =", round(gamma, 4), "| delta =", round(delta, 4))
    print("alpha =", round(alpha, 4), "| beta =", beta, "| k_sig =", k_sig)

    # Verificar condición de viabilidad térmica del informe
    lhs = (k1 * delta) / (k2 * gamma)
    rhs = (T_crit - T_amb) / R_obj
    print("Viabilidad (lhs < rhs):", round(lhs, 6), "<", round(rhs, 6), "->", lhs < rhs)

    # Punto de equilibrio teórico
    P_eq = delta * R_obj / gamma
    T_eq = T_amb + (k1 * delta * R_obj) / (k2 * gamma)
    print("Equilibrio teórico: P* =", round(P_eq, 4), "W | T* =", round(T_eq, 4), "°C")

    tE,  TE,  RE,  PE  = Euler(h, sistema, estado0, tFinal)
    tEM, TEM, REM, PEM = EulerMejorado(h, sistema, estado0, tFinal)
    tRK, TRK, RRK, PRK = RungeKutta(h, sistema, estado0, tFinal)

    return (tE, TE, RE, PE), (tEM, TEM, REM, PEM), (tRK, TRK, RRK, PRK)


def correrTodosLosEscenarios(estado0, tFinal):
    print("\n" + "="*60)
    print("SIMULACIÓN DE LOS CUATRO ESCENARIOS DE INTERVENCIÓN")
    print("="*60)

    # Parámetros base — hardware × factores de escala
    k1_b    = kappa0 * (fp * Nc)
    k2_b    = eta0   * (Phi * Hd)
    gamma_b = gamma0 * (Nh * fp)
    delta_b = delta0 / min(v_ram, v_bus)
    alpha_b = alpha0 * (Nh / Nc)
    beta_b  = 12.0
    k_sig_b = 0.5

    resultados = {}

    # Escenario 0: Base — sin modificaciones
    resultados["Base"] = correrEscenario(
        "Base (control)",
        k1_b, k2_b, gamma_b, delta_b, alpha_b, beta_b, k_sig_b,
        estado0, tFinal
    )

    # Escenario 1: Undervolting — alpha0 al 50%
    # Modificación: alpha = alpha0 * 0.5 * (Nh / Nc)
    alpha_soft = (alpha0 * 0.5) * (Nh / Nc)
    resultados["Undervolting"] = correrEscenario(
        "Undervolting (perfil conservador — alpha al 50%)",
        k1_b, k2_b, gamma_b, delta_b, alpha_soft, beta_b, k_sig_b,
        estado0, tFinal
    )

    # Escenario 2: Base refrigerante — flujo de aire duplicado
    # Modificación: Phi * 2 -> k2 = eta0 * (Phi*2) * Hd
    Phi_aumentado = Phi * 2.0
    k2_refrig = eta0 * (Phi_aumentado * Hd)
    resultados["Refrigerante"] = correrEscenario(
        "Hardware ligero (base refrigerante — Phi x2)",
        k1_b, k2_refrig, gamma_b, delta_b, alpha_b, beta_b, k_sig_b,
        estado0, tFinal
    )

    # Escenario 3: Metal líquido — conductancia del disipador triplicada
    # Modificación: Hd * 3 -> k2 = eta0 * Phi * (Hd*3)
    Hd_metalico = Hd * 3.0
    k2_metalico = eta0 * (Phi * Hd_metalico)
    resultados["MetalLiquido"] = correrEscenario(
        "Hardware profundo (pasta de metal líquido — Hd x3)",
        k1_b, k2_metalico, gamma_b, delta_b, alpha_b, beta_b, k_sig_b,
        estado0, tFinal
    )

    # Restaurar parámetros base al terminar
    global k1, k2, gamma, delta, alpha, beta, k_sig
    k1    = k1_b
    k2    = k2_b
    gamma = gamma_b
    delta = delta_b
    alpha = alpha_b
    beta  = beta_b
    k_sig = k_sig_b

    return resultados


# =============================================================================
# EJECUCIÓN PRINCIPAL
# =============================================================================

estado0 = [T0, R0, P0]

print("="*60)
print("PARÁMETROS DEL MODELO")
print("="*60)
print("Variables de hardware:")
print("  Nc =", Nc, "| Nh =", Nh, "| fp =", fp, "GHz")
print("  Phi =", Phi, "CFM | Hd =", Hd, "W/°C")
print("  v_ram =", v_ram, "MT/s | v_bus =", v_bus, "GT/s")
print()
print("Constantes del modelo:")
print("  k1    =", round(k1, 6),    "  kappa0 * (fp * Nc)   =", round(kappa0, 4), "* (", fp, "*", Nc, ")")
print("  k2    =", round(k2, 6),    "  eta0   * (Phi * Hd)  =", round(eta0, 4),   "* (", Phi, "*", Hd, ")")
print("  gamma =", round(gamma, 6), "  gamma0 * (Nh * fp)   =", round(gamma0, 4), "* (", Nh, "*", fp, ")")
print("  delta =", round(delta, 6), "  delta0 / min(v_ram, v_bus) =", delta0, "/ min(", v_ram, ",", v_bus, ")")
print("  alpha =", round(alpha, 6), "  alpha0 * (Nh / Nc)   =", round(alpha0, 4), "* (", Nh, "/", Nc, ")")
print("  beta  =", beta)
print("  k_sig =", k_sig)

print("\nCondición de viabilidad térmica: k1*delta / (k2*gamma) < (T_crit - T_amb) / R_obj")
lhs = (k1 * delta) / (k2 * gamma)
rhs = (T_crit - T_amb) / R_obj
print("  Lado izquierdo:", round(lhs, 6))
print("  Lado derecho:  ", round(rhs, 6))
print("  ¿Se cumple?    ", lhs < rhs)

P_eq = delta * R_obj / gamma
T_eq = T_amb + (k1 * delta * R_obj) / (k2 * gamma)
print("\nEquilibrio teórico base:")
print("  P* =", round(P_eq, 4), "W")
print("  T* =", round(T_eq, 4), "°C")
print("  R* =", R_obj, "ops/s")

print("\n" + "="*60)
print("PRUEBA RÁPIDA — h = 0.1 s, t_final =", t_final, "s")
print("="*60)
Euler(0.1, sistema, estado0, t_final)
EulerMejorado(0.1, sistema, estado0, t_final)
RungeKutta(0.1, sistema, estado0, t_final)
RK45Referencia(estado0, t_final)

analisisError(estado0, t_final)

resultados = correrTodosLosEscenarios(estado0, t_final)
