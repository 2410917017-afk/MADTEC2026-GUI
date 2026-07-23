# Código para la adquisición de datos preliminar en la validación de la instrumentación del proceso de soldadura por puntos.
# Incluye interfaz gráfica simple para el muestreo y graficación de datos, así como guardar las gráficas en una carpeta dedicada.
# Comandos para instalar librerías requeridas, contando ya con Python (usamos versión 3.10.0):

# pip install matplotlib python-snap7 PyQt5 requests pyserial
import sys
from pathlib import Path
import sonyilx_camera as ilx
import subprocess

import time
import os

import matplotlib
import snap7

import cv2
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QLineEdit, QLabel, QGroupBox,
    QComboBox, QTabWidget, QMainWindow, QTableWidget, QMessageBox, QTableWidgetItem
)
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer
from datetime import datetime

from hmi.config import BASE_URL, PLC_HOST, PLC_RACK, PLC_SLOT, PLOTS_DIR, SERIAL_BAUDRATE, SERIAL_PORT
from hmi.services.api_client import ApiClient
from hmi.services.plc import (
    read_bool as plc_read_bool,
    read_dword_array as plc_read_dword_array,
    read_int_array as plc_read_int_array,
    read_real_array as plc_read_real_array,
    write_bool as plc_write_bool,
    write_int as plc_write_int,
)
from hmi.utils.plotting import style_axis
from hmi.widgets import AlertLog


# Inicialización de interfaz gráfica
class HMI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PLC Plotter")  # Configuración de la ventana de la GUI
        self.setStyleSheet("background-color: #060c06; color: white")

        # Crear el widget de pestañas principal
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # --- Pestaña 1 ---
        self.pestana1 = QWidget()

        # --- Pestaña 2 ---
        self.pestana2 = QWidget()
        self.layout_pestana2 = QGridLayout()

        # --- Pestaña 2 ---
        self.pestana3 = QWidget()
        self.layout_pestana3 = QGridLayout()


        main_layout = QGridLayout()  # Distribución de rejilla, renglones y columnas
        main_layout.setContentsMargins(30, 30, 30, 30)
        param_layout = QGridLayout()
        param_layout.setContentsMargins(50, 30, 30, 30)
        cntrl_layout = QGridLayout()
        cntrl_layout.setContentsMargins(10, 20, 10, 20)

        cntrl2_layout = QGridLayout()
        cntrl2_layout.setContentsMargins(10, 20, 10, 20)
        casos_layout = QGridLayout()
        casos_layout.setContentsMargins(60, 35, 60, 35)

        cntrl3_layout = QGridLayout()
        cntrl3_layout.setContentsMargins(30, 30, 30, 30)

        self.base_url = BASE_URL
        self.api = ApiClient(self.base_url)
        self.puerto = SERIAL_PORT
        self.baudios = SERIAL_BAUDRATE
        self.busqueda = None
        self.ser = None
        self.detector = cv2.QRCodeDetector()
        self.camera = ilx.CameraLibrary()

        self.last_data = ""

        self.timer = QTimer()
        self.zoom = None


        self.labelImagen = QLabel(self)
        #self.labelImagen.setMaximumSize(500, 1000)
        self.label2Imagen = QLabel(self)

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

        self.confirm = False
        self.casoEliminar = None

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
        self.force_array = []
        self.time_array = []
        self.current_array = []
        self.fecha_formateada = ahora.strftime("%d-%m-%Y-%H-%M-%S")

        self.plc = snap7.client.Client()

        self.casoElimimar = ""

        self.alerts = AlertLog()
        self.alerts2 = AlertLog()

        self.paramGroup = QGroupBox()
        self.paramGroup.setStyleSheet("background-color: #1e1e1e; color: whitesmoke; border-radius: 10px")
        self.paramGroup.setFont(QFont("Arial", 14))
        self.paramGroup.setMaximumSize(640, 1100)

        self.controlGroup = QGroupBox()
        self.controlGroup.setStyleSheet("background-color: #1e1e1e; color: whitesmoke; border-radius: 10px")
        self.controlGroup.setFont(QFont("Arial", 14))
        self.controlGroup.setMaximumSize(2000, 125)

        self.casosGroup = QGroupBox()
        self.casosGroup.setStyleSheet("background-color: #1e1e1e; color: whitesmoke; border-radius: 10px")
        self.casosGroup.setFont(QFont("Arial", 14))

        self.control2Group = QGroupBox()
        self.control2Group.setStyleSheet("background-color: #1e1e1e; color: whitesmoke; border-radius: 10px")
        self.control2Group.setFont(QFont("Arial", 14))
        self.control2Group.setMaximumSize(2000, 125)

        self.control3Group = QGroupBox()
        self.control3Group.setStyleSheet("background-color: #1e1e1e; color: whitesmoke; border-radius: 10px")
        self.control3Group.setFont(QFont("Arial", 14))
        self.control3Group.setMaximumSize(2000, 125)

        self.figure = Figure(figsize=(5, 4), dpi=100)  # Creación de espacio para graficar datos adquiridos del PLC
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMaximumSize(400, 400)
        self.figure.set_facecolor('#1e1e1e')

        self.figure2 = Figure(figsize=(5, 4), dpi=100)
        self.canvas2 = FigureCanvas(self.figure2)
        self.canvas2.setMaximumSize(400, 400)
        self.figure2.set_facecolor('#1e1e1e')

        self.buttonstart = QPushButton("Iniciar")  # Creación y configuración de elementos incluidos en la GUI
        self.buttonstart.setFont(QFont("Arial", 20))
        self.buttonstart.setFixedSize(160, 80)
        self.buttonstart.setStyleSheet("""
                                  QPushButton {
                                  background-color: #494be7;
                                  color: #dddcde; border: none; 
                                  border-radius: 36px; 
                                  padding: 10px 10px
                                  }
                                  QPushButton:hover {
                                  background-color: #9193FF;
                                  }
                                  QPushButton:pressed {
                                  padding: 11px 9px 9px 11px;
                                  }
                                  """)
        self.buttonstart.clicked.connect(self.actualizar_nombre)  # Llamada a funciones que ejecutan el comportamiento de botones
        self.buttonstart.clicked.connect(self.iniciar_PLC)

        self.buttonconnect = QPushButton("Conectar")
        self.buttonconnect.setFont(QFont("Arial", 20))
        self.buttonconnect.setFixedSize(150, 75)
        self.buttonconnect.setStyleSheet("""
                                  QPushButton {
                                  background-color: #5e5e5e; 
                                  color: #dddcde; border: none; 
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
        self.buttonconnect.clicked.connect(self.connectPLC)

        self.buttonset = QPushButton("Enviar")
        self.buttonset.setFont(QFont("Arial", 20))
        self.buttonset.setFixedSize(160, 75)
        self.buttonset.setStyleSheet("""
                                  QPushButton {
                                  background-color: #494be7; 
                                  color: #dddcde; border: none; 
                                  border-radius: 34px; 
                                  padding: 10px 10px
                                  }
                                  QPushButton:hover {
                                  background-color: #9193FF;
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
                                  background-color: #494be7; 
                                  color: #dddcde; border: none; 
                                  border-radius: 34px; 
                                  padding: 10px 10px
                                  }
                                  QPushButton:hover {
                                  background-color: #9193FF;
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
                                  background-color: #494be7; 
                                  color: #dddcde; border: none; 
                                  border-radius: 34px; 
                                  padding: 10px 10px
                                  }
                                  QPushButton:hover {
                                  background-color: #9193FF;
                                  }
                                  QPushButton:pressed {
                                  padding: 11px 9px 9px 11px;
                                  }
                                  """)
        self.buttonimage.clicked.connect(self.load_image)


        self.labelParams1 = QLabel("Parametros ideales")
        self.labelParams1.setFont(QFont("Arial", 18))
        self.labelParams1.setStyleSheet("color: #dddcde")
        fuente = self.labelParams1.font()
        fuente.setUnderline(True)
        self.labelParams1.setFont(fuente)
        self.labelParams1.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.label1 = QLabel("Tiempo:")
        self.label1.setFont(QFont("Arial", 14))
        self.label1.setStyleSheet("color: #dddcde")

        self.mat1Edit = QLabel("200ms-300ms")
        self.mat1Edit.setFont(QFont("Arial", 14))
        self.mat1Edit.setFixedSize(150, 60)
        self.mat1Edit.setStyleSheet("color: black; background-color: #dddcde; border-radius: 2px")
        self.mat1Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label2 = QLabel("Fuerza:")
        self.label2.setFont(QFont("Arial", 14))
        self.label2.setStyleSheet("color: #dddcde")

        self.mat2Edit = QLabel("2.0 kN–4.5 kN")
        self.mat2Edit.setFont(QFont("Arial", 14))
        self.mat2Edit.setFixedSize(150, 60)
        self.mat2Edit.setStyleSheet("color: black; background-color: #dddcde; border-radius: 2px")
        self.mat2Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label3 = QLabel("Tiempo de compresión:")
        self.label3.setFont(QFont("Arial", 14))
        self.label3.setStyleSheet("color: #dddcde")

        self.mat3Edit = QLabel("150 ms–300 ms")
        self.mat3Edit.setFont(QFont("Arial", 14))
        self.mat3Edit.setFixedSize(150, 60)
        self.mat3Edit.setStyleSheet("color: black; background-color: #dddcde; border-radius: 2px")
        self.mat3Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label4 = QLabel("Pulsos:")
        self.label4.setFont(QFont("Arial", 14))
        self.label4.setStyleSheet("color: #dddcde")

        self.mat4Edit = QLabel("1")
        self.mat4Edit.setFont(QFont("Arial", 14))
        self.mat4Edit.setFixedSize(150, 60)
        self.mat4Edit.setStyleSheet("color: black; background-color: #dddcde; border-radius: 2px")
        self.mat4Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label5 = QLabel("Material:")
        self.label5.setFont(QFont("Arial", 14))
        self.label5.setStyleSheet("color: #dddcde")

        self.mat5Edit = QLabel("Acero")
        self.mat5Edit.setFont(QFont("Arial", 14))
        self.mat5Edit.setFixedSize(150, 60)
        self.mat5Edit.setStyleSheet("color: black; background-color: #dddcde; border-radius: 2px")
        self.mat5Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label6 = QLabel("Grosor:")
        self.label6.setFont(QFont("Arial", 14))
        self.label6.setStyleSheet("color: #dddcde")

        self.mat6Edit = QLabel("0.4mm-0.8mm")
        self.mat6Edit.setFont(QFont("Arial", 14))
        self.mat6Edit.setFixedSize(150, 60)
        self.mat6Edit.setStyleSheet("color: black; background-color: #dddcde; border-radius: 2px")
        self.mat6Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label7 = QLabel("Separación:")
        self.label7.setFont(QFont("Arial", 14))
        self.label7.setStyleSheet("color: #dddcde")

        self.mat7Edit = QLabel("0")
        self.mat7Edit.setFont(QFont("Arial", 14))
        self.mat7Edit.setFixedSize(150, 60)
        self.mat7Edit.setStyleSheet("color: black; background-color: #dddcde; border-radius: 2px")
        self.mat7Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)


        self.conf1Edit = QLabel("...")
        self.conf1Edit.setFont(QFont("Arial", 14))
        self.conf1Edit.setFixedSize(150, 60)
        self.conf1Edit.setStyleSheet("color: black; background-color: #dddcde; border-radius: 2px")
        self.conf1Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.conf2Edit = QLabel("...")
        self.conf2Edit.setFont(QFont("Arial", 14))
        self.conf2Edit.setFixedSize(150, 60)
        self.conf2Edit.setStyleSheet("color: black; background-color: #dddcde; border-radius: 2px")
        self.conf2Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.conf3Edit = QLabel("...")
        self.conf3Edit.setFont(QFont("Arial", 14))
        self.conf3Edit.setFixedSize(150, 60)
        self.conf3Edit.setStyleSheet("color: black; background-color: #dddcde; border-radius: 2px")
        self.conf3Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.conf4Edit = QLabel("...")
        self.conf4Edit.setFont(QFont("Arial", 14))
        self.conf4Edit.setFixedSize(150, 60)
        self.conf4Edit.setStyleSheet("color: black; background-color: #dddcde; border-radius: 2px")
        self.conf4Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.conf5Edit = QLabel("...")
        self.conf5Edit.setFont(QFont("Arial", 14))
        self.conf5Edit.setFixedSize(150, 60)
        self.conf5Edit.setStyleSheet("color: black; background-color: #dddcde; border-radius: 2px")
        self.conf5Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.conf6Edit = QLabel("...")
        self.conf6Edit.setFont(QFont("Arial", 14))
        self.conf6Edit.setFixedSize(150, 60)
        self.conf6Edit.setStyleSheet("color: black; background-color: #dddcde; border-radius: 2px")
        self.conf6Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.conf7Edit = QLabel("...")
        self.conf7Edit.setFont(QFont("Arial", 14))
        self.conf7Edit.setFixedSize(150, 60)
        self.conf7Edit.setStyleSheet("color: black; background-color: #dddcde; border-radius: 2px")
        self.conf7Edit.setAlignment(Qt.AlignmentFlag.AlignCenter)


        self.cases = self.fetch_cases()
        self.nombres = []
        self.indices = []

        for m in range(len(self.cases)):
            self.nombres.append(self.cases[m].get("Nombre"))
            self.indices.append(self.cases[m].get("id"))

        self.casesCB = QComboBox()
        self.casesCB.addItems(self.nombres)
        self.casesCB.setFont(QFont("Arial", 18))
        self.casesCB.setStyleSheet("color: #dddcde; background-color: #5e5e5e")
        self.casesCB.currentTextChanged.connect(self.case_changed)
        self.casesCB.setFixedSize(220, 75)
        self.casesCB.setEnabled(True)


        self.samplesEdit = QLineEdit()  # Bloque de edición para definición de número de muestras a recopilar
        self.samplesEdit.setPlaceholderText("N. de muestras...")
        self.samplesEdit.setFont(QFont("Arial", 18))
        self.samplesEdit.setFixedSize(160, 75)
        self.samplesEdit.setStyleSheet("color: #dddcde; background-color: #5e5e5e")
        self.samplesEdit.textChanged.connect(self.updatesamp)


        # Pestaña 2
        self.buttonNuevo = QPushButton("Nuevo")
        self.buttonNuevo.setFont(QFont("Arial", 20))
        self.buttonNuevo.setFixedSize(220, 75)
        self.buttonNuevo.setStyleSheet("""
                                          QPushButton {
                                          background-color: #494be7; 
                                          color: #dddcde; border: none; 
                                          border-radius: 34px; 
                                          padding: 10px 10px
                                          }
                                          QPushButton:hover {
                                          background-color: #9193FF;
                                          }
                                          QPushButton:pressed {
                                          padding: 11px 9px 9px 11px;
                                          }
                                          """)
        self.buttonNuevo.clicked.connect(self.nuevo_caso)


        self.buttonSave = QPushButton("Guardar")
        self.buttonSave.setFont(QFont("Arial", 20))
        self.buttonSave.setFixedSize(220, 75)
        self.buttonSave.setStyleSheet("""
                                          QPushButton {
                                          background-color: #494be7; 
                                          color: #dddcde; border: none; 
                                          border-radius: 34px; 
                                          padding: 10px 10px
                                          }
                                          QPushButton:hover {
                                          background-color: #9193FF;
                                          }
                                          QPushButton:pressed {
                                          padding: 11px 9px 9px 11px;
                                          }
                                          """)
        self.buttonSave.clicked.connect(self.mostrar_confirmacion)
        self.buttonSave.clicked.connect(self.guardar_caso)

        self.buttonBorrar = QPushButton("Borrar")
        self.buttonBorrar.setFont(QFont("Arial", 20))
        self.buttonBorrar.setFixedSize(220, 75)
        self.buttonBorrar.setStyleSheet("""
                                          QPushButton {
                                          background-color: #494be7; 
                                          color: silver; border: none; 
                                          color: #dddcde; border: none; 
                                          border-radius: 34px; 
                                          padding: 10px 10px
                                          }
                                          QPushButton:hover {
                                          background-color: #9193FF;
                                          }
                                          QPushButton:pressed {
                                          padding: 11px 9px 9px 11px;
                                          }
                                          """)
        self.buttonBorrar.clicked.connect(self.mostrar_confirmacion)
        self.buttonBorrar.clicked.connect(self.borrar_caso)

        self.buttonRefresh = QPushButton("Actualizar")
        self.buttonRefresh.setFont(QFont("Arial", 20))
        self.buttonRefresh.setFixedSize(220, 75)
        self.buttonRefresh.setStyleSheet("""
                                                  QPushButton {
                                                  background-color: #494be7; 
                                                  color: silver; border: none; 
                                                  color: #dddcde; border: none; 
                                                  border-radius: 34px; 
                                                  padding: 10px 10px
                                                  }
                                                  QPushButton:hover {
                                                  background-color: #9193FF;
                                                  }
                                                  QPushButton:pressed {
                                                  padding: 11px 9px 9px 11px;
                                                  }
                                                  """)
        self.buttonRefresh.clicked.connect(self.Refresh_tabla)

        self.tablaCasos = QTableWidget(len(self.cases), 10)
        self.tablaCasos.setStyleSheet("""
                    QTableWidget {
                        color: darkslategrey;
                        background-color: #F8F9FA;
                        alternate-background-color: #E9ECEF;
                        gridline-color: #DEE2E6;
                        border: 1px solid #CED4DA;
                        font-size: 14px;
                    }
                    QTableWidget::item {
                        padding: 5px;
                    }
                    QTableWidget::item:selected {
                        background-color: #D1E7DD;
                        color: #0F5132;
                    }
                    QHeaderView::section {
                        background-color: #343A40;
                        color: white;
                        padding: 6px;
                        font-weight: bold;
                        border: 1px solid #6C757D;
                    }
                """)
        self.tablaCasos.cellClicked.connect(self.on_cell_clicked)

        # Configuración extra
        self.tablaCasos.setAlternatingRowColors(True)

        for i in range(10):
            self.tablaCasos.setColumnWidth(i, 136)

        self.tablaCasos.setHorizontalHeaderLabels(
            ["Nombre", "Tiempo", "Fuerza", "Compresion", "Pulsos", "Material", "Grosor", "Separacion",
             "QR", "id"])

        for i in range(len(self.cases)):
            self.tablaCasos.setRowHeight(i, 80)

            for j in range(10):
                match j:
                    case 9:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("id"))))
                    case 0:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(self.nombres[i]))
                    case 1:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("Tiempo"))))
                    case 2:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("Fuerza"))))
                    case 3:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("Compresion"))))
                    case 4:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("Pulsos"))))
                    case 5:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("Material"))))
                    case 6:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("Grosor"))))
                    case 7:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("Separacion"))))
                    case 8:
                        iden = "utils/QRCodes/qr_" + str(self.cases[i].get("id")) + ".png"

                        ruta_archivo = self.obtener_ruta_recurso(os.path.join('hmi', iden))
                        item_link = QTableWidgetItem(
                            f'<a href="{ruta_archivo}" style="color:#0000EE; text-decoration:underline;">Abrir Archivo</a>')

                        item_link.setData(Qt.ItemDataRole.UserRole, True)

                        self.tablaCasos.setItem(i, j, item_link)

        #Widgets de pestaña3
        self.buttonZP = QPushButton("+")
        self.buttonZP.setFont(QFont("Arial", 20))
        self.buttonZP.setFixedSize(80, 80)
        self.buttonZP.setStyleSheet("""
                                                          QPushButton {
                                                          background-color: #494be7; 
                                                          color: silver; border: none; 
                                                          color: #dddcde; border: none; 
                                                          border-radius: 34px; 
                                                          padding: 10px 10px
                                                          }
                                                          QPushButton:hover {
                                                          background-color: #9193FF;
                                                          }
                                                          QPushButton:pressed {
                                                          padding: 11px 9px 9px 11px;
                                                          }
                                                          """)
        self.buttonZP.clicked.connect(self.zoomPlus)

        self.buttonZM = QPushButton("-")
        self.buttonZM.setFont(QFont("Arial", 20))
        self.buttonZM.setFixedSize(80, 80)
        self.buttonZM.setStyleSheet("""
                                                                  QPushButton {
                                                                  background-color: #494be7; 
                                                                  color: silver; border: none; 
                                                                  color: #dddcde; border: none; 
                                                                  border-radius: 34px; 
                                                                  padding: 10px 10px
                                                                  }
                                                                  QPushButton:hover {
                                                                  background-color: #9193FF;
                                                                  }
                                                                  QPushButton:pressed {
                                                                  padding: 11px 9px 9px 11px;
                                                                  }
                                                                  """)
        self.buttonZM.clicked.connect(self.zoomMinus)


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

        param_layout.addWidget(self.conf1Edit, 1, 2, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.conf2Edit, 2, 2, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.conf3Edit, 3, 2, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.conf4Edit, 4, 2, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.conf5Edit, 5, 2, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.conf6Edit, 6, 2, Qt.AlignmentFlag.AlignTop)
        param_layout.addWidget(self.conf7Edit, 7, 2, Qt.AlignmentFlag.AlignTop)

        self.paramGroup.setLayout(param_layout)

        cntrl_layout.addWidget(self.buttonstart, 0, 4)
        cntrl_layout.addWidget(self.buttonconnect, 0, 0)
        cntrl_layout.addWidget(self.casesCB, 0, 1)
        cntrl_layout.addWidget(self.samplesEdit, 0, 2)
        cntrl_layout.addWidget(self.buttonset, 0, 3)
        cntrl_layout.addWidget(self.buttonload, 0, 5)
        cntrl_layout.addWidget(self.buttonimage, 0, 6)

        self.controlGroup.setLayout(cntrl_layout)

        main_layout.addWidget(self.controlGroup, 0, 0, 1, 4)
        main_layout.addWidget(self.paramGroup, 1, 0, 2, 1)
        main_layout.addWidget(self.labelImagen, 1, 1, 1, 2)
        main_layout.addWidget(self.canvas, 2, 1, 1, 1)
        main_layout.addWidget(self.canvas2, 2, 2, 1, 1)
        main_layout.addWidget(self.alerts, 1, 3, 2, 1)


        # Pestaña 2

        cntrl2_layout.addWidget(self.buttonNuevo, 0, 0)
        cntrl2_layout.addWidget(self.buttonSave, 0, 1)
        cntrl2_layout.addWidget(self.buttonBorrar, 0, 2)
        cntrl2_layout.addWidget(self.buttonRefresh, 0, 3)

        casos_layout.addWidget(self.tablaCasos)

        cntrl3_layout.addWidget(self.buttonZP, 0, 0)
        cntrl3_layout.addWidget(self.buttonZM, 0, 1)

        self.control3Group.setLayout(cntrl3_layout)

        self.layout_pestana3.addWidget(self.control3Group)
        self.layout_pestana3.addWidget(self.label2Imagen)

        self.pestana3.setLayout(self.layout_pestana3)

        self.control2Group.setLayout(cntrl2_layout)
        self.casosGroup.setLayout(casos_layout)


        self.layout_pestana2.addWidget(self.control2Group, 0, 0, 1, 2)
        self.layout_pestana2.addWidget(self.casosGroup, 1, 0)
        self.layout_pestana2.addWidget(self.alerts2, 1, 1)

        self.pestana2.setLayout(self.layout_pestana2)

        self.pestana1.setLayout(main_layout)

        self.tabs.addTab(self.pestana1, "Inicio")
        self.tabs.addTab(self.pestana2, "Configuración")
        self.tabs.addTab(self.pestana3, "Cámara")
        self.tabs.setStyleSheet("color: whitesmoke")
        self.tabs.setFont(QFont("Arial", 14))
        #self.alerts.escribirAlerta(str(ilx.debug_enumerate_cameras()))


    def fetch_cases(self):
        try:
            return self.api.list_cases() or []
        except Exception as e:
            if hasattr(self, "alerts2"):
                self.alerts2.escribirAlerta("Error. Error al solicitar casos: " + str(e))
            return []

    def write_int(self, db_number, byte_offset, value: int):
        plc_write_int(self.plc, db_number, byte_offset, value)

    def read_int_array(self, db_number, start_byte, count):
        return plc_read_int_array(self.plc, db_number, start_byte, count)

    def read_dword_array(self, db_number, start_byte, count):
        return plc_read_dword_array(self.plc, db_number, start_byte, count)

    def read_real_array(self, db_number, start_byte, count):
        return plc_read_real_array(self.plc, db_number, start_byte, count)

    def read_bool(self, db_number, byte_offset, bit):
        return plc_read_bool(self.plc, db_number, byte_offset, bit)

    def write_bool(self, db, byte_offset, bit, value: bool):
        plc_write_bool(self.plc, db, byte_offset, bit, value)

    def update_frame(self):
        if self.camera.is_connected():
            try:

                live_view = self.camera.refresh_live_view()
                frame = cv2.imread(live_view)

                frame = frame[0:450, 0:810]

                data, bbox, _ = self.detector.detectAndDecode(frame)

                if bbox is not None:

                    pts = bbox.astype(int)

                    for i in range(len(pts)):
                        p1 = tuple(pts[i][0])
                        p2 = tuple(pts[(i + 1) % len(pts)][0])
                        cv2.line(frame, p1, p2, (0, 255, 0), 2)

                if data and data != self.last_data:

                    self.last_data = data

                    self.alerts.escribirAlerta("Qr encontrado: " + str(data))
                    self.buscarid(data)
                    time.sleep(2)
                    self.setParams()

                    self.iniciar_PLC()


                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                h, w, ch = rgb.shape

                image = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)

                self.labelImagen.setPixmap(QPixmap.fromImage(image))
                self.label2Imagen.setPixmap(QPixmap.fromImage(image))

            except Exception as e:
                self.alerts.escribirAlerta("Error. Error tomar video" + str(e))
                self.camera.disconnect_camera()
                self.camera.shutdown()

        else:
            self.alerts.escribirAlerta("Error. Cámara no conectada.")

    def zoomPlus(self):
        self.zoom = self.zoom + 100
        self.camera.set_zoom_position(self.zoom)  # Sin zoom
        print(self.zoom)

    def zoomMinus(self):
        self.zoom = self.zoom - 100
        self.camera.set_zoom_position(self.zoom )  # Sin zoom
        print(self.zoom)

    def buscarid(self, text):
        ident = int(text)
        self.caso = self.api.get_case(ident)
        self.alerts.escribirAlerta("Caso seleccionado: " + str(self.caso.get("Nombre")))

        self.conf1Edit.setText(str(self.caso.get("Tiempo")))
        self.conf2Edit.setText(str(self.caso.get("Fuerza")))
        self.conf3Edit.setText(str(self.caso.get("Compresion")))
        self.conf4Edit.setText(str(self.caso.get("Pulsos")))
        self.conf5Edit.setText(str(self.caso.get("Material")))
        self.conf6Edit.setText(str(self.caso.get("Grosor")))
        self.conf7Edit.setText(str(self.caso.get("Separacion")))

    def obtener_ruta_recurso(self, ruta_relativa):
        """ Obtiene la ruta absoluta al recurso tanto en desarrollo como en el ejecutable de PyInstaller """
        try:
            # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, ruta_relativa)

    def case_changed(self, texto):
        try:
            index = ""
            for n in range(len(self.cases)):
                casos = self.cases[n].get("Nombre")
                if casos == self.casesCB.currentText():

                    index = str(self.cases[n].get("id"))

            if not index:
                return

            self.caso = self.api.get_case(index)
            self.alerts.escribirAlerta("Caso seleccionado: " + str(self.caso.get("Nombre")))

            self.conf1Edit.setText(str(self.caso.get("Tiempo")))
            self.conf2Edit.setText(str(self.caso.get("Fuerza")))
            self.conf3Edit.setText(str(self.caso.get("Compresion")))
            self.conf4Edit.setText(str(self.caso.get("Pulsos")))
            self.conf5Edit.setText(str(self.caso.get("Material")))
            self.conf6Edit.setText(str(self.caso.get("Grosor")))
            self.conf7Edit.setText(str(self.caso.get("Separacion")))


        except Exception as e:
            self.alerts.escribirAlerta("Error. Error al solicitar casos: " + str(e))

    def Refresh_tabla(self):
        for i in range(len(self.cases)):

            for j in range(10):
                self.tablaCasos.setItem(i, j, QTableWidgetItem(""))

        self.cases = self.fetch_cases()
        self.tablaCasos.setRowCount(len(self.cases))

        for i in range(len(self.cases)):

            for j in range(10):
                match j:
                    case 9:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("id"))))
                    case 0:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("Nombre"))))
                    case 1:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("Tiempo"))))
                    case 2:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("Fuerza"))))
                    case 3:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("Compresion"))))
                    case 4:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("Pulsos"))))
                    case 5:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("Material"))))
                    case 6:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("Grosor"))))
                    case 7:
                        self.tablaCasos.setItem(i, j, QTableWidgetItem(str(self.cases[i].get("Separacion"))))
                    case 8:

                        iden = "QRCodes/qr_" + str(self.cases[i].get("id")) + ".png"

                        ruta_archivo = self.obtener_ruta_recurso(os.path.join('utils', iden))
                        item_link = QTableWidgetItem(f'<a href="{ruta_archivo}" style="color:#0000EE; text-decoration:underline;">Abrir Archivo</a>')

                        item_link.setData(Qt.ItemDataRole.UserRole, True)

                        self.tablaCasos.setItem(i, j, item_link)

        for row in range(self.tablaCasos.rowCount() - 1, -1, -1):
            item = self.tablaCasos.item(row, 0)
            if item is None or item.text() == "":
                self.tablaCasos.removeRow(row)

        self.nombres.clear()
        self.indices.clear()

        for m in range(len(self.cases)):
            self.nombres.append(self.cases[m].get("Nombre"))


        self.casesCB.clear()
        self.casesCB.addItems(self.nombres)

        self.alerts2.escribirAlerta("Tabla actualizada con exito.")

    def on_cell_clicked(self, row, column):

        item = self.tablaCasos.item(row, 9)
        if item is not None:
            self.casoEliminar = item.text()

        item2 = self.tablaCasos.item(row, column)
        if item2 and item2.data(Qt.ItemDataRole.UserRole) == True:
            # Extraer la ruta del enlace del texto HTML
            texto_html = item2.text()
            inicio = texto_html.find('href="') + 6
            fin = texto_html.find('"', inicio)
            ruta = texto_html[inicio:fin]

            # Abrir el archivo con la aplicación predeterminada del sistema operativo
            try:
                subprocess.run(['xdg-open', ruta])
            except subprocess.CalledProcessError as e:
                print(f"Error al abrir el archivo: {e}")

    def borrar_caso(self):
        if self.confirm:
            if not self.casoEliminar:
                self.alerts2.escribirAlerta("Error. Seleccione un caso para borrar.")
                return

            try:
                self.api.delete_case(self.casoEliminar)
                self.alerts2.escribirAlerta("Caso eliminado correctamente.")
            except Exception as e:
                self.alerts2.escribirAlerta("Error. Error al borrar caso: " + str(e))


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

                self.api.create_test(self.datos)

                for m in range(len(self.time_array)):

                    self.datos_2 = {
                        "Id" : self.identif,
                        "Caso" : self.casesCB.currentText(),
                        "Tiempo" : self.time_array[m],
                        "Fuerza" : self.force_array[m],
                        "Corriente" : self.current_array[m]
                    }

                    self.api.create_sample(self.datos_2)

                self.alerts.escribirAlerta("Datos registrados correctamente ✓")

            except Exception as e:
                self.alerts.escribirAlerta("Error. Error al registrar datos: " + str(e))

        else:
            self.alerts.escribirAlerta("Error. PLC no conectado.")


    def connectPLC(self):  # Función para establecer conexión
        try:

            self.plc.disconnect()
            self.plc.connect(PLC_HOST, rack=PLC_RACK, slot=PLC_SLOT)

            self.connected = True
            self.casesCB.setEnabled(True)
            self.alerts.escribirAlerta("Conectado a PLC.")
            self.buttonconnect.setStyleSheet("background-color: green")

        except Exception as e:
            self.buttonconnect.setStyleSheet("background-color: red")
            self.alerts.escribirAlerta("Error. Error al conectar PLC: " + str(e))

        try:
            self.camera.initialize()
            self.camera.connect_camera()

            time.sleep(2)
            if self.camera.is_connected():
                self.timer.timeout.connect(self.update_frame)
                self.timer.start(30)
                self.zoom = self.camera.zoom_position()
                #print(self.zoom)
                #print(self.camera.zoom_position_minimum(), "-", self.camera.zoom_position_maximum())

                self.alerts.escribirAlerta("Conectado a cámara.")

        except Exception as e:
            self.buttonconnect.setStyleSheet("background-color: red")
            self.alerts.escribirAlerta("Error. Error al conectar camara: " + str(e))



    def load_image(self):
        if self.connected:
            self.figure.savefig(self.nombre1)
            self.figure2.savefig(self.nombre2)
            self.alerts.escribirAlerta("Imágenes guardadas. ✓")

        else:
            self.alerts.escribirAlerta("Error. PLC no conectado.")


    def nuevo_caso(self):
        indice = self.tablaCasos.rowCount()
        self.tablaCasos.insertRow(indice)
        self.tablaCasos.setRowHeight(indice, 80)

    def guardar_caso(self):
        if self.confirm:
            try:
                datos_tabla = []
                for fila in range(self.tablaCasos.rowCount()):
                    fila_datos = {}
                    for columna in range(self.tablaCasos.columnCount()):
                        item = self.tablaCasos.item(fila, columna)
                        # Verificar si el item no está vacío o nulo
                        if item is not None:
                            encabezado = self.tablaCasos.horizontalHeaderItem(columna).text()

                            match columna:
                                case 0:
                                    fila_datos[encabezado] = item.text()
                                case 1:
                                    fila_datos[encabezado] = float(item.text())
                                case 2:
                                    fila_datos[encabezado] = float(item.text())
                                case 3:
                                    fila_datos[encabezado] = float(item.text())
                                case 4:
                                    fila_datos[encabezado] = int(item.text())
                                case 5:
                                    fila_datos[encabezado] = item.text()
                                case 6:
                                    fila_datos[encabezado] = float(item.text())
                                case 7:
                                    fila_datos[encabezado] = float(item.text())

                                case 9:
                                    fila_datos[encabezado] = int(item.text())
                                case 10:
                                    fila_datos[encabezado] = item.text()
                        else:
                            fila_datos[self.tablaCasos.horizontalHeaderItem(columna).text()] = ""
                    datos_tabla.append(fila_datos)


                if len(datos_tabla) == len(self.cases):
                    for i in range(len(datos_tabla)):
                        if datos_tabla[i] == self.cases[i]:
                            pass
                        else:
                            iden = datos_tabla[i].get("id")
                            self.api.update_case(iden, datos_tabla[i])

                elif len(datos_tabla) > len(self.cases):
                    index = len(datos_tabla) - len(self.cases)
                    total = self.tablaCasos.rowCount() - index

                    for i in range(len(self.cases)):
                        if datos_tabla[i] == self.cases[i]:
                            pass
                        else:
                            iden = datos_tabla[i].get("id")
                            self.api.update_case(iden, datos_tabla[i])

                    for i in range(index):
                        self.api.create_case(datos_tabla[i + total])

                self.confirm = False
                self.alerts2.escribirAlerta("Casos actualizados en la base de datos.")

            except Exception as e:
                self.alerts2.escribirAlerta("Error. Error al guardar: " + str(e))


    def updatesamp(self, text):  # Funciones para comportamiento de botones y conexión a PLC
        if text != "":
            try:
                num = text
                self.texto = int(num)
            except Exception:
                self.alerts.escribirAlerta("Error. En este campo solo puede ingresar números enteros.")
                self.samplesEdit.setText("")

    def setParams(self):
        if self.connected:
            try:

                num = self.texto
                self.write_int(db_number=12, byte_offset=0, value=num)

                tiempo = float(self.caso.get("Tiempo"))
                #self.write_real(db_number=, byte_offset=0, value=tiempo) # Enviar tiempo de soldadura
                self.alerts.escribirAlerta("Parametros configurados ✓")

            except Exception as e:
                self.alerts.escribirAlerta("Error. Error al enviar datos: " + str(e))
        else:
            self.alerts.escribirAlerta("Error. PLC no conectado.")

    def actualizar_nombre(self):  # Función para actualizar nombre de gráfica a guardar
        self.index = int(self.index)
        self.index = self.index + 1
        self.index = str(self.index)

        ahora = datetime.now()

        self.fecha_formateada = ahora.strftime("%d-%m-%Y-%H-%M-%S")

        self.identif = str(self.index) + "-" + self.fecha_formateada

        PLOTS_DIR.mkdir(parents=True, exist_ok=True)

        self.nombre1 = str(PLOTS_DIR / ("grafica_F_" + self.identif + ".png"))
        self.nombre2 = str(PLOTS_DIR / ("grafica_I_" + self.identif + ".png"))

    def temporizador(self, segundos):
        while segundos > 0:
            signal = self.read_bool() #Señal de terminación de ciclo
            if signal:
                break
            time.sleep(1)
            segundos -= 1

    def iniciar_PLC(self):
        if self.connected:
            try:
                self.show_plot()
                self.write_bool(db=5, byte_offset=12, bit=0, value= 1) #Señal de activación de ciclo
                time.sleep(1)
                self.write_bool(db=5, byte_offset=12, bit=0, value= 0)

                self.temporizador(segundos= 40)

                signal = self.read_bool() # Señal de terminación de ciclo
                if signal:
                    self.show_plot()
                    self.escribirAlerta("Ciclo completo")

                else:
                    self.escribirAlerta("Error. Error en el ciclo de soldadura")

            except Exception as e:
                self.alerts.escribirAlerta("Error. Error al iniciar: " + str(e))

        else:
            self.alerts.escribirAlerta("Error. PLC no conectado.")


    def show_plot(self):

        if self.connected:
            try:
                self.max = 0
                self.maxcurr = 0
                num = self.texto

                self.figure.clear()
                self.figure2.clear()


                self.time_array = self.read_dword_array(db_number=13, start_byte=0, count=num)
                self.force_array = self.read_real_array(db_number=1, start_byte=0, count=num)
                self.current_array = self.read_real_array(db_number=15, start_byte=0, count=num)

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
                ax.plot(self.time_array, self.force_array, marker="o", color="#51F564")
                ax.set_title(
                    f"Fuerza vs tiempo\n"
                    f"Tiempo de soldadura: {self.tSoldadura} ms | "
                    f"N. de muestras: {self.texto} | "
                    f"F máxima: {self.max} N \n"
                    f"Fecha: {self.fecha_formateada}"
                    , fontweight='bold', fontsize=6, color = '#dddcde'
                )

                #ax.legend()
                style_axis(ax, "", "")
                self.canvas.draw()  # Refresca el lienzo

                ax2 = self.figure2.add_subplot(111)
                ax2.clear()
                ax2.plot(self.time_array, self.current_array, marker="o", color="#FA4141")
                ax2.set_title(
                    f"Corriente vs tiempo\n"
                    f"Tiempo de soldadura: {self.tSoldadura} ms | "
                    f"N. de muestras: {self.texto} | "
                    f"I máxima: {self.maxcurr} A \n"
                    f"Fecha: {self.fecha_formateada}"
                    , fontweight='bold', fontsize=6, color = '#dddcde'
                )
                #ax2.legend()
                style_axis(ax2, "", "")
                self.canvas2.draw()  # Refresca el lienzo

                self.alerts.escribirAlerta("Datos obtenidos correctamente ✓")
                self.alerts.escribirAlerta(f"Número de identificación: {self.identif}")

                # print("Datos de fuerza:", self.force_array)
                # print("Datos de tiempo:", self.time_array)
                # print("Datos de corriente:", self.current_array)


            except Exception as e:
                self.alerts.escribirAlerta("Error. Error al solicitar datos: " + str(e))

        else:
            self.alerts.escribirAlerta("Error. Tarjeta de adquisición de datos no conectada.")


    def mostrar_confirmacion(self):
        # Crear la ventana de confirmación
        respuesta = QMessageBox.question(
            self,
            'Confirmar acción', # Título
            '¿Estás seguro de que deseas realizar esta acción?', # Mensaje
            QMessageBox.Yes | QMessageBox.No, # Botones
            QMessageBox.No # Botón por defecto
        )

        # Evaluar la respuesta del usuario
        if respuesta == QMessageBox.Yes:
            self.confirm = True
            # self.accept() # Útil si la ventana es un QDialog
        else:
            self.confirm = False



    def closeEvent(self, event):

        reply = QMessageBox.question(self, 'Salir',
                                     '¿Estás seguro de que quieres salir?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.timer.stop()
            self.camera.disconnect_camera()
            self.camera.shutdown()

            if self.ser is not None and self.ser.is_open:
                self.ser.close()
            if self.plc.connected:
                self.plc.disconnect()

            event.accept()  # Cierra la ventana

        else:
            event.ignore()  # Cancela el cierre de la ventana


def main():
    app = QApplication(sys.argv)
    window = HMI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
