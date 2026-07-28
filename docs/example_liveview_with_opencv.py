#!/usr/bin/env python3
"""
🎥 Ejemplo: SonyILX Live View + OpenCV en Tiempo Real
Captura vista en vivo de la cámara Sony y la analiza con OpenCV
Presiona 'q' en la ventana de video para salir
"""

import sonyilx_camera as ilx
import cv2
import numpy as np
import os
from pathlib import Path
import time

class SonyLiveViewWithOpenCV:
    def __init__(self, output_folder="/tmp/sonyilx-liveview-opencv"):
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)
        self.camera = ilx.CameraLibrary()
        self.frame_count = 0
        self.analysis_results = {
            'motion': [],
            'brightness': [],
            'contrast': []
        }
    
    def initialize(self):
        """Inicializar y conectar cámara"""
        print("🔧 Inicializando cámara...")
        
        if not self.camera.initialize():
            raise RuntimeError(f"Error inicializando: {self.camera.last_error()}")
        
        if not self.camera.connect_first_camera():
            raise RuntimeError(f"Error conectando: {self.camera.last_error()}")
        
        print(f"✅ Cámara conectada: {self.camera.camera_name()}")
        self.camera.set_target_folder(str(self.output_folder))
        print(f"📁 Carpeta de salida: {self.output_folder}")
    
    def get_liveview_frame(self):
        """Obtener frame de vista en vivo"""
        try:
            live_view_path = self.camera.refresh_live_view()
            if not live_view_path or not os.path.exists(live_view_path):
                return None
            
            frame = cv2.imread(live_view_path)
            return frame
        except Exception as e:
            print(f"⚠️  Error obteniendo frame: {e}")
            return None
    
    # === ANÁLISIS 1: Detección de Movimiento ===
    def detect_motion(self, frame, prev_frame):
        """Detecta movimiento entre dos frames"""
        if prev_frame is None:
            return None, 0
        
        gray1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        diff = cv2.absdiff(gray1, gray2)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        
        motion_pixels = cv2.countNonZero(thresh)
        total_pixels = thresh.shape[0] * thresh.shape[1]
        motion_percentage = (motion_pixels / total_pixels) * 100
        
        return thresh, motion_percentage
    
    # === ANÁLISIS 2: Detección de Aristas ===
    def detect_edges(self, frame):
        """Detecta bordes (Canny Edge Detection)"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
        edges = cv2.Canny(blurred, 100, 200)
        return edges
    
    # === ANÁLISIS 3: Detección de Esquinas ===
    def detect_corners(self, frame):
        """Detecta esquinas (Harris Corner Detection)"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detectar esquinas
        corners = cv2.cornerHarris(gray, blockSize=2, ksize=3, k=0.04)
        corners = cv2.dilate(corners, None)
        
        # Crear imagen con círculos en esquinas
        result = frame.copy()
        threshold = 0.01 * corners.max()
        for i in range(corners.shape[0]):
            for j in range(corners.shape[1]):
                if corners[i, j] > threshold:
                    cv2.circle(result, (j, i), 5, (0, 255, 0), -1)
        
        num_corners = np.sum(corners > threshold)
        return result, num_corners
    
    # === ANÁLISIS 4: Estadísticas de Brillo y Contraste ===
    def analyze_brightness_contrast(self, frame):
        """Analiza brillo y contraste de la imagen"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        return brightness, contrast
    
    # === ANÁLISIS 5: Histograma ===
    def analyze_color_histogram(self, frame):
        """Analiza histograma de color"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Calcular histogramas
        hist_hue = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        
        # Normalizar
        hist_hue = cv2.normalize(hist_hue, hist_hue).flatten()
        
        # Encontrar color dominante (hue)
        dominant_hue = np.argmax(hist_hue) * 2
        
        return dominant_hue
    
    def run_liveview_analysis(self, duration_seconds=30, show_analysis=True):
        """Ejecutar análisis de vista en vivo"""
        print(f"\n🎬 Capturando vista en vivo por {duration_seconds} segundos...")
        print("   Presiona 'q' en la ventana de video para salir antes")
        print("   Análisis en tiempo real:")
        print("     • Detección de movimiento")
        print("     • Detección de aristas")
        print("     • Detección de esquinas")
        print("     • Análisis de brillo y contraste")
        print()
        
        start_time = time.time()
        prev_frame = None
        
        while time.time() - start_time < duration_seconds:
            # Obtener frame
            frame = self.get_liveview_frame()
            if frame is None:
                continue
            
            height, width = frame.shape[:2]
            
            # === Análisis ===
            
            # 1. Movimiento
            motion_mask, motion_pct = self.detect_motion(frame, prev_frame)
            
            # 2. Aristas
            edges = self.detect_edges(frame)
            
            # 3. Esquinas
            corners_img, num_corners = self.detect_corners(frame)
            
            # 4. Brillo y contraste
            brightness, contrast = self.analyze_brightness_contrast(frame)
            
            # 5. Color dominante
            dominant_hue = self.analyze_color_histogram(frame)
            
            # Guardar en resultados
            self.analysis_results['motion'].append(motion_pct if motion_pct else 0)
            self.analysis_results['brightness'].append(brightness)
            self.analysis_results['contrast'].append(contrast)
            
            # === Visualización ===
            
            # Frame original con texto
            result_frame = frame.copy()
            
            # Texto de análisis
            cv2.putText(result_frame, f"Motion: {motion_pct:.2f}%" if motion_pct else "Motion: N/A",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(result_frame, f"Corners: {num_corners}",
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(result_frame, f"Brightness: {brightness:.1f}",
                       (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(result_frame, f"Contrast: {contrast:.1f}",
                       (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(result_frame, f"Hue: {dominant_hue}°",
                       (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(result_frame, f"Frame: {self.frame_count}",
                       (width - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            if show_analysis:
                # Mostrar ventanas
                cv2.imshow("📷 Sony Live View (Original)", result_frame)
                cv2.imshow("🔍 Edges (Aristas)", edges)
                cv2.imshow("📍 Corners (Esquinas)", corners_img)
                
                # Mostrar máscara de movimiento
                if motion_mask is not None:
                    motion_display = cv2.cvtColor(motion_mask, cv2.COLOR_GRAY2BGR)
                    cv2.imshow("➡️  Motion (Movimiento)", motion_display)
            
            # Guardar frames importantes cada 10 frames
            if self.frame_count % 10 == 0:
                output_file = self.output_folder / f"frame_{self.frame_count:04d}.jpg"
                cv2.imwrite(str(output_file), result_frame)
            
            prev_frame = frame.copy()
            self.frame_count += 1
            
            # Tecla 'q' para salir
            if cv2.waitKey(100) & 0xFF == ord('q'):
                print("\n⏹️  Parado por el usuario")
                break
        
        cv2.destroyAllWindows()
        print(f"✅ Captura completada: {self.frame_count} frames analizados")
    
    def print_analysis_summary(self):
        """Imprimir resumen de análisis"""
        if not self.analysis_results['motion']:
            print("⚠️  No hay datos de análisis disponibles")
            return
        
        print("\n" + "="*60)
        print("📊 RESUMEN DEL ANÁLISIS")
        print("="*60)
        
        # Movimiento
        motion_data = [x for x in self.analysis_results['motion'] if x is not None]
        if motion_data:
            print(f"\n🔄 Movimiento:")
            print(f"   Promedio: {np.mean(motion_data):.2f}%")
            print(f"   Máximo: {np.max(motion_data):.2f}%")
            print(f"   Mínimo: {np.min(motion_data):.2f}%")
        
        # Brillo
        brightness_data = self.analysis_results['brightness']
        print(f"\n💡 Brillo:")
        print(f"   Promedio: {np.mean(brightness_data):.1f}")
        print(f"   Máximo: {np.max(brightness_data):.1f}")
        print(f"   Mínimo: {np.min(brightness_data):.1f}")
        
        # Contraste
        contrast_data = self.analysis_results['contrast']
        print(f"\n⚡ Contraste:")
        print(f"   Promedio: {np.mean(contrast_data):.1f}")
        print(f"   Máximo: {np.max(contrast_data):.1f}")
        print(f"   Mínimo: {np.min(contrast_data):.1f}")
        
        print("\n" + "="*60)
    
    def shutdown(self):
        """Limpiar y desconectar"""
        print("\n🛑 Desconectando cámara...")
        self.camera.disconnect_camera()
        self.camera.shutdown()
        print("✅ Cámara desconectada")

# ============================================================
# PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    analyzer = SonyLiveViewWithOpenCV()
    
    try:
        print("\n" + "="*60)
        print("🎥 SonyILX + OpenCV: Análisis de Vista en Vivo")
        print("="*60)
        
        # Inicializar
        analyzer.initialize()
        
        # Ejecutar análisis por 30 segundos
        analyzer.run_liveview_analysis(duration_seconds=30, show_analysis=True)
        
        # Mostrar resumen
        analyzer.print_analysis_summary()
        
        print(f"\n📁 Imágenes guardadas en: {analyzer.output_folder}")
        
    except RuntimeError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Sugerencias:")
        print("   • Verifica que la cámara Sony esté conectada por USB")
        print("   • Asegúrate de que el entorno conda esté activado")
        print("   • Comprueba que la cámara esté en modo 'Remote Shooting'")
    
    except KeyboardInterrupt:
        print("\n⏹️  Interrumpido por el usuario")
    
    finally:
        analyzer.shutdown()
