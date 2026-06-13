# Código para la adquisición de datos preliminar en la validación de la instrumentación del proceso de soldadura por puntos.
# Incluye interfaz gráfica simple para el muestreo y graficación de datos, así como guardar las gráficas en una carpeta dedicada.
# Comandos para instalara librerías requeridas, contando ya con Python (usamos versión 3.14):

# pip install matplotlib, pip install python-snap7, pip install pyqt6

import sys, matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import snap7
from snap7.util import get_int, get_real, get_bool, set_int, set_bool, get_dword
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QLineEdit
)
from PyQt6.QtGui import  QFont
from datetime import datetime

# Inicialización de interfaz gráfica
class HMI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PLC Plotter") # Configuración de la ventana de la GUI
        self.setFixedSize(1300, 600)
        self.setStyleSheet("background-color: #001b1b")

        main_layout = QGridLayout(self) # Distribución de rejilla, renglones y columnas

        self.connected = False # Declaración de variables utilizadas
        self.texto = 0
        self.index = 0
        self.nombre = ""
        self.tSoldadura = 0
        self.max = 0
        self.presion = 0

        self.plc = snap7.client.Client() # Creación de objeto para comunicación con PLC Siemens S7-1200

        self.figure = Figure(figsize=(6, 6), dpi=100) # Creación de espacio para graficar datos adquiridos del PLC
        self.canvas = FigureCanvas(self.figure)

        self.figure2 = Figure(figsize=(6, 6), dpi=100)
        self.canvas2 = FigureCanvas(self.figure2)
        

        self.buttonstart = QPushButton("Start") # Creación y configuración de elementos incluidos en la GUI
        self.buttonstart.setFont(QFont("Arial", 28))
        self.buttonstart.setFixedSize(115, 115)
        self.buttonstart.setStyleSheet("""
                                  QPushButton {
                                  background-color: darkslategrey; 
                                  color: silver; border: none; 
                                  border-radius: 48px; 
                                  padding: 10px 10px
                                  }
                                  QPushButton:hover {
                                  background-color: darkgrey;
                                  }
                                  QPushButton:pressed {
                                  padding: 11px 9px 9px 11px;
                                  }
                                  """)
        self.buttonstart.clicked.connect(self.actualizar_nombre) # Llamada a funciones que ejecutan el comportamiento de botones
        self.buttonstart.clicked.connect(self.showplot)
        


        self.buttonconnect = QPushButton("Connect")
        self.buttonconnect.setFont(QFont("Arial", 28))
        self.buttonconnect.setFixedSize(200, 80)
        self.buttonconnect.setStyleSheet("""
                                  QPushButton {
                                  background-color: darkslategrey; 
                                  color: silver; border: none; 
                                  border-radius: 20px; 
                                  padding: 10px 10px
                                  }
                                  QPushButton:hover {
                                  background-color: darkgrey;
                                  }
                                  QPushButton:pressed {
                                  padding: 11px 9px 9px 11px;
                                  }
                                  """)
        self.buttonconnect.clicked.connect(self.connectPLC)

        self.buttonset = QPushButton("Set")
        self.buttonset.setFont(QFont("Arial", 28))
        self.buttonset.setFixedSize(180, 80)
        self.buttonset.setStyleSheet("""
                                  QPushButton {
                                  background-color: darkslategrey; 
                                  color: silver; border: none; 
                                  border-radius: 20px; 
                                  padding: 10px 10px
                                  }
                                  QPushButton:hover {
                                  background-color: darkgrey;
                                  }
                                  QPushButton:pressed {
                                  padding: 11px 9px 9px 11px;
                                  }
                                  """)
        self.buttonset.clicked.connect(self.setSamples)
        
        self.samplesEdit = QLineEdit() # Bloque de edición para definición de número de muestras a recopilar
        self.samplesEdit.setPlaceholderText("N. of samples...")
        self.samplesEdit.setFont(QFont("Arial", 18))
        self.samplesEdit.setFixedSize(200, 70)
        self.samplesEdit.setStyleSheet("color: ghostwhite")
        self.samplesEdit.textChanged.connect(self.updatesamp)

    
        main_layout.addWidget(self.buttonstart, 1, 0) # Agregado de widgets y elementos a distribución principal de la ventana
        main_layout.addWidget(self.buttonconnect, 1, 1)
        main_layout.addWidget(self.samplesEdit, 1, 2)
        main_layout.addWidget(self.canvas, 0,  0, 1, 2)
        main_layout.addWidget(self.canvas2, 0,  2, 1, 2) 
        main_layout.addWidget(self.buttonset, 1, 3)


    def write_int(self, db_number, byte_offset, value: int): # Funciones para comunicación GUI <-> PLC
        data = bytearray(2)
        set_int(data, 0, value)
        self.plc.db_write(db_number, byte_offset, data)


    def read_int_array(self, db_number, start_byte, bytes):
        total_size = bytes * 2

        data = self.plc.db_read(db_number, start_byte, size=total_size)

        values = []
        for i in range(bytes):
            offset = i * 2
            values.append(get_int(data, offset))
   
        return values
    
    def read_dword_array(self, db_number, start_byte, bytes):
        total_size = bytes * 4

        data = self.plc.db_read(db_number, start_byte, size=total_size)

        values = []
        for i in range(bytes):
            offset = i * 4
            values.append(get_dword(data, offset))
   
        return values
    
    def read_real_array(self, db_number, start_byte, bytes):
        total_size = bytes * 4

        data = self.plc.db_read(db_number, start_byte, size=total_size)

        values = []
        for i in range(bytes):
            offset = i * 4
            values.append(get_real(data, offset))
   
        return values


    def read_bool(self, db_number, byte_offset, bit):

        data = self.plc.db_read(db_number, byte_offset, 1)
        data = get_bool(data, 0, bit)
        return data


    def write_bool(self, db, byte_offset, bit, value: bool):
        data = self.plc.db_read(db, byte_offset, 1)
        set_bool(data, 0, bit, value)
        self.plc.db_write(db, byte_offset, data)


    def connectPLC(self): # Función para establecer conexión
        try:
            
            self.plc.disconnect()
            self.plc.connect("192.168.0.1", rack=0, slot=1)

            self.connected = True

            if not self.plc.get_connected():
                raise ConnectionError("No se pudo conectar al PLC.")
        
        except Exception as e:
            print(f"Error: {e}")


    def updatesamp(self, text): # Funciones para comportamiento de botones y conexión a PLC
        
        if text != "":
            num = text
            self.texto = int(num)


    def setSamples(self):
        try:
            num = self.texto
            self.write_int(db_number=12, byte_offset=0, value=num)

        except Exception as e:
            print(f"Error: {e}")
            

    def actualizar_nombre(self): # Función para actualizar nombre de gráfica a guardar
        self.index = int(self.index) 
        self.index = self.index + 1
        self.index = str(self.index)
        ahora = datetime.now()
        
        fecha_formateada = ahora.strftime("%d-%m-%Y")
        fecha_formateada = str(fecha_formateada)

        self.nombre = "Plots/grafica_" + self.index + "_" + fecha_formateada


    def showplot(self):

        if self.connected:
            try:
                num = self.texto
                self.max = 0

                ahora = datetime.now()
                
                # Formatear solo la fecha
                fecha_formateada = ahora.strftime("%d-%m-%Y")

                time_array = self.read_dword_array(db_number=13, start_byte=0, bytes=num)
                force_array = self.read_real_array(db_number=1, start_byte=0, bytes=num)
                #current_array = self.read_rel_array(db_number=4, start_byte=0, bytes=num)

                x = time_array
                y = force_array
                #y2 = current_array

                if len(x) and len(y) > 5 :
                    for i in range(len(y)):
                        
                        if y[i] > self.max:
                            self.max = y[i]
                    
                    self.max = str(self.max)

                    self.tSoldadura = x[len(x) - 1]
                        

                ax = self.figure.add_subplot(111)
                ax.clear()  # Limpia la gráfica anterior
                ax.plot(x, y, marker="o", color="blue")
                ax.set_title(
                f"Fuerza vs tiempo\n"
                f"Tiempo de soldadura: {self.tSoldadura} | "
                f"Fuerza máxima: {self.max} 1\n"
                f"Fecha: {fecha_formateada}"
                , fontweight='bold', fontsize=8
                )
                
                ax.set_xlabel("Tiempo")
                ax.set_ylabel("Fuerza")
                ax.legend()
                self.canvas.draw()  # Refresca el lienzo

                #ax2 = self.figure2.add_subplot(111)
                #ax2.clear()  # Limpia la gráfica anterior
                #ax2.plot(x, y2, marker="o", color="blue")
                #ax2.set_title("Corriente vs tiempo")
                #ax2.set_xlabel("Tiempo")
                #ax2.set_ylabel("Corriente")
                #ax2.legend()
                #self.canvas2.draw()  # Refresca el lienzo
                self.figure.savefig(self.nombre)
                


                print("Datos de fuerza:", y)
                print("Datos de tiempo:", x)


            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HMI()
    window.show()
    sys.exit(app.exec())

