# Proyecto instrumentación y control de brazo robot.

> Proyecto que incluye la adecuación de un robot industrial ABB con soldadura por puntos, para establecer un sistema de control e instrumentación sobre su función en diferentes condiciones de trabajo.

---

##  Descripción del proyecto


**Este proyecto implementa:**

---

##  Motivación y problemática


---

##  Teoría y fundamentos

### Sistema físico

El sistema tiene **2 grados de libertad**:
- `θ` — ángulo del péndulo respecto a la vertical
- `φ` — ángulo de la rueda respecto al péndulo

### Ecuaciones de movimiento (Lagrangiano)


---

##  Estructura del repositorio

```
Reaction_wheel_pendulum/
│
│
├── CAD/                             # Diseño mecánico
│   ├── STL/                         # Archivos listos para imprimir
│   │   ├── Arm_V10_STL.stl
│   │   ├── Support_V5.stl
│   │   ├── Tower_V7_STL.stl
│   │   └── Wheel_V5_STL.stl
│   ├──planos/                      # Planos dimensionales PDF
│   │   ├── Arm.pdf
│   │   ├── ExplodedView.pdf
│   │   ├── Support_V5.pdf
│   │   ├── Tower_V7.pdf
│   │   └── Wheel_V5_Sheet.pdf
│   └──step/                        # Archivos STEP 
│       └── ensamble_completo.step
│
├── System_dinamics_test/            # Simulación y diseño de control
│   ├── params.m                     # Parámetros físicos del sistema
│   ├── model.m                      # Matrices A,B, controlabilidad, LQR
│   ├── simulation.m                 # Simulación no lineal ODE45
│   ├── system.m                     # Función dinámica no lineal 
│   └── resultados/                  # Gráficas exportadas
│       ├── respuesta_lineal.png
│       ├── simulacion_no_lineal.png
│       ├── lineal_vs_nolineal.png
│       └── lugar_de_raices.png
│
├── docs/                            # Documentación adicional
│   ├── teoria_completa.pdf          # Derivación matemática completa
│   └── img/
│       └── Assembly 1.png
│
├── src/                        # Código ESP32
│   ├── main/
│   │   ├── rwp_main.ino             # Controlador LQR completo
│   │   └── real_time_monitor.py     # Monitor en tiempo real
│   └── tools/
│       ├── sensors.h                # Lectura AS5600 + Encoder
│       └── identify_deadzone.ino    # Identificación zona muerta motor
│
├── electronics/                     # Diseño electrónico
│   └── schematic.pdf                # Esquemático completo
│
├── README.md
└── LICENSE

```

---

### Lista de componentes

---

Notas:

---

### Flujo de operación

```
1. Encender →

```

---

##  Simulación

---

### Parámetros de programación del robot

---

##  Resultados


---

##  Trabajo futuro

- [ ] **Identificación experimental** de parámetros del motor (Kt, Ra, Ke)
- [ ] **Comparación PID vs LQR** con métricas cuantitativas (ISE, IAE, ITAE)
- [ ] **Control swing-up** mediante control por energía para llevar el péndulo desde posición colgante hasta vertical
- [ ] **Filtro de Kalman** para estimación de estados con fusión de sensores
- [ ] **Extensión a 2 ejes** (dual axis reaction wheel — balanceo sobre una punta)
- [ ] **Interfaz web** vía WiFi del ESP32 para ajuste de ganancias en tiempo real
- [ ] **Validación experimental** con comparación cuantitativa simulación vs hardware

---

<p align="center">
  Hecho con café y demasiadas horas en MATLAB
</p>
