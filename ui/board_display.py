import tkinter as tk
import chess
from config import BOARD_SQUARE_SIZE, BOARD_COLORS, PIECE_SYMBOLS

class BoardDisplay:
    
    def __init__(self, parent):
        self.canvas = tk.Canvas(parent, width=400, height=400, bg="white")
        self.canvas.pack(pady=5)
        
        self.no_game_label = None
        self.board = chess.Board() 
    
    def draw_board(self, board=None):
        if board:
            self.board = board
            
        self.canvas.delete("all")
        
        square_size = BOARD_SQUARE_SIZE
        colors = BOARD_COLORS
        
        for row in range(8):
            for col in range(8):
                color_idx = (row + col) % 2
                x1, y1 = col * square_size, row * square_size
                x2, y2 = x1 + square_size, y1 + square_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=colors[color_idx], outline="")
                
                if col == 0:  
                    self.canvas.create_text(
                        x1 + 5, y1 + square_size/2, 
                        text=str(8-row), anchor=tk.W, fill="#000000" if color_idx == 0 else "#ffffff"
                    )
                
                if row == 7:  
                    self.canvas.create_text(
                        x1 + square_size/2, y2 - 10, 
                        text=chr(97 + col), anchor=tk.S, fill="#000000" if color_idx == 0 else "#ffffff"
                    )
        
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                col = chess.square_file(square)
                row = 7 - chess.square_rank(square) 
                x = col * square_size + square_size/2
                y = row * square_size + square_size/2
                
                color = "black" if piece.color == chess.BLACK else "white"
                symbol = PIECE_SYMBOLS[piece.symbol()]
                
                self.canvas.create_text(x, y, text=symbol, font=("Arial", 30), fill=color)
    
    def show_no_game_message(self):
        if not self.no_game_label:
            self.no_game_label = tk.Label(
                self.canvas,
                text="No active game found\nStart a game on Lichess to see analysis",
                font=("Arial", 12, "bold"),
                bg="white",
                fg="blue"
            )
            self.canvas.create_window(200, 200, window=self.no_game_label, tags="message")
    
    def hide_no_game_message(self):
        self.canvas.delete("message")
        if self.no_game_label:
            self.no_game_label = None