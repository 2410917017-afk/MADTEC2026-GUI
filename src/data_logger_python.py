import sys
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import snap7
from snap7.types import Areas
from snap7.util import get_int, get_real, get_bool, set_int, set_bool
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QLineEdit
)
from PyQt6.QtGui import  QFont




class HMI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PLC Plotter")
        self.setFixedSize(900, 500)
        self.setStyleSheet("background-color: #001b1b")

        main_layout = QGridLayout(self)

        self.plc = snap7.client.Client()
        self.connected = False
        self.texto = 0

        self.figure = Figure(figsize=(5, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        

        self.buttonstart = QPushButton("Start")
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
        self.buttonstart.clicked.connect(self.showplot)
        
        self.buttonsamples = QPushButton("Set samples")
        self.buttonsamples.setFont(QFont("Arial", 28))
        self.buttonsamples.setFixedSize(230, 70)
        self.buttonsamples.setStyleSheet("""
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
        self.buttonsamples.clicked.connect(self.sendSamples)

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
        
        self.samplesEdit = QLineEdit()
        self.samplesEdit.setPlaceholderText("N. of samples...")
        self.samplesEdit.setFont(QFont("Arial", 18))
        self.samplesEdit.setFixedSize(150, 60)
        self.samplesEdit.setStyleSheet("color: ghostwhite")

    
        main_layout.addWidget(self.buttonstart, 1, 0)
        main_layout.addWidget(self.buttonsamples, 1, 2)
        main_layout.addWidget(self.buttonconnect, 1, 1)
        main_layout.addWidget(self.samplesEdit, 1, 3)
        main_layout.addWidget(self.canvas, 0,  0, 1, 4)


    def read_int_array(self, db_number, start_byte, count):

        size_bytes = count * 2
        data = self.plc.read_area(Areas.DB, db_number, start_byte, size_bytes)
        ints = [get_int(data, i * 2) for i in range(count)]
        return ints


    def write_int(self, db_number, byte_offset, value: int):
        data = bytearray(2)
        set_int(data, 0, value)
        self.plc.db_write(db_number, byte_offset, data)


    def read_real_array(self, db_number, start_byte, count):

        size_bytes = count * 4
        data = self.plc.read_area(Areas.DB, db_number, start_byte, size_bytes)
        reals = [get_real(data, i * 4) for i in range(count)]
        return reals


    def read_bool(self, db_number, byte_offset, bit):

        data = self.plc.db_read(db_number, byte_offset, 1)
        data = get_bool(data, 0, bit)
        return data


    def write_bool(self, db, byte_offset, bit, value: bool):
        data = self.plc.db_read(db, byte_offset, 1)
        set_bool(data, 0, bit, value)
        self.plc.db_write(db, byte_offset, data)


    def connectPLC(self):
        try:
            self.plc.connect("192.168.0.1", rack=0, slot=1)
            self.connected = True

            if not self.plc.get_connected():
                raise ConnectionError("No se pudo conectar al PLC.")
        
        except Exception as e:
            print(f"Error: {e}")

    def sendSamples(self):

        if self.connected:
            try:

                numero = self.samplesEdit.text
                self.texto = int(numero)
                self.write_int(db_number=2, byte_offset=0, value=self.texto)

            except Exception as e:
                print(f"Error: {e}")
        
    def showplot(self):

        if self.connected:
            try:

                #int_array = self.read_int_array(plc, db_number=1, start_byte=0, count=20)
                real_array = self.read_real_array(db_number=1, start_byte=0, count=5)

                #x = int_array
                y = real_array

                #ax = self.figure.add_subplot(111)
                #ax.clear()  # Limpia la gráfica anterior
                #ax.plot(x, y, marker="o", color="blue", label="y = x²")
                #ax.set_title("Ejemplo de gráfica")
                #ax.set_xlabel("Tiempo")
                #ax.set_ylabel("Fuerza")
                #ax.legend()
                #self.canvas.draw()  # Refresca el lienzo

                print("Datos leídos del PLC:", y)


            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HMI()
    window.show()
    #self.plc.disconnect() 
    sys.exit(app.exec())