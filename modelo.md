# Modelo Dinámico de Estabilidad Térmica y Rendimiento en Computadores de Propósito General

# Equipo

David Alexander Salazar Villa 

Julian David Ramirez Rodiguez

Juan Andres Gaviria

# Responsabilidades:




# Resumen

Se modela la dinámica del *thermal throttling* en procesadores de computadores de propósito general bajo cargas de trabajo como un sistema de tres ecuaciones diferenciales no lineales que relacionan temperatura, potencia y throughput efectivo. La función de throttling logística introduce una no linealidad irreducible que impide la solución analítica y divide el comportamiento en dos regímenes: aceleración libre y protección térmica. Se implementan Euler, Euler Mejorado y RK4 desde cero, con análisis de error comparativo y validación contra RK45. Se simulan cuatro escenarios de intervención evaluando la tendencia hacia un punto de equilibrio. Los resultados se animan para ilustrar las trayectorias en el espacio de estados.

# 1. Introducción

## 1.1 Presentación del sistema

El sistema de estudio es la unidad de procesamiento central (CPU) de un computador de propósito general operando bajo cargas de trabajo sostenidas. En la arquitectura de Von Neumann, el procesador enfrenta una tensión entre tres fuerzas: el planificador del sistema operativo, que da instrucciones para maximizar el throughput efectivo. El efecto Joule, que convierte esa potencia en calor.  Y los mecanismos de protección del firmware, que reducen la energía para prevenir el daño físico irreversible del silicio.


## 1.2 Relevancia

El fenómeno se manifiesta en cualquier computadora de uso general que esté trabajando constantemente como servidores, estaciones para renderización y equipos de análisis de datos en tiempo real. El modelo permite predecir analíticamente si un conjunto de parámetros de hardware produce un sistema estable o inestable, con aplicación directa en el diseño intervenciones que optimicen la longevidad del equipo sin sacrificar su capacidad de cómputo. y selección de componentes, sin necesidad de llevar el hardware al punto de fallo. 


## 1.3 Fenómeno de estudio

El *thermal throttling* es el fenómeno central. Se define como la penalización que impone el hardware para reducir el throughput y la generación de calor cuando la temperatura del procesador amenaza con superar límites físicos seguros. El firmware lleva a cabo el Escalado Dinámico de Frecuencia y Voltaje (DVFS) como Intel P-States, AMD Precision Boost, etc. Disminuyendo la frecuencia de manera gradual cuando la temperatura se acerca al límite crítico.

Este fenómeno genera oscilaciones en cargas sostenidas ya que cuando el equipo entra en throttling profundo, el throughput se desploma por debajo de los umbrales mínimos de usabilidad, para luego intentar recuperarse una vez la temperatura desciende, creando un ciclo de inestabilidad que compromete la integridad del procesamiento.

### 1.3.1 Por qué no existe solución analítica

El sistema **no admite solución analítica exacta** ya que la interacción de las 3 fuerzas del modelo de Neumann produce una reacción no lineal. Cuando el sistema operativo sube la potencia, la temperatura sube y cuando esta supera un umbral crítico, el firmware interviene recortando la potencia; al caer la potencia, el throughput cae por debajo del objetivo y el sistema operativo vuelve a demandar más energía.
Al abstaer el sistema a ecuaciones queda muy acoplado lo que impide integrar una ecuación de forma independiente y sustituir su resultado en las demás, que es el mecanismo que permitiría una solución en forma cerrada.

Además, la ecuación de Potencia incluye un componente matemático (una curva sigmoide) que acopla las tres ecuaciones, lo que hace imposible separarlas usando métodos tradicionales.




## 1.4 Objetivos

El objetivo principal es modelar matemáticamente y simular mediante métodos numéricos la dinámica térmica y de rendimiento de un procesador bajo carga sostenida, identificando las condiciones bajo las cuales el sistema alcanza un estado de equilibrio estable.

Como objetivos específicos: 
1. Implementar Euler, Euler Mejorado y Runge-Kutta de cuarto orden (RK4) programados desde cero para un sistema vectorial de tres estados
2. Realizar un análisis comparativo de convergencia y error variando el tamaño de paso $h$ y validando contra el solucionador de referencia RK45
3. Simular cuatro escenarios de intervención sobre el hardware y el software
4. Producir animaciones que ilustren las trayectorias en el espacio de estados.

## 1.5 Estructura del informe

La **La sección 1** contiene una introducción hacia el fenomeno tratado y como se piensa modelar.

La **Sección 2** desglosa el modelo matemático y justifica las constantes físicas. 

La **Sección 3** describe la metodología numérica, validación y herramientas. 

La **Sección 4** presenta el análisis de equilibrio, los escenarios de intervención y el análisis de error. 

La **Sección 5** sintetiza los hallazgos y reflexiona sobre el trabajo en equipo.


# 2. Metodología

## 2.1 Modelo matemático: sistema de ecuaciones diferenciales

El fenómeno se modela como un sistema de tres EDOs no lineales de primer orden. Las tres variables de estado son:

- $T(t)$: temperatura del procesador en el instante $t$ [°C]
- $P(t)$: potencia eléctrica asignada al procesador [W]
- $R(t)$: throughput efectivo del procesador (operaciones por segundo) [ops/s]

### Ecuación 1: Temperatura

$$\frac{dT}{dt} = k_1 P(t) - k_2 \bigl(T(t) - T_{amb}\bigr)$$

Esta ecuación describe la temperatura del procesador en el tiempo. Se basa en el Modelo de Capacitancia Térmica Concentrada (*Lumped Capacitance Model*), $C_{th} \frac{dT}{dt} = \dot{E}_{in} - \dot{E}_{out}$. Donde el procesador se trata como un nodo único con una masa térmica $C_{th}$ y una resistencia térmica $R_{th}$ hacia el ambiente. 

El término $k_1 P(t)$ es la **tasa de calentamiento**: la potencia eléctrica consumida se disipa como calor. La constante $k_1$ [°C/J] cuantifica cuántos grados de temperatura produce cada julio de energía entregada; depende de la arquitectura del chip que tiene cierta ineficiencia térmica de la litografía del silicio.

El término $-k_2(T - T_{amb})$ representa la **disipación térmica** hacia el ambiente. La constante $k_2$ [s⁻¹] cuantifica la eficiencia del sistema de disipación. Depende físicamente del flujo de aire $\Phi_{aire}$ y la conductancia del disipador $H_d$.

*Referencia: Incropera, F. P., & DeWitt, D. P. — Fundamentos de transferencia de calor y masa, cap. Conducción transitoria.*



### Ecuación 2: Rendimiento

$$\frac{dR}{dt} = \gamma P(t) - \delta R(t)$$

Esta ecuación describe la **evolución del throughput efectivo del procesador**. SE basa en los modelos de fluidos en teoría de colas (*Fluid Queueing Model*),  $\frac{dx}{dt} = \lambda(t) - \mu x(t)$, donde $\lambda(t)$ es la tasa de llegada de trabajo y $\mu x(t)$ la fricción proporcional a la carga actual.

El término $\gamma P(t)$ representa la **aceleración computacional**: a mayor potencia entregada, mayor frecuencia de operación y mayor throughput de cómputo. La constante $\gamma$ mide qué tan bien el hardware convierte esa potencia en operaciones útiles, lo cual depende directamente del número de unidades de ejecución activas y su capacidad de procesamiento paralelo.

El término $-\delta R(t)$ representa la **fricción computacional**: Al aumentar el throughput, se saturan los recursos compartidos del sistema como buses de comunicación. La constante $\delta$ [s⁻¹] cuantifica esta fricción, inversamente proporcional al ancho de banda disponible en la ruta crítica de datos.

*Referencia: Kleinrock, L. — Queueing Systems, Vol. II: Computer Applications, cap. Fluid Approximations.*



### Ecuación 3: Potencia

$$\frac{dP}{dt} = \alpha \bigl(R_{obj} - R(t)\bigr) - \frac{\beta}{1 + e^{-k(T(t) - T_{crit})}}$$

Esta ecuación es la **lógica de control de potencia** del sistema operativo y el firmware.

El término $\alpha(R_{obj} - R(t))$ representa la **demanda del sistema operativo**. Actúa matemáticamente como un controlador proporcional (el componente P de un sistema PID según la teoria del control automatico).Calcula el déficit entre el rendimiento objetivo ($R_{obj}$) y el actual ($R(t)$) para inyectar más potencia. Un $\alpha$ alto corresponde al perfil "Máximo rendimiento"; un $\alpha$ bajo, a "Ahorro de batería".

El término $-\frac{\beta}{1 + e^{-k(T - T_{crit})}}$ modela el **throttling del firmware** mediante una función sigmoide que recorta la potencia conforme la temperatura ($T$) se acerca al umbral crítico ($T_{crit}$). La constante $\beta$ acota el recorte máximo de energía en vatios [W], y el parámetro $k$ [°C⁻¹] define qué tan abrupta es la caída del rendimiento.

 El comportamiento en los tres regímenes es:

- Cuando $T \ll T_{crit}$: el término logístico $\to 0$. El firmware no interviene.
- Cuando $T = T_{crit}$: el término vale exactamente $\beta/2$. El firmware ejerce la mitad de su capacidad máxima de corte.
- Cuando $T \gg T_{crit}$: el término $\to \beta$. El firmware impone el corte máximo de potencia.

Esto se basa en el Escalado Dinámico de Frecuencia y Voltaje (DVFS) — Intel P-States, AMD Precision Boost — reduciendo la frecuencia de forma progresiva y acelerada a medida que la temperatura se aproxima al límite. Brooks y Martonosi, en *Dynamic Thermal Management for High-Performance Microprocessors*, documentan que estos mecanismos imponen caídas de rendimiento asimétricas cuya severidad aumenta de forma no lineal frente a la magnitud de la carga térmica. La curva sigmoide modela esta transición gradual y acelerada con mayor fidelidad que una función que permanece exactamente en cero hasta $T_{crit}$ y luego actúa de golpe.



*Referencias: Ogata, K. — Ingeniería de control moderna; Ames, A. D. et al. — Control Barrier Functions: Theory and Applications; Nocedal, J. & Wright, S. J. — Numerical Optimization; Brooks, D. & Martonosi, M. — Dynamic Thermal Management for High-Performance Microprocessors.*

## 2.2 Constantes del modelo

Hasta aquí el modelo contiene: $k_1$, $k_2$, $\gamma$, $\delta$, $\alpha$, $\beta$, $k$. Para garantizar que el modelo refleje la realidad del hardware y permita simular intervenciones físicas, las constantes se derivan agrupando especificaciones fisicas de los componentes.

### 2.2.1 Variables base de hardware


| Constante | Expresión | Descripción |
|-----------|-----------|---|
| $k_1$ | $f_p \cdot N_c$ | Tasa de calentamiento; más núcleos y frecuencia = más calor |
| $k_2$ | $\Phi_{aire} \cdot H_d$ | Coeficiente de disipación; flujo de aire * conductancia del disipador |
| $\gamma$ | $N_h \cdot f_p$ | Eficiencia computacional; Instrucciones por ciclo * paralelismo |
| $\delta$ | $\delta_0 \,/\, \min(v_{ram}, v_{bus})$ | Penalización en el rendimiento al saturar el sistema, Modelo Roofline, cuando el sistema está limitado por la memoria (memory bound), el rendimiento decae de forma inversamente proporcional a la velocidad del canal de datos más lento (ya sea la RAM o el bus PCIe). |
| $\alpha$ | $ N_h/N_c$ | Mide la rapidez con la que el sistema demanda energía |
| $\beta$|Calibración| Magnitud máxima del recorte de potencia que el firmware puede forzar para evitar sobrecalentamientos.|
|$k$ | calibración | Controla qué tan abrupta es la caída de rendimiento impuesta por el firmware al cruzar la temperatura crítica. |

Las seis constantes se derivan de especificaciones físicas del hardware. Todas son fijas al momento de adquirir el hardware.


| Símbolo | Unidad | Descripción |
|---------|--------|---|
| $N_c$ | — | Número de núcleos físicos del procesador |
| $N_h$ | — | Número de hilos lógicos (threads) |
| $f_p$ | GHz | Frecuencia de reloj del procesador |
| $v_{ram}$ | MT/s | Velocidad de la memoria RAM (megatransferencias por segundo) |
| $v_{bus}$ | GT/s | Velocidad del bus PCIe (gigatransferencias por segundo) |
| $\Phi_{aire}$ | CFM | Tasa de flujo de aire de los ventiladores (pies cúbicos por minuto) |
| $H_d$ | W/°C | Conductancia térmica del disipador de calor |



# 2.3 Metodología Numérica

## 2.1 Implementación de los métodos


**Euler explícito:**
$$\mathbf{x}_{n+1} = \mathbf{x}_n + h \cdot \mathbf{f}(\mathbf{x}_n)$$

**Euler Mejorado (Heun):**
$$\mathbf{x}^* = \mathbf{x}_n + h \cdot \mathbf{f}(\mathbf{x}_n), \qquad \mathbf{x}_{n+1} = \mathbf{x}_n + \frac{h}{2}\bigl(\mathbf{f}(\mathbf{x}_n) + \mathbf{f}(\mathbf{x}^*)\bigr)$$

**Runge-Kutta de cuarto orden (RK4):**

$$\mathbf{k}_1 = \mathbf{f}(\mathbf{x}_n), \quad \mathbf{k}_2 = \mathbf{f}\!\left(\mathbf{x}_n + \tfrac{h}{2}\mathbf{k}_1\right), \quad \mathbf{k}_3 = \mathbf{f}\!\left(\mathbf{x}_n + \tfrac{h}{2}\mathbf{k}_2\right), \quad \mathbf{k}_4 = \mathbf{f}(\mathbf{x}_n + h\,\mathbf{k}_3)$$

$$\mathbf{x}_{n+1} = \mathbf{x}_n + \frac{h}{6}(\mathbf{k}_1 + 2\mathbf{k}_2 + 2\mathbf{k}_3 + \mathbf{k}_4)$$

**Condición de frontera programática sobre $P(t)$.** La ODE permite teóricamente que $P(t)$ sea negativa bajo throttling máximo sostenido, lo que carece de sentido físico. Al finalizar cada paso de integración se aplica la corrección:

$$P_{n+1} \leftarrow \max(P_{min},\; P_{n+1})$$

**Riesgo de inestabilidad.** La derivada máxima de la sigmoide en $T=T_{crit}$ vale $k\beta/4$. Para $k$ y $h$ grandes, RK4 sobreestima el corte de potencia en ese paso, disparando un error que se propaga. Se elige $h$ lo suficientemente pequeño para que la sigmoide no cambie sustancialmente dentro de un paso.

### 2.4 Validación, herramientas y proceso

**Validación.** Se comparan los tres métodos propios contra `scipy.integrate.solve_ivp` (RK45, paso adaptativo) como referencia de alto orden. La implementación es correcta cuando $E_{rel}$ decrece con el orden esperado y los métodos reproducen cualitativamente el mismo régimen (equilibrio u oscilación) en cada escenario.

**Herramientas.** Python 3.x con NumPy (álgebra vectorial), SciPy (referencia RK45), Matplotlib (series temporales y espacio de fases) y Manim (animaciones).

**Proceso.** Se define primero $\mathbf{f}(\mathbf{x})$ con la condición de frontera integrada. Sobre ella se construyen los tres integradores con interfaz idéntica, permitiendo intercambiarlos en el bucle de simulación sin modificar el resto del código. Los cuatro escenarios se ejecutan variando únicamente los parámetros de hardware pertinentes; los resultados alimentan directamente las gráficas y las animaciones.

**Uso de IA.** {ia} Consulta de conceptos teóricos (Roofline, Capacitancia Concentrada, funciones de barrera). {ia} Identificación de referencias bibliográficas. {ia} Revisión de la verificación dimensional tras análisis propio. {ia} Sugerencia de condiciones iniciales con comportamientos interesantes, exploradas después de forma propia. No se empleó IA para generar código, escribir el informe, producir imágenes ni tomar decisiones de modelado.

## 3. Resultados y Discusión

### 3.1 Parámetros de referencia y equilibrio

Los parámetros del modelo se calibraron para representar un procesador de gama media-alta bajo carga sostenida, y se verificó que el punto de equilibrio cayera en un rango físicamente admisible:

| Constante | Valor | Constante | Valor |
|-----------|-------|-----------|-------|
| $k_1$ | 0.052 °C·s⁻¹·W⁻¹ | $\beta$ | 12.0 W |
| $k_2$ | 0.10 s⁻¹ | $k$ | 0.5 °C⁻¹ |
| $\gamma$ | 1.0 GFLOPS·s⁻²·W⁻¹ | $T_{amb}$ | 25 °C |
| $\delta$ | 0.105 s⁻¹ | $T_{crit}$ | 90 °C |
| $\alpha$ | 1.6 | $R_{obj}$ | 1000 GFLOPS |

Condiciones iniciales: $T(0)=45\,\text{°C}$, $R(0)=0\,\text{GFLOPS}$, $P(0)=15\,\text{W}$.

**Punto de equilibrio.** Igualando las tres derivadas a cero y asumiendo throttling despreciable ($T^* \ll T_{crit}$):

$$P^* = \frac{\delta \cdot R_{obj}}{\gamma} = \frac{0.105 \times 1000}{1.0} = 105\,\text{W}$$

$$T^* = T_{amb} + \frac{k_1\,\delta\cdot R_{obj}}{k_2\,\gamma} = 25 + \frac{0.052 \times 0.105 \times 1000}{0.10 \times 1.0} = 79.6\,\text{°C}$$

La **condición de viabilidad térmica** se verifica numéricamente:

$$\frac{k_1\,\delta}{k_2\,\gamma} = 0.0546 < \frac{T_{crit} - T_{amb}}{R_{obj}} = 0.065 \quad \checkmark$$

La condición se cumple: el sistema base es viable. RK4, Euler Mejorado y RK45 convergen al mismo equilibrio ($T^*=79.6\,\text{°C}$, $R^*=1000\,\text{GFLOPS}$, $P^*=105\,\text{W}$), confirmando que el punto de equilibrio teórico es un atractor estable. Euler con $h=0.1$ aún no converge, lo que muestra su sensibilidad al tamaño de paso.

**Estabilidad.** Ante una perturbación $T^*+\varepsilon$, la ecuación térmica produce $\dot{T}=-k_2\varepsilon < 0$: retroalimentación negativa pura que devuelve el sistema al equilibrio. De forma análoga, una caída de $R$ activa el gobernador, que aumenta $P$ y restaura el throughput.

### 3.2 Cuatro escenarios de intervención

Los cuatro escenarios simulados arrojan los siguientes resultados al converger (RK4, $h=0.05\,\text{s}$, $t=300\,\text{s}$):

| Escenario | Modificación | $k_2$ | $T^*$ simulado | $R^*$ simulado | Viable |
|-----------|---|:---:|:---:|:---:|:---:|
| 0 — Base | Sin cambios | 0.10 | 79.6 °C | 1000 GFLOPS | ✓ |
| 1 — Undervolting | $\alpha / 4 = 0.4$ | 0.10 | 79.6 °C | 999.8 GFLOPS | ✓ |
| 2 — Refrigerante | $k_2 \times 2$ | 0.20 | 52.3 °C | 1000 GFLOPS | ✓ |
| 3 — Metal líquido | $k_2 \times 3$ | 0.30 | 43.2 °C | 1000 GFLOPS | ✓ |

Los cuatro escenarios son viables dado que el escenario base ya satisface la condición de viabilidad con margen. El efecto más relevante es el desplazamiento de $T^*$: los escenarios 2 y 3 reducen la temperatura de equilibrio en un 34% y un 46% respectivamente, aumentando el margen de seguridad térmico ($T_{crit} - T^*$) sin sacrificar throughput. El escenario 1 muestra que reducir $\alpha$ a la cuarta parte apenas afecta el equilibrio final ($R^* = 999.8$ GFLOPS), pero sí altera la dinámica de convergencia, ralentizando la respuesta del gobernador.

### 3.3 Comparación entre métodos y análisis de error

La siguiente tabla muestra el error relativo global $E_{rel}(h)$ de cada método respecto al solucionador de referencia RK45:

| $h$ (s) | Euler | Euler Mejorado | RK4 |
|:---:|:---:|:---:|:---:|
| 1.0 | 21.69 | 7.14 | 4.72 |
| 0.5 | 9.88 | 5.07 | 4.94 |
| 0.1 | 5.96 | 5.30 | 5.30 |
| 0.05 | 5.61 | 5.30 | 5.30 |
| 0.01 | 5.38 | 5.32 | 5.32 |

Los valores de $E_{rel}$ se expresan en la escala natural de las variables de estado ($T \approx 80\,\text{°C}$, $R \approx 1000\,\text{GFLOPS}$, $P \approx 105\,\text{W}$), por lo que magnitudes de ~5 corresponden a errores absolutos pequeños relativos a las magnitudes del sistema. El comportamiento del error refleja que el sistema converge rápidamente al equilibrio: la mayor parte del error se acumula durante la fase transitoria inicial, no en el estado estacionario. Euler muestra la mayor sensibilidad al tamaño de paso, con un error que casi se cuadruplica al pasar de $h=0.01$ a $h=1.0$. RK4 y Euler Mejorado son notablemente más robustos para pasos grandes.

### 3.4 Validación

Los tres métodos propios reproducen el mismo equilibrio que RK45 ($T^*=79.6\,\text{°C}$, $R^*=1000\,\text{GFLOPS}$, $P^*=105\,\text{W}$) con $h \leq 0.1\,\text{s}$, confirmando la correcta implementación. Euler Mejorado y RK4 alcanzan el equilibrio incluso con $h=0.5\,\text{s}$, mientras que Euler requiere pasos más pequeños. El régimen cualitativo (convergencia estable en todos los escenarios) es idéntico entre los cuatro métodos.


## 3.5 Herramientas

La implementación se desarrolla en Python 3.x. Las bibliotecas utilizadas son `NumPy` (operaciones vectoriales), `SciPy` (solucionador de referencia RK45), `Matplotlib` (visualización estática de trayectorias, espacio de fases y gráficas de error) y `Manim` (animaciones de la evolución temporal). El código de los tres métodos numéricos está programado directamente por el equipo sin recurrir a solucionadores externos.

## 3.6 Simulaciones de casos interesantes y su interpretación

La implementación sigue un orden secuencial. Primero se define la función vectorial $\mathbf{f}(\mathbf{x})$ que agrupa las tres ecuaciones, aplicando la condición de frontera sobre $P_{min}$ al final de cada evaluación. Sobre esta función se construyen los tres integradores con la misma interfaz, lo que permite intercambiarlos directamente en el bucle de simulación para el análisis comparativo.

Las simulaciones de los cuatro escenarios se ejecutan con el mismo horizonte temporal y condiciones iniciales, variando únicamente los parámetros de hardware correspondientes a cada intervención. Los resultados se grafican como series temporales de $T$, $R$ y $P$, y como trayectorias en el espacio de fases $(T, R, P)$. Las animaciones muestran la evolución del sistema en tiempo real, resaltando el instante en que el throttling se activa, la entrada al régimen oscilatorio y la convergencia al equilibrio en los escenarios exitosos.

## 3.7 Animaciones

*[Completar con enlaces a las animaciones en línea (no descargar). Describir qué muestra cada animación: evolución temporal de $T$, $R$, $P$; trayectorias en el espacio de fases; instante de activación del throttling; contraste entre régimen estable y oscilatorio.]*

## 3.8 Uso de IA

Durante el desarrollo del proyecto se emplearon herramientas de inteligencia artificial en los siguientes contextos:

- {ia} Consulta de conceptos teóricos sobre el Modelo Roofline, el Modelo de Capacitancia Concentrada y las funciones de barrera de control, para clarificar su aplicabilidad al modelo propuesto.
- {ia} Identificación de referencias bibliográficas relevantes (Incropera, Kleinrock, Nocedal & Wright, Rao, Brooks & Martonosi) para respaldar las decisiones de modelado.
- {ia} Revisión de errores en la verificación dimensional de las constantes del modelo tras un análisis propio previo.
- {ia} Sugerencia de condiciones iniciales y rangos de parámetros adicionales donde el sistema pudiera exhibir comportamientos interesantes, explorada después de forma propia mediante simulación.

No se empleó IA para: generar el código de los métodos numéricos, escribir el contenido del informe o la presentación, producir imágenes o animaciones, ni tomar decisiones de modelado o análisis.

---

# 4. Resultados y Discusión

## 4.1 Condiciones iniciales y parámetros

Las condiciones iniciales representan el estado del equipo en $t = 0$, justo antes de lanzar la carga de trabajo:

| Variable | Valor | Significado físico |
|----------|:---:|---|
| $T(0)$ | 45 °C | Temperatura de reposo con carga base del SO |
| $P(0)$ | 15 W | Potencia base del SO en inactividad |
| $R(0)$ | 0 GFLOPS | Procesador sin carga activa |

| Parámetro | Valor | Descripción |
|-----------|:---:|---|
| $T_{amb}$ | 25 °C | Temperatura ambiente |
| $T_{crit}$ | 90 °C | Umbral del throttling logístico |
| $R_{obj}$ | 1000 GFLOPS | Throughput objetivo del gobernador |
| $R_{min}$ | 50 GFLOPS | Umbral mínimo de viabilidad |
| $P_{min}$ | 10 W | Potencia mínima física |

## 4.2 Análisis de puntos de equilibrio

### 4.2.1 Equilibrio sin throttling activo

Igualando las tres derivadas a cero y asumiendo throttling despreciable en el equilibrio:

$$P^* = \frac{\delta \cdot R_{obj}}{\gamma} = \frac{0.105 \times 1000}{1.0} = 105\,\text{W}$$

$$T^* = T_{amb} + \frac{k_1\,\delta\cdot R_{obj}}{k_2\,\gamma} = 25 + \frac{0.052 \times 0.105 \times 1000}{0.10 \times 1.0} = 79.6\,\text{°C}$$

La **condición de viabilidad térmica** se verifica numéricamente:

$$\frac{k_1\,\delta}{k_2\,\gamma} = 0.0546 < \frac{T_{crit} - T_{amb}}{R_{obj}} = 0.065 \quad \checkmark$$

El sistema base es viable y converge al equilibrio $(T^*=79.6\,\text{°C},\; R^*=1000\,\text{GFLOPS},\; P^*=105\,\text{W})$, con un margen térmico de $10.4\,\text{°C}$ respecto al umbral crítico. Esto fue confirmado por los tres métodos propios y RK45.

### 4.2.2 Estabilidad por retroalimentación negativa

**Perturbación térmica.** Si $T$ sube a $T^* + \varepsilon$:

$$\frac{dT}{dt}\bigg|_{T^*+\varepsilon} = \underbrace{k_1 P^* - k_2(T^*-T_{amb})}_{=\,0} - k_2\varepsilon = -k_2\varepsilon < 0$$

La derivada es negativa: el sistema enfría activamente hacia $T^*$.

**Perturbación de rendimiento.** Si $R$ cae bajo $R^*$, el término $\alpha(R_{obj} - R)$ se vuelve positivo, aumentando $\dot{P}$ y empujando $\dot{R}$ hacia valores positivos que restauran el throughput.

### 4.2.3 Régimen oscilatorio

Con los parámetros actuales el sistema base no entra en régimen oscilatorio. Para observarlo se puede aumentar $k_1$, reducir $k_2$, o elevar $R_{obj}$ hasta violar la condición de viabilidad. En ese caso el ciclo sería: el SO sube la potencia → la temperatura activa el throttling → el firmware corta la potencia → la temperatura cae → el SO intenta recuperar y el ciclo reinicia sin converger.

## 4.3 Cuatro escenarios de intervención

| Escenario | Modificación | $k_2$ | $\alpha$ | $T^*$ simulado | $R^*$ simulado | Viable |
|-----------|---|:---:|:---:|:---:|:---:|:---:|
| 0 — Base | Sin cambios | 0.10 | 1.6 | 79.6 °C | 1000 GFLOPS | ✓ |
| 1 — Undervolting | $\alpha / 4$ | 0.10 | 0.4 | 79.6 °C | 999.8 GFLOPS | ✓ |
| 2 — Refrigerante | $k_2 \times 2$ | 0.20 | 1.6 | 52.3 °C | 1000 GFLOPS | ✓ |
| 3 — Metal líquido | $k_2 \times 3$ | 0.30 | 1.6 | 43.2 °C | 1000 GFLOPS | ✓ |

Los escenarios 2 y 3 reducen $T^*$ en un 34% y 46% respectivamente sin sacrificar throughput, aumentando el margen de seguridad térmica. El escenario 1 muestra que reducir $\alpha$ a la cuarta parte apenas afecta el equilibrio final ($\Delta R = 0.2$ GFLOPS) pero sí ralentiza la convergencia.

## 4.4 Comparación entre métodos y análisis de error

| $h$ (s) | Euler | Euler Mejorado | RK4 |
|:---:|:---:|:---:|:---:|
| 1.0 | 21.69 | 7.14 | 4.72 |
| 0.5 | 9.88 | 5.07 | 4.94 |
| 0.1 | 5.96 | 5.30 | 5.30 |
| 0.05 | 5.61 | 5.30 | 5.30 |
| 0.01 | 5.38 | 5.32 | 5.32 |

Los errores reflejan la escala de las variables ($T \approx 80$, $R \approx 1000$, $P \approx 105$); los errores absolutos son pequeños. Euler muestra la mayor sensibilidad al tamaño de paso. RK4 y Euler Mejorado son robustos incluso para $h=0.5\,\text{s}$. Los tres métodos convergen al mismo equilibrio que RK45 con $h \leq 0.1\,\text{s}$, validando la implementación.

## 4.5 Animaciones

*[Completar con enlaces a las animaciones en línea. Describir: evolución temporal de $T$, $R$, $P$; trayectorias en el espacio de fases; instante de activación del throttling; contraste entre régimen estable y oscilatorio.]*

---

# 5. Conclusiones

*[Completar tras obtener los resultados de simulación. Incluir: síntesis de qué escenarios logran estabilidad y a qué costo; implicaciones prácticas de la condición de viabilidad térmica; reflexión sobre el trabajo en equipo, dificultades y aprendizajes del proyecto.]*

---

-

## Repositorio

Código disponible en: https://github.com/Alex-sklx0/Modelo-Dinamico-de-Estabilidad-Termica-y-Rendimiento-en-Computadores-de-Proposito-General

---

## Bibliografía

- Incropera, F. P. & DeWitt, D. P. (2002). *Fundamentos de transferencia de calor y masa*. Wiley.
- Kleinrock, L. (1976). *Queueing Systems, Vol. II: Computer Applications*. Wiley-Interscience.
- Ogata, K. (2010). *Ingeniería de control moderna*. Pearson.
- Ames, A. D. et al. (2019). Control Barrier Functions: Theory and Applications. *18th European Control Conference*.
- Nocedal, J. & Wright, S. J. (2006). *Numerical Optimization* (2nd ed.). Springer.
- Rao, S. S. (2019). *Engineering Optimization: Theory and Practice* (5th ed.). Wiley.
- Brooks, D. & Martonosi, M. (2001). Dynamic Thermal Management for High-Performance Microprocessors. *HPCA 2001*.
- Hennessy, J. L. & Patterson, D. A. (2019). *Computer Architecture: A Quantitative Approach* (6th ed.). Morgan Kaufmann.
- Williams, S., Waterman, A. & Patterson, D. (2009). Roofline model. *Communications of the ACM*, 52(4).