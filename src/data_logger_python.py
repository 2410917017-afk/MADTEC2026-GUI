# Código para la adquisición de datos preliminar en la validación de la instrumentación del proceso de soldadura por puntos.
# Incluye interfaz gráfica simple para el muestreo y graficación de datos, así como guardar las gráficas en una carpeta dedicada.
# Comandos para instalara librerías requeridas, contando ya con Python (usamos versión 3.14):

# pip install matplotlib, pip install python-snap7, pip install pyqt6

import gspread, time
from google.oauth2.service_account import Credentials

import sys, matplotlib.pyplot as plt, os, snap7
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from snap7.util import get_int, get_real, get_bool, set_int, set_bool, get_dword
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QLineEdit, QLabel, QGroupBox, QMessageBox, QTextEdit
)
from PyQt6.QtGui import  QFont
from PyQt6.QtCore import Qt
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
        cntrl_layout = QGridLayout()
        cntrl_layout.setContentsMargins(10, 20, 10, 20)


        # Alcances necesarios para leer/escribir en Google Sheets
        self.SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

        # Ruta al archivo de credenciales JSON
        self.SERVICE_ACCOUNT_FILE = "imposing-eye-463014-c6-dc68c49329ea.json"

        # ID de la hoja de cálculo (lo obtienes de la URL de Google Sheets)
        self.SPREADSHEET_ID = "1lXYWTcKbLMyeU1un209UrB6Grzs2deBy58QLIhDxg70"

        # Nombre de la pestaña dentro de la hoja
        self.WORKSHEET_NAME = "Hoja 1"

        self.WORKSHEET_NAME2 = "Hoja 2"

        ahora = datetime.now()

        self.connected = False # Declaración de variables utilizadas
        self.texto = 0
        self.index = 0
        self.nombre1 = ""
        self.nombre2 = ""
        self.tSoldadura = 0
        self.max = 0.0
        self.maxcurr = 0.0
        self.mat1 = 0
        self.mat2 = ""
        self.mat3 = ""
        self.force_array = [0, 1, 2, 4, 5, 4, 2, 1, 0]
        self.time_array = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.current_array = [0, 1, 2, 1, 0, 1, 2, 1, 0]
        self.fecha_formateada = ahora.strftime("%d-%m-%Y-%H-%M-%S")

        self.plc = snap7.client.Client() # Creación de objeto para comunicación con PLC Siemens S7-1200


        self.paramGroup = QGroupBox("Parametros")
        self.paramGroup.setStyleSheet("background-color: dimgrey; color: whitesmoke; border-radius: 10px")
        self.paramGroup.setFont(QFont("Arial", 14))

        self.controlGroup = QGroupBox("Control")
        self.controlGroup.setStyleSheet("background-color: #001b1b; color: whitesmoke; border-radius: 10px")
        self.controlGroup.setFont(QFont("Arial", 14))

        self.figure = Figure(figsize=(6, 6), dpi=100) # Creación de espacio para graficar datos adquiridos del PLC
        self.canvas = FigureCanvas(self.figure)

        self.figure2 = Figure(figsize=(6, 6), dpi=100)
        self.canvas2 = FigureCanvas(self.figure2)
        

        self.buttonstart = QPushButton("Leer datos") # Creación y configuración de elementos incluidos en la GUI
        self.buttonstart.setFont(QFont("Arial", 20))
        self.buttonstart.setFixedSize(160, 80)
        self.buttonstart.setStyleSheet("""
                                  QPushButton {
                                  background-color: darkslategrey; 
                                  color: silver; border: none; 
                                  border-radius: 34px; 
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
        


        self.buttonconnect = QPushButton("Conectar")
        self.buttonconnect.setFont(QFont("Arial", 20))
        self.buttonconnect.setFixedSize(150, 75)
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

        self.buttonset = QPushButton("Configurar")
        self.buttonset.setFont(QFont("Arial", 20))
        self.buttonset.setFixedSize(160, 75)
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

        self.buttonload = QPushButton("Guardar datos")
        self.buttonload.setFont(QFont("Arial", 20))
        self.buttonload.setFixedSize(200, 75)
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
        #self.buttonload.clicked.connect(self.generar_pdf)

        self.buttonimage = QPushButton("Guardar imagen")
        self.buttonimage.setFont(QFont("Arial", 20))
        self.buttonimage.setFixedSize(220, 75)
        self.buttonimage.setStyleSheet("""
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
        self.buttonimage.clicked.connect(self.load_image)

        
        self.label1 = QLabel("Grosor del material [mm]:")
        self.label1.setFont(QFont("Arial", 16))
        self.label1.setStyleSheet("color: whitesmoke")
        self.label1.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.label1.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.mat1Edit = QLineEdit() # Bloque de edición para definición de número de muestras a recopilar
        self.mat1Edit.setPlaceholderText("...")
        self.mat1Edit.setFont(QFont("Arial", 16))
        self.mat1Edit.setFixedSize(200, 60)
        self.mat1Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat1Edit.textChanged.connect(self.mat1update)

        self.label2 = QLabel("Tipo de material:")
        self.label2.setFont(QFont("Arial", 16))
        self.label2.setStyleSheet("color: whitesmoke")
        self.label2.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.label2.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.mat2Edit = QLineEdit() # Bloque de edición para definición de número de muestras a recopilar
        self.mat2Edit.setPlaceholderText("...")
        self.mat2Edit.setFont(QFont("Arial", 16))
        self.mat2Edit.setFixedSize(200, 60)
        self.mat2Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat2Edit.textChanged.connect(self.mat2update)

        self.label3 = QLabel("Diam. de soldadura [mm]:")
        self.label3.setFont(QFont("Arial", 16))
        self.label3.setStyleSheet("color: whitesmoke")
        self.label3.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.label3.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.mat3Edit = QLineEdit() # Bloque de edición para definición de número de muestras a recopilar
        self.mat3Edit.setPlaceholderText("...")
        self.mat3Edit.setFont(QFont("Arial", 16))
        self.mat3Edit.setFixedSize(200, 60)
        self.mat3Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat3Edit.textChanged.connect(self.mat3update)

        self.samplesEdit = QLineEdit() # Bloque de edición para definición de número de muestras a recopilar
        self.samplesEdit.setPlaceholderText("N. de muestras...")
        self.samplesEdit.setFont(QFont("Arial", 18))
        self.samplesEdit.setFixedSize(160, 75)
        self.samplesEdit.setStyleSheet("color: black; background-color: silver")
        self.samplesEdit.textChanged.connect(self.updatesamp)

        self.alerts = QTextEdit()
        self.alerts.setPlaceholderText("...")
        self.alerts.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.alerts.setStyleSheet("color: black; background-color: silver")
        self.alerts.setReadOnly(True)

        param_layout.addWidget(self.label1, 0, 0)
        param_layout.addWidget(self.mat1Edit, 0, 1)
        param_layout.addWidget(self.label2, 0, 2)
        param_layout.addWidget(self.mat2Edit, 0, 3)
        param_layout.addWidget(self.label3, 0, 4)
        param_layout.addWidget(self.mat3Edit, 0, 5)

        self.paramGroup.setLayout(param_layout)

        cntrl_layout.addWidget(self.buttonstart, 0, 0)
        cntrl_layout.addWidget(self.buttonconnect, 0, 1)
        cntrl_layout.addWidget(self.samplesEdit, 0, 2)
        cntrl_layout.addWidget(self.buttonset, 0, 3)
        cntrl_layout.addWidget(self.buttonload, 0, 4)
        cntrl_layout.addWidget(self.buttonimage, 0, 5)

        self.controlGroup.setLayout(cntrl_layout)


        main_layout.addWidget(self.paramGroup, 3, 0, 1, 3)
        main_layout.addWidget(self.controlGroup, 4, 0, 1, 3)
        main_layout.addWidget(self.canvas, 0,  0, 2, 1)
        main_layout.addWidget(self.canvas2, 0,  1, 2, 1)
        main_layout.addWidget(self.alerts, 0, 2, 2, 1) 


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
            self.alerts.setPlainText("Conectado a PLC.")
            self.buttonconnect.setStyleSheet("background-color: green")
        
        except Exception as e:
            self.buttonconnect.setStyleSheet("background-color: red")
            self.escribirAlerta("Error. Error al conectar: " + str(e))

    def escribirAlerta(self, texto):
        texto_actual = self.alerts.toPlainText()
        # Insertar nuevo texto antes del existente
        self.alerts.setPlainText(">" + texto + "\n" + texto_actual)

    def load_image(self):
        self.figure.savefig(self.nombre1)
        self.figure2.savefig(self.nombre2)
        self.escribirAlerta("Imágenes guardadas. ✓")


    def mat1update(self, text): # Funciones para comportamiento de botones y conexión a PLC
        
        if text != "":
            try:
                num = text
                self.mat1 = float(num)
            except Exception:
                self.escribirAlerta("Error. En este campo solo puede ingresar números.")

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
                self.escribirAlerta("Error. En este campo solo puede ingresar números.")
                self.mat3Edit.setText("")

    def updatesamp(self, text): # Funciones para comportamiento de botones y conexión a PLC
        if text != "":
            try:
                num = text
                self.texto = int(num)
            except Exception:
                self.escribirAlerta("Error. En este campo solo puede ingresar números enteros.")
                self.samplesEdit.setText("")


    def setSamples(self):
        if self.connected:
            try:
                num = self.texto
                self.write_int(db_number=12, byte_offset=0, value=num)
                self.escribirAlerta("Número de muestras configurado ✓")

            except Exception as e:
                self.escribirAlerta("Error. Error al enviar datos")
        else:
            self.escribirAlerta("Error. PLC no conectado.")

                

    def actualizar_nombre(self): # Función para actualizar nombre de gráfica a guardar
        self.index = int(self.index) 
        self.index = self.index + 1
        self.index = str(self.index)

        ahora = datetime.now()
        
        self.fecha_formateada = ahora.strftime("%d-%m-%Y-%H-%M-%S")

        self.identif = str(self.index) + "-" + self.fecha_formateada

        self.nombre1 = "Plots/grafica_" +  "F" + "_" + self.identif
        self.nombre2 = "Plots/grafica_" +  "I" + "_" + self.identif


    def log_to_google_sheets(self):
        if self.connected:
            try:

                presion = self.max / 6

                data_row = [self.identif,
                                 self.texto,
                                 presion, 
                                 self.tSoldadura, 
                                 "Orientación", 
                                 self.max, 
                                 self.maxcurr, 
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

                # Agregar las filas al final
                sheet.append_row(data_row)

                sheet2 = client.open_by_key(self.SPREADSHEET_ID).worksheet(self.WORKSHEET_NAME2)

                if len(self.time_array) > 50:
                    ciclos = (len(self.time_array) + 49) // 50  
                    
                    for i in range(ciclos):
                        start = i * 50
                        end = min(start + 50, len(self.time_array))  
                        
                        for j in range(start, end):
                            sheet2.append_row([self.identif, self.time_array[j], self.force_array[j], self.current_array[j]])
                        
                        if i < ciclos - 1: 
                            time.sleep(60)
                else:
                    for i in range(len(self.time_array)):
                        sheet2.append_row([self.identif, self.time_array[i], self.force_array[i], self.current_array[i]])

                self.escribirAlerta("Datos registrados correctamente ✓")
            

            except Exception as e:
                self.escribirAlerta("Error." + str(e))
        else:
            self.escribirAlerta("Error. PLC no conectado.")


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
        self.escribirAlerta("Reporte guardado ✓")

    def showplot(self):

        if  self.connected:
            try:
                self.max = 0
                self.maxcurr = 0
                num = self.texto

                self.figure.clear()
                self.figure2.clear()

                self.time_array = self.read_dword_array(db_number=13, start_byte=0, bytes=num)
                self.force_array = self.read_real_array(db_number=1, start_byte=0, bytes=num)
                self.current_array = self.read_real_array(db_number=15, start_byte=0, bytes=num)


                if len(self.time_array) and len(self.force_array) > 5 :
                    for i in range(len(self.force_array)):
                        
                        if self.force_array[i] > self.max:
                            self.max = self.force_array[i]

                    for i in range(len(self.current_array)):
                        
                        if self.current_array[i] > self.maxcurr:
                            self.maxcurr = self.current_array[i]
                    

                    self.tSoldadura = self.time_array[len(self.time_array) - 1]
                        

                ax = self.figure.add_subplot(111)
                ax.clear()  
                ax.plot(self.time_array, self.force_array, marker="o", color="blue")
                ax.set_title(
                f"Fuerza vs tiempo\n"
                f"Tiempo de soldadura: {self.tSoldadura} ms | "
                f"N. de muestras: {self.texto} | "
                f"F máxima: {self.max} N \n"
                f"Fecha: {self.fecha_formateada}"
                , fontweight='bold', fontsize=8
                )
                ax.set_xlabel("Tiempo")
                ax.set_ylabel("Fuerza")
                ax.legend()
                self.canvas.draw()  # Refresca el lienzo

                ax2 = self.figure2.add_subplot(111)
                ax2.clear() 
                ax2.plot(self.time_array, self.current_array, marker="o", color="blue")
                ax2.set_title(
                f"Corriente vs tiempo\n"
                f"Tiempo de soldadura: {self.tSoldadura} ms | "
                f"N. de muestras: {self.texto} | "
                f"I máxima: {self.maxcurr} A \n"
                f"Fecha: {self.fecha_formateada}"
                , fontweight='bold', fontsize=8
                )
                ax2.set_xlabel("Tiempo")
                ax2.set_ylabel("Corriente")
                ax2.legend()
                self.canvas2.draw()  # Refresca el lienzo

                self.escribirAlerta("Datos obtenidos correctamente ✓")
                self.escribirAlerta(f"Número de identificación: {self.identif}")
                

                #print("Datos de fuerza:", self.force_array)
                #print("Datos de tiempo:", self.time_array)
                #print("Datos de corriente:", self.current_array)


            except Exception as e:
                self.escribirAlerta("Error. Error al solicitar datos: " + str(e))

        else:
            self.escribirAlerta("Error. PLC no conectado.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HMI()
    window.show()
    sys.exit(app.exec())