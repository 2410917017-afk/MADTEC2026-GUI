from pathlib import Path


BASE_URL = "http://192.168.2.199:8000"
PLC_HOST = "192.168.0.1"
PLC_RACK = 0
PLC_SLOT = 1
SERIAL_PORT = "/dev/ttyUSB0"
SERIAL_BAUDRATE = 9600
HTTP_TIMEOUT_SECONDS = 5

HMI_ROOT = Path(__file__).resolve().parents[1]
PLOTS_DIR = HMI_ROOT / "Plots"
