import chess
import chess.engine
import tkinter as tk
from tkinter import ttk, font, messagebox
from PIL import Image, ImageTk
import os
import threading
import time
import requests
import json

stockfish_path = r"C:\Users\makar\Desktop\stockfish\stockfish-windows-x86-64-avx2.exe"
lichess_server_url = "http://localhost:3000"
lichess_username = "soniconchess" 

class ChessAssistant:
    def __init__(self):
        self.no_game_label = None

        if not os.path.exists(stockfish_path):
            print(f"Error: Could not find Stockfish at {os.path.abspath(stockfish_path)}")
            print("Please make sure the path points to the stockfish.exe file")
            exit(1)
        else:
            print(f"Found Stockfish at {os.path.abspath(stockfish_path)}")
        
        self.board = chess.Board()
        self.lichess_connected = False
        self.lichess_game_active = False
        self.lichess_status = "Not connected"
        self.lichess_polling_thread = None
        self.polling_active = False
        self.username = lichess_username
        
        self.setup_ui()
        
        self.status_label.config(text="Initializing Stockfish engine...")
        self.root.update()
        
        self.init_engine_thread = threading.Thread(target=self.initialize_engine)
        self.init_engine_thread.daemon = True
        self.init_engine_thread.start()
        
        self.start_lichess_connection()
        
        self.root.mainloop()
    
    def initialize_engine(self):
        """Initialize Stockfish engine in a separate thread"""
        try:
            print(f"Attempting to initialize Stockfish at: {stockfish_path}")
            self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
            self.engine.configure({"Threads": 4, "Hash": 128})
            print("Stockfish engine initialized successfully")
            
            self.root.after(0, lambda: self.status_label.config(text="Stockfish engine initialized successfully"))
            self.root.after(500, self.analyze_current_position)
        except Exception as e:
            error_msg = f"Error initializing Stockfish: {e}"
            print(error_msg)
            
            self.root.after(0, lambda: self.status_label.config(text=error_msg))
    
    def setup_ui(self):
        """Setup the user interface"""
   
        self.root = tk.Tk()
        self.root.title("Chess Assistant")
        self.root.geometry("650x850")  # Made a bit taller for Lichess integration
        
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"+{screen_width - 700}+50")
        
        self.title_font = font.Font(family="Arial", size=14, weight="bold")
        self.large_font = font.Font(family="Arial", size=12)
        self.normal_font = font.Font(family="Arial", size=10)
        
        self.status_label = tk.Label(self.root, text="Initializing...", fg="blue", font=self.large_font)
        self.status_label.pack(pady=5)
        
        # Add Lichess status 
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
        
        fen_frame = tk.Frame(self.root)
        fen_frame.pack(pady=10, fill=tk.X, padx=10)
        
        tk.Label(fen_frame, text="FEN String:", font=self.normal_font).pack(anchor=tk.W)
        
        self.fen_entry = tk.Entry(fen_frame, width=50, font=self.normal_font)
        self.fen_entry.pack(fill=tk.X, pady=5)
        self.fen_entry.insert(0, self.board.fen())  # Default starting position
        
        button_frame = tk.Frame(fen_frame)
        button_frame.pack(fill=tk.X)
        
        tk.Button(button_frame, text="Starting Position", command=self.set_starting_position, 
                  font=self.normal_font, bg="#e0e0e0").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Load FEN", command=self.load_fen, 
                  font=self.normal_font, bg="#e0e0e0").pack(side=tk.LEFT, padx=5)
        
        self.restart_button = tk.Button(button_frame, text="Restart Stockfish", command=self.restart_stockfish, 
                                        font=self.normal_font, bg="#f0c0c0")
        self.restart_button.pack(side=tk.RIGHT, padx=5)
        
        ttk.Separator(self.root, orient='horizontal').pack(fill=tk.X, pady=10)
        
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        board_frame = tk.Frame(main_frame)
        board_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(board_frame, text="Current Position:", font=self.normal_font).pack(anchor=tk.W)
        
        self.board_canvas = tk.Canvas(board_frame, width=400, height=400, bg="white")
        self.board_canvas.pack(pady=5)
        
        analysis_frame = tk.Frame(main_frame)
        analysis_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        move_frame = tk.LabelFrame(analysis_frame, text="Best Move", font=self.large_font, padx=5, pady=5)
        move_frame.pack(fill=tk.X, pady=5)
        
        self.move_label = tk.Label(move_frame, text="Calculating...", font=("Arial", 16, "bold"), fg="#009900")
        self.move_label.pack(pady=5)
        
        self.eval_label = tk.Label(move_frame, text="", font=self.normal_font)
        self.eval_label.pack(pady=2)
        
        self.tab_control = ttk.Notebook(analysis_frame)
        
        basic_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(basic_tab, text="Basic Analysis")
        
        detailed_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(detailed_tab, text="Detailed Analysis")
        
        self.tab_control.pack(expand=1, fill=tk.BOTH, pady=10)
        
        self.explanation_text = tk.Text(basic_tab, height=16, width=50, font=self.normal_font, wrap=tk.WORD)
        self.explanation_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        explanation_scrollbar = tk.Scrollbar(basic_tab, command=self.explanation_text.yview)
        explanation_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.explanation_text.config(yscrollcommand=explanation_scrollbar.set)
        
        self.detailed_text = tk.Text(detailed_tab, height=16, width=50, font=self.normal_font, wrap=tk.WORD)
        self.detailed_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        detailed_scrollbar = tk.Scrollbar(detailed_tab, command=self.detailed_text.yview)
        detailed_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.detailed_text.config(yscrollcommand=detailed_scrollbar.set)
        
        controls_frame = tk.Frame(self.root)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        settings_frame = tk.LabelFrame(controls_frame, text="Analysis Settings", font=self.normal_font, padx=5, pady=5)
        settings_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        depth_frame = tk.Frame(settings_frame)
        depth_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(depth_frame, text="Depth:", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        
        self.depth_var = tk.IntVar(value=15)  # Default depth
        depth_spinner = tk.Spinbox(depth_frame, from_=5, to=30, width=5, textvariable=self.depth_var, font=self.normal_font)
        depth_spinner.pack(side=tk.LEFT, padx=5)
        
        tk.Label(depth_frame, text="Time (sec):", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        
        self.time_var = tk.DoubleVar(value=1.0)  # Default 1 second
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
        
        self.fen_entry.bind("<Return>", lambda e: self.on_fen_change())
       
        if not self.lichess_game_active:
            self.move_label.config(text="No active game")
            self.no_game_label = tk.Label(
                self.board_canvas,
                text="No active game found\nStart a game on Lichess to see analysis",
                font=self.large_font,
                bg="white",
                fg="blue"
            )
            self.board_canvas.create_window(200, 200, window=self.no_game_label, tags="message")
        self.draw_board()
    
    def on_fen_change(self):
        """Handle FEN changes and auto-analyze if enabled"""
        self.load_fen()
        if self.auto_analyze_var.get():
            self.analyze_current_position()
    
    def set_starting_position(self):
        """Set the board to the starting position"""
        self.board = chess.Board()
        self.fen_entry.delete(0, tk.END)
        self.fen_entry.insert(0, self.board.fen())
        self.draw_board()
        self.status_label.config(text="Board reset to starting position")
        
        if self.auto_analyze_var.get():
            self.analyze_current_position()
    
    def load_fen(self):
        """Load a board position from FEN string"""
        try:
            fen = self.fen_entry.get()
            fen_parts = fen.split()
            if len(fen_parts) < 2:
                turn = "w" if self.turn_var.get() == "White" else "b"
                fen = f"{fen} {turn} - - 0 1"
            
            self.board = chess.Board(fen)
            self.draw_board()
            self.status_label.config(text="FEN loaded successfully")
            return True
        except ValueError as e:
            self.status_label.config(text=f"Invalid FEN: {e}")
            print(f"Invalid FEN: {e}")
            return False
    
    def restart_stockfish(self):
        """Restart the Stockfish engine"""
        self.status_label.config(text="Restarting engine...")
        
        if hasattr(self, 'engine'):
            try:
                self.engine.quit()
            except:
                pass
        
        self.init_engine_thread = threading.Thread(target=self.initialize_engine)
        self.init_engine_thread.daemon = True
        self.init_engine_thread.start()
    
    def draw_board(self):
        """Draw the current board position on the canvas"""
        self.board_canvas.delete("all")
        
        square_size = 50
        colors = ["#f0d9b5", "#b58863"] 
        
        for row in range(8):
            for col in range(8):
                color_idx = (row + col) % 2
                x1, y1 = col * square_size, row * square_size
                x2, y2 = x1 + square_size, y1 + square_size
                self.board_canvas.create_rectangle(x1, y1, x2, y2, fill=colors[color_idx], outline="")
                
                if col == 0:  
                    self.board_canvas.create_text(
                        x1 + 5, y1 + square_size/2, 
                        text=str(8-row), anchor=tk.W, fill="#000000" if color_idx == 0 else "#ffffff"
                    )
                if row == 7:  
                    self.board_canvas.create_text(
                        x1 + square_size/2, y2 - 10, 
                        text=chr(97 + col), anchor=tk.S, fill="#000000" if color_idx == 0 else "#ffffff"
                    )
        
        piece_symbols = {
            'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
            'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
        }
        
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                col = chess.square_file(square)
                row = 7 - chess.square_rank(square) 
                x = col * square_size + square_size/2
                y = row * square_size + square_size/2
                
                color = "black" if piece.color == chess.BLACK else "white"
                symbol = piece_symbols[piece.symbol()]
                
                self.board_canvas.create_text(x, y, text=symbol, font=("Arial", 30), fill=color)
    
    def analyze_position(self, board):
        if not hasattr(self, 'engine'):
            self.status_label.config(text="Waiting for Stockfish to initialize...")
            return []
        
        if not any(board.piece_map()):
            self.status_label.config(text="No pieces detected on board.")
            return []
        
        try:
            print(f"Analyzing position: {board.fen()}")
            depth = self.depth_var.get()
            time_limit = self.time_var.get()
            
            self.move_label.config(text="Analyzing...", fg="#CC7700")
            self.root.update()
            
            result = self.engine.analyse(board, chess.engine.Limit(time=time_limit, depth=depth), multipv=3)
            self.status_label.config(text=f"Analysis complete (depth {depth}, {time_limit}s)")
            return result
        except chess.engine.EngineTerminatedError:
            self.status_label.config(text="Stockfish engine crashed. Restarting...")
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
                self.status_label.config(text="Stockfish engine restarted. Try analyzing again.")
            except Exception as e:
                self.status_label.config(text=f"Failed to restart Stockfish: {e}")
            return []
        except Exception as e:
            self.status_label.config(text=f"Analysis error: {e}")
            return []
    
    def generate_explanation(self, board, analysis):
        explanation = "Chess Assistant Analysis:\n\n"
        
        if not analysis:
            return "No analysis available. Try adjusting the analysis settings or check if Stockfish is initialized."
        
        top_move = analysis[0]["pv"][0]
        if analysis[0]["score"].is_mate():
            mate_in = analysis[0]["score"].relative.mate()
            score_text = f"Checkmate in {abs(mate_in)}"
            score = 10000 if mate_in > 0 else -10000  # Arbitrary large value for mate
        else:
            score = analysis[0]["score"].relative.score(mate_score=10000) / 100.0
            score_text = f"{score:.2f}"
        
        explanation += f"Best move: {board.san(top_move)}\n"
        
        if analysis[0]["score"].is_mate():
            explanation += f"Evaluation: {score_text} for {'you' if mate_in > 0 else 'opponent'}\n\n"
        else:
            if score > 3:
                status = "strongly winning for you"
            elif score > 1:
                status = "better for you"
            elif score > 0.3:
                status = "slightly better for you"
            elif score > -0.3:
                status = "roughly equal"
            elif score > -1:
                status = "slightly better for opponent"
            elif score > -3:
                status = "better for opponent"
            else:
                status = "strongly winning for opponent"
            
            explanation += f"Evaluation: {score:.2f} ({status})\n\n"
        
        moving_piece = board.piece_at(top_move.from_square)
        piece_name = self.get_piece_name(moving_piece)
        
        target_piece = board.piece_at(top_move.to_square)
        is_capture = target_piece is not None
        
        if is_capture:
            target_name = self.get_piece_name(target_piece)
            explanation += f"This move {piece_name} captures {target_name}.\n"
        else:
            explanation += f"This move improves the position of your {piece_name}.\n"
        
        from_square = chess.square_name(top_move.from_square)
        to_square = chess.square_name(top_move.to_square)
        explanation += f"Move details: {from_square} → {to_square}\n\n"
        
        if len(analysis) > 1:
            explanation += "Alternative moves:\n"
            for i in range(1, min(3, len(analysis))):
                alt_move = analysis[i]["pv"][0]
                
                if analysis[i]["score"].is_mate():
                    alt_mate_in = analysis[i]["score"].relative.mate()
                    alt_score = 10000 if alt_mate_in > 0 else -10000
                    alt_score_text = f"Mate in {abs(alt_mate_in)}"
                else:
                    alt_score = analysis[i]["score"].relative.score(mate_score=10000) / 100.0
                    alt_score_text = f"{alt_score:.2f}"
                
                diff = alt_score - score
                
                if abs(diff) < 0.2:
                    quality = "almost equally good"
                elif abs(diff) < 0.5:
                    quality = "slightly worse"
                elif abs(diff) < 1.0:
                    quality = "noticeably worse"
                else:
                    quality = "significantly worse"
            
                explanation += f"• {board.san(alt_move)} ({quality}, {alt_score_text})\n"
        
        explanation += "\n"
        
        explanation += "Chess principles to consider:\n"
        
        if board.is_check():
            explanation += "• You are in check! You must address this threat.\n"
        
        if board.is_checkmate():
            explanation += "• Checkmate! The game is over.\n"
        elif board.is_stalemate():
            explanation += "• Stalemate! The game is a draw.\n"
        
        material = sum(len(board.pieces(piece_type, color)) 
                        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]
                        for color in [chess.WHITE, chess.BLACK])
        
        if material > 28: 
            explanation += "• In the opening, focus on developing pieces and controlling the center.\n"
            explanation += "• Try to castle early to protect your king.\n"
            explanation += "• Avoid moving the same piece multiple times in the opening.\n"
        elif material > 15:  
            explanation += "• In the middlegame, look for tactical opportunities and strategic advantages.\n"
            explanation += "• Control open files with your rooks.\n"
            explanation += "• Look for ways to improve your worst-placed piece.\n"
        else:  
            explanation += "• In the endgame, activate your king and push pawns when safe.\n"
            explanation += "• Connected passed pawns are very strong in the endgame.\n"
            explanation += "• Trade pieces (but not pawns) when ahead in material.\n"
        
        return explanation
    
    def generate_detailed_analysis(self, board, analysis):
        """Generate detailed analysis information"""
        if not analysis:
            return "No analysis available."
        
        detailed = "Detailed Analysis:\n\n"
        
        for i, info in enumerate(analysis):
            move = info["pv"][0]
            san = board.san(move)
                
            prefix = "►" if i == 0 else " "
            
            if info["score"].is_mate():
                mate_in = info["score"].relative.mate()
                score_text = f"Mate in {abs(mate_in)}"
            else:
                score = info["score"].relative.score(mate_score=10000) / 100.0
                score_text = f"{score:.2f}"
            
            detailed += f"{prefix} {i+1}. {san} ({score_text})\n"
            
            if len(info["pv"]) > 1:
                test_board = board.copy()
                line = []
                move_num = test_board.fullmove_number
                is_white_to_move = test_board.turn == chess.WHITE
                
                for j, m in enumerate(info["pv"]):
                    try:
                        if j == 0:
                            test_board.push(m)
                            continue  
                        
                        if is_white_to_move:
                            line.append(f"{move_num}.")
                        
                        line.append(test_board.san(m))
                        test_board.push(m)
                        
                        if not is_white_to_move:
                            move_num += 1
                        is_white_to_move = not is_white_to_move
                        
                    except Exception as e:
                        print(f"Error in line processing: {e}")
                        break  # Stop if we encounter an invalid move
                
                if line:
                    detailed += f"   Line: {' '.join(line)}\n"
            
            detailed += "\n"
        
        detailed += "Position Assessment:\n"
        
        w_pawns = len(board.pieces(chess.PAWN, chess.WHITE))
        b_pawns = len(board.pieces(chess.PAWN, chess.BLACK))
        w_knights = len(board.pieces(chess.KNIGHT, chess.WHITE))
        b_knights = len(board.pieces(chess.KNIGHT, chess.BLACK))
        w_bishops = len(board.pieces(chess.BISHOP, chess.WHITE))
        b_bishops = len(board.pieces(chess.BISHOP, chess.BLACK))
        w_rooks = len(board.pieces(chess.ROOK, chess.WHITE))
        b_rooks = len(board.pieces(chess.ROOK, chess.BLACK))
        w_queens = len(board.pieces(chess.QUEEN, chess.WHITE))
        b_queens = len(board.pieces(chess.QUEEN, chess.BLACK))
        
        w_minor = w_knights + w_bishops
        b_minor = b_knights + b_bishops
        
        detailed += f"• Material breakdown:\n"
        detailed += f"  White: {w_queens}Q, {w_rooks}R, {w_bishops}B, {w_knights}N, {w_pawns}P\n"
        detailed += f"  Black: {b_queens}Q, {b_rooks}R, {b_bishops}B, {b_knights}N, {b_pawns}P\n"
        
        material_score = w_pawns - b_pawns + 3*(w_knights - b_knights) + 3*(w_bishops - b_bishops) + 5*(w_rooks - b_rooks) + 9*(w_queens - b_queens)
        
        detailed += f"• Material balance: {'White +' if material_score > 0 else 'Black +' if material_score < 0 else 'Equal'} {abs(material_score)}\n\n"
        
        w_king_square = board.king(chess.WHITE) if board.king(chess.WHITE) is not None else -1
        b_king_square = board.king(chess.BLACK) if board.king(chess.BLACK) is not None else -1
        
        if w_king_square != -1 and b_king_square != -1:
            w_king_attackers = len(board.attackers(chess.BLACK, w_king_square))
            b_king_attackers = len(board.attackers(chess.WHITE, b_king_square))
            
            w_king_danger = 0
            b_king_danger = 0
            
            for offset in [-9, -8, -7, -1, 1, 7, 8, 9]:
                if 0 <= w_king_square + offset < 64:
                    w_sq = w_king_square + offset
                    if board.is_attacked_by(chess.BLACK, w_sq):
                        w_king_danger += 1
                
                if 0 <= b_king_square + offset < 64:
                    b_sq = b_king_square + offset
                    if board.is_attacked_by(chess.WHITE, b_sq):
                        b_king_danger += 1
            
            detailed += f"• King safety:\n"
            detailed += f"  White king: {w_king_attackers} direct attacker(s), {w_king_danger} threatened squares around king\n"
            detailed += f"  Black king: {b_king_attackers} direct attacker(s), {b_king_danger} threatened squares around king\n\n"
        
        center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
        w_center = sum(1 for sq in center_squares if board.is_attacked_by(chess.WHITE, sq))
        b_center = sum(1 for sq in center_squares if board.is_attacked_by(chess.BLACK, sq))
        
        w_control = sum(1 for sq in chess.SQUARES if board.is_attacked_by(chess.WHITE, sq))
        b_control = sum(1 for sq in chess.SQUARES if board.is_attacked_by(chess.BLACK, sq))
        
        detailed += f"• Board control:\n"
        detailed += f"  Center control: White {w_center}/4, Black {b_center}/4\n"
        detailed += f"  Total squares attacked: White {w_control}, Black {b_control}\n\n"
        
        w_isolated = 0
        b_isolated = 0
        w_doubled = 0
        b_doubled = 0
        
        for file in range(8):
            w_pawns_in_file = 0
            b_pawns_in_file = 0
            
            for rank in range(8):
                square = chess.square(file, rank)
                piece = board.piece_at(square)
                
                if piece and piece.piece_type == chess.PAWN:
                    if piece.color == chess.WHITE:
                        w_pawns_in_file += 1
                    else:
                        b_pawns_in_file += 1
            
            if w_pawns_in_file > 1:
                w_doubled += w_pawns_in_file - 1
            if b_pawns_in_file > 1:
                b_doubled += b_pawns_in_file - 1
            
            has_adjacent_w_pawn = False
            has_adjacent_b_pawn = False
            
            for adj_file in [file-1, file+1]:
                if 0 <= adj_file < 8:
                    for rank in range(8):
                        square = chess.square(adj_file, rank)
                        piece = board.piece_at(square)
                        if piece and piece.piece_type == chess.PAWN:
                            if piece.color == chess.WHITE:
                                has_adjacent_w_pawn = True
                            else:
                                has_adjacent_b_pawn = True
            
            if w_pawns_in_file > 0 and not has_adjacent_w_pawn:
                w_isolated += w_pawns_in_file
            if b_pawns_in_file > 0 and not has_adjacent_b_pawn:
                b_isolated += b_pawns_in_file
        
        detailed += f"• Pawn structure:\n"
        detailed += f"  White: {w_isolated} isolated pawn(s), {w_doubled} doubled pawn(s)\n"
        detailed += f"  Black: {b_isolated} isolated pawn(s), {b_doubled} doubled pawn(s)\n"
        
        return detailed
    
    def get_piece_name(self, piece):
        if piece is None:
            return "empty square"
        
        color = "white" if piece.color else "black"
        piece_types = {
            chess.PAWN: "pawn",
            chess.KNIGHT: "knight",
            chess.BISHOP: "bishop",
            chess.ROOK: "rook",
            chess.QUEEN: "queen",
            chess.KING: "king"
        }
        return f"{color} {piece_types[piece.piece_type]}"
    
    def analyze_current_position(self):
        current_fen = self.fen_entry.get().split()[0]  # Get board part of FEN
        board_fen = self.board.board_fen()
        
        if current_fen != board_fen:
            self.load_fen()
        
        if len(self.fen_entry.get().split()) < 2:
            turn = chess.WHITE if self.turn_var.get() == "White" else chess.BLACK
            self.board.turn = turn
        
        self.fen_entry.delete(0, tk.END)
        self.fen_entry.insert(0, self.board.fen())
        
        self.draw_board()
        
        self.status_label.config(text="Analyzing position...")
        
        analysis = self.analyze_position(self.board)
        
        basic_explanation = self.generate_explanation(self.board, analysis)
        detailed_explanation = self.generate_detailed_analysis(self.board, analysis)
        
        if analysis and len(analysis) > 0:
            top_move = analysis[0]["pv"][0]
            self.move_label.config(text=f"Suggested Move: {self.board.san(top_move)}", fg="#009900")
        else:
            self.move_label.config(text="No move found")
        
        self.explanation_text.delete(1.0, tk.END)
        self.explanation_text.insert(tk.END, basic_explanation)
        
        self.detailed_text.delete(1.0, tk.END)
        self.detailed_text.insert(tk.END, detailed_explanation)
    
    def start_lichess_connection(self):
        """Start polling the Lichess server for game updates"""
        if self.polling_active:
            return
            
        self.lichess_status_label.config(text="Status: Connecting to Lichess...")
        
        self.lichess_connect_button.config(state=tk.DISABLED)
        self.lichess_disconnect_button.config(state=tk.NORMAL)
        
        try:
            response = requests.post(f"{lichess_server_url}/api/start-polling?username={self.username}")
            if response.status_code == 200:
                self.polling_active = True
                self.lichess_status_label.config(text=f"Status: Connected to Lichess as {self.username}")
                self.status_label.config(text=f"Connected to Lichess as {self.username}")
                
                self.lichess_polling_thread = threading.Thread(target=self.check_for_game_updates)
                self.lichess_polling_thread.daemon = True
                self.lichess_polling_thread.start()
            else:
                error_msg = f"Failed to connect to Lichess: {response.json().get('error', 'Unknown error')}"
                self.lichess_status_label.config(text=f"Status: {error_msg}")
                self.status_label.config(text=error_msg)
                
                self.lichess_connect_button.config(state=tk.NORMAL)
                self.lichess_disconnect_button.config(state=tk.DISABLED)
        except Exception as e:
            error_msg = f"Error connecting to Lichess server: {e}"
            print(error_msg)
            self.lichess_status_label.config(text=f"Status: Error - {error_msg}")
            self.status_label.config(text=error_msg)
        
            self.lichess_connect_button.config(state=tk.NORMAL)
            self.lichess_disconnect_button.config(state=tk.DISABLED)
    
    def stop_lichess_connection(self):
        """Stop polling the Lichess server"""
        if not self.polling_active:
            return
            
        try:
            response = requests.post(f"{lichess_server_url}/api/stop-polling")
            
            self.polling_active = False
            self.lichess_status_label.config(text="Status: Disconnected from Lichess")
            self.status_label.config(text="Disconnected from Lichess")
            
            self.lichess_connect_button.config(state=tk.NORMAL)
            self.lichess_disconnect_button.config(state=tk.DISABLED)
        except Exception as e:
            error_msg = f"Error disconnecting from Lichess: {e}"
            print(error_msg)
            self.lichess_status_label.config(text=f"Status: Error - {error_msg}")
    
    
    def analyze_position_from_fen(self, fen):
            try:
                self.status_label.config(text="Your turn - Analyzing position...")
                
                if self.auto_analyze_var.get():
                    self.analyze_current_position()
            except Exception as e:
                print(f"Error analyzing position: {e}")
            
    def update_position_from_fen(self, fen):
            try:
                if fen:
                    self.fen_entry.delete(0, tk.END)
                    self.fen_entry.insert(0, fen)
                    
                    self.load_fen()
                    self.status_label.config(text="Position updated from Lichess - It's your turn!")
                    
                    # Analyze the position
                    if self.auto_analyze_var.get():
                        self.analyze_current_position()
            except Exception as e:
                print(f"Error updating position: {e}")
    
    
    def check_for_game_updates(self):
        last_fen = None
        last_game_id = None
        
        while self.polling_active:
            try:
                response = requests.get(f"{lichess_server_url}/api/polling-status")
                if response.status_code == 200:
                    status_data = response.json()
                    
                    is_my_turn = status_data.get("isMyTurn", False)
                    current_fen = status_data.get("lastFen")
                    current_game_id = status_data.get("currentGameId")
                    board_updated = status_data.get("boardUpdated", False)
                    
                    if current_game_id:
                        if not self.lichess_game_active or current_game_id != last_game_id:
                            self.lichess_game_active = True
                            self.root.after(0, lambda gid=current_game_id: self.update_game_active_state(True, gid))
                            last_game_id = current_game_id
                        
                        if current_fen and current_fen != last_fen and board_updated:
                            last_fen = current_fen
                            print(f"Board updated with FEN: {current_fen}, My turn: {is_my_turn}")
                            
                            self.root.after(0, lambda fen=current_fen: self.update_board_position(fen))
                            
                            if is_my_turn:
                                self.root.after(100, lambda fen=current_fen: self.analyze_position_from_fen(fen))
                    else:
                        if self.lichess_game_active:
                            self.lichess_game_active = False
                            self.root.after(0, lambda: self.update_game_active_state(False))
                        last_fen = None
                        last_game_id = None
                else:
                    print(f"Error getting polling status: {response.status_code}")
                    if self.lichess_game_active:
                        self.lichess_game_active = False
                        self.root.after(0, lambda: self.update_game_active_state(False))
                        
            except Exception as e:
                print(f"Error checking game updates: {e}")
            
            time.sleep(1)
    
    def update_board_position(self, fen):
        try:
            if fen:
                self.fen_entry.delete(0, tk.END)
                self.fen_entry.insert(0, fen)
                
                self.load_fen()
                
                self.board_canvas.delete("message")
        except Exception as e:
            print(f"Error updating board position: {e}")

        
    
    def __del__(self):
        if hasattr(self, 'engine'):
            try:
                self.engine.quit()
            except:
                pass
        
        if self.polling_active:
            try:
                requests.get(f"{lichess_server_url}/api/stop-polling")
            except:
                pass
            
    def update_game_active_state(self, is_active, game_id=None):
        if is_active and game_id:
            self.lichess_status_label.config(text=f"Status: Active game - {game_id}")
            
            self.tab_control.pack(expand=1, fill=tk.BOTH, pady=10)
            self.move_label.config(text="Waiting for your turn...")
            
            self.analyze_button.config(state=tk.NORMAL)
            
            if hasattr(self, 'no_game_label') and self.no_game_label:
                self.no_game_label.pack_forget()
                
        else:
            self.lichess_status_label.config(text="Status: Connected to Lichess - No active game")
            
            self.explanation_text.delete(1.0, tk.END)
            self.detailed_text.delete(1.0, tk.END)
            self.move_label.config(text="No active game")
            
            if not hasattr(self, 'no_game_label') or not self.no_game_label:
                self.no_game_label = tk.Label(
                    self.board_canvas,
                    text="No active game found\nStart a game on Lichess to see analysis",
                    font=self.large_font,
                    bg="white",
                    fg="blue"
                )
                self.board_canvas.create_window(200, 200, window=self.no_game_label)
            else:
                self.board_canvas.create_window(200, 200, window=self.no_game_label)
                
            self.board = chess.Board()
            self.draw_board()
            self.fen_entry.delete(0, tk.END)
            self.fen_entry.insert(0, self.board.fen())







if __name__ == "__main__":
    app = ChessAssistant()