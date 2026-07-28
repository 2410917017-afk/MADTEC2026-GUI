#  SonyILX + OpenCV: Guía Rápida

##  Resumen en 60 segundos

La **SonyILX Library** permite controlar cámaras Sony para:
- Capturar fotos de alta precisión
- Obtener vista en vivo (Live View)
- Crear videos a partir de ráfagas de fotos
- Combinar con OpenCV para análisis de imagen

**OpenCV** se conecta leyendo archivos JPEG que genera la vista en vivo.

---

##  3 Usos Principales

### 1️⃣ **Vista en Vivo + OpenCV (EN TIEMPO REAL)**
```python
import sonyilx_camera as ilx
import cv2

camera = ilx.CameraLibrary()
camera.initialize()
camera.connect_first_camera()
camera.set_target_folder("/tmp")

# Capturar vista en vivo y analizar
frame = cv2.imread(camera.refresh_live_view())
edges = cv2.Canny(frame, 100, 200)

cv2.imshow("Aristas", edges)
```

### 2️⃣ **Ráfaga de Fotos → Video**
```python
# Capturar 60 fotos
for i in range(60):
    camera.take_shot()

# Convertir a video con OpenCV
images = sorted(glob("*.jpg"))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('output.mp4', fourcc, 30, (1920, 1080))

for img in images:
    frame = cv2.imread(img)
    out.write(frame)
out.release()
```

### 3️⃣ **Análisis Avanzado (Detección de Rostros, Movimiento, etc.)**
```python
# Detección de movimiento
diff = cv2.absdiff(frame1, frame2)
_, motion_mask = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

# Detección de rostros
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
faces = face_cascade.detectMultiScale(gray_frame, 1.3, 5)

# Detección de esquinas
corners = cv2.cornerHarris(gray_frame, 2, 3, 0.04)
```

---

##  API de SonyILX (Métodos Principales)

```python
# ===== INICIALIZACIÓN =====
camera.initialize()              # Iniciar SDK
camera.connect_first_camera()    # Conectar cámara
camera.shutdown()                # Apagar SDK

# ===== CAPTURA =====
camera.take_shot()               # Capturar 1 foto
camera.refresh_live_view()       # Obtener vista en vivo (JPEG)

# ===== CONFIGURACIÓN =====
camera.set_focus_mode(mode)              # "AF-S", "AF-C", "MF"
camera.set_zoom_position(pos)            # 0-100
camera.set_target_folder(path)           # Dónde guardar fotos
camera.set_still_capture_mode(mode)      # Modo de captura

# ===== LECTURA =====
camera.camera_name()             # "ILX-LR1"
camera.current_focus_mode()      # Modo actual
camera.zoom_position()           # Zoom actual
camera.is_connected()            # ¿Conectado?
```

---

##  Instalación Rápida

```bash
# 1. Copiar librerías SDK
CRSDK_PATH="/home/cetevi/Documents/GitHub/MADTEC-PROJECT-CODES/PAQUETES SDK/CrSDK_v2.01.00_20260203a_Linux64PC"
TARGET_DIR="/home/cetevi/Documents/GitHub/MADTEC-PROJECT-CODES/CAMARA/CPP/SonyILXLibrary/external/crsdk"
cp "$CRSDK_PATH/RemoteCli/external/crsdk"/*.so "$TARGET_DIR/"
cp -r "$CRSDK_PATH/RemoteCli/external/crsdk"/CrAdapter "$TARGET_DIR/"

# 2. Instalar librería
cd /home/cetevi/Documents/GitHub/MADTEC-PROJECT-CODES/CAMARA/CPP/SonyILXLibrary
pip install .

# 3. Crear enlaces simbólicos
SITE_PACKAGES="$(python -c 'import pathlib, sonyilx_camera; print(pathlib.Path(sonyilx_camera.__file__).resolve().parent)')"
ENV_PREFIX="$(python -c 'import sys; print(sys.prefix)')"
ln -sfn "$SITE_PACKAGES/CrAdapter" "$ENV_PREFIX/bin/CrAdapter"
ln -sfn "$SITE_PACKAGES/libmonitor_protocol_pf.so" "$ENV_PREFIX/lib/libmonitor_protocol_pf.so"
ln -sfn "$SITE_PACKAGES/libmonitor_protocol.so" "$ENV_PREFIX/lib/libmonitor_protocol.so"

# 4. Instalar OpenCV
pip install opencv-python numpy
```

---

##  Ejemplo Completo: Análisis de Vista en Vivo

```python
import sonyilx_camera as ilx
import cv2
import numpy as np

# Inicializar
camera = ilx.CameraLibrary()
camera.initialize()
camera.connect_first_camera()
camera.set_target_folder("/tmp/sony")

print(f"Cámara: {camera.camera_name()}")

# Obtener frame y analizar
for i in range(30):
    # Obtener vista en vivo
    live_view = camera.refresh_live_view()
    frame = cv2.imread(live_view)
    
    # Análisis con OpenCV
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    brightness = np.mean(gray)
    
    # Mostrar
    print(f"Frame {i}: Brillo={brightness:.0f}")
    cv2.imshow("Original", frame)
    cv2.imshow("Aristas", edges)
    
    if cv2.waitKey(100) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
camera.disconnect_camera()
camera.shutdown()
```

---

##  Técnicas OpenCV Comunes

| Técnica | Código | Uso |
|---------|--------|-----|
| **Escala de grises** | `cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)` | Preprocesamiento |
| **Detección de aristas** | `cv2.Canny(gray, 100, 200)` | Detectar bordes |
| **Gaussian blur** | `cv2.GaussianBlur(frame, (5,5), 0)` | Suavizar ruido |
| **Threshold** | `cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)` | Segmentación |
| **Contornos** | `cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)` | Detectar objetos |
| **Corners (Harris)** | `cv2.cornerHarris(gray, 2, 3, 0.04)` | Detectar esquinas |
| **Motion** | `cv2.absdiff(frame1, frame2)` | Detectar cambios |
| **Histogram** | `cv2.calcHist([frame], [0], None, [256], [0,256])` | Analizar colores |

---

##  Configuración de Cámara

```python
# Modos de enfoque
camera.set_focus_mode("AF-S")      # Autofocus singlas
camera.set_focus_mode("AF-C")      # Autofocus continuo
camera.set_focus_mode("MF")        # Enfoque manual

# Zoom
camera.set_zoom_position(0)        # Sin zoom
camera.set_zoom_position(50)       # 50% zoom
camera.set_zoom_position(100)      # Zoom máximo

# Modos de captura (consulta con camera.possible_still_capture_modes())
camera.set_still_capture_mode("Normal")
camera.set_still_capture_mode("Burst")

# Ver opciones disponibles
print(camera.possible_focus_modes())
print(camera.possible_still_capture_modes())
print(camera.zoom_position_minimum(), "-", camera.zoom_position_maximum())
```

---

##  Casos de Uso Típicos

###  Fotografía de Producto
```python
camera.set_zoom_position(80)
camera.take_shot()
# Analizar con OpenCV para QA
```

###  Microscopía
```python
camera.set_zoom_distance(50)  # 50mm
camera.zoom_in()
camera.take_shot()
```

###  Vigilancia en Tiempo Real
```python
import time

prev_frame = None
while camera.is_connected():
    frame = cv2.imread(camera.refresh_live_view())
    diff = cv2.absdiff(prev_frame, frame) if prev_frame is not None else 0
    
    if np.mean(diff) > 30:  # Movimiento detectado
        camera.take_shot()
        print("ALERTA: Movimiento detectado")
    
    prev_frame = frame
    time.sleep(1)
```

###  Calibración de Cámara
```python
# La librería tiene herramientas de calibración integradas
camera_params = camera.camera_calibration_folder()
# Ver más en: README.md → "Image Processing, Calculation, and Measurements"
```

---

##  Ejecutar Ejemplos

```bash
# Script simple de liveview con OpenCV
python example_liveview_with_opencv.py

# Ver más ejemplos en OPENCV_VIDEO_ANALYSIS.md
```

---

## ✅ Verificación Rápida

```bash
# Probar que todo funciona
python -c "
import sonyilx_camera as ilx
import cv2
import numpy as np

print('✅ sonyilx_camera importado')
print('✅ cv2 importado')
print('✅ numpy importado')

# Ver API disponible
camera = ilx.CameraLibrary()
methods = [m for m in dir(camera) if not m.startswith('_')]
print(f'✅ Métodos disponibles: {len(methods)}')
print('✅ ¡Listo para usar!')
"
```

---

## ⚠️ Problemas Comunes

| Error | Solución |
|-------|----------|
| `ModuleNotFoundError: sonyilx_camera` | Reinstalar: `pip install --force-reinstall .` |
| `Adaptor_Create` | Recrear enlaces simbólicos (paso 3 de instalación) |
| `Cámara no detectada` | Verificar modo USB de cámara, aplicar permisos udev |
| `cv2 no encontrado` | `pip install opencv-python` |

---

##  Documentos de Referencia

- **Setup**: SETUP_GUIDE.md (instalación completa)
- **Análisis avanzado**: OPENCV_VIDEO_ANALYSIS.md (técnicas OpenCV)
- **Ejemplos**: example_liveview_with_opencv.py (código ejecutable)

