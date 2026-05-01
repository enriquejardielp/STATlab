"""
STATlab - Punto de entrada principal.
Framework: PyQt6
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from app import MainWindow

if __name__ == "__main__":
    # Forzar modo claro profesional
    os.environ["QT_QPA_PLATFORM"] = "cocoa"
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
