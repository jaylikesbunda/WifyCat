import subprocess
import sys
import os

def main():
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller', 'pillow'])
    from PIL import Image
    png_path = os.path.join(os.path.dirname(__file__), 'wifycat.png')
    ico_path = os.path.join(os.path.dirname(__file__), 'wifycat.ico')
    Image.open(png_path).save(ico_path, format='ICO')
    subprocess.check_call([
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--add-data', 'wifycat.png;.',
        '--icon', ico_path,
        'wifycat.py'
    ])

if __name__ == '__main__':
    main()