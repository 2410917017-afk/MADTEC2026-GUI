# Código para la adquisición de datos preliminar en la validación de la instrumentación del proceso de soldadura por puntos.
# Incluye interfaz gráfica simple para el muestreo y graficación de datos, así como guardar las gráficas en una carpeta dedicada.
# Comandos para instalar librerías requeridas, contando ya con Python (usamos versión 3.10.0):

# pip install matplotlib python-snap7 PyQt5 psycopg2-binary

import sys, matplotlib.pyplot as plt, snap7, psycopg2, psycopg2.extras, matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from snap7.util import get_int, get_real, get_bool, set_int, set_bool, get_dword
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QLineEdit, QLabel, QGroupBox, QTextEdit
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

        ahora = datetime.now()

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

        self.figure = Figure(figsize=(6, 6), dpi=100)  # Creación de espacio para graficar datos adquiridos del PLC
        self.canvas = FigureCanvas(self.figure)

        self.figure2 = Figure(figsize=(6, 6), dpi=100)
        self.canvas2 = FigureCanvas(self.figure2)

        self.buttonstart = QPushButton("Leer datos")  # Creación y configuración de elementos incluidos en la GUI
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
        self.buttonstart.clicked.connect(
            self.actualizar_nombre)  # Llamada a funciones que ejecutan el comportamiento de botones
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
        self.buttonload.clicked.connect(self.log_postgresql)
        # self.buttonload.clicked.connect(self.generar_pdf)

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


        self.mat1Edit = QLineEdit()  # Bloque de edición para definición de número de muestras a recopilar
        self.mat1Edit.setPlaceholderText("...")
        self.mat1Edit.setFont(QFont("Arial", 16))
        self.mat1Edit.setFixedSize(200, 60)
        self.mat1Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat1Edit.textChanged.connect(self.mat1update)

        self.label2 = QLabel("Tipo de material:")
        self.label2.setFont(QFont("Arial", 16))
        self.label2.setStyleSheet("color: whitesmoke")


        self.mat2Edit = QLineEdit()  # Bloque de edición para definición de número de muestras a recopilar
        self.mat2Edit.setPlaceholderText("...")
        self.mat2Edit.setFont(QFont("Arial", 16))
        self.mat2Edit.setFixedSize(200, 60)
        self.mat2Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat2Edit.textChanged.connect(self.mat2update)

        self.label3 = QLabel("Diam. de soldadura [mm]:")
        self.label3.setFont(QFont("Arial", 16))
        self.label3.setStyleSheet("color: whitesmoke")


        self.mat3Edit = QLineEdit()  # Bloque de edición para definición de número de muestras a recopilar
        self.mat3Edit.setPlaceholderText("...")
        self.mat3Edit.setFont(QFont("Arial", 16))
        self.mat3Edit.setFixedSize(200, 60)
        self.mat3Edit.setStyleSheet("color: black; background-color: silver; border-radius: 2px")
        self.mat3Edit.textChanged.connect(self.mat3update)

        self.samplesEdit = QLineEdit()  # Bloque de edición para definición de número de muestras a recopilar
        self.samplesEdit.setPlaceholderText("N. de muestras...")
        self.samplesEdit.setFont(QFont("Arial", 18))
        self.samplesEdit.setFixedSize(160, 75)
        self.samplesEdit.setStyleSheet("color: black; background-color: silver")
        self.samplesEdit.textChanged.connect(self.updatesamp)

        self.alerts = QTextEdit()
        self.alerts.setPlaceholderText("...")
        self.alerts.setFont(QFont("Arial", 14, QFont.Bold))
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
        main_layout.addWidget(self.canvas, 0, 0, 2, 1)
        main_layout.addWidget(self.canvas2, 0, 1, 2, 1)
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

    def connectPLC(self):  # Función para establecer conexión
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
        self.alerts.setPlainText(">" + texto + "\n" + "\n" + texto_actual)

    def load_image(self):
        self.figure.savefig(self.nombre1)
        self.figure2.savefig(self.nombre2)
        self.escribirAlerta("Imágenes guardadas. ✓")

    def mat1update(self, text):  # Funciones para comportamiento de botones y conexión a PLC

        if text != "":
            try:
                num = text
                self.mat1 = float(num)
            except Exception:
                self.escribirAlerta("Error. En este campo solo puede ingresar números.")

                self.mat1Edit.setText("")

    def mat2update(self, text):  # Funciones para comportamiento de botones y conexión a PLC

        if text != "":
            self.mat2 = text

    def mat3update(self, text):  # Funciones para comportamiento de botones y conexión a PLC

        if text != "":
            try:
                num = text
                self.mat3 = float(num)

            except Exception:
                self.escribirAlerta("Error. En este campo solo puede ingresar números.")
                self.mat3Edit.setText("")

    def updatesamp(self, text):  # Funciones para comportamiento de botones y conexión a PLC
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

    def actualizar_nombre(self):  # Función para actualizar nombre de gráfica a guardar
        self.index = int(self.index)
        self.index = self.index + 1
        self.index = str(self.index)

        ahora = datetime.now()

        self.fecha_formateada = ahora.strftime("%d-%m-%Y-%H-%M-%S")

        self.identif = str(self.index) + "-" + self.fecha_formateada

        self.nombre1 = "Plots/grafica_" + "F" + "_" + self.identif
        self.nombre2 = "Plots/grafica_" + "I" + "_" + self.identif

    def log_postgresql(self):

        conn = psycopg2.connect(
            host="localhost",
            database="CETEVI_1",
            user="postgres",
            password="cetevi123",
            port=5432
        )

        id_array = [0] * len(self.time_array)

        for i in range(len(self.time_array)):
            id_array[i] = self.identif

        if self.connected:
            try:
                cursor = conn.cursor()

                cursor.execute("""
                               INSERT INTO public."Pruebas"("Id", "Muestras", "Tiempo", "Orientación", "Fmax", "Imax",
                                                            "Grosor", "Material", "Diametro")
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                               """,
                               (

                                   self.identif,
                                   self.texto,
                                   self.tSoldadura,
                                   "Orientación",
                                   self.max,
                                   self.maxcurr,
                                   self.mat1,
                                   self.mat2,
                                   self.mat3

                               ))

                for m in range(len(self.time_array)):
                    cursor.execute("""
                                   INSERT INTO public."Datos"("Id", "Tiempo", "Fuerza", "Corriente")
                                   VALUES (%s, %s, %s, %s);
                                   """,
                                   (

                                       id_array[m],
                                       self.time_array[m],
                                       self.force_array[m],
                                       self.current_array[m]

                                   ))

                conn.commit()
                cursor.close()
                conn.close()
                self.escribirAlerta("Datos registrados correctamente ✓")


            except Exception as e:
                self.escribirAlerta("Error. Error al registrar datos: " + str(e))

        else:
            self.escribirAlerta("Error. PLC no conectado.")

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