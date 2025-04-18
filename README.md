# WifyCat - Hashcat GUI

A Hashcat GUI with a user-friendly interface.

![image](https://github.com/user-attachments/assets/32eaadea-1536-446e-8b32-b28cb54e1ff8)


### Requirements

- Python 3.7 or newer
- PySide6
- requests
- pillow (for icon conversion when bundling)
- Windows 10 or newer (right now)

Install dependencies:

```bash
pip install PySide6 requests pillow
```

### Running from source

```bash
python wifycat.py
```

### Building a standalone executable

Use the provided build script to install PyInstaller, generate the icon, and bundle the application:

```bash
python build.py
```

The built executable will be in the `dist/` folder as `wifycat.exe`, complete with the application icon.

