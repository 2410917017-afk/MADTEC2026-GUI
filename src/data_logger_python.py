import sys,  numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import snap7
from snap7 import Area
from snap7.util import get_int, get_real
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton
)
from PyQt6.QtGui import  QFont


plc = snap7.client.Client()


class HMI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PLC Plotter")
        self.setFixedSize(900, 500)
        self.setStyleSheet("background-color: #001b1b")

        main_layout = QVBoxLayout(self)

        self.figure = Figure(figsize=(5, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas , )

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
    
        main_layout.addWidget(self.buttonstart)

    def read_int_array(self, client, db_number, start_byte, count):

        size_bytes = count * 2
        data = client.read_area(Area.DB, db_number, start_byte, size_bytes)
        ints = [get_int(data, i * 2) for i in range(count)]
        return ints

    #def read_real_array(self, client, db_number, start_byte, count):

    #    size_bytes = count * 4
    #    data = client.read_area(Area.DB, db_number, start_byte, size_bytes)
    #    reals = [get_real(data, i * 4) for i in range(count)]
    #    return reals
        
    def showplot(self):

        try:
            
            plc.connect("192.168.0.1", rack=0, slot=1)

            if not plc.get_connected():
                raise ConnectionError("No se pudo conectar al PLC.")

            # Ejemplo: leer 3 arrays distintos desde DB1
            int_array = self.read_int_array(plc, db_number=1, start_byte=0, count=20)
            #real_array = self.read_real_array(plc, db_number=2, start_byte=0, count=11)

            x = int_array
            #y = real_array
            print("Datos leídos del PLC:", x)


        except Exception as e:
            print(f"Error: {e}")
        finally:
            plc.disconnect() 


        #ax = self.figure.add_subplot(111)
        #ax.clear()  # Limpia la gráfica anterior
        #ax.plot(x, y, marker="o", color="blue", label="y = x²")
        #ax.set_title("Ejemplo de gráfica")
        #ax.set_xlabel("Tiempo")
        #ax.set_ylabel("Fuerza")
        #ax.legend()
        #self.canvas.draw()  # Refresca el lienzo


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HMI()
    window.show()
    
    sys.exit(app.exec())