import os
import sys
import tkinter as tk
import chess

from ui.main_window import MainWindow
from analysis.position_analyzer import PositionAnalyzer
from lichess_connector import LichessConnector
from config import STOCKFISH_PATH


def check_dependencies():
    if not os.path.exists(STOCKFISH_PATH):
        print(f"Error: Could not find Stockfish at {os.path.abspath(STOCKFISH_PATH)}")
        print("Please make sure the path points to the stockfish.exe file")
        return False
    
    try:
        import chess
        import chess.engine
        import requests
        import PIL
        import PIL.Image
        import PIL.ImageTk
    except ImportError as e:
        print(f"Error: Missing required Python library - {e}")
        print("Please install all required dependencies using:")
        print("pip install python-chess requests pillow")
        return False
    
    return True


def main():
    if not check_dependencies():
        sys.exit(1)
    
    position_analyzer = PositionAnalyzer()
    lichess_connector = LichessConnector()
    
    main_window = MainWindow(position_analyzer, lichess_connector)


if __name__ == "__main__":
    main()