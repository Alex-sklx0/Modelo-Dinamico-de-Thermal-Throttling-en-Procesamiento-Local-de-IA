Enfocar el analisis mas en el rendimiento del procesador vs su temperatura, teniendo en cuenta otras variables que afectan su velocidad y potencia para llegar a un punto de equilibrio donde la temperatura sea aceptable y el rendimiento (en medidas como punto flotante o algo asi) tambien lo sea.

# Modelo Dinámico de Estabilidad Térmica y Rendimiento en Computadores de Propósito General

# Equipo

# Responsabilidades:

---

# Resumen

Se modela la dinámica del *thermal throttling* en procesadores de computadores de propósito general bajo cargas de trabajo sostenidas como un sistema de tres ecuaciones diferenciales no lineales acopladas que relacionan temperatura, potencia y throughput efectivo. La función de throttling logística (sigmoide) introduce una no linealidad suave pero irreducible que impide la solución analítica y divide el comportamiento del sistema en dos regímenes: aceleración libre y protección térmica. Se implementan tres métodos numéricos programados desde cero — Euler, Euler Mejorado y Runge-Kutta de cuarto orden (RK4) — y se realiza un análisis comparativo de error variando el tamaño de paso, validando contra el solucionador de referencia RK45. Se simulan cuatro escenarios de intervención — base, *undervolting*, mejora de disipación y cambio de pasta térmica — evaluando en cada uno si el sistema converge a un equilibrio estable con throughput viable. Los resultados se animan para ilustrar las trayectorias en el espacio de estados.

---

# 1. Introducción

## 1.1 Presentación del sistema

El sistema de estudio es la unidad de procesamiento central (CPU) de un computador de propósito general operando bajo cargas de trabajo sostenidas de alto rendimiento. En la arquitectura de Von Neumann, el procesador enfrenta una tensión permanente entre tres fuerzas en competencia: el planificador del sistema operativo, que inyecta potencia para maximizar el throughput efectivo; la generación de calor por efecto Joule, proporcional a esa potencia; y los mecanismos de protección del firmware, que reducen la energía para prevenir el daño físico irreversible del silicio.

Esta interacción produce una retroalimentación altamente no lineal. Cuando el sistema operativo sube la potencia, la temperatura sube; cuando la temperatura supera un umbral crítico, el firmware interviene recortando la potencia; al caer la potencia, el throughput cae por debajo del objetivo y el sistema operativo vuelve a demandar más energía. Dependiendo de los parámetros físicos del hardware, este ciclo puede converger a un equilibrio estable o mantenerse como una oscilación incontrolable que compromete la viabilidad operativa del equipo.

## 1.2 Relevancia

El fenómeno es transversal a cualquier computador de propósito general sometido a carga sostenida: servidores de cómputo científico, estaciones de trabajo de renderizado, equipos de procesamiento de datos en tiempo real. La relevancia del modelo reside en que permite predecir analíticamente si un conjunto de parámetros de hardware produce un sistema estable o inestable, sin necesidad de ejecutar la carga real hasta el punto de fallo. Esto tiene aplicación directa en el diseño de políticas de refrigeración, perfiles de energía del sistema operativo y selección de componentes.

En términos concretos, el sistema enfrenta tres fuerzas:

- El sistema operativo busca maximizar la productividad asignando la mayor potencia posible para maximizar el throughput con baja latencia.
- El procesador, por efecto Joule, incrementa su temperatura de forma proporcional a esa carga de trabajo.
- El firmware interviene como mecanismo de seguridad reduciendo la energía de forma progresiva pero agresiva para prevenir daños irreversibles en la arquitectura del chip.

Definir el equilibrio entre estas tres fuerzas permite predecir el "punto de fatiga" del hardware y diseñar intervenciones que optimicen la longevidad del equipo sin sacrificar su capacidad de cómputo.

## 1.3 Fenómeno de estudio

El *thermal throttling* es el fenómeno central. En términos de sistemas se define como la penalización que impone el hardware para reducir el throughput y la generación de calor cuando la temperatura del procesador amenaza con superar límites físicos seguros. El firmware no actúa como un interruptor binario: implementa el Escalado Dinámico de Frecuencia y Voltaje (DVFS) — Intel P-States, AMD Precision Boost — reduciendo la frecuencia de operación de forma progresiva y acelerada a medida que la temperatura se aproxima al umbral crítico.

Este fenómeno genera oscilaciones severas en cargas sostenidas: cuando el equipo entra en throttling profundo, el throughput se desploma por debajo de los umbrales mínimos de usabilidad, para luego intentar recuperarse una vez la temperatura desciende, creando un ciclo de inestabilidad que compromete la integridad del procesamiento.

### 1.3.1 Por qué no existe solución analítica

El sistema **no admite solución analítica exacta** por dos razones complementarias.

La primera es estructural. La función de throttling logístico introduce una no linealidad suave pero irreducible en la ecuación de control de potencia. A diferencia de un sistema lineal acoplado, cuya solución en forma cerrada existe siempre que los coeficientes sean constantes, la presencia de un término sigmoide en $T(t)$ impide desacoplar las tres ecuaciones mediante transformaciones estándar. No existe transformación de variables conocida que linealice simultáneamente los tres estados.

La segunda es analítica. Las tres ecuaciones están doblemente acopladas: $P$ aparece como término fuente en $\dot{T}$ y en $\dot{R}$; $R$ aparece en $\dot{P}$; y $T$ aparece en $\dot{P}$ a través de la función logística. Este acoplamiento circular impide integrar una ecuación de forma independiente y sustituir su resultado en las demás, que es el mecanismo que permitiría una solución en forma cerrada.

Por tanto, el uso de métodos numéricos no es una simplificación del problema sino la **única metodología válida** para estudiar el comportamiento completo del sistema.

## 1.4 Objetivos

El objetivo principal es modelar matemáticamente y simular mediante métodos numéricos la dinámica térmica y de rendimiento de un procesador bajo carga sostenida, identificando las condiciones bajo las cuales el sistema alcanza un estado de equilibrio estable.

Como objetivos específicos, se busca: implementar Euler, Euler Mejorado y Runge-Kutta de cuarto orden (RK4) programados desde cero para un sistema vectorial de tres estados; realizar un análisis comparativo de convergencia y error variando el tamaño de paso $h$ y validando contra el solucionador de referencia RK45; simular cuatro escenarios de intervención sobre el hardware y el software; y producir animaciones que ilustren las trayectorias en el espacio de estados.

## 1.5 Estructura del informe

La **Sección 2** desglosa el modelo matemático y justifica las constantes físicas. La **Sección 3** describe la metodología numérica, validación y herramientas. La **Sección 4** presenta el análisis de equilibrio, los escenarios de intervención y el análisis de error. La **Sección 5** sintetiza los hallazgos y reflexiona sobre el trabajo en equipo.

---

# 2. Metodología

## 2.1 Modelo matemático: sistema de ecuaciones diferenciales

El fenómeno se modela como un sistema de tres ecuaciones diferenciales ordinarias no lineales acopladas de primer orden. Las tres variables de estado son:

- $T(t)$: temperatura del procesador en el instante $t$ [°C]
- $P(t)$: potencia eléctrica asignada al procesador [W]
- $R(t)$: throughput efectivo del procesador (operaciones por segundo) [ops/s]

Las tres están acopladas: la potencia determina cuánto se calienta el procesador y cuán rápido procesa; la temperatura activa el throttling que recorta la potencia; la potencia recortada reduce el throughput, lo que impulsa al sistema operativo a demandar más potencia.

---

### Ecuación 1: Dinámica Térmica

$$\frac{dT}{dt} = k_1 P(t) - k_2 \bigl(T(t) - T_{amb}\bigr)$$

Esta ecuación describe la **evolución de la temperatura del procesador** en el tiempo. Es una aplicación directa del Modelo de Capacitancia Térmica Concentrada (*Lumped Capacitance Model*), donde el procesador se trata como un nodo único con una masa térmica $C_{th}$ y una resistencia térmica $R_{th}$ hacia el ambiente. El balance de energía canónico de este modelo es $C_{th} \frac{dT}{dt} = \dot{E}_{in} - \dot{E}_{out}$, donde la energía entrante es la potencia eléctrica disipada como calor (Efecto Joule) y la energía saliente sigue la Ley de Enfriamiento de Newton. Dividiendo entre $C_{th}$ se obtiene la forma exacta de la ecuación, con $k_1 \equiv \frac{1}{C_{th}}$ y $k_2 \equiv \frac{1}{R_{th}C_{th}}$.

El término $k_1 P(t)$ es la **tasa de calentamiento**: la potencia eléctrica consumida se disipa parcialmente como calor. La constante $k_1$ [°C/J] cuantifica cuántos grados de temperatura produce cada julio de energía entregada; depende de la arquitectura del chip a través de $\kappa_0$, que agrupa la ineficiencia térmica de la litografía del silicio.

El término $-k_2(T - T_{amb})$ representa la **disipación térmica** hacia el ambiente. La constante $k_2$ [s⁻¹] cuantifica la eficiencia del sistema de disipación: cuando $T = T_{amb}$ el procesador no pierde calor neto; cuando $T \gg T_{amb}$ la disipación es máxima. Depende físicamente del flujo de aire $\Phi_{aire}$ y la conductancia del disipador $H_d$.

*Referencia: Incropera, F. P., & DeWitt, D. P. — Fundamentos de transferencia de calor y masa, cap. Conducción transitoria.*

---

### Ecuación 2: Dinámica de Rendimiento

$$\frac{dR}{dt} = \gamma P(t) - \delta R(t)$$

Esta ecuación describe la **evolución del throughput efectivo del procesador**. Su forma proviene de los modelos de fluidos en teoría de colas (*Fluid Queueing Model*), donde la tasa de cambio de la variable de rendimiento depende de una tasa de inyección de trabajo y una tasa de decaimiento proporcional al nivel actual de saturación. La ecuación general de estos modelos es $\frac{dx}{dt} = \lambda(t) - \mu x(t)$, donde $\lambda(t)$ es la tasa de llegada de trabajo y $\mu x(t)$ la fricción proporcional a la carga actual. La variable de estado $R(t)$ actúa como la variable de flujo $x(t)$.

El término $\gamma P(t)$ representa la **aceleración computacional**: a mayor potencia entregada, mayor frecuencia de operación y mayor throughput de cómputo. La constante $\gamma$ mide la eficiencia con que la energía se convierte en operaciones útiles, determinada por la capacidad de procesamiento paralelo del hardware: número de unidades de ejecución activas y frecuencia de operación.

El término $-\delta R(t)$ representa la **fricción computacional**: ningún sistema acelera indefinidamente. Al aumentar el throughput, se saturan los recursos compartidos del sistema — buses de comunicación, controladores de memoria, colas de instrucciones — introduciendo un decaimiento natural proporcional al nivel de actividad actual. La constante $\delta$ [s⁻¹] cuantifica esta fricción, inversamente proporcional al ancho de banda disponible en la ruta crítica de datos.

*Referencia: Kleinrock, L. — Queueing Systems, Vol. II: Computer Applications, cap. Fluid Approximations.*

---

### Ecuación 3: Control de Potencia con Throttling Logístico

$$\frac{dP}{dt} = \alpha \bigl(R_{obj} - R(t)\bigr) - \frac{\beta}{1 + e^{-k(T(t) - T_{crit})}}$$

Esta ecuación es la **lógica de control de potencia** del sistema operativo y el firmware, y contiene el término no lineal que hace al sistema matemáticamente irresoluble de forma analítica.

El término $\alpha(R_{obj} - R(t))$ representa la **demanda del sistema operativo**. En la teoría de control automático, este término corresponde exactamente a la acción de un controlador proporcional (componente P de un PID): la ganancia $\alpha$ actúa sobre el error $e(t) = R_{obj} - R(t)$ para ajustar la potencia asignada. Cuando el throughput actual está por debajo del objetivo, el planificador de energía incrementa la potencia proporcionalmente al déficit. Un $\alpha$ alto corresponde al perfil "Máximo rendimiento"; un $\alpha$ bajo, a "Ahorro de batería".

El término $-\frac{\beta}{1 + e^{-k(T - T_{crit})}}$ modela el **throttling del firmware** mediante una función logística (sigmoide). A diferencia de un interruptor abrupto, esta función produce una transición continua y acelerada alrededor del umbral crítico $T_{crit}$. El comportamiento en los dos regímenes es:

- Cuando $T \ll T_{crit}$: el término logístico $\to 0$. El firmware no interviene.
- Cuando $T = T_{crit}$: el término vale exactamente $\beta/2$. El firmware ejerce la mitad de su capacidad máxima de corte.
- Cuando $T \gg T_{crit}$: el término $\to \beta$. El firmware impone el corte máximo de potencia.

El parámetro $k$ [°C⁻¹] controla la agresividad de la transición: un $k$ alto produce una curva casi vertical (throttling casi instantáneo al cruzar $T_{crit}$); un $k$ bajo, una respuesta más gradual. Su valor se fija durante la calibración de la simulación.

La elección de la función logística se justifica por dos criterios técnicos:

**Realismo físico — DVFS.** Los procesadores modernos no esperan a sobrepasar un umbral térmico para actuar. Implementan el Escalado Dinámico de Frecuencia y Voltaje (DVFS) — Intel P-States, AMD Precision Boost — reduciendo la frecuencia de forma progresiva y acelerada a medida que la temperatura se aproxima al límite. Brooks y Martonosi, en *Dynamic Thermal Management for High-Performance Microprocessors*, documentan que estos mecanismos imponen caídas de rendimiento asimétricas cuya severidad aumenta de forma no lineal frente a la magnitud de la carga térmica. La curva sigmoide modela esta transición gradual y acelerada con mayor fidelidad que una función que permanece exactamente en cero hasta $T_{crit}$ y luego actúa de golpe.

**Estabilidad matemática — diferenciabilidad $C^\infty$.** La función logística es infinitamente diferenciable en todo $\mathbb{R}$: no presenta discontinuidades en ninguna derivada en ningún punto, incluyendo la vecindad de $T_{crit}$. Esto garantiza que RK4, al evaluar sus cuatro pendientes en el intervalo $[t_n, t_{n+1}]$, nunca encuentre un cambio brusco de curvatura independientemente del régimen térmico. El orden de convergencia del método se mantiene globalmente, no solo por tramos. Nocedal y Wright, en *Numerical Optimization*, establecen que la diferenciabilidad continua de orden superior es la condición que preserva el orden local de los métodos de integración explícitos.

La constante $\beta$ [W] acota la potencia máxima de corte que el firmware puede imponer. Un fabricante conservador usará un $\beta$ alto; uno orientado al rendimiento sostenido, un $\beta$ bajo.

*Referencias: Ogata, K. — Ingeniería de control moderna; Ames, A. D. et al. — Control Barrier Functions: Theory and Applications; Nocedal, J. & Wright, S. J. — Numerical Optimization; Brooks, D. & Martonosi, M. — Dynamic Thermal Management for High-Performance Microprocessors.*

---

## 2.2 Definición de constantes

Hasta aquí el modelo contiene: $k_1$, $k_2$, $\gamma$, $\delta$, $\alpha$, $\beta$, $k$. Para garantizar que el modelo refleje la realidad del hardware y permita simular intervenciones físicas, las constantes se derivan agrupando especificaciones tangibles de los componentes.

### 2.2.1 Variables base de hardware

Estas son las especificaciones del equipo que alimentan los parámetros del modelo. Todas son fijas al momento de adquirir el hardware; los únicos parámetros intervenibles entre escenarios son $\Phi_{aire}$ (base refrigerante o limpieza) y $H_d$ (cambio de pasta térmica).

| Símbolo | Unidad | Descripción |
|---------|--------|---|
| $N_c$ | — | Número de núcleos físicos del procesador |
| $N_h$ | — | Número de hilos lógicos (threads) |
| $f_p$ | GHz | Frecuencia de reloj del procesador |
| $v_{ram}$ | MT/s | Velocidad de la memoria RAM (megatransferencias por segundo) |
| $v_{bus}$ | GT/s | Velocidad del bus PCIe (gigatransferencias por segundo) |
| $\Phi_{aire}$ | CFM | Tasa de flujo de aire de los ventiladores (pies cúbicos por minuto) |
| $H_d$ | W/°C | Conductancia térmica del disipador de calor |

### 2.2.2 Factores de escala empíricos

Cada constante global se expresa como el producto de un **factor de escala empírico** (subíndice $0$) y una combinación de variables de hardware. Los factores de escala agrupan fenómenos microscópicos no modelados individualmente (resistencia del silicio, geometría del chasis, overhead del kernel) y ajustan las unidades para garantizar la consistencia dimensional del modelo.

**Dinámica Térmica:**

- $k_1 = \kappa_0 \cdot (f_p \cdot N_c)$ [°C·s⁻¹·W⁻¹]. A mayor frecuencia y más núcleos activos, más transistores conmutan simultáneamente y mayor disipación de energía como calor (Efecto Joule). El factor $\kappa_0$ captura la resistencia térmica específica del proceso litográfico del silicio y equivale a $1/C_{th}$ del modelo de Incropera.

- $k_2 = \eta_0 \cdot (\Phi_{aire} \cdot H_d)$ [s⁻¹]. La capacidad de enfriamiento depende del flujo de aire $\Phi_{aire}$ [CFM] y la conductancia del disipador $H_d$ [W/°C]. El factor $\eta_0$ corrige la geometría real del chasis (obstrucciones en rejillas, flujo no laminar, presión ambiental) y equivale a $1/(R_{th} C_{th})$.

**Dinámica de Rendimiento:**

- $\gamma = \gamma_0 \cdot (N_h \cdot f_p)$ [ops·s⁻²·W⁻¹]. El throughput bruto de cómputo es proporcional al número de unidades de ejecución lógicas y a la frecuencia del reloj, siguiendo la Ley de Hierro del Rendimiento (*Iron Law*). El factor $\gamma_0$ representa la eficiencia de ejecución por ciclo de la arquitectura (IPC efectivo para la carga de trabajo estudiada).

- $\delta = \frac{\delta_0}{\min(v_{ram},\, v_{bus})}$ [s⁻¹]. Según el Modelo Roofline, cuando el sistema opera en el régimen *memory bound*, el cuello de botella real es el ancho de banda por el que los datos llegan al procesador. El decaimiento del throughput es inversamente proporcional a la velocidad del enlace más lento, ya sea la RAM (MT/s) o el bus PCIe (GT/s). El factor $\delta_0$ cuantifica el overhead intrínseco del sistema operativo.

**Control de Potencia:**

- $\alpha = \alpha_0 \cdot (N_h / N_c)$ [W·s⁻¹·(ops/s)⁻¹]. La ratio $N_h/N_c$ es el índice de hyperthreading: un procesador con HT activo expone más capacidad lógica al sistema operativo, induciendo al gobernador de energía a ser más agresivo. El factor $\alpha_0$ representa la sensibilidad del perfil energético: alto en "Máximo rendimiento", bajo en "Ahorro de batería".

- $\beta$ [W]. Amplitud máxima del corte de potencia impuesto por el firmware. No se deriva de variables de hardware individuales sino de la política de protección del fabricante: valores altos para fabricantes conservadores, bajos para orientados al rendimiento.

- $k$ [°C⁻¹]. Agresividad de la transición logística. Valor fijo calibrado por escenario en la simulación; no se deriva de variables de hardware sino de la caracterización empírica del comportamiento DVFS del procesador.

## 2.3 Análisis dimensional

Las unidades de las variables de estado son: $T(t)$ [°C], $R(t)$ [ops/s], $P(t)$ [W].

**Ecuación térmica** ($dT/dt$ en °C/s):

$$k_1 \,[\text{°C·s}^{-1}\text{·W}^{-1}] \cdot P \,[\text{W}] = \text{°C/s} \qquad k_2 \,[\text{s}^{-1}] \cdot (T - T_{amb}) \,[\text{°C}] = \text{°C/s}$$

**Ecuación de rendimiento** ($dR/dt$ en ops/s²):

$$\gamma \,[\text{ops·s}^{-2}\text{·W}^{-1}] \cdot P \,[\text{W}] = \text{ops/s}^2 \qquad \delta \,[\text{s}^{-1}] \cdot R \,[\text{ops/s}] = \text{ops/s}^2$$

**Ecuación de potencia** ($dP/dt$ en W/s):

$$\alpha \,[\text{W·s}^{-1}\text{·(ops/s)}^{-1}] \cdot (R_{obj} - R) \,[\text{ops/s}] = \text{W/s}$$

$$\frac{\beta \,[\text{W}]}{1 + e^{-k \,[\text{°C}^{-1}] \cdot (T - T_{crit}) \,[\text{°C}]}} = \text{W} \quad \Rightarrow \quad \frac{d}{dt}\!\left(\frac{\beta}{1+e^{-k\Delta T}}\right) \,[\text{W/s}] \checkmark$$

---

# 3. Metodología Numérica

## 3.1 Implementación de los métodos

El sistema vectorial $\dot{\mathbf{x}} = \mathbf{f}(\mathbf{x})$ con $\mathbf{x} = (T, R, P)^\top$ se resuelve con tres métodos programados desde cero.

**Euler explícito:**
$$\mathbf{x}_{n+1} = \mathbf{x}_n + h \cdot \mathbf{f}(\mathbf{x}_n)$$

**Euler Mejorado (Heun):**
$$\mathbf{x}^* = \mathbf{x}_n + h \cdot \mathbf{f}(\mathbf{x}_n), \qquad \mathbf{x}_{n+1} = \mathbf{x}_n + \frac{h}{2}\bigl(\mathbf{f}(\mathbf{x}_n) + \mathbf{f}(\mathbf{x}^*)\bigr)$$

**Runge-Kutta de cuarto orden (RK4):**

$$\mathbf{k}_1 = \mathbf{f}(\mathbf{x}_n), \quad \mathbf{k}_2 = \mathbf{f}\!\left(\mathbf{x}_n + \tfrac{h}{2}\mathbf{k}_1\right), \quad \mathbf{k}_3 = \mathbf{f}\!\left(\mathbf{x}_n + \tfrac{h}{2}\mathbf{k}_2\right), \quad \mathbf{k}_4 = \mathbf{f}(\mathbf{x}_n + h\,\mathbf{k}_3)$$

$$\mathbf{x}_{n+1} = \mathbf{x}_n + \frac{h}{6}(\mathbf{k}_1 + 2\mathbf{k}_2 + 2\mathbf{k}_3 + \mathbf{k}_4)$$

**Condición de frontera programática sobre $P(t)$.** La ODE permite teóricamente que $P(t)$ sea negativa bajo throttling máximo sostenido, lo que carece de sentido físico. Al finalizar cada paso de integración se aplica la corrección:

$$P_{n+1} \leftarrow \max(P_{min},\; P_{n+1})$$

Esta corrección **no modifica la ODE**; es una regla lógica aplicada en el código que descarta resultados matemáticamente válidos pero físicamente imposibles, garantizando que el modelo permanezca en un dominio admisible durante toda la simulación.

## 3.2 Inestabilidad inducida por gradientes extremos

RK4 es un integrador explícito: en cada paso calcula cuatro pendientes locales y las combina para extrapolar el estado. Esta estrategia funciona bien cuando las pendientes cambian suavemente entre $t_n$ y $t_{n+1}$.

La función logística tiene derivada máxima en $T = T_{crit}$, donde vale $k\beta/4$. Para valores altos de $k$ (transición agresiva), esta derivada puede ser grande y el cambio de pendiente dentro del intervalo $[t_n, t_{n+1}]$ puede ser significativo si $h$ es demasiado grande. En ese caso, RK4 sobreestima o subestima el corte de potencia en ese paso, produciendo que $P_{n+1}$ se aleje del valor real y propague error al siguiente paso. La solución es reducir $h$ lo suficiente para que la función logística no cambie sustancialmente dentro de un paso, condición que se verifica empíricamente en el análisis de convergencia.

Una ventaja clave de la sigmoide frente a otras funciones de penalización es que, al ser $C^\infty$, no introduce discontinuidades de curvatura en ningún punto. Esto significa que la degradación del orden de convergencia de RK4 es gradual y proporcional a $k$ y $h$, no abrupta como ocurriría con una función no diferenciable.

## 3.3 Análisis de error y convergencia

Para cada $h \in \{1.0,\; 0.5,\; 0.1,\; 0.05,\; 0.01\}$ segundos, se calcula el error relativo global respecto al solucionador de referencia RK45:

$$E_{rel}(h) = \max_{t \in [0, T_{sim}]} \frac{\|\mathbf{x}_{aprox}(t;\,h) - \mathbf{x}_{RK45}(t)\|}{\|\mathbf{x}_{RK45}(t)\|}$$

Se espera convergencia de orden 1 para Euler ($E \sim h$), orden 2 para Euler Mejorado ($E \sim h^2$) y orden 4 para RK4 ($E \sim h^4$). La gráfica log-log de $E_{rel}$ vs $h$ debe mostrar estas pendientes características.

## 3.4 Validación

La validación se realiza comparando las soluciones de los tres métodos propios contra `scipy.integrate.solve_ivp` con método RK45 de paso adaptativo, que constituye el solucionador de referencia de alto orden. La implementación se considera correcta cuando $E_{rel}$ disminuye con el orden esperado al reducir $h$, y cuando los tres métodos producen los mismos puntos de equilibrio $(T^*, R^*, P^*)$ y el mismo comportamiento cualitativo en cada escenario.

## 3.5 Herramientas

La implementación se desarrolla en Python 3.x. Las bibliotecas utilizadas son `NumPy` (operaciones vectoriales), `SciPy` (solucionador de referencia RK45), `Matplotlib` (visualización estática de trayectorias, espacio de fases y gráficas de error) y `Manim` (animaciones de la evolución temporal). El código de los tres métodos numéricos está programado directamente por el equipo sin recurrir a solucionadores externos.

## 3.6 Proceso de programación, simulación y animación

La implementación sigue un orden secuencial. Primero se define la función vectorial $\mathbf{f}(\mathbf{x})$ que agrupa las tres ecuaciones, aplicando la condición de frontera sobre $P_{min}$ al final de cada evaluación. Sobre esta función se construyen los tres integradores con la misma interfaz, lo que permite intercambiarlos directamente en el bucle de simulación para el análisis comparativo.

Las simulaciones de los cuatro escenarios se ejecutan con el mismo horizonte temporal y condiciones iniciales, variando únicamente los parámetros de hardware correspondientes a cada intervención. Los resultados se grafican como series temporales de $T$, $R$ y $P$, y como trayectorias en el espacio de fases $(T, R, P)$. Las animaciones muestran la evolución del sistema en tiempo real, resaltando el instante en que el throttling se activa, la entrada al régimen oscilatorio y la convergencia al equilibrio en los escenarios exitosos.

## 3.7 Uso de IA

Durante el desarrollo del proyecto se emplearon herramientas de inteligencia artificial en los siguientes contextos:

- {ia} Consulta de conceptos teóricos sobre el Modelo Roofline, el Modelo de Capacitancia Concentrada y las funciones de barrera de control, para clarificar su aplicabilidad al modelo propuesto.
- {ia} Identificación de referencias bibliográficas relevantes (Incropera, Kleinrock, Nocedal & Wright, Rao, Brooks & Martonosi) para respaldar las decisiones de modelado.
- {ia} Revisión de errores en la verificación dimensional de las constantes del modelo tras un análisis propio previo.
- {ia} Sugerencia de condiciones iniciales y rangos de parámetros adicionales donde el sistema pudiera exhibir comportamientos interesantes, explorada después de forma propia mediante simulación.

No se empleó IA para: generar el código de los métodos numéricos, escribir el contenido del informe o la presentación, producir imágenes o animaciones, ni tomar decisiones de modelado o análisis.

---

# 4. Resultados y Discusión

## 4.1 Condiciones iniciales y parámetros

Las condiciones iniciales representan el estado del equipo en $t = 0$, justo antes de lanzar la carga de trabajo (equipo encendido en reposo):

| Variable | Valor inicial | Significado físico |
|----------|:---:|---|
| $T(0)$ | $45$ °C | Temperatura de reposo con carga base del SO |
| $P(0)$ | $15$ W | Potencia base del SO en inactividad |
| $R(0)$ | $0$ ops/s | Procesador sin carga de trabajo activa |

**Parámetros fijos del entorno:**

| Parámetro | Valor | Descripción |
|-----------|:---:|---|
| $T_{amb}$ | $25$ °C | Temperatura ambiente |
| $T_{crit}$ | $90$ °C | Umbral de referencia del throttling logístico |
| $R_{obj}$ | $20$ ops/s (normalizado) | Throughput objetivo del gobernador del SO |
| $R_{min}$ | $5$ ops/s (normalizado) | Umbral mínimo de viabilidad operativa |
| $P_{min}$ | $5$ W | Potencia mínima física del procesador |

Para que el modelo sea simulable, se usan como referencia las especificaciones de un computador de propósito general de gama media-alta (procesador de 8 núcleos a 3.5 GHz):

| Variable de hardware | Símbolo | Valor de referencia | Unidad |
|---|---|:---:|---|
| Núcleos físicos | $N_c$ | 8 | — |
| Hilos lógicos | $N_h$ | 16 | — |
| Frecuencia del procesador | $f_p$ | 3.5 | GHz |
| Velocidad RAM | $v_{ram}$ | 4800 | MT/s |
| Velocidad del bus | $v_{bus}$ | 16 | GT/s |
| Flujo de aire | $\Phi_{aire}$ | 2.5 | CFM |
| Conductancia del disipador | $H_d$ | 5.0 | W/°C |

| Factor de escala | Símbolo | Valor inicial | Justificación |
|---|---|:---:|---|
| Ineficiencia térmica del silicio | $\kappa_0$ | $0.002$ | Proceso de 7 nm |
| Constante de convección | $\eta_0$ | $0.004$ | Chasis con rejillas parcialmente obstruidas |
| Eficiencia IPC de la arquitectura | $\gamma_0$ | $0.015$ | Cálculo paralelo eficiente |
| Factor de latencia intrínseca | $\delta_0$ | $1.2 \times 10^{8}$ | SO con overhead estándar |
| Ganancia del gobernador del SO | $\alpha_0$ | $0.8$ | Perfil "Máximo Rendimiento" |
| Amplitud de corte del firmware | $\beta$ | $12$ W | Fabricante con protección moderada |
| Agresividad logística | $k$ | $0.5$ °C⁻¹ | Calibrado para DVFS típico |

Con estos valores, los parámetros del modelo resultan:

$$k_1 = 0.002 \times (3.5 \times 8) = 0.056 \text{ °C·s}^{-1}\text{·W}^{-1}$$

$$k_2 = 0.004 \times (2.5 \times 5.0) = 0.050 \text{ s}^{-1}$$

$$\gamma = 0.015 \times (16 \times 3.5) = 0.840 \text{ ops·s}^{-2}\text{·W}^{-1}$$

$$\delta = \frac{1.2 \times 10^{8}}{\min(4800, 16)} = \frac{1.2 \times 10^{8}}{16} = 7.5 \times 10^{6} \text{ s}^{-1}$$

$$\alpha = 0.8 \times \frac{16}{8} = 1.6 \text{ W·s}^{-1}\text{·(ops/s)}^{-1}$$

> **Nota de calibración:** Los factores $\gamma_0$ y $\delta_0$ deben ajustarse iterativamente hasta que el punto de equilibrio $P^* = \delta \cdot R_{obj} / \gamma$ caiga en el rango físico esperado para el equipo (15–45 W bajo carga). Este proceso de calibración es parte de la metodología y debe documentarse en el informe.

## 4.2 Análisis de puntos de equilibrio

### 4.2.1 Equilibrio sin throttling activo

Igualando las tres derivadas a cero y asumiendo que en el equilibrio la temperatura está suficientemente alejada de $T_{crit}$ para que el throttling logístico sea despreciable:

$$\frac{dT}{dt} = 0 \implies T^* = T_{amb} + \frac{k_1}{k_2} P^*$$

$$\frac{dR}{dt} = 0 \implies R^* = \frac{\gamma}{\delta} P^*$$

$$\frac{dP}{dt} = 0 \implies R^* = R_{obj}$$

De la tercera ecuación se obtiene $R^* = R_{obj}$. Sustituyendo:

$$P^* = \frac{\delta \cdot R_{obj}}{\gamma}, \qquad T^* = T_{amb} + \frac{k_1 \delta \cdot R_{obj}}{k_2 \gamma}$$

La condición de existencia del equilibrio estable es la **condición de viabilidad térmica**:

$$T^* < T_{crit} \iff \frac{k_1 \delta}{k_2 \gamma} < \frac{T_{crit} - T_{amb}}{R_{obj}}$$

Cuando se cumple, el sistema puede alcanzar un punto de equilibrio estable con throughput pleno. Cuando no se cumple, el sistema entra en régimen oscilatorio.

### 4.2.2 Estabilidad por retroalimentación negativa

Para verificar que $(T^*, R^*, P^*)$ es un atractor estable, se analiza la dirección de las derivadas ante perturbaciones directamente desde la física de las ecuaciones.

**Perturbación térmica.** Si la temperatura sube a $T^* + \varepsilon$ con $\varepsilon > 0$:

$$\frac{dT}{dt}\bigg|_{T^*+\varepsilon} = \underbrace{k_1 P^* - k_2(T^*-T_{amb})}_{=\,0 \text{ en equilibrio}} - k_2\varepsilon = -k_2\varepsilon < 0$$

La derivada es negativa: el sistema enfría activamente hacia $T^*$. El coeficiente $k_2 > 0$ actúa como fuerza de amortiguación proporcional al desvío — retroalimentación negativa pura.

**Perturbación de rendimiento.** Si $R$ cae por debajo de $R^*$, el término $\alpha(R_{obj} - R)$ se vuelve positivo, aumentando $\dot{P}$, lo que empuja $\dot{R} = \gamma P - \delta R$ hacia valores positivos, recuperando el throughput. El término $-\delta R(t)$ actúa simultáneamente como fricción que impide sobrepasar $R^*$.

La estabilidad del equilibrio requiere que se satisfaga la misma condición de viabilidad térmica derivada anteriormente.

### 4.2.3 Régimen oscilatorio

Cuando la condición de viabilidad no se cumple, el sistema entra en el siguiente ciclo:

1. El sistema operativo aumenta la potencia buscando alcanzar $R_{obj}$.
2. La temperatura sube y activa progresivamente el throttling logístico.
3. El firmware reduce la potencia de forma acelerada.
4. La temperatura cae al perder la fuente de calor.
5. El sistema operativo intenta recuperar la potencia y el ciclo reinicia.

Este régimen hace al equipo inviable para cargas sostenidas: el throughput oscila sin converger a un estado estable con $R \geq R_{min}$.

---

## 4.3 Cuatro escenarios de intervención

Los escenarios modifican los parámetros del hardware para evaluar qué intervenciones permiten mover el sistema desde el régimen oscilatorio hacia un equilibrio estable.

### Escenario 0 — Base (Control)

Hardware estándar sin modificaciones. Parámetros de la Sección 4.1. Este escenario puede o no satisfacer la condición de viabilidad según los parámetros del equipo. Es el punto de referencia para calcular variaciones porcentuales.

### Escenario 1 — Intervención de Software (Undervolting / Perfil Conservador)

**Modificación:** Reducción de $\alpha_0$ (gobernador menos agresivo).

**Efecto esperado:** El sistema operativo sube la potencia más lentamente, dando tiempo al disipador para mantenerse alejado de $T_{crit}$. Puede estabilizar el sistema a costa de un throughput de equilibrio $R^*$ inferior al objetivo.

**Variable de comparación:** ¿Alcanza $R^* \geq R_{min}$ en equilibrio?

### Escenario 2 — Intervención de Hardware Ligera (Base Refrigerante / Limpieza)

**Modificación:** Aumento de $\Phi_{aire}$ → $k_2$ sube.

**Efecto esperado:** Mayor disipación térmica desplaza $T^*$ hacia abajo, acercando el sistema a la condición de viabilidad sin sacrificar throughput.

**Variable de comparación:** Variación porcentual de $T^*$ y de la frecuencia de oscilación respecto al escenario base.

### Escenario 3 — Intervención de Hardware Profunda (Pasta Térmica de Metal Líquido)

**Modificación:** Aumento de $H_d$ → $k_2$ sube sustancialmente.

**Efecto esperado:** Si el nuevo $k_2$ cumple la condición de viabilidad, el sistema converge al equilibrio estable con throughput pleno.

**Variable de comparación:** Tiempo de convergencia al equilibrio y temperatura máxima alcanzada durante la transición.

---

## 4.4 Comparación entre métodos y tamaños de paso

*[Sección por completar con los resultados numéricos de la simulación. Incluir tabla de $E_{rel}(h)$ para cada método y cada $h$, y gráfica log-log mostrando las pendientes de orden 1, 2 y 4.]*

---

# 5. Conclusiones

*[Sección por completar tras obtener los resultados de simulación.]*

---

# Repositorio

Código disponible en: [enlace por completar]

---

# Bibliografía

- Incropera, F. P. & DeWitt, D. P. (2002). *Fundamentos de transferencia de calor y masa*. Wiley. Cap. Conducción transitoria.
- Kleinrock, L. (1976). *Queueing Systems, Vol. II: Computer Applications*. Wiley-Interscience.
- Ogata, K. (2010). *Ingeniería de control moderna*. Pearson.
- Ames, A. D. et al. (2019). Control Barrier Functions: Theory and Applications. *18th European Control Conference*.
- Nocedal, J. & Wright, S. J. (2006). *Numerical Optimization* (2nd ed.). Springer.
- Rao, S. S. (2019). *Engineering Optimization: Theory and Practice* (5th ed.). Wiley.
- Brooks, D. & Martonosi, M. (2001). Dynamic Thermal Management for High-Performance Microprocessors. *HPCA 2001*.
- Hennessy, J. L. & Patterson, D. A. (2019). *Computer Architecture: A Quantitative Approach* (6th ed.). Morgan Kaufmann.
- Williams, S., Waterman, A. & Patterson, D. (2009). Roofline: An Insightful Visual Performance Model. *Communications of the ACM*, 52(4).
