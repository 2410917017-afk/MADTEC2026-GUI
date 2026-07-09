# Código para la adquisición de datos preliminar en la validación de la instrumentación del proceso de soldadura por puntos.
# Incluye interfaz gráfica simple para el muestreo y graficación de datos, así como guardar las gráficas en una carpeta dedicada.
# Comandos para instalar librerías requeridas, contando ya con Python (usamos versión 3.10.0):

# pip install matplotlib python-snap7 PyQt5 psycopg2-binary request

import sys, snap7, matplotlib, requests
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from snap7.util import get_int, get_real, get_bool, set_int, set_bool, get_dword
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QLineEdit, QLabel, QGroupBox, QTextEdit, QComboBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from datetime import datetime


# Inicialización de interfaz gráfica
class HMI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PLC Plotter")  # Configuración de la ventana de la GUI
        # self.setFixedSize(1300, 600)
        self.setStyleSheet("background-color: #001b1b")


        main_layout = QGridLayout(self)  # Distribución de rejilla, renglones y columnas
        main_layout.setContentsMargins(10, 10, 10, 10)
        param_layout = QGridLayout()
        param_layout.setContentsMargins(10, 20, 10, 20)
        cntrl_layout = QGridLayout()
        cntrl_layout.setContentsMargins(10, 20, 10, 20)

        self.base_url = "http://192.168.2.199:8000"
        self.datos = {
              "Id" : "",
              "Caso" : "",
              "Muestras" : 0,
              "Tiempo" : 0,
              "Orientacion": "",
              "FMax" : 0,
              "IMax" : 0,
              "Grosor" : 0,
              "Material" : "",
              "Diametro" : 0
            }

        self.datos_2 = {
            "Id" : "",
            "Caso" : "",
            "Tiempo" : 0,
            "Fuerza" : 0,
            "Corriente" : 0
        }

        ahora = datetime.now()

        self.identif = ""
        self.cases = {"" : ""}

        self.connected = False  # Declaración de variables utilizadas
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

        self.plc = snap7.client.Client()  # Creación de objeto para comunicación con PLC Siemens S7-1200

        self.paramGroup = QGroupBox("Parametros")
        self.paramGroup.setStyleSheet("background-color: dimgrey; color: whitesmoke; border-radius: 10px")
        self.paramGroup.setFont(QFont("Arial", 14))

        self.controlGroup = QGroupBox("Control")
        self.controlGroup.setStyleSheet("background-color: #001b1b; color: whitesmoke; border-radius: 10px")
        self.controlGroup.setFont(QFont("Arial", 14))

        self.figure = Figure(figsize=(6, 4), dpi=100)  # Creación de espacio para graficar datos adquiridos del PLC
        self.canvas = FigureCanvas(self.figure)

        self.figure2 = Figure(figsize=(6, 4), dpi=100)
        self.canvas2 = FigureCanvas(self.figure2)

        self.buttonstart = QPushButton("Iniciar")  # Creación y configuración de elementos incluidos en la GUI
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
        self.buttonstart.clicked.connect(self.actualizar_nombre)  # Llamada a funciones que ejecutan el comportamiento de botones

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

        self.buttonset = QPushButton("Enviar")
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
        self.buttonset.clicked.connect(self.setParams)

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
        self.buttonload.clicked.connect(self.crear_prueba)

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


        self.labelParams1 = QLabel("Parametros ideales")
        self.labelParams1.setFont(QFont("Arial", 16))
        self.labelParams1.setStyleSheet("color: whitesmoke")
        fuente = self.labelParams1.font()
        fuente.setUnderline(True)
        self.labelParams1.setFont(fuente)
        self.labelParams1.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.label1 = QLabel("Tiempo:")
        self.label1.setFont(QFont("Arial", 14))
        self.label1.setStyleSheet("color: whitesmoke")

        self.mat1Edit = QLabel("200ms-300ms")
        self.mat1Edit.setFont(QFont("Arial", 14))
        self.mat1Edit.setFixedSize(150, 60)
        self.mat1Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat1Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label2 = QLabel("Fuerza:")
        self.label2.setFont(QFont("Arial", 14))
        self.label2.setStyleSheet("color: whitesmoke")

        self.mat2Edit = QLabel("2.0 kN–4.5 kN")
        self.mat2Edit.setFont(QFont("Arial", 14))
        self.mat2Edit.setFixedSize(150, 60)
        self.mat2Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat2Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label3 = QLabel("Tiempo de compresión:")
        self.label3.setFont(QFont("Arial", 14))
        self.label3.setStyleSheet("color: whitesmoke")

        self.mat3Edit = QLabel("150 ms–300 ms")
        self.mat3Edit.setFont(QFont("Arial", 14))
        self.mat3Edit.setFixedSize(150, 60)
        self.mat3Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat3Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label4 = QLabel("Pulsos:")
        self.label4.setFont(QFont("Arial", 14))
        self.label4.setStyleSheet("color: whitesmoke")

        self.mat4Edit = QLabel("1")
        self.mat4Edit.setFont(QFont("Arial", 14))
        self.mat4Edit.setFixedSize(150, 60)
        self.mat4Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat4Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label5 = QLabel("Material:")
        self.label5.setFont(QFont("Arial", 14))
        self.label5.setStyleSheet("color: whitesmoke")

        self.mat5Edit = QLabel("Acero")
        self.mat5Edit.setFont(QFont("Arial", 14))
        self.mat5Edit.setFixedSize(150, 60)
        self.mat5Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat5Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label6 = QLabel("Grosor:")
        self.label6.setFont(QFont("Arial", 14))
        self.label6.setStyleSheet("color: whitesmoke")

        self.mat6Edit = QLabel("0.4mm-0.8mm")
        self.mat6Edit.setFont(QFont("Arial", 14))
        self.mat6Edit.setFixedSize(150, 60)
        self.mat6Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat6Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label7 = QLabel("Separación:")
        self.label7.setFont(QFont("Arial", 14))
        self.label7.setStyleSheet("color: whitesmoke")

        self.mat7Edit = QLabel("0")
        self.mat7Edit.setFont(QFont("Arial", 14))
        self.mat7Edit.setFixedSize(150, 60)
        self.mat7Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat7Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label8 = QLabel("Proximidad:")
        self.label8.setFont(QFont("Arial", 14))
        self.label8.setStyleSheet("color: whitesmoke")

        self.mat8Edit = QLabel("> 6mm")
        self.mat8Edit.setFont(QFont("Arial", 14))
        self.mat8Edit.setFixedSize(150, 60)
        self.mat8Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat8Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)



        self.labelParams2 = QLabel("Parametros Configurados")
        self.labelParams2.setFont(QFont("Arial", 16))
        self.labelParams2.setStyleSheet("color: whitesmoke")
        fuente = self.labelParams2.font()
        fuente.setUnderline(True)
        self.labelParams2.setFont(fuente)
        self.labelParams2.setAlignment(Qt.AlignmentFlag.AlignHCenter)


        self.conf1Edit = QLabel("...")
        self.conf1Edit.setFont(QFont("Arial", 14))
        self.conf1Edit.setFixedSize(150, 60)
        self.conf1Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.conf1Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.conf2Edit = QLabel("...")
        self.conf2Edit.setFont(QFont("Arial", 14))
        self.conf2Edit.setFixedSize(150, 60)
        self.conf2Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.conf2Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.conf3Edit = QLabel("...")
        self.conf3Edit.setFont(QFont("Arial", 14))
        self.conf3Edit.setFixedSize(150, 60)
        self.conf3Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.conf3Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.conf4Edit = QLabel("...")
        self.conf4Edit.setFont(QFont("Arial", 14))
        self.conf4Edit.setFixedSize(150, 60)
        self.conf4Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.conf4Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.conf5Edit = QLabel("...")
        self.conf5Edit.setFont(QFont("Arial", 14))
        self.conf5Edit.setFixedSize(150, 60)
        self.conf5Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.conf5Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.conf6Edit = QLabel("...")
        self.conf6Edit.setFont(QFont("Arial", 14))
        self.conf6Edit.setFixedSize(150, 60)
        self.conf6Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.conf6Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.conf7Edit = QLabel("...")
        self.conf7Edit.setFont(QFont("Arial", 14))
        self.conf7Edit.setFixedSize(150, 60)
        self.conf7Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.conf7Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.conf8Edit = QLabel("...")
        self.conf8Edit.setFont(QFont("Arial", 14))
        self.conf8Edit.setFixedSize(150, 60)
        self.conf8Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.conf8Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cases = requests.get(f"{self.base_url}/casos").json()
        nombres = []
        for m in range(len(self.cases)):
            nombres.append(self.cases[m].get("Nombre"))

        self.casesCB = QComboBox()
        self.casesCB.addItems(nombres)
        self.casesCB.setFont(QFont("Arial", 18))
        self.casesCB.setStyleSheet("color: black; background-color: silver")
        self.casesCB.currentTextChanged.connect(self.case_changed)
        self.casesCB.setFixedSize(160, 75)
        self.casesCB.setEnabled(False)


        self.samplesEdit = QLineEdit()  # Bloque de edición para definición de número de muestras a recopilar
        self.samplesEdit.setPlaceholderText("N. de muestras...")
        self.samplesEdit.setFont(QFont("Arial", 18))
        self.samplesEdit.setFixedSize(160, 75)
        self.samplesEdit.setStyleSheet("color: black; background-color: silver")
        self.samplesEdit.textChanged.connect(self.updatesamp)

        self.alerts = QTextEdit()
        self.alerts.setMaximumSize(300, 2000)
        self.alerts.setPlaceholderText("...")
        self.alerts.setFont(QFont("Arial", 12, QFont.Bold))
        self.alerts.setStyleSheet("color: black; background-color: silver")
        self.alerts.setReadOnly(True)

        param_layout.addWidget(self.labelParams1, 0, 0, 1, 2, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.label1, 1, 0, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.mat1Edit, 1, 1, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.label2, 2, 0, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.mat2Edit, 2, 1, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.label3, 3, 0, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.mat3Edit, 3, 1, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.label4, 4, 0, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.mat4Edit, 4, 1, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.label5, 5, 0, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.mat5Edit, 5, 1, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.label6, 6, 0, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.mat6Edit, 6, 1, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.label7, 7, 0, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.mat7Edit, 7, 1, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.label8, 8, 0, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.mat8Edit, 8, 1, Qt.AlignmentFlag.AlignTop)

        param_layout.addWidget(self.labelParams2, 0, 2, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.conf1Edit, 1, 2, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.conf2Edit, 2, 2, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.conf3Edit, 3, 2, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.conf4Edit, 4, 2, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.conf5Edit, 5, 2, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.conf6Edit, 6, 2, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.conf7Edit, 7, 2, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.conf8Edit, 8, 2, Qt.AlignmentFlag.AlignTop)

        self.paramGroup.setLayout(param_layout)

        cntrl_layout.addWidget(self.buttonstart, 0, 4)
        cntrl_layout.addWidget(self.buttonconnect, 0, 0)
        cntrl_layout.addWidget(self.casesCB, 0, 1)
        cntrl_layout.addWidget(self.samplesEdit, 0, 2)
        cntrl_layout.addWidget(self.buttonset, 0, 3)
        cntrl_layout.addWidget(self.buttonload, 0, 5)
        cntrl_layout.addWidget(self.buttonimage, 0, 6)

        self.controlGroup.setLayout(cntrl_layout)

        main_layout.addWidget(self.paramGroup, 0, 0, 2, 1)
        main_layout.addWidget(self.controlGroup, 2, 0, 1, 3)
        main_layout.addWidget(self.canvas, 0, 1, 1, 1)
        main_layout.addWidget(self.canvas2, 1, 1, 1, 1)
        main_layout.addWidget(self.alerts, 0, 2, 2, 1)

    def write_int(self, db_number, byte_offset, value: int):  # Funciones para comunicación GUI <-> PLC
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

    def case_changed(self, texto):
        try:
            index = ""
            for n in range(len(self.cases)):
                casos = self.cases[n].get("Nombre")
                if casos == self.casesCB.currentText():

                    index = str(self.cases[n].get("id"))

            caso = requests.get(f"{self.base_url}/casos/" + index).json()
            print(caso)

            self.conf1Edit.setText(str(caso.get("Tiempo")))
            self.conf2Edit.setText(str(caso.get("Fuerza")))
            self.conf3Edit.setText(str(caso.get("Compresion")))
            self.conf4Edit.setText(str(caso.get("Pulsos")))
            self.conf5Edit.setText(str(caso.get("Material")))
            self.conf6Edit.setText(str(caso.get("Grosor")))
            self.conf7Edit.setText(str(caso.get("Separacion")))
            self.conf7Edit.setText(str(caso.get("Proximidad")))


        except Exception as e:
            self.escribirAlerta("Error. Error al solicitar casos: " + str(e))


    def crear_prueba(self):
        if self.connected:
            try:

                self.datos = {
                      "Id": self.identif,
                      "Caso": self.casesCB.currentText(),
                      "Muestras": self.texto,
                      "Tiempo": self.tSoldadura,
                      "FMax": self.max,
                      "IMax": self.maxcurr,
                      "Diametro": self.mat3
                }

                requests.post(f"{self.base_url}/pruebas", json=self.datos).json()

                for m in range(len(self.time_array)):

                    self.datos_2 = {
                        "Id" : self.identif,
                        "Caso" : self.casesCB.currentText(),
                        "Tiempo" : self.time_array[m],
                        "Fuerza" : self.force_array[m],
                        "Corriente" : self.current_array[m]
                    }

                    requests.post(f"{self.base_url}/datos", json=self.datos_2).json()

                self.escribirAlerta("Datos registrados correctamente ✓")

            except Exception as e:
                self.escribirAlerta("Error. Error al registrar datos: " + str(e))

        else:
            self.escribirAlerta("Error. PLC no conectado.")


    def connectPLC(self):  # Función para establecer conexión
        try:

            self.plc.disconnect()
            self.plc.connect("192.168.0.1", rack=0, slot=1)

            self.connected = True
            self.casesCB.setEnabled(True)
            self.alerts.setPlainText("Conectado a PLC.")
            self.buttonconnect.setStyleSheet("background-color: green")

        except Exception as e:
            self.buttonconnect.setStyleSheet("background-color: red")
            self.escribirAlerta("Error. Error al conectar: " + str(e))


    def escribirAlerta(self, texto):
        texto_actual = self.alerts.toPlainText()
        # Insertar nuevo texto antes del existente
        self.alerts.setPlainText(">" + texto + "\n" + "\n" + texto_actual)

    def load_image(self):
        if self.connected:
            self.figure.savefig(self.nombre1)
            self.figure2.savefig(self.nombre2)
            self.escribirAlerta("Imágenes guardadas. ✓")

        else:
            self.escribirAlerta("Error. PLC no conectado.")


    def updatesamp(self, text):  # Funciones para comportamiento de botones y conexión a PLC
        if text != "":
            try:
                num = text
                self.texto = int(num)
            except Exception:
                self.escribirAlerta("Error. En este campo solo puede ingresar números enteros.")
                self.samplesEdit.setText("")

    def setParams(self):
        if self.connected:
            try:

                num = self.texto
                self.write_int(db_number=12, byte_offset=0, value=num)
                #self.write_real() # Enviar tiempo de soldadura
                self.escribirAlerta("Parametros configurados ✓")

            except Exception as e:
                self.escribirAlerta("Error. Error al enviar datos: " + str(e))
        else:
            self.escribirAlerta("Error. PLC no conectado.")

    def actualizar_nombre(self):  # Función para actualizar nombre de gráfica a guardar
        self.index = int(self.index)
        self.index = self.index + 1
        self.index = str(self.index)

        ahora = datetime.now()

        self.fecha_formateada = ahora.strftime("%d-%m-%Y-%H-%M-%S")

        self.identif = str(self.index) + "-" + self.fecha_formateada

        self.nombre1 = "Plots/grafica_" + "F" + "_" + self.identif
        self.nombre2 = "Plots/grafica_" + "I" + "_" + self.identif


    def showplot(self):

        if self.connected:
            try:
                self.max = 0
                self.maxcurr = 0
                num = self.texto

                self.figure.clear()
                self.figure2.clear()

                self.time_array = self.read_dword_array(db_number=13, start_byte=0, bytes=num)
                self.force_array = self.read_real_array(db_number=1, start_byte=0, bytes=num)
                self.current_array = self.read_real_array(db_number=15, start_byte=0, bytes=num)

                if len(self.time_array) and len(self.force_array) > 5:
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

                # print("Datos de fuerza:", self.force_array)
                # print("Datos de tiempo:", self.time_array)
                # print("Datos de corriente:", self.current_array)


            except Exception as e:
                self.escribirAlerta("Error. Error al solicitar datos: " + str(e))

        else:
            self.escribirAlerta("Error. PLC no conectado.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HMI()
    window.show()
    sys.exit(app.exec_())
