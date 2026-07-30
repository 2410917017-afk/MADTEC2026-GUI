# Guía: Instalación de SonyILX Library para Python en Ubuntu Linux

##  Resumen del Proyecto
La **SonyILX Library** es una librería Python + C++ que proporciona un wrapper para las cámaras Sony Remote SDK (como Sony ILX-LR1). Se distribuye como módulo de extensión Python compilado con `pybind11`.

---

##  Requisitos Previos en Ubuntu

### 1. **Dependencias del Sistema**
```bash
sudo apt update
sudo apt install -y \
  cmake \
  ninja-build \
  build-essential \
  libxml2-dev \
  python3-dev \
  libusb-1.0-0-dev
```

### 2. **Conda/Miniconda**
Si aún no tienes Conda instalado:
```bash
# Descargar Miniconda
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Reiniciar terminal o ejecutar
source ~/miniconda3/bin/activate
```

---

##  Pasos de Instalación (COMPLETOS Y VERIFICADOS)

### **Paso 1: Crear Entorno Conda**
```bash
conda create -n sonyilx python=3.10
conda activate sonyilx
```

### **Paso 2: Instalar Herramientas de Compilación**
```bash
conda install -c conda-forge \
  cmake \
  ninja \
  pip \
  pybind11 \
  scikit-build-core
```

### **Paso 3: Copiar Librerías Compiladas del Sony SDK**  **IMPORTANTE**
Las librerías compiladas del Sony SDK NO están incluidas en el repositorio. Se encuentran en `PAQUETES SDK/`. Cópialas:

```bash
# Encontrar y copiar las librerías del Sony SDK (v2.01.00)
CRSDK_PATH="/home/cetevi/Documents/GitHub/MADTEC-PROJECT-CODES/PAQUETES SDK/CrSDK_v2.01.00_20260203a_Linux64PC"
TARGET_DIR="/home/cetevi/Documents/GitHub/MADTEC-PROJECT-CODES/CAMARA/CPP/SonyILXLibrary/external/crsdk"

# Copiar librerías compiladas
cp "$CRSDK_PATH/RemoteCli/external/crsdk"/*.so "$TARGET_DIR/" 2>/dev/null || true
cp -r "$CRSDK_PATH/RemoteCli/external/crsdk"/CrAdapter "$TARGET_DIR/" 2>/dev/null || true

# Verificar que se copiaron
echo "✓ Librerías copiadas:"
ls -lh "$TARGET_DIR"/*.so "$TARGET_DIR"/CrAdapter/*.so
```

**Salida esperada:**
```
libCr_Core.so                2.2M
libmonitor_protocol.so       6.9M
libmonitor_protocol_pf.so    5.0M
CrAdapter/libCr_PTP_USB.so   640K
CrAdapter/libCr_PTP_IP.so    705K
CrAdapter/libusb-1.0.so      113K
CrAdapter/libssh2.so         5.3M
```

### **Paso 4: Compilar e Instalar la Librería**
Navega al directorio del proyecto:
```bash
cd /home/cetevi/Documents/GitHub/MADTEC-PROJECT-CODES/CAMARA/CPP/SonyILXLibrary
```

Compila e instala:
```bash
python -m pip install --force-reinstall --no-cache-dir .
```

 **Esto puede tomar 5-10 minutos**

**Salida esperada:**
```
Successfully built sonyilx-camera
Successfully installed sonyilx-camera-0.1.0
```

### **Paso 5: Verificar Instalación del Módulo Python**
```bash
python -c "import sys, sonyilx_camera; print('✓ Python:', sys.executable); print('✓ Módulo:', sonyilx_camera.__file__)"
```

**Salida esperada:**
```
✓ Python: /home/cetevi/miniconda3/bin/python
✓ Módulo: /home/cetevi/miniconda3/lib/python3.13/site-packages/sonyilx_camera.cpython-313-x86_64-linux-gnu.so
```

### **Paso 6: Crear Enlaces Simbólicos del Runtime Sony SDK**  **CRÍTICO**
El SDK Sony busca archivos de configuración en directorios específicos. Crea estos enlaces:

```bash
SITE_PACKAGES="$(python -c 'import pathlib, sonyilx_camera; print(pathlib.Path(sonyilx_camera.__file__).resolve().parent)')"
ENV_PREFIX="$(python -c 'import sys; print(sys.prefix)')"

ln -sfn "$SITE_PACKAGES/CrAdapter" "$ENV_PREFIX/bin/CrAdapter"
ln -sfn "$SITE_PACKAGES/libmonitor_protocol_pf.so" "$ENV_PREFIX/lib/libmonitor_protocol_pf.so"
ln -sfn "$SITE_PACKAGES/libmonitor_protocol.so" "$ENV_PREFIX/lib/libmonitor_protocol.so"
```

Verifica que se crearon correctamente:
```bash
ls -l "$ENV_PREFIX/bin/CrAdapter"
ls -l "$ENV_PREFIX/lib/libmonitor_protocol"*.so
```

**Salida esperada:**
```
lrwxrwxrwx 1 cetevi cetevi 62 Jul 17 12:26 /home/cetevi/miniconda3/bin/CrAdapter -> .../site-packages/CrAdapter
lrwxrwxrwx 1 cetevi cetevi 78 Jul 17 12:26 /home/cetevi/miniconda3/lib/libmonitor_protocol_pf.so -> ...
lrwxrwxrwx 1 cetevi cetevi 75 Jul 17 12:26 /home/cetevi/miniconda3/lib/libmonitor_protocol.so -> ...
```

### **Paso 7: Permisos USB para la Cámara (Opcional, pero Recomendado)**
Si conectarás una cámara Sony:

```bash
sudo tee /etc/udev/rules.d/99-sony-camera-remote.rules >/dev/null <<'EOF'
SUBSYSTEM=="usb", ATTR{idVendor}=="054c", MODE="0666", TAG+="uaccess"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger
```

Desconecta y reconecta la cámara después de esto.

---

##  Pruebas de Funcionalidad

### **Prueba 1: Enumeración de Cámaras**  VERIFICADA
```bash
python -c "import sonyilx_camera as ilx; print(ilx.debug_enumerate_cameras())"
```

**Salida esperada (sin cámara conectada):**
```python
{
  'initialized': True,
  'enum_error_code': 0,
  'enum_error_name': '',
  'count': 0,
  'cameras': []
}
```

**Si está bien con cámara conectada:**
```python
{
  'initialized': True,
  'enum_error_code': 0,
  'enum_error_name': '',
  'count': 1,
  'cameras': [
    {
      'model': 'ILX-LR1',
      'connection_type': 'USB',
      'adaptor_name': 'Cr_PTP_USB'
    }
  ]
}
```

### **Prueba 2: Script Python Básico**
Crea un archivo `test_camera.py`:

```python
import sonyilx_camera as ilx

# Crear instancia
camera = ilx.CameraLibrary()

# Inicializar
if not camera.initialize():
    raise RuntimeError(f"Error al inicializar: {camera.last_error()}")

print("✓ Librería inicializada correctamente")

# Conectar primera cámara disponible
if not camera.connect_first_camera():
    print(f"⚠ Sin cámaras conectadas: {camera.last_error()}")
else:
    print(f"✓ Cámara conectada: {camera.camera_name()}")
    camera.disconnect_camera()

# Limpiar
camera.shutdown()
print("✓ Librería cerrada correctamente")
```

Ejecuta:
```bash
python test_camera.py
```

**Salida esperada:**
```
✓ Librería inicializada correctamente
⚠ Sin cámaras conectadas: Couldn't connect
✓ Librería cerrada correctamente
```

### **Prueba 3: Ejecutar Tests Unitarios**
```bash
pip install pytest
python -m pytest
```

---

##  API Principal de Python

Una vez instalado, puedes usar la librería así:

```python
import sonyilx_camera as ilx

# Crear instancia de control
camera = ilx.CameraLibrary()

# Métodos principales disponibles:
# - initialize()
# - connect_camera() / connect_first_camera()
# - disconnect_camera()
# - take_shot()
# - focus_view()
# - set_focus_mode(mode)
# - set_still_capture_mode(mode)
# - zoom_in() / zoom_out()
# - refresh_live_view()
# - set_target_folder(path)
# - last_error()
# - is_connected()
# ... y más (ver README.md completo)
```

---

##  Solución de Problemas

### **Problema: "ModuleNotFoundError: No module named 'sonyilx_camera'"**
```bash
# Verifica que el entorno esté activado
conda activate sonyilx

# Reinstala
python -m pip install --force-reinstall --no-cache-dir .
```

### **Problema: "Could not find camera_remote using the following names: Cr_Core"**
**SOLUCIÓN:** No copiaste las librerías compiladas. Repite el **Paso 3** (copiar librerías del Sony SDK).

### **Problema: "enum_error_name: Adaptor_Create"**
Los enlaces simbólicos del SDK Sony no están creados. Ejecuta el **Paso 6** nuevamente:
```bash
SITE_PACKAGES="$(python -c 'import pathlib, sonyilx_camera; print(pathlib.Path(sonyilx_camera.__file__).resolve().parent)')"
ENV_PREFIX="$(python -c 'import sys; print(sys.prefix)')"

ln -sfn "$SITE_PACKAGES/CrAdapter" "$ENV_PREFIX/bin/CrAdapter"
ln -sfn "$SITE_PACKAGES/libmonitor_protocol_pf.so" "$ENV_PREFIX/lib/libmonitor_protocol_pf.so"
ln -sfn "$SITE_PACKAGES/libmonitor_protocol.so" "$ENV_PREFIX/lib/libmonitor_protocol.so"
```

### **Problema: Cámara no enumerada pero SDK cargó bien**
- Verificar que la cámara esté en modo "Remote Shooting" USB
- Aplicar permisos udev (**Paso 7**)
- Desconectar y reconectar la cámara

### **Problema: Errores de compilación**
```bash
# Limpia build anterior
cd /home/cetevi/Documents/GitHub/MADTEC-PROJECT-CODES/CAMARA/CPP/SonyILXLibrary
rm -rf build-python *.egg-info

# Asegúrate de haber copiado las librerías (Paso 3)
# Luego reinstala
python -m pip install --force-reinstall --no-cache-dir --verbose .
```

---

##  Usar la Librería en Proyectos Independientes

Una vez instalada, en **cualquier script Python**:

```bash
# Asegúrate de activar el entorno
conda activate sonyilx

# Ejecuta tu script
python mi_proyecto_camera.py
```

**Ejemplo de proyecto independiente:**

```
mi_proyecto/
├── requirements.txt
└── main.py
```

**requirements.txt:**
```
# La librería ya está instalada en el entorno conda
# No necesitas agregar dependencias aquí si usas conda
```

**main.py:**
```python
import sonyilx_camera as ilx
import json
from pathlib import Path

def capturar_imagen():
    camera = ilx.CameraLibrary()
    
    if not camera.initialize():
        raise RuntimeError(camera.last_error())
    
    if not camera.connect_first_camera():
        print("No hay cámaras disponibles")
        return
    
    camera.set_target_folder("/tmp/sonyilx-images")
    camera.take_shot()
    
    camera.disconnect_camera()
    camera.shutdown()
    
    print("Imagen capturada exitosamente")

if __name__ == "__main__":
    capturar_imagen()
```

---

##  Resumen Rápido (Pasos Finales Verificados)

| # | Paso | Comando | Estado |
|---|------|---------|--------|
| 1 | Crear entorno | `conda create -n sonyilx python=3.10` |
| 2 | Activar entorno | `conda activate sonyilx` | 
| 3 | Instalar herramientas | `conda install -c conda-forge cmake ninja pip pybind11 scikit-build-core` | 
| 4 | **Copiar librerías SDK** | `cp $CRSDK_PATH/RemoteCli/external/crsdk/*.so $TARGET_DIR/` |  **CRÍTICO** |
| 5 | Compilar e instalar | `cd SonyILXLibrary && pip install .` | 
| 6 | Crear enlaces simbólicos | Script de enlaces (ver Paso 6 arriba) | 
| 7 | Probar instalación | `python -c "import sonyilx_camera as ilx; print(ilx.debug_enumerate_cameras())"` | 

---

##  Estado Actual

 **¡Librería Lista para Usar!**

-  Módulo compilado e instalado
-  Enlaces simbólicos del SDK Sony configurados
-  Enumeración de cámaras funcional
-  API de Python accesible

Puedes empezar a usar `sonyilx_camera` en tus scripts Python en cualquier momento.

---

##  Recursos Útiles
- **Documentación Python API**: Ver sección "Python API" en README.md del proyecto
- **Calibración de Cámara**: Ver sección "Image Processing, Calculation, and Measurements"
- **Tests**: `python -m pytest --help` para más opciones
- **Ubicación del Proyecto**: `/home/cetevi/Documents/GitHub/MADTEC-PROJECT-CODES/CAMARA/CPP/SonyILXLibrary`
- **Ubicación del SDK**: `/home/cetevi/Documents/GitHub/MADTEC-PROJECT-CODES/PAQUETES SDK/`

