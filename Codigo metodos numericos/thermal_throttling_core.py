import math
from scipy.integrate import solve_ivp
import numpy as np


# PARAMETROS

# tasa de calentamiento        
k1    = 0.052    

# disipación térmica            
k2    = 0.10  

# eficiencia computacional 
gamma = 1.0   

# inercia del rendimiento     
delta = 0.105  

# agresividad del SO         
alpha = 1.6    

# amplitud máxima del throttling 
beta  = 12.0   

# agresividad de la sigmoide     
k = 0.5      


# parametros del entorno
T_amb  = 25      # temperatura ambiente 
T_crit = 90      # maxima temperatura admitica
R_obj  = 1000    # operaciones de punto flotante objetivo
R_min  = 50      # minimo de operaciones punto flotante
P_min  = 10      # potencia minima fisica

# condiciones iniciales
T0 = 45     
R0 = 0       
P0 = 15     

# tiempo de simulación
t_inicio = 0
t_final  = 300   


# SISTEMA DE ECUACIONES DIFERENCIALES

def sistema(estado):
    T, R, P = estado

    # Ecuación 1: Temperatura 
    dT_dt = k1 * P - k2 * (T - T_amb)

    # Ecuación 2: Rendimiento 
    dR_dt = gamma * P - delta * R

    # Ecuación 3: Potencia 
    throttling = beta / (1 + math.exp(-k * (T - T_crit)))
    dP_dt = alpha * (R_obj - R) - throttling

    return [dT_dt, dR_dt, dP_dt]


def aplicarFrontera(estado):
    # P no puede caer por debajo de P_min 
    estado[2] = max(P_min, estado[2])
    return estado


# METODO 1: EULER 

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

    print("Euler con h =", h, "-> T:", round(TSalida[-1], 1),
          "°C | R:", round(RSalida[-1], 1), "GFLOPS | P:", round(PSalida[-1], 1), "W")
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

    print("Euler Mejorado con h =", h, "-> T:", round(TSalida[-1], 1),
          "°C | R:", round(RSalida[-1], 1), "GFLOPS | P:", round(PSalida[-1], 1), "W")
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

    print("Runge-Kutta con h =", h, "-> T:", round(TSalida[-1], 1),
          "°C | R:", round(RSalida[-1], 1), "GFLOPS | P:", round(PSalida[-1], 1), "W")
    return tSalida, TSalida, RSalida, PSalida


# =============================================================================
# SOLUCIONADOR DE REFERENCIA: RK45 (SciPy)
# Solo para validación — no es un método propio
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

    print("RK45 referencia -> T:", round(TSalida[-1], 1),
          "°C | R:", round(RSalida[-1], 1), "GFLOPS | P:", round(PSalida[-1], 1), "W")
    return tSalida, TSalida, RSalida, PSalida


# =============================================================================
# ANÁLISIS DE ERROR
# E_rel(h) = max_t || x_aprox - x_RK45 || / || x_RK45 ||
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
        print("  h =", h, "-> error relativo global:", round(error, 4))

    print("\n--- Euler Mejorado ---")
    for h in tamaniosPaso:
        tA, TA, RA, PA = EulerMejorado(h, sistema, estado0, tFinal)
        error = errorRelativoGlobal(tRef, TRef, RRef, PRef, tA, TA, RA, PA)
        print("  h =", h, "-> error relativo global:", round(error, 4))

    print("\n--- Runge-Kutta RK4 ---")
    for h in tamaniosPaso:
        tA, TA, RA, PA = RungeKutta(h, sistema, estado0, tFinal)
        error = errorRelativoGlobal(tRef, TRef, RRef, PRef, tA, TA, RA, PA)
        print("  h =", h, "-> error relativo global:", round(error, 4))


# =============================================================================
# ESCENARIOS DE INTERVENCIÓN
# =============================================================================

def correrEscenario(nombre, k2v, alphav, estado0, tFinal, h=0.05):
    global k2, alpha

    k2    = k2v
    alpha = alphav

    print("\n" + "-"*50)
    print("ESCENARIO:", nombre)
    print("-"*50)
    print("k2 =", round(k2, 4), "| alpha =", round(alpha, 4))

    lhs = (k1 * delta) / (k2 * gamma)
    rhs = (T_crit - T_amb) / R_obj
    print("Viabilidad (lhs < rhs):", round(lhs, 4), "<", round(rhs, 4), "->", lhs < rhs)

    P_eq = delta * R_obj / gamma
    T_eq = T_amb + (k1 * delta * R_obj) / (k2 * gamma)
    print("Equilibrio: P* =", round(P_eq, 1), "W | T* =", round(T_eq, 1), "°C | R* =", R_obj, "GFLOPS")

    tE,  TE,  RE,  PE  = Euler(h, sistema, estado0, tFinal)
    tEM, TEM, REM, PEM = EulerMejorado(h, sistema, estado0, tFinal)
    tRK, TRK, RRK, PRK = RungeKutta(h, sistema, estado0, tFinal)

    return (tE, TE, RE, PE), (tEM, TEM, REM, PEM), (tRK, TRK, RRK, PRK)


def correrTodosLosEscenarios(estado0, tFinal):
    global k2, alpha

    print("\n" + "="*60)
    print("SIMULACIÓN DE ESCENARIOS DE INTERVENCIÓN")
    print("="*60)

    k2_base    = 0.10
    alpha_base = 1.6

    resultados = {}

    # Escenario 0: Base
    resultados["Base"] = correrEscenario(
        "Base (control)",
        k2_base, alpha_base,
        estado0, tFinal
    )

    # Escenario 1: Undervolting — alpha reducida a la cuarta parte
    resultados["Undervolting"] = correrEscenario(
        "Undervolting (alpha / 4)",
        k2_base, alpha_base / 4,
        estado0, tFinal
    )

    # Escenario 2: Base refrigerante — k2 duplicada
    resultados["Refrigerante"] = correrEscenario(
        "Base refrigerante (k2 x2)",
        k2_base * 2, alpha_base,
        estado0, tFinal
    )

    # Escenario 3: Metal líquido — k2 triplicada
    resultados["MetalLiquido"] = correrEscenario(
        "Metal líquido (k2 x3)",
        k2_base * 3, alpha_base,
        estado0, tFinal
    )

    # Restaurar parámetros base
    k2    = k2_base
    alpha = alpha_base

    return resultados


# =============================================================================
# EJECUCIÓN PRINCIPAL
# =============================================================================

estado0 = [T0, R0, P0]

print("="*60)
print("PARÁMETROS DEL MODELO")
print("="*60)
print("k1    =", k1,    "  Tasa de calentamiento")
print("k2    =", k2,    "  Disipación térmica")
print("gamma =", gamma, "  Eficiencia computacional")
print("delta =", delta, "  Inercia del rendimiento")
print("alpha =", alpha, "  Agresividad del gobernador")
print("beta  =", beta,  "  Amplitud de throttling")
print("k =", k, "  Pendiente sigmoide")
print()
print("T_amb =", T_amb, "°C | T_crit =", T_crit, "°C")
print("R_obj =", R_obj, "GFLOPS | R_min =", R_min, "GFLOPS | P_min =", P_min, "W")

print("\nCondición de viabilidad: k1*delta / (k2*gamma) < (T_crit - T_amb) / R_obj")
lhs = (k1 * delta) / (k2 * gamma)
rhs = (T_crit - T_amb) / R_obj
print("  LHS:", round(lhs, 4))
print("  RHS:", round(rhs, 4))
print("  ¿Viable?", lhs < rhs)

P_eq = delta * R_obj / gamma
T_eq = T_amb + (k1 * delta * R_obj) / (k2 * gamma)
print("\nEquilibrio teórico:")
print("  P* =", round(P_eq, 1), "W")
print("  T* =", round(T_eq, 1), "°C")
print("  R* =", R_obj, "GFLOPS")

print("\n" + "="*60)
print("PRUEBA RÁPIDA — h = 0.1 s, t_final =", t_final, "s")
print("="*60)
Euler(0.1, sistema, estado0, t_final)
EulerMejorado(0.1, sistema, estado0, t_final)
RungeKutta(0.1, sistema, estado0, t_final)
RK45Referencia(estado0, t_final)

analisisError(estado0, t_final)
resultados = correrTodosLosEscenarios(estado0, t_final)