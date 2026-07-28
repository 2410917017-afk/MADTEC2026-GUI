# 🎥 SonyILX + OpenCV: Video en Vivo y Análisis

## 📌 Introducción

La **SonyILX Library** es principalmente para **fotografía** (captura de imágenes estáticas), pero podemos usarla en combinación con **OpenCV** de diferentes formas:

1. **Live View (Vista en Vivo)**: Capturar frames en tiempo real
2. **Secuencia de Fotos Rápidas**: Tomar múltiples fotos para crear un video
3. **Análisis de Imágenes Capturadas**: Aplicar visión por computadora a las fotos

---

## 🚀 Instalación de Dependencias

```bash
conda activate sonyilx

# Instalar OpenCV
pip install opencv-python numpy

# Para análisis avanzado (opcional)
pip install scikit-image matplotlib
```

---

## 📚 API Principal de SonyILX

```python
import sonyilx_camera as ilx

camera = ilx.CameraLibrary()

# === INICIALIZACIÓN ===
camera.initialize()           # Inicializar SDK
camera.connect_first_camera() # Conectar primera cámara disponible

# === CAPTURA ===
camera.take_shot()            # Capturar una foto
camera.refresh_live_view()    # Obtener vista en vivo (JPEG)

# === CONFIGURACIÓN ===
camera.set_focus_mode(mode)
camera.set_still_capture_mode(mode)
camera.set_zoom_position(position)
camera.set_target_folder(path)

# === LECTURA DE ESTADO ===
camera.camera_name()
camera.current_focus_mode()
camera.zoom_position()
camera.is_connected()

# === CLEANUP ===
camera.disconnect_camera()
camera.shutdown()
```

---

## 🎬 Ejemplo 1: Live View (Vista en Vivo en Tiempo Real)

Este es el caso más común: capturar frames de la vista en vivo y analizarlos con OpenCV.

```python
import sonyilx_camera as ilx
import cv2
import numpy as np
import os
from pathlib import Path

class SonyLiveViewAnalyzer:
    def __init__(self, output_folder="/tmp/sonyilx-liveview"):
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)
        self.camera = ilx.CameraLibrary()
        self.frame_count = 0
    
    def initialize(self):
        """Inicializar cámara"""
        if not self.camera.initialize():
            raise RuntimeError(f"Error inicializando: {self.camera.last_error()}")
        
        if not self.camera.connect_first_camera():
            raise RuntimeError(f"Error conectando: {self.camera.last_error()}")
        
        print(f"✓ Cámara conectada: {self.camera.camera_name()}")
        self.camera.set_target_folder(str(self.output_folder))
    
    def get_liveview_frame(self):
        """Obtener frame de vista en vivo"""
        try:
            # Obtener ruta del archivo JPEG de la vista en vivo
            live_view_path = self.camera.refresh_live_view()
            
            if not live_view_path or not os.path.exists(live_view_path):
                return None
            
            # Leer imagen con OpenCV
            frame = cv2.imread(live_view_path)
            return frame
        except Exception as e:
            print(f"Error getting liveview: {e}")
            return None
    
    def analyze_frame(self, frame):
        """Análisis de ejemplo: detectar bordes"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        return edges
    
    def process_liveview_stream(self, duration_seconds=30):
        """Procesar stream de vista en vivo por N segundos"""
        print(f"\n📹 Capturando vista en vivo por {duration_seconds} segundos...")
        print("   Presiona 'q' en la ventana de video para salir antes")
        
        import time
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            # Obtener frame
            frame = self.get_liveview_frame()
            if frame is None:
                print("⚠ No se pudo obtener frame")
                continue
            
            # Analizar
            edges = self.analyze_frame(frame)
            
            # Mostrar
            cv2.imshow("Sony Live View", frame)
            cv2.imshow("Edges (Análisis)", edges)
            
            # Guardar cada 10 frames
            if self.frame_count % 10 == 0:
                output_file = self.output_folder / f"frame_{self.frame_count:04d}.jpg"
                cv2.imwrite(str(output_file), frame)
                print(f"   Frame {self.frame_count} guardado")
            
            self.frame_count += 1
            
            # Tecla 'q' para salir
            if cv2.waitKey(100) & 0xFF == ord('q'):
                break
        
        cv2.destroyAllWindows()
        print(f"✓ Captura completada: {self.frame_count} frames")
    
    def shutdown(self):
        """Limpiar"""
        self.camera.disconnect_camera()
        self.camera.shutdown()
        print("✓ Cámara desconectada")

# USO
if __name__ == "__main__":
    analyzer = SonyLiveViewAnalyzer()
    
    try:
        analyzer.initialize()
        analyzer.process_liveview_stream(duration_seconds=30)
    finally:
        analyzer.shutdown()
```

**Nota:** La vista en vivo se guarda como JPEG en la ruta especificada. OpenCV lo lee y lo analiza en tiempo real.

---

## 🎬 Ejemplo 2: Captura Rápida (Burst Photography + Video)

Capturar múltiples fotos rápidamente y procesarlas como video.

```python
import sonyilx_camera as ilx
import cv2
import numpy as np
from pathlib import Path
import time
import os

class SonyBurstVideoCapture:
    def __init__(self, output_folder="/tmp/sonyilx-burst", fps=30):
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)
        self.camera = ilx.CameraLibrary()
        self.fps = fps
        self.captured_images = []
    
    def initialize(self):
        """Inicializar cámara"""
        if not self.camera.initialize():
            raise RuntimeError(f"Error: {self.camera.last_error()}")
        
        if not self.camera.connect_first_camera():
            raise RuntimeError(f"Error: {self.camera.last_error()}")
        
        # Configurar modo de captura rápida
        print(f"✓ Cámara: {self.camera.camera_name()}")
        
        # Ver modos disponibles
        capture_modes = self.camera.possible_still_capture_modes()
        print(f"   Modos disponibles: {capture_modes}")
        
        self.camera.set_target_folder(str(self.output_folder))
    
    def capture_burst(self, num_shots=30):
        """Capturar ráfaga de fotos"""
        print(f"\n📸 Capturando {num_shots} fotos...")
        
        for i in range(num_shots):
            try:
                if not self.camera.take_shot():
                    print(f"   ⚠ Error en captura {i}: {self.camera.last_error()}")
                    continue
                
                print(f"   ✓ Foto {i+1}/{num_shots}")
                time.sleep(0.2)  # Esperar 200ms entre fotos
                
            except Exception as e:
                print(f"   ✗ Error: {e}")
        
        print("✓ Captura completada")
    
    def create_video_from_burst(self, output_video="output.mp4"):
        """Crear video a partir de las fotos capturadas"""
        image_folder = self.output_folder
        
        # Obtener lista de imágenes
        images = sorted([f for f in os.listdir(image_folder) if f.endswith(('.jpg', '.png'))])
        
        if not images:
            print("⚠ No hay imágenes para crear video")
            return
        
        print(f"\n🎬 Creando video con {len(images)} imágenes...")
        
        # Leer primera imagen para obtener dimensiones
        first_image = cv2.imread(os.path.join(image_folder, images[0]))
        height, width = first_image.shape[:2]
        
        # Crear writer de video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video, fourcc, self.fps, (width, height))
        
        # Escribir frames
        for img_name in images:
            img_path = os.path.join(image_folder, img_name)
            frame = cv2.imread(img_path)
            
            if frame is not None:
                out.write(frame)
        
        out.release()
        print(f"✓ Video guardado: {output_video}")
    
    def shutdown(self):
        """Limpiar"""
        self.camera.disconnect_camera()
        self.camera.shutdown()

# USO
if __name__ == "__main__":
    burst = SonyBurstVideoCapture(fps=15)
    
    try:
        burst.initialize()
        burst.capture_burst(num_shots=30)  # 30 fotos
        burst.create_video_from_burst("/tmp/sonyilx_burst_output.mp4")
    finally:
        burst.shutdown()
```

---

## 🔍 Ejemplo 3: Análisis Avanzado con OpenCV

Detectar objetos, rostros, movimiento, etc.

```python
import sonyilx_camera as ilx
import cv2
import numpy as np
from pathlib import Path

class SonyAdvancedAnalyzer:
    def __init__(self):
        self.camera = ilx.CameraLibrary()
        self.output_folder = Path("/tmp/sonyilx-analysis")
        self.output_folder.mkdir(exist_ok=True)
    
    def initialize(self):
        if not self.camera.initialize():
            raise RuntimeError(self.camera.last_error())
        
        if not self.camera.connect_first_camera():
            raise RuntimeError(self.camera.last_error())
        
        self.camera.set_target_folder(str(self.output_folder))
    
    # === ANÁLISIS 1: Detección de Movimiento ===
    def motion_detection(self, frame, prev_frame):
        """Detectar movimiento entre frames"""
        if prev_frame is None:
            return None, 0
        
        # Convertir a escala de grises
        gray1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calcular diferencia
        diff = cv2.absdiff(gray1, gray2)
        
        # Threshold
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        
        # Porcentaje de movimiento
        motion_pixels = cv2.countNonZero(thresh)
        total_pixels = thresh.shape[0] * thresh.shape[1]
        motion_percentage = (motion_pixels / total_pixels) * 100
        
        return thresh, motion_percentage
    
    # === ANÁLISIS 2: Detección de Aristas ===
    def edge_detection(self, frame):
        """Detectar bordes (Canny)"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
        edges = cv2.Canny(blurred, 100, 200)
        return edges
    
    # === ANÁLISIS 3: Detección de Rostros ===
    def face_detection(self, frame):
        """Detectar rostros"""
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Dibujar rectángulos
        result = frame.copy()
        for (x, y, w, h) in faces:
            cv2.rectangle(result, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(result, f"Face", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, (255, 0, 0), 2)
        
        return result, len(faces)
    
    # === ANÁLISIS 4: Contornos y Objetos ===
    def contour_detection(self, frame):
        """Detectar contornos de objetos"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Dibujar contornos
        result = frame.copy()
        cv2.drawContours(result, contours, -1, (0, 255, 0), 2)
        
        return result, len(contours)
    
    # === ANÁLISIS 5: Histograma de Color ===
    def color_histogram(self, frame):
        """Analizar distribución de colores"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Calcular histogramas
        hist_hue = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        hist_sat = cv2.calcHist([hsv], [1], None, [256], [0, 256])
        hist_val = cv2.calcHist([hsv], [2], None, [256], [0, 256])
        
        return hist_hue, hist_sat, hist_val
    
    def run_analysis_stream(self, duration_seconds=30):
        """Ejecutar análisis en stream de vista en vivo"""
        print(f"\n🔍 Analizando vista en vivo por {duration_seconds} seg...")
        
        import time
        start_time = time.time()
        prev_frame = None
        frame_count = 0
        
        while time.time() - start_time < duration_seconds:
            # Obtener frame
            live_view_path = self.camera.refresh_live_view()
            if not live_view_path:
                continue
            
            frame = cv2.imread(live_view_path)
            if frame is None:
                continue
            
            # === Análisis 1: Movimiento ===
            motion_mask, motion_pct = self.motion_detection(frame, prev_frame)
            
            # === Análisis 2: Aristas ===
            edges = self.edge_detection(frame)
            
            # === Análisis 3: Rostros ===
            face_frame, num_faces = self.face_detection(frame)
            
            # === Análisis 4: Contornos ===
            contour_frame, num_contours = self.contour_detection(frame)
            
            # Mostrar resultados
            cv2.putText(frame, f"Motion: {motion_pct:.2f}% | Faces: {num_faces}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow("Original", frame)
            cv2.imshow("Edges", edges)
            cv2.imshow("Faces", face_frame)
            cv2.imshow("Contours", contour_frame)
            
            prev_frame = frame.copy()
            frame_count += 1
            
            if cv2.waitKey(100) & 0xFF == ord('q'):
                break
        
        cv2.destroyAllWindows()
        print(f"✓ Análisis completado ({frame_count} frames)")
    
    def shutdown(self):
        self.camera.disconnect_camera()
        self.camera.shutdown()

# USO
if __name__ == "__main__":
    analyzer = SonyAdvancedAnalyzer()
    
    try:
        analyzer.initialize()
        analyzer.run_analysis_stream(duration_seconds=30)
    finally:
        analyzer.shutdown()
```

---

## 💡 Técnicas Típicas de OpenCV

| Técnica | Descripción | Uso |
|---------|-------------|-----|
| **Edge Detection (Canny)** | Detecta bordes en la imagen | Análisis de formas, contornos |
| **Motion Detection** | Detecta cambios entre frames | Vigilancia, tracking |
| **Face Detection** | Detecta rostros | Reconocimiento facial, seguridad |
| **Contour Detection** | Detecta objetos/formas | Análisis de objetos, segmentación |
| **Color Histogram** | Analiza distribución de colores | Análisis de iluminación |
| **Corner Detection (Harris/FAST)** | Detecta esquinas | Feature matching, tracking |
| **Template Matching** | Busca patrones | Detección de objetos específicos |
| **Morphological Operations** | Erosión, dilatación | Limpieza de imágenes |
| **Optical Flow** | Detecta movimiento de píxeles | Análisis de movimiento detallado |
| **Threshold/Segmentation** | Separa objetos por intensidad | Segmentación de imagen |

---

## 📋 Usos Generales de SonyILX Library

### 1. **Fotografía de Producto**
```python
# Capturar productos con precisión
camera.set_focus_mode("Manual")
camera.set_zoom_position(100)
camera.take_shot()
```

### 2. **Inspección Industrial**
```python
# Inspeccionar piezas con zoom de precisión
for zoom in range(0, 100, 10):
    camera.set_zoom_position(zoom)
    camera.take_shot()
    # Analizar con OpenCV
```

### 3. **Documentación de Archivos**
```python
# Escanear documentos de forma automatizada
camera.set_target_folder("/documentos")
camera.set_still_capture_mode("Normal")
for page_num in range(total_pages):
    camera.take_shot()
```

### 4. **Calibración de Cámara**
```python
# La librería incluye herramientas de calibración
# (Ver sección "Image Processing" en README.md)
camera_params = camera.camera_calibration_folder()
```

### 5. **Vigilancia y Grabación de Eventos**
```python
# Capturar a intervalos o por eventos
import time
while True:
    live_view = camera.refresh_live_view()
    # Analizar con OpenCV
    # Capturar si hay cambios significativos
    if motion_detected:
        camera.take_shot()
    time.sleep(1)
```

### 6. **Fotogrametría**
```python
# Capturar objeto desde múltiples ángulos para reconstrucción 3D
for angle in range(0, 360, 15):
    rotate_object(angle)  # Tu código
    camera.take_shot()
    # Procesar con OpenCV/herramientas 3D
```

### 7. **Microscopía**
```python
# Control preciso de zoom para análisis microscópico
camera.set_zoom_distance(50)  # 50mm de distancia
camera.zoom_in()
camera.take_shot()
```

### 8. **Live View para QA/Control de Calidad**
```python
# Monitor en tiempo real durante producción
while camera.is_connected():
    frame = get_liveview_frame()
    if detect_defect(frame):
        alert_operator()
```

---

## 🎬 Flujo Típico Completo

```python
import sonyilx_camera as ilx
import cv2
import numpy as np
from pathlib import Path
import time

def complete_workflow():
    # 1️⃣ INICIALIZAR
    camera = ilx.CameraLibrary()
    camera.initialize()
    camera.connect_first_camera()
    camera.set_target_folder("/tmp/sonyilx-workflow")
    
    # 2️⃣ CONFIGURAR
    camera.set_focus_mode("AF-S")  # Autofocus
    camera.set_zoom_position(50)    # 50% zoom
    
    # 3️⃣ VISTA PREVIA EN VIVO
    print("Ajusta el encuadre en la vista en vivo...")
    for i in range(5):
        live_view_path = camera.refresh_live_view()
        frame = cv2.imread(live_view_path)
        cv2.imshow("Live View", frame)
        cv2.waitKey(500)
    cv2.destroyAllWindows()
    
    # 4️⃣ CAPTURAR
    print("Capturando...")
    for i in range(5):
        camera.take_shot()
        time.sleep(1)
    
    # 5️⃣ ANALIZAR CON OPENCV
    import os
    capture_folder = "/tmp/sonyilx-workflow"
    images = sorted([f for f in os.listdir(capture_folder) if f.endswith('.jpg')])
    
    for img_name in images:
        img_path = os.path.join(capture_folder, img_name)
        frame = cv2.imread(img_path)
        
        # Análisis básico
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        
        print(f"Analizando {img_name}: {edges.shape}")
    
    # 6️⃣ LIMPIAR
    camera.disconnect_camera()
    camera.shutdown()

if __name__ == "__main__":
    complete_workflow()
```

---

## 📦 Dependencias Completas

```bash
# Instalar todo
pip install opencv-python numpy scikit-image matplotlib scipy
```

---

## ⚠️ Limitaciones Importantes

1. **NO es una cámara de video**: No captura video continuo, solo fotos
2. **Live View es JPEG**: No es tiempo real perfecto (hay latencia)
3. **Requiere cámara Sony conectada**: La mayoría de funciones necesitan hardware
4. **USB es principal**: La conexión de red requiere más configuración

---

## ✅ Resumen

| Aspecto | Cómo Usar |
|--------|----------|
| **Video en vivo** | `refresh_live_view()` + OpenCV |
| **Video file** | Capturar ráfagas + `cv2.VideoWriter` |
| **Análisis de imagen** | Leer JPEG + OpenCV functions |
| **Inspección** | Zoom + capture + análisis |
| **Vigilancia** | Loop + detect changes + capture |

