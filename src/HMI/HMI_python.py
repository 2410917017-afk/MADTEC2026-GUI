import sys

from PyQt5.QtWidgets import QApplication

from hmi.app import HMI


def main():
    app = QApplication(sys.argv)
    window = HMI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
