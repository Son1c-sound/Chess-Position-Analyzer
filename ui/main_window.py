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
        
        self.setup_fen_frame()
        
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
        
        self.setup_controls_frame()
        
        self.board = chess.Board()
        self.board_display.draw_board(self.board)
        
        if not self.lichess_connector.game_active:
            self.analysis_display.set_move("No active game")
            self.board_display.show_no_game_message()
    
    def setup_lichess_frame(self):
        lichess_frame = tk.LabelFrame(self.root, text="Lichess Connection", font=self.normal_font, padx=5, pady=5)
        lichess_frame.pack(pady=5, fill=tk.X, padx=10)
        
        self.lichess_status_label = tk.Label(lichess_frame, text="Status: Not connected", font=self.normal_font)
        self.lichess_status_label.pack(side=tk.LEFT, padx=5)
        
        self.lichess_connect_button = tk.Button(lichess_frame, text="Connect to Lichess", 
                                               command=self.start_lichess_connection, 
                                               font=self.normal_font, bg="#90ee90")
        self.lichess_connect_button.pack(side=tk.RIGHT, padx=5)
        
        self.lichess_disconnect_button = tk.Button(lichess_frame, text="Disconnect", 
                                                 command=self.stop_lichess_connection, 
                                                 font=self.normal_font, bg="#f0c0c0", state=tk.DISABLED)
        self.lichess_disconnect_button.pack(side=tk.RIGHT, padx=5)
    
    def setup_fen_frame(self):
        fen_frame = tk.Frame(self.root)
        fen_frame.pack(pady=10, fill=tk.X, padx=10)
        
        tk.Label(fen_frame, text="FEN String:", font=self.normal_font).pack(anchor=tk.W)
        
        self.fen_entry = tk.Entry(fen_frame, width=50, font=self.normal_font)
        self.fen_entry.pack(fill=tk.X, pady=5)
        self.fen_entry.insert(0, chess.Board().fen())  # Default starting position
        
        button_frame = tk.Frame(fen_frame)
        button_frame.pack(fill=tk.X)
        
        tk.Button(button_frame, text="Starting Position", command=self.set_starting_position, 
                  font=self.normal_font, bg="#e0e0e0").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Load FEN", command=self.load_fen, 
                  font=self.normal_font, bg="#e0e0e0").pack(side=tk.LEFT, padx=5)
        
        self.restart_button = tk.Button(button_frame, text="Restart Stockfish", command=self.restart_stockfish, 
                                        font=self.normal_font, bg="#f0c0c0")
        self.restart_button.pack(side=tk.RIGHT, padx=5)
        
        self.fen_entry.bind("<Return>", lambda e: self.on_fen_change())
    
    def setup_controls_frame(self):
        controls_frame = tk.Frame(self.root)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        settings_frame = tk.LabelFrame(controls_frame, text="Analysis Settings", font=self.normal_font, padx=5, pady=5)
        settings_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        depth_frame = tk.Frame(settings_frame)
        depth_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(depth_frame, text="Depth:", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        
        self.depth_var = tk.IntVar(value=DEFAULT_DEPTH)
        depth_spinner = tk.Spinbox(depth_frame, from_=5, to=30, width=5, textvariable=self.depth_var, font=self.normal_font)
        depth_spinner.pack(side=tk.LEFT, padx=5)
        
        tk.Label(depth_frame, text="Time (sec):", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        
        self.time_var = tk.DoubleVar(value=DEFAULT_TIME)
        time_spinner = tk.Spinbox(depth_frame, from_=0.1, to=10, increment=0.1, width=5, textvariable=self.time_var, font=self.normal_font)
        time_spinner.pack(side=tk.LEFT, padx=5)
        
        self.turn_var = tk.StringVar(value="White")
        turn_frame = tk.Frame(settings_frame)
        turn_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(turn_frame, text="Turn:", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(turn_frame, text="White", variable=self.turn_var, value="White", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(turn_frame, text="Black", variable=self.turn_var, value="Black", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        
        button_frame = tk.Frame(controls_frame)
        button_frame.pack(side=tk.RIGHT, padx=10)
        
        self.analyze_button = tk.Button(button_frame, text="Analyze Position", command=self.analyze_current_position, 
                                       font=self.large_font, bg="#90ee90", padx=10, pady=5)
        self.analyze_button.pack(pady=5)
        
        self.auto_analyze_var = tk.BooleanVar(value=True)
        auto_analyze_check = tk.Checkbutton(button_frame, text="Auto-analyze on FEN change", 
                                           variable=self.auto_analyze_var, font=self.normal_font)
        auto_analyze_check.pack(anchor=tk.W)
    
    def initialize_engine(self):
        success = self.position_analyzer.initialize_engine()
        if success:
            self.root.after(0, lambda: self.status_label.config(text="Stockfish engine initialized successfully"))
            self.root.after(500, self.analyze_current_position)
        else:
            self.root.after(0, lambda: self.status_label.config(text="Failed to initialize Stockfish engine"))
    
    def on_fen_change(self):
        self.load_fen()
        if self.auto_analyze_var.get():
            self.analyze_current_position()
    
    def set_starting_position(self):
        self.board = chess.Board()
        self.fen_entry.delete(0, tk.END)
        self.fen_entry.insert(0, self.board.fen())
        self.board_display.draw_board(self.board)
        self.status_label.config(text="Board reset to starting position")
        
        if self.auto_analyze_var.get():
            self.analyze_current_position()
    
    def load_fen(self):
        try:
            fen = self.fen_entry.get()
            fen_parts = fen.split()
            if len(fen_parts) < 2:
                turn = "w" if self.turn_var.get() == "White" else "b"
                fen = f"{fen} {turn} - - 0 1"
            
            self.board = chess.Board(fen)
            self.board_display.draw_board(self.board)
            self.status_label.config(text="FEN loaded successfully")
            return True
        except ValueError as e:
            self.status_label.config(text=f"Invalid FEN: {e}")
            print(f"Invalid FEN: {e}")
            return False
    
    def restart_stockfish(self):
        self.status_label.config(text="Restarting engine...")
        
        success = self.position_analyzer.restart_engine()
        if success:
            self.status_label.config(text="Stockfish engine restarted successfully")
        else:
            self.status_label.config(text="Failed to restart Stockfish engine")
    
    def analyze_current_position(self):
        current_fen = self.fen_entry.get().split()[0] 
        board_fen = self.board.board_fen()
        
        if current_fen != board_fen:
            self.load_fen()
        
        if len(self.fen_entry.get().split()) < 2:
            turn = chess.WHITE if self.turn_var.get() == "White" else chess.BLACK
            self.board.turn = turn
        
        self.fen_entry.delete(0, tk.END)
        self.fen_entry.insert(0, self.board.fen())
        
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
            self.lichess_connect_button.config(state=tk.DISABLED)
            self.lichess_disconnect_button.config(state=tk.NORMAL)
    
    def stop_lichess_connection(self):
        if self.lichess_connector.stop_connection():
            self.lichess_connect_button.config(state=tk.NORMAL)
            self.lichess_disconnect_button.config(state=tk.DISABLED)
    
    def on_board_update(self, fen, is_my_turn):
        if fen:
            self.fen_entry.delete(0, tk.END)
            self.fen_entry.insert(0, fen)
            
            self.load_fen()
            
            if is_my_turn:
                self.status_label.config(text="Position updated from Lichess - It's your turn!")
                if self.auto_analyze_var.get():
                    self.analyze_current_position()
            else:
                self.status_label.config(text="Position updated from Lichess - Waiting for opponent's move")
    
    def on_game_state_change(self, is_active, game_id=None):
        if is_active and game_id:
            self.lichess_status_label.config(text=f"Status: Active game - {game_id}")
            self.board_display.hide_no_game_message()
            self.analysis_display.set_move("Waiting for your turn...")
            self.analyze_button.config(state=tk.NORMAL)
        else:
            self.lichess_status_label.config(text="Status: Connected to Lichess - No active game")
            self.analysis_display.clear_analysis()
            
            self.board = chess.Board()
            self.board_display.draw_board(self.board)
            self.fen_entry.delete(0, tk.END)
            self.fen_entry.insert(0, self.board.fen())
            self.board_display.show_no_game_message()
    
    def __del__(self):
        if hasattr(self, 'position_analyzer'):
            self.position_analyzer.quit()
    
        if hasattr(self, 'lichess_connector'):
            self.lichess_connector.stop_connection()