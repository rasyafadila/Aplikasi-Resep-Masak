# main.py (di dalam folder CookEasy, BUKAN di dalam modules!)

import os
import sys

# Tambahkan folder utama ke sys.path agar bisa import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Sekarang baru import
from modules.app_ui import ResepApp
import customtkinter as ctk

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

if __name__ == "__main__":
    app = ResepApp()
    app.mainloop()