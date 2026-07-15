# HMI packaging

The PyInstaller executable is Linux-specific and architecture-specific. A binary built on an x86_64 PC runs on compatible x86_64 Linux systems; it will not run on ARM/aarch64 systems such as NVIDIA Jetson Orin AGX.

## Build for the current machine

```bash
./packaging/build_hmi.sh
```

The script creates `dist/HMI_python` and also copies it to an architecture-labeled name such as:

- `dist/HMI_python_linux_x86_64` for regular 64-bit PCs
- `dist/HMI_python_linux_aarch64` for Jetson/ARM64 systems

## Jetson Orin AGX

Build directly on the Jetson, or inside an aarch64 Jetson-compatible container. PyInstaller does not produce a reliable ARM executable from an x86_64 host.

Recommended Jetson steps:

```bash
sudo apt update
sudo apt install -y python3 python3-pip libxcb-cursor0 libxkbcommon-x11-0
./packaging/build_hmi.sh
```

Copy the resulting `dist/HMI_python_linux_aarch64` to other Jetson devices with a similar JetPack/Ubuntu version.

## Runtime notes

The executable still depends on the target system architecture, glibc/Ubuntu compatibility, Qt display libraries, serial permissions, PLC/network access, and the configured backend URL in `src/HMI/hmi/config.py`.
