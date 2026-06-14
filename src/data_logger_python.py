# Código para la adquisición de datos preliminar en la validación de la instrumentación del proceso de soldadura por puntos.
# Incluye interfaz gráfica simple para el muestreo y graficación de datos, así como guardar las gráficas en una carpeta dedicada.
# Comandos para instalara librerías requeridas, contando ya con Python (usamos versión 3.14):

# pip install matplotlib, pip install python-snap7, pip install pyqt6

import gspread
from google.oauth2.service_account import Credentials

import sys, matplotlib.pyplot as plt, os, snap7
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from snap7.util import get_int, get_real, get_bool, set_int, set_bool, get_dword
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QLineEdit, QLabel, QGroupBox, QMessageBox
)
from PyQt6.QtGui import  QFont
from datetime import datetime
from openpyxl import load_workbook, Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Inicialización de interfaz gráfica
class HMI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PLC Plotter") # Configuración de la ventana de la GUI
        #self.setFixedSize(1300, 600)
        self.setStyleSheet("background-color: #001b1b")

        main_layout = QGridLayout(self) # Distribución de rejilla, renglones y columnas
        main_layout.setContentsMargins(10, 10, 10, 10)
        param_layout = QGridLayout()
        param_layout.setContentsMargins(10, 20, 10, 20)

        ahora = datetime.now()
        
        self.fecha_formateada = ahora.strftime("%d-%m-%Y")
        self.fecha_formateada = str(self.fecha_formateada)

        # Alcances necesarios para leer/escribir en Google Sheets
        self.SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

        # Ruta al archivo de credenciales JSON
        self.SERVICE_ACCOUNT_FILE = "imposing-eye-463014-c6-dc68c49329ea.json"

        # ID de la hoja de cálculo (lo obtienes de la URL de Google Sheets)
        self.SPREADSHEET_ID = "1lXYWTcKbLMyeU1un209UrB6Grzs2deBy58QLIhDxg70"

        # Nombre de la pestaña dentro de la hoja
        self.WORKSHEET_NAME = "Hoja 1"

        self.connected = False # Declaración de variables utilizadas
        self.texto = 0
        self.index = 0
        self.nombre = ""
        self.tSoldadura = 0
        self.max = 0.0
        self.mat1 = 0
        self.mat2 = ""
        self.mat3 = ""
        self.data_row = []

        self.plc = snap7.client.Client() # Creación de objeto para comunicación con PLC Siemens S7-1200


        self.paramGroup = QGroupBox("Parameters")
        self.paramGroup.setFixedWidth(300)
        self.paramGroup.setStyleSheet("background-color: dimgrey; color: whitesmoke; border-radius: 10px")
        self.paramGroup.setFont(QFont("Arial", 16))

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
                                  background-color: dimgrey; 
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

        self.buttonload = QPushButton("Load data")
        self.buttonload.setFont(QFont("Arial", 28))
        self.buttonload.setFixedSize(180, 80)
        self.buttonload.setStyleSheet("""
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
        self.buttonload.clicked.connect(self.log_to_google_sheets)
        self.buttonload.clicked.connect(self.generar_pdf)
        
        self.label1 = QLabel("Material thickness [mm]")
        self.label1.setFont(QFont("Arial", 18))
        self.label1.setStyleSheet("color: whitesmoke")

        self.mat1Edit = QLineEdit() # Bloque de edición para definición de número de muestras a recopilar
        self.mat1Edit.setPlaceholderText("...")
        self.mat1Edit.setFont(QFont("Arial", 16))
        self.mat1Edit.setFixedSize(200, 60)
        self.mat1Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat1Edit.textChanged.connect(self.mat1update)

        self.label2 = QLabel("Material type")
        self.label2.setFont(QFont("Arial", 18))
        self.label2.setStyleSheet("color: whitesmoke")

        self.mat2Edit = QLineEdit() # Bloque de edición para definición de número de muestras a recopilar
        self.mat2Edit.setPlaceholderText("...")
        self.mat2Edit.setFont(QFont("Arial", 16))
        self.mat2Edit.setFixedSize(200, 60)
        self.mat2Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat2Edit.textChanged.connect(self.mat2update)

        self.label3 = QLabel("Nugget diameter [mm]")
        self.label3.setFont(QFont("Arial", 18))
        self.label3.setStyleSheet("color: whitesmoke")

        self.mat3Edit = QLineEdit() # Bloque de edición para definición de número de muestras a recopilar
        self.mat3Edit.setPlaceholderText("...")
        self.mat3Edit.setFont(QFont("Arial", 16))
        self.mat3Edit.setFixedSize(200, 60)
        self.mat3Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat3Edit.textChanged.connect(self.mat3update)

        self.samplesEdit = QLineEdit() # Bloque de edición para definición de número de muestras a recopilar
        self.samplesEdit.setPlaceholderText("N. of samples...")
        self.samplesEdit.setFont(QFont("Arial", 18))
        self.samplesEdit.setFixedSize(200, 70)
        self.samplesEdit.setStyleSheet("color: ghostwhite")
        self.samplesEdit.textChanged.connect(self.updatesamp)

        param_layout.addWidget(self.label1)
        param_layout.addWidget(self.mat1Edit)
        param_layout.addWidget(self.label2)
        param_layout.addWidget(self.mat2Edit)
        param_layout.addWidget(self.label3)
        param_layout.addWidget(self.mat3Edit)

        self.paramGroup.setLayout(param_layout)
    
        main_layout.addWidget(self.buttonstart, 1, 0) # Agregado de widgets y elementos a distribución principal de la ventana
        main_layout.addWidget(self.buttonconnect, 1, 1)
        main_layout.addWidget(self.samplesEdit, 1, 2)
        main_layout.addWidget(self.canvas, 0,  0, 1, 2)
        main_layout.addWidget(self.canvas2, 0,  2, 1, 2) 
        main_layout.addWidget(self.buttonset, 1, 3)
        main_layout.addWidget(self.paramGroup, 0, 5)
        main_layout.addWidget(self.buttonload, 1, 5)


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

            if not self.plc.get_connected():
                self.buttonconnect.setStyleSheet("""
                                    QPushButton {
                                    background-color: red""")
                raise ConnectionError("No se pudo conectar al PLC.")
            
            self.connected = True
            self.buttonconnect.setStyleSheet("""
                        QPushButton {
                        background-color: lime""")
        
        except Exception as e:
            QMessageBox.about(self, 'Error','Error al conectar: {e}')


    def mat1update(self, text): # Funciones para comportamiento de botones y conexión a PLC
        
        if text != "":
            try:
                num = text
                self.mat1 = float(num)
            except Exception:
                QMessageBox.about(self, 'Error','Input can only be a number')
                self.mat1Edit.setText("")

    def mat2update(self, text): # Funciones para comportamiento de botones y conexión a PLC
        
        if text != "":

            self.mat2 = text

    def mat3update(self, text): # Funciones para comportamiento de botones y conexión a PLC
        
        if text != "":
            try:
                num = text
                self.mat3 = float(num)
            except Exception:
                QMessageBox.about(self, 'Error','Input can only be a number')
                self.mat3Edit.setText("")

    def updatesamp(self, text): # Funciones para comportamiento de botones y conexión a PLC
        if text != "":
            try:
                num = text
                self.texto = int(num)
            except Exception:
                QMessageBox.about(self, 'Error','Input can only be an int number')
                self.samplesEdit.setText("")


    def setSamples(self):
        if self.connected:
            try:
                num = self.texto
                self.write_int(db_number=12, byte_offset=0, value=num)

            except Exception as e:
                QMessageBox.about(self, 'Error','Error al enviar datos: {e}')

                

    def actualizar_nombre(self): # Función para actualizar nombre de gráfica a guardar
        self.index = int(self.index) 
        self.index = self.index + 1
        self.index = str(self.index)


        self.nombre = "Plots/grafica_" + self.index + "_" + self.fecha_formateada


    def log_to_google_sheets(self):
        if not self.connected:
            try:

                presion = self.max / 6
                self.data_row = [self.fecha_formateada, 
                                 self.index, 
                                 presion, 
                                 self.tSoldadura, 
                                 "Orientación", 
                                 self.max, 
                                 "Corriente", 
                                 self.mat1, 
                                 self.mat2, 
                                 self.mat3]

                # Autenticación con credenciales de servicio
                creds = Credentials.from_service_account_file(
                    self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES
                )
                client = gspread.authorize(creds)

                # Abrir la hoja y seleccionar la pestaña
                sheet = client.open_by_key(self.SPREADSHEET_ID).worksheet(self.WORKSHEET_NAME)

                # Agregar la fila al final
                sheet.append_row(self.data_row)
                QMessageBox.about(self, 'Completed','Datos registrados correctamente.')


            except Exception as e:
                QMessageBox.about(self, 'Error','Error al registrar datos: {e}')


    def generar_pdf(self):
        grafico_file = self.figure

        c = canvas.Canvas("reporte.pdf", pagesize=A4)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 800, "Reporte Automático")
        c.setFont("Helvetica", 12)
        c.drawString(50, 780, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Insertar gráfico
        #c.drawImage(grafico_file, 50, 500, width=500, height=250)

        c.showPage()
        c.save()

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
                QMessageBox.about(self, 'Error','Error al solicitar datos: {e}')



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HMI()
    window.show()
    sys.exit(app.exec())
