# MADTEC2026-GUI

> Sistema de adquisición de datos e interfaz gráfica para control de robot industrial ABB con soldadura por puntos.

Repositorio que recopila la programación Python y modelos CAD para análisis de datos en tiempo real del proceso de soldadura por puntos.

---

##  Descripción Rápida

Este proyecto implementa una **interfaz gráfica (HMI)** en Python/PyQt5 para:
- **Controlar** el robot ABB mediante conexión Snap7 al PLC
- **Adquirir datos** de sensores de fuerza y corriente durante soldadura
- **Visualizar gráficas** en tiempo real (Fuerza vs Tiempo, Corriente vs Tiempo)
- **Gestionar casos de prueba** con parámetros de soldadura
- **Capturar QR** para escaneo automático de casos
- **Guardar datos** en base de datos remota

---

##  Estructura del Repositorio

```
MADTEC2026-GUI/
│
├── src/HMI/                          # Código principal de la interfaz gráfica
│   ├── HMI_python.py                 # Punto de entrada principal
│   └── hmi/
│       ├── app.py                    # Clase principal HMI (PyQt5)
│       ├── config.py                 # Configuración (URLs, IPs, puertos)
│       ├── services/
│       │   ├── api_client.py        # Cliente HTTP para API backend
│       │   ├── plc.py               # Interfaz Snap7 con PLC
│       │   └── ...
│       ├── widgets/                  # Componentes UI personalizados
│       │   └── AlertLog.py           # Widget de alertas
│       ├── utils/
│       │   ├── plotting.py           # Funciones de graficación
│       │   ├── QRCodes/             # Códigos QR generados
│       │   └── ...
│       └── __init__.py
│
├── packaging/                        # Scripts de compilación
│   ├── build_hmi.sh                 # Script para PyInstaller
│   └── README_HMI.md                # Documentación de packaging
│
├── CAD/                             # Modelos 3D y planos (si aplica)
├── docs/                            # Documentación adicional
├── requirements.txt                 # Dependencias Python
├── .gitignore
└── README.md                        # Este archivo
```

---

##  Inicio Rápido

### Requisitos
- **Python 3.10**
- **Linux** (Tested en Ubuntu 20.04, Jetson)
- Conexión a PLC ABB y backend API REST

### Opción 1: Ejecución Directa

**En PC Linux (x86_64):**
```bash
conda activate MADTEC2026
cd /home/cetevi/Documents/GitHub/MADTEC2026-GUI/src/HMI
python3 HMI_python.py
```

**En Jetson Linux (ARM64):**
```bash
conda activate sonyilx
cd /home/cetevi/MADTEC2026-GUI/src/HMI
python3 HMI_python.py
```

### Opción 2: Instalación Manual desde Cero

1. **Clonar repositorio:**
   ```bash
   git clone https://github.com/2410917017-afk/MADTEC2026-GUI.git
   cd MADTEC2026-GUI
   ```

2. **Crear entorno Conda:**
   ```bash
   conda create -n MADTEC2026 python=3.10
   conda activate MADTEC2026
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar parámetros (IMPORTANTE):**
   Editar `src/HMI/hmi/config.py`:
   ```python
   BASE_URL = "http://192.168.2.199:8000"  # URL del backend
   PLC_HOST = "192.168.0.1"               # IP del PLC
   PLC_RACK = 0                           # Rack del PLC
   PLC_SLOT = 1                           # Slot del PLC
   SERIAL_PORT = "/dev/ttyUSB0"          # Puerto serial (si aplica)
   ```

5. **Ejecutar:**
   ```bash
   python3 src/HMI/HMI_python.py
   ```

### Opción 3: Usar Ejecutable Precompilado

Ver [packaging/README_HMI.md](packaging/README_HMI.md) para compilar con PyInstaller.

```bash
./packaging/build_hmi.sh
./dist/HMI_python_linux_x86_64  # o aarch64 en Jetson
```

---

##  Interfaz Gráfica (Tabs)

### Tab 1: **Inicio** (Adquisición de datos)
- **Conectar**: Establece conexión con PLC y cámara
- **Seleccionar caso**: Elige parámetros de soldadura predefinidos
- **Muestras**: Define número de puntos de datos a capturar
- **Enviar**: Envía parámetros al PLC
- **Iniciar**: Activa ciclo de soldadura
- **Gráficas**: Visualización en tiempo real de Fuerza e Corriente
- **Guardar datos**: Almacena prueba en base de datos

### Tab 2: **Configuración** (Gestión de casos)
- **Nuevo**: Añade fila para nuevo caso de prueba
- **Guardar**: Persiste cambios en base de datos
- **Borrar**: Elimina caso seleccionado
- **Actualizar**: Recarga tabla desde servidor
- **Tabla**: Ver/editar parámetros: Tiempo, Fuerza, Compresión, Pulsos, Material, Grosor, Separación

### Tab 3: **Cámara** (Monitoreo con QR)
- **Vista en vivo**: Captura de cámara Sony ILX
- **Detección QR**: Identificación automática de casos mediante código QR
- **+/-**: Controles de zoom

---

##  Configuración Avanzada

### Cambiar Estilos
En `src/HMI/hmi/app.py`, busca `setStyleSheet`:
```python
self.setStyleSheet("background-color: #060c06; color: white")  # Tema oscuro
```

### Modificar Botones
Cada botón tiene su propia configuración de estilo:
```python
self.buttonstart.setStyleSheet("""
    QPushButton {
        background-color: #494be7;
        color: #dddcde;
        border-radius: 36px;
        ...
    }
""")
```

### Agregar Nuevos Parámetros
1. Añadir en la tabla `Tab 2` (editar headers en línea 554)
2. Actualizar `show_plot()` en `app.py` para lectura de datos
3. Modificar API calls en `services/api_client.py`

---

##  Dependencias Principales

```
PyQt5              # Interfaz gráfica
python-snap7       # Comunicación Snap7 con PLC
matplotlib         # Graficación
cv2                # Visión por computadora
requests           # Cliente HTTP
sonyilx_camera     # Control de cámara Sony
```

Ver `requirements.txt` para versiones exactas.

---

##  Solución de Problemas

### Error: "No module named 'sonyilx_camera'"

-Instalar librería Sonyilx (Revisar archivo Help.md)


### Error: "Connection refused" al PLC
- Verificar IP en `config.py` (debe coincidir con PLC)
- Probar conectividad: `ping 192.168.0.1`

### Error: "Camera not connected"
- Verificar conexión física de cámara Sony
- Revisar permisos USB: `sudo usermod -a -G dialout $USER`

### Ejecutable no funciona en otra máquina
- Usar arquitectura compatible: x86_64 en PC, aarch64 en Jetson
- Verificar glibc compatible: `ldd ./dist/HMI_python`

---

##  Flujo de Datos

```
PLC (ABB)
    ↓ (Snap7)
[HMI GUI] ← Lee datos de fuerza, corriente, tiempo
    ↓
[Matplotlib] ← Grafica en tiempo real
    ↓
[Backend API] ← Envía datos almacenados
    ↓
[Base de datos] ← Registra pruebas
```

---

##  Edición de Código

### Agregar Nueva Funcionalidad

1. **Crear método en `app.py`:**
   ```python
   def mi_nueva_funcion(self):
       try:
           # Tu código
           self.alerts.escribirAlerta("Éxito ✓")
       except Exception as e:
           self.alerts.escribirAlerta(f"Error: {e}")
   ```

2. **Conectar con botón:**
   ```python
   self.miBoton = QPushButton("Mi Botón")
   self.miBoton.clicked.connect(self.mi_nueva_funcion)
   ```

3. **Añadir al layout:**
   ```python
   main_layout.addWidget(self.miBoton, fila, columna)
   ```

### Modificar Lectura de Datos PLC

En `app.py`, función `show_plot()` (línea 1184):
```python
self.force_array = self.read_real_array(db_number=1, start_byte=0, count=num)
```

Cambiar `db_number`, `start_byte` según configuración de memoria PLC.

---


**Última actualización:** Julio 2026  
**Estado:** En desarrollo  
**Versión Python:** 3.10  
**Sistemas Soportados:** Linux x86_64, ARM64 (Jetson)
