import tkinter as tk
from tkinter import ttk, font, messagebox
import chess
import threading

from config import DEFAULT_DEPTH, DEFAULT_TIME
from .board_display import BoardDisplay
from .analysis_display import AnalysisDisplay

class MainWindow:
    
    def __init__(self, position_analyzer, lichess_connector):
        self.position_analyzer = position_analyzer
        self.lichess_connector = lichess_connector
        
        self.lichess_connector.on_status_change = self.update_lichess_status
        self.lichess_connector.on_board_update = self.on_board_update
        self.lichess_connector.on_game_state_change = self.on_game_state_change
        
        self.root = tk.Tk()
        self.root.title("Chess Assistant")
        self.root.geometry("650x850") 
        
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"+{screen_width - 700}+50")
        
        self.title_font = font.Font(family="Arial", size=14, weight="bold")
        self.large_font = font.Font(family="Arial", size=12)
        self.normal_font = font.Font(family="Arial", size=10)
        
        self.setup_ui()
        
        self.status_label.config(text="Initializing Stockfish engine...")
        self.root.update()
        
        self.init_engine_thread = threading.Thread(target=self.initialize_engine)
        self.init_engine_thread.daemon = True
        self.init_engine_thread.start()
        
        self.lichess_connector.start_connection()
        
        self.root.mainloop()
    
    def setup_ui(self):
        self.status_label = tk.Label(self.root, text="Initializing...", fg="blue", font=self.large_font)
        self.status_label.pack(pady=5)
        
        self.setup_lichess_frame()
        
        
        ttk.Separator(self.root, orient='horizontal').pack(fill=tk.X, pady=10)
        
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        board_frame = tk.Frame(main_frame)
        board_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(board_frame, text="Current Position:", font=self.normal_font).pack(anchor=tk.W)
        
        self.board_display = BoardDisplay(board_frame)
        
        analysis_frame = tk.Frame(main_frame)
        analysis_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        self.analysis_display = AnalysisDisplay(analysis_frame)
        
        
        self.board = chess.Board()
        self.board_display.draw_board(self.board)
        
        if not self.lichess_connector.game_active:
            self.analysis_display.set_move("No active game")
            self.board_display.show_no_game_message()
            
        self.depth_var = tk.IntVar(value=DEFAULT_DEPTH)
        self.time_var = tk.DoubleVar(value=DEFAULT_TIME)
        self.turn_var = tk.StringVar(value="White")
        self.auto_analyze_var = tk.BooleanVar(value=True)
    
    def setup_lichess_frame(self):
        lichess_frame = tk.LabelFrame(self.root, text="Lichess Connection", font=self.normal_font, padx=5, pady=5)
        lichess_frame.pack(pady=5, fill=tk.X, padx=10)
        
        self.lichess_status_label = tk.Label(lichess_frame, text="Status: Not connected", font=self.normal_font)
        self.lichess_status_label.pack(side=tk.LEFT, padx=5)
        
    
    def setup_fen_frame(self):
        pass
    
    def setup_controls_frame(self):
        pass
    
    def initialize_engine(self):
        success = self.position_analyzer.initialize_engine()
        if success:
            self.root.after(0, lambda: self.status_label.config(text="Stockfish engine initialized successfully"))
            self.root.after(500, self.analyze_current_position)
        else:
            self.root.after(0, lambda: self.status_label.config(text="Failed to initialize Stockfish engine"))
    
    def restart_stockfish(self):
        self.status_label.config(text="Restarting engine...")
        
        success = self.position_analyzer.restart_engine()
        if success:
            self.status_label.config(text="Stockfish engine restarted successfully")
        else:
            self.status_label.config(text="Failed to restart Stockfish engine")
    
    def analyze_current_position(self):
        # Simplified analysis function without FEN entry field
        self.board_display.draw_board(self.board)
        
        self.position_analyzer.set_analysis_params(
            depth=self.depth_var.get(),
            time_limit=self.time_var.get()
        )
        
        def on_move_found(move_san):
            self.analysis_display.set_move(f"Suggested Move: {move_san}")
        
        def on_analysis_complete(basic, detailed):
            self.analysis_display.set_basic_analysis(basic)
            self.analysis_display.set_detailed_analysis(detailed)
        
        self.analysis_display.set_move("Analyzing...", "#CC7700")
        self.status_label.config(text="Analyzing position...")
        
        basic, detailed = self.position_analyzer.analyze_position(
            self.board,
            on_move_found=on_move_found,
            on_analysis_complete=on_analysis_complete
        )
    
    def update_lichess_status(self, status_text):
        self.lichess_status_label.config(text=f"Status: {status_text}")
        self.status_label.config(text=status_text)
    
    def start_lichess_connection(self):
        if self.lichess_connector.start_connection():
            pass  # Button references removed
    
    def stop_lichess_connection(self):
        if self.lichess_connector.stop_connection():
            pass  # Button references removed
    
    def on_board_update(self, fen, is_my_turn):
        if fen:
            try:
                self.board = chess.Board(fen)
                self.board_display.draw_board(self.board)
                
                if is_my_turn:
                    self.status_label.config(text="Position updated from Lichess - It's your turn!")
                    # Always analyze since we removed the checkbox
                    self.analyze_current_position()
                else:
                    self.status_label.config(text="Position updated from Lichess - Waiting for opponent's move")
            except ValueError as e:
                self.status_label.config(text=f"Invalid FEN from Lichess: {e}")
                print(f"Invalid FEN: {e}")
    
    def on_game_state_change(self, is_active, game_id=None):
        if is_active and game_id:
            self.lichess_status_label.config(text=f"Status: Active game - {game_id}")
            self.board_display.hide_no_game_message()
            self.analysis_display.set_move("Waiting for your turn...")
        else:
            self.lichess_status_label.config(text="Status: Connected to Lichess - No active game")
            self.analysis_display.clear_analysis()
            
            self.board = chess.Board()
            self.board_display.draw_board(self.board)
            self.board_display.show_no_game_message()
    
    def __del__(self):
        if hasattr(self, 'position_analyzer'):
            self.position_analyzer.quit()
    
        if hasattr(self, 'lichess_connector'):
            self.lichess_connector.stop_connection()