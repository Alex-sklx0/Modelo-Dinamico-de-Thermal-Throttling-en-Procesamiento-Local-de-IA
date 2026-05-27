import math
from scipy.integrate import solve_ivp
import numpy as np


# variables base de hardware 

Nc      = 6        # nucleos procesador
Nh      = 12       # hilos 
fp      = 3.6      # frecuencia de reloj 
v_ram   = 3200     # velocidad de la RAM 
v_bus   = 16.0     # velocidad del bus 
flujo_aire = 45.0     # flujo de aire del disipador 
conduc_term      = 0.004    # conductancia termica del disipador 

# ajuste dimensional 

k1_ajuste    = 0.0024   
k2_ajuste    = 0.556    
gamma_ajuste = 0.0231  
delta_ajuste = 336.0    
alpha_ajuste = 0.8      


# constantes del modelo calculadas desde el hardware

k1    = k1_ajuste    * (fp * Nc)                  # tasa de calentamiento  
k2    = k2_ajuste    * (flujo_aire * conduc_term) # disipacion termica      
gamma = gamma_ajuste * (Nh * fp)                  # eficiencia computacional 
delta = delta_ajuste / min(v_ram, v_bus * 1000)   # friccion de memoria 
alpha = alpha_ajuste * (Nh / Nc)                  # agresividad del SO 

# estos dos se calibran directamente, no dependen de hardware medible
beta  = 12.0   # recorte de potencia del firmware
k_sig = 0.5    # caída de rendimiento impuesta por el firmware


# parametros del entorno
T_amb  = 25      # temperatura ambiente 
T_crit = 90      # temperatira maxima
R_obj  = 1000    # operaciones punto flotante objetivo
R_min  = 50      # operaciones punto flotante minimo
P_min  = 10      # potencia minima fisica 

# condiciones iniciales
T0 = 45
R0 = 0
P0 = 15

# tiempo de simulacion
t_inicio = 0
t_final  = 300


# sistema de ecuaciones diferenciales

def sistema(estado):
    T, R, P = estado

    dT_dt = k1 * P - k2 * (T - T_amb)
    dR_dt = gamma * P - delta * R
    throttling = beta / (1 + math.exp(-k_sig * (T - T_crit)))
    dP_dt = alpha * (R_obj - R) - throttling

    return [dT_dt, dR_dt, dP_dt]


def aplicarFrontera(estado):
    estado[2] = max(P_min, estado[2])
    return estado


# metodo 1: euler

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

    print("Euler con h =", h, ", resultados T:", round(TSalida[-1], 1),
          "°C, R:", round(RSalida[-1], 1), "GFLOPS, P:", round(PSalida[-1], 1), "W")
    return tSalida, TSalida, RSalida, PSalida


# metodo 2: euler mejorado

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

    print("Euler Mejorado con h =", h, ", resultados T:", round(TSalida[-1], 1),
          "°C, R:", round(RSalida[-1], 1), "GFLOPS, P:", round(PSalida[-1], 1), "W")
    return tSalida, TSalida, RSalida, PSalida


# metodo 3: runge-kutta 4

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

    print("RK4 con h =", h, ", resultados T:", round(TSalida[-1], 1),
          "°C, R:", round(RSalida[-1], 1), "GFLOPS, P:", round(PSalida[-1], 1), "W")
    return tSalida, TSalida, RSalida, PSalida


# solucionador de referencia rk45 (scipy)

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

    print("RK45 referencia, resultados T:", round(TSalida[-1], 1),
          "°C, R:", round(RSalida[-1], 1), "GFLOPS, P:", round(PSalida[-1], 1), "W")
    return tSalida, TSalida, RSalida, PSalida


# analisis de error

def errorAbsoluto(valorReal, valorAprox):
    print("valor real:     ", round(valorReal, 4))
    print("error absoluto: ", round(abs(valorReal - valorAprox), 4), "\n")

def errorRelativo(valorReal, valorAprox):
    print("valor real:     ", round(valorReal, 4))
    print("error relativo: ", round(abs(valorReal - valorAprox) / abs(valorReal), 6), "\n")

def diferenciaErrores(valorReal, vEuler, vEulerMejorado, vRungeKutta, variable="T"):
    errEuler         = abs(valorReal - vEuler)
    errEulerMejorado = abs(valorReal - vEulerMejorado)
    errRungeKutta    = abs(valorReal - vRungeKutta)

    print("variable:", variable)
    print("error absoluto Euler:          ", round(errEuler, 4))
    print("error absoluto Euler Mejorado: ", round(errEulerMejorado, 4))
    print("error absoluto Runge-Kutta:    ", round(errRungeKutta, 4))
    print("diferencia (Euler - Euler Mejorado):       ", round(errEuler - errEulerMejorado, 4))
    print("diferencia (Euler Mejorado - Runge-Kutta): ", round(errEulerMejorado - errRungeKutta, 4), "\n")

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

    print("\nanalisis de error relativo global vs RK45")

    tRef, TRef, RRef, PRef = RK45Referencia(estado0, tFinal)
    TReal = TRef[-1]
    RReal = RRef[-1]
    PReal = PRef[-1]

    print("\nEuler")
    for h in tamaniosPaso:
        tA, TA, RA, PA = Euler(h, sistema, estado0, tFinal)
        error = errorRelativoGlobal(tRef, TRef, RRef, PRef, tA, TA, RA, PA)
        print("  h =", h, " error relativo global:", round(error, 4))

    print("\nEuler Mejorado")
    for h in tamaniosPaso:
        tA, TA, RA, PA = EulerMejorado(h, sistema, estado0, tFinal)
        error = errorRelativoGlobal(tRef, TRef, RRef, PRef, tA, TA, RA, PA)
        print("  h =", h, " error relativo global:", round(error, 4))

    print("\nRK4")
    for h in tamaniosPaso:
        tA, TA, RA, PA = RungeKutta(h, sistema, estado0, tFinal)
        error = errorRelativoGlobal(tRef, TRef, RRef, PRef, tA, TA, RA, PA)
        print("  h =", h, " error relativo global:", round(error, 4))

    # comparacion directa en el estado final con h = 0.05
    h_ref = 0.05
    print("\ncomparacion directa en t =", tFinal, "s con h =", h_ref)

    _, TE_f,  RE_f,  PE_f  = Euler(h_ref, sistema, estado0, tFinal)
    _, TEM_f, REM_f, PEM_f = EulerMejorado(h_ref, sistema, estado0, tFinal)
    _, TRK_f, RRK_f, PRK_f = RungeKutta(h_ref, sistema, estado0, tFinal)

    diferenciaErrores(TReal, TE_f[-1], TEM_f[-1], TRK_f[-1], variable="T (°C)")
    diferenciaErrores(RReal, RE_f[-1], REM_f[-1], RRK_f[-1], variable="R (GFLOPS)")
    diferenciaErrores(PReal, PE_f[-1], PEM_f[-1], PRK_f[-1], variable="P (W)")


# casos de prueba

def correrCaso(nombre, params, estado0=None, tFinal=300, h=0.05):
    global k1, k2, gamma, delta, alpha, beta, k_sig, R_obj

    if estado0 is None:
        estado0 = [T0, R0, P0]

    # guardar base
    k1_b    = k1;    k2_b = k2;    gamma_b = gamma; delta_b = delta
    alpha_b = alpha; beta_b = beta; ksig_b  = k_sig; Robj_b  = R_obj

    # aplicar parametros del caso
    k1    = params.get("k1",    k1)
    k2    = params.get("k2",    k2)
    gamma = params.get("gamma", gamma)
    delta = params.get("delta", delta)
    alpha = params.get("alpha", alpha)
    beta  = params.get("beta",  beta)
    k_sig = params.get("k_sig", k_sig)
    R_obj = params.get("R_obj", R_obj)

    print("\ncaso:", nombre)
    print("k1 =", round(k1,4), "| k2 =", round(k2,4), "| gamma =", round(gamma,4),
          "| delta =", round(delta,6), "| alpha =", round(alpha,4),
          "| beta =", beta, "| k_sig =", k_sig, "| R_obj =", R_obj)



    P_eq = delta * R_obj / gamma
    T_eq = T_amb + (k1 * delta * R_obj) / (k2 * gamma)
    print("equilibrio teorico: P* =", round(P_eq,1), "W | T* =", round(T_eq,1), "°C | R* =", R_obj, "GFLOPS")

    tRK, TRK, RRK, PRK = RungeKutta(h, sistema, estado0, tFinal)

    # restaurar base
    k1    = k1_b;   k2    = k2_b;   gamma = gamma_b; delta = delta_b
    alpha = alpha_b; beta = beta_b; k_sig = ksig_b;  R_obj = Robj_b

    return tRK, TRK, RRK, PRK


def correrTodosLosCasos():
    k1_a = k1; k2_a = k2; gamma_a = gamma; delta_a = delta

    casos = [
        ("1 - base estable",
         {"k1": k1_a, "k2": k2_a, "gamma": gamma_a, "delta": delta_a,
          "alpha": 1.6, "beta": 12, "k_sig": 0.5, "R_obj": 1000}),

        ("2 - alta carga oscilatorio",
         {"k1": k1_a, "k2": k2_a, "gamma": gamma_a, "delta": delta_a,
          "alpha": 1.6, "beta": 12, "k_sig": 0.5, "R_obj": 1500}),

        ("3 - undervolting lento pero estable",
         {"k1": k1_a, "k2": k2_a, "gamma": gamma_a, "delta": delta_a,
          "alpha": 0.4, "beta": 12, "k_sig": 0.5, "R_obj": 1000}),

        ("4 - sobrevoltaje overshoot",
         {"k1": k1_a, "k2": k2_a, "gamma": gamma_a, "delta": delta_a,
          "alpha": 3.2, "beta": 12, "k_sig": 0.5, "R_obj": 1000}),

        ("5 - mejor disipacion muy estable",
         {"k1": k1_a, "k2": k2_a * 2, "gamma": gamma_a, "delta": delta_a,
          "alpha": 1.6, "beta": 12, "k_sig": 0.5, "R_obj": 1000}),

        ("6 - mala disipacion oscilatorio fuerte",
         {"k1": k1_a, "k2": k2_a * 0.4, "gamma": gamma_a, "delta": delta_a,
          "alpha": 1.6, "beta": 12, "k_sig": 0.5, "R_obj": 1000}),

        ("7 - CPU eficiente bajo consumo",
         {"k1": k1_a, "k2": k2_a, "gamma": gamma_a * 2, "delta": delta_a,
          "alpha": 1.6, "beta": 12, "k_sig": 0.5, "R_obj": 1000}),

        ("8 - CPU ineficiente alta potencia",
         {"k1": k1_a, "k2": k2_a, "gamma": gamma_a * 0.5, "delta": delta_a,
          "alpha": 1.6, "beta": 12, "k_sig": 0.5, "R_obj": 1000}),

        ("9 - throttling suave oscilacion leve",
         {"k1": k1_a, "k2": k2_a, "gamma": gamma_a, "delta": delta_a,
          "alpha": 1.6, "beta": 5, "k_sig": 0.2, "R_obj": 1300}),

        ("10 - throttling agresivo cortes bruscos",
         {"k1": k1_a, "k2": k2_a, "gamma": gamma_a, "delta": delta_a,
          "alpha": 1.6, "beta": 25, "k_sig": 2.0, "R_obj": 1300}),
    ]

    resultados = {}
    for nombre, params in casos:
        resultados[nombre] = correrCaso(nombre, params)

    return resultados


# ejecucion principal

estado0 = [T0, R0, P0]

print("hardware del equipo simulado")
print("Nc =", Nc, "nucleos | Nh =", Nh, "hilos | fp =", fp, "GHz")
print("v_ram =", v_ram, "MT/s | v_bus =", v_bus, "GT/s")
print("flujo_aire =", flujo_aire, "CFM | conduc_term =", conduc_term, "W/°C")

print("\nparametros derivados del hardware")
print("k1    =", round(k1, 4),    "  tasa de calentamiento")
print("k2    =", round(k2, 4),    "  disipacion termica")
print("gamma =", round(gamma, 4), "  eficiencia computacional")
print("delta =", round(delta, 6), "  friccion de memoria")
print("alpha =", round(alpha, 4), "  agresividad del SO")
print("beta  =", beta,             "  recorte de potencia del firmware")
print("k_sig =", k_sig,            "  caída de rendimiento impuesta por el firmware")



P_eq = delta * R_obj / gamma
T_eq = T_amb + (k1 * delta * R_obj) / (k2 * gamma)
print("\nequilibrio teorico:")
print("  P* =", round(P_eq, 1), "W")
print("  T* =", round(T_eq, 1), "°C")
print("  R* =", R_obj, "GFLOPS")

print("\nprueba rapida con h = 0.1 s, t_final =", t_final, "s")
Euler(0.1, sistema, estado0, t_final)
EulerMejorado(0.1, sistema, estado0, t_final)
RungeKutta(0.1, sistema, estado0, t_final)
RK45Referencia(estado0, t_final)

analisisError(estado0, t_final)

print("\nsimulacion de todos los casos de prueba")
resultados = correrTodosLosCasos()