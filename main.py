import chess
import chess.engine
import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageTk
import os
import threading
import time

# Stockfish path - update this to your stockfish path
stockfish_path = r"C:\Users\makar\Desktop\stockfish\stockfish-windows-x86-64-avx2.exe"

class ChessAssistant:
    def __init__(self):
        # Check if Stockfish exists
        if not os.path.exists(stockfish_path):
            print(f"Error: Could not find Stockfish at {os.path.abspath(stockfish_path)}")
            print("Please make sure the path points to the stockfish.exe file")
            exit(1)
        else:
            print(f"Found Stockfish at {os.path.abspath(stockfish_path)}")
        
        # Initialize the board with the standard starting position
        self.board = chess.Board()
        
        # Setup UI
        self.setup_ui()
        
        # Initialize Stockfish in a separate thread
        self.status_label.config(text="Initializing Stockfish engine...")
        self.root.update()
        
        self.init_engine_thread = threading.Thread(target=self.initialize_engine)
        self.init_engine_thread.daemon = True
        self.init_engine_thread.start()
        
        # Start the main loop
        self.root.mainloop()
    
    def initialize_engine(self):
        """Initialize Stockfish engine in a separate thread"""
        try:
            print(f"Attempting to initialize Stockfish at: {stockfish_path}")
            self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
            # Configure engine
            self.engine.configure({"Threads": 4, "Hash": 128})
            print("Stockfish engine initialized successfully")
            
            # Update status label in the main thread
            self.root.after(0, lambda: self.status_label.config(text="Stockfish engine initialized successfully"))
            # Auto-analyze the current position
            self.root.after(500, self.analyze_current_position)
        except Exception as e:
            error_msg = f"Error initializing Stockfish: {e}"
            print(error_msg)
            
            # Update status label in the main thread
            self.root.after(0, lambda: self.status_label.config(text=error_msg))
    
    def setup_ui(self):
        """Setup the user interface"""
        self.root = tk.Tk()
        self.root.title("Chess Assistant")
        self.root.geometry("650x800")  # Increased size for larger UI
        
        # Position the window to the right side of the screen
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"+{screen_width - 700}+50")
        
        # Create custom fonts
        self.title_font = font.Font(family="Arial", size=14, weight="bold")
        self.large_font = font.Font(family="Arial", size=12)
        self.normal_font = font.Font(family="Arial", size=10)
        
        # Status label at the top
        self.status_label = tk.Label(self.root, text="Initializing...", fg="blue", font=self.large_font)
        self.status_label.pack(pady=5)
        
        # Frame for FEN input
        fen_frame = tk.Frame(self.root)
        fen_frame.pack(pady=10, fill=tk.X, padx=10)
        
        tk.Label(fen_frame, text="FEN String:", font=self.normal_font).pack(anchor=tk.W)
        
        self.fen_entry = tk.Entry(fen_frame, width=50, font=self.normal_font)
        self.fen_entry.pack(fill=tk.X, pady=5)
        self.fen_entry.insert(0, self.board.fen())  # Default starting position
        
        # Add buttons for FEN input
        button_frame = tk.Frame(fen_frame)
        button_frame.pack(fill=tk.X)
        
        tk.Button(button_frame, text="Starting Position", command=self.set_starting_position, 
                  font=self.normal_font, bg="#e0e0e0").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Load FEN", command=self.load_fen, 
                  font=self.normal_font, bg="#e0e0e0").pack(side=tk.LEFT, padx=5)
        
        # Add a restart Stockfish button
        self.restart_button = tk.Button(button_frame, text="Restart Stockfish", command=self.restart_stockfish, 
                                        font=self.normal_font, bg="#f0c0c0")
        self.restart_button.pack(side=tk.RIGHT, padx=5)
        
        # Separator
        ttk.Separator(self.root, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Board and Analysis in a side-by-side layout
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side: Board Display
        board_frame = tk.Frame(main_frame)
        board_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(board_frame, text="Current Position:", font=self.normal_font).pack(anchor=tk.W)
        
        # Create a canvas to draw the chess board
        self.board_canvas = tk.Canvas(board_frame, width=400, height=400, bg="white")
        self.board_canvas.pack(pady=5)
        
        # Right side: Analysis
        analysis_frame = tk.Frame(main_frame)
        analysis_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        # Top move info
        move_frame = tk.LabelFrame(analysis_frame, text="Best Move", font=self.large_font, padx=5, pady=5)
        move_frame.pack(fill=tk.X, pady=5)
        
        self.move_label = tk.Label(move_frame, text="Calculating...", font=("Arial", 16, "bold"), fg="#009900")
        self.move_label.pack(pady=5)
        
        self.eval_label = tk.Label(move_frame, text="", font=self.normal_font)
        self.eval_label.pack(pady=2)
        
        # Analysis tabs
        self.tab_control = ttk.Notebook(analysis_frame)
        
        # Tab for basic analysis
        basic_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(basic_tab, text="Basic Analysis")
        
        # Tab for detailed analysis
        detailed_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(detailed_tab, text="Detailed Analysis")
        
        self.tab_control.pack(expand=1, fill=tk.BOTH, pady=10)
        
        # Basic analysis content - much larger text area
        self.explanation_text = tk.Text(basic_tab, height=16, width=50, font=self.normal_font, wrap=tk.WORD)
        self.explanation_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        explanation_scrollbar = tk.Scrollbar(basic_tab, command=self.explanation_text.yview)
        explanation_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.explanation_text.config(yscrollcommand=explanation_scrollbar.set)
        
        # Detailed analysis content
        self.detailed_text = tk.Text(detailed_tab, height=16, width=50, font=self.normal_font, wrap=tk.WORD)
        self.detailed_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        detailed_scrollbar = tk.Scrollbar(detailed_tab, command=self.detailed_text.yview)
        detailed_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.detailed_text.config(yscrollcommand=detailed_scrollbar.set)
        
        # Analysis controls in a bottom frame
        controls_frame = tk.Frame(self.root)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Left side: Analysis settings
        settings_frame = tk.LabelFrame(controls_frame, text="Analysis Settings", font=self.normal_font, padx=5, pady=5)
        settings_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Analysis depth control
        depth_frame = tk.Frame(settings_frame)
        depth_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(depth_frame, text="Depth:", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        
        self.depth_var = tk.IntVar(value=15)  # Default depth
        depth_spinner = tk.Spinbox(depth_frame, from_=5, to=30, width=5, textvariable=self.depth_var, font=self.normal_font)
        depth_spinner.pack(side=tk.LEFT, padx=5)
        
        # Analysis time control
        tk.Label(depth_frame, text="Time (sec):", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        
        self.time_var = tk.DoubleVar(value=1.0)  # Default 1 second
        time_spinner = tk.Spinbox(depth_frame, from_=0.1, to=10, increment=0.1, width=5, textvariable=self.time_var, font=self.normal_font)
        time_spinner.pack(side=tk.LEFT, padx=5)
        
        # Toggle for who's turn it is
        self.turn_var = tk.StringVar(value="White")
        turn_frame = tk.Frame(settings_frame)
        turn_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(turn_frame, text="Turn:", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(turn_frame, text="White", variable=self.turn_var, value="White", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(turn_frame, text="Black", variable=self.turn_var, value="Black", font=self.normal_font).pack(side=tk.LEFT, padx=5)
        
        # Right side: Analyze button
        button_frame = tk.Frame(controls_frame)
        button_frame.pack(side=tk.RIGHT, padx=10)
        
        self.analyze_button = tk.Button(button_frame, text="Analyze Position", command=self.analyze_current_position, 
                                       font=self.large_font, bg="#90ee90", padx=10, pady=5)
        self.analyze_button.pack(pady=5)
        
        # Add auto-analysis checkbox
        self.auto_analyze_var = tk.BooleanVar(value=True)
        auto_analyze_check = tk.Checkbutton(button_frame, text="Auto-analyze on FEN change", 
                                           variable=self.auto_analyze_var, font=self.normal_font)
        auto_analyze_check.pack(anchor=tk.W)
        
        # Bind the FEN entry to automatically analyze when changed (if auto-analyze is enabled)
        self.fen_entry.bind("<Return>", lambda e: self.on_fen_change())
    
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
            # Handle the case where the FEN might not include the full information
            # If the FEN doesn't specify whose turn it is, use the turn_var setting
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
        colors = ["#f0d9b5", "#b58863"]  # Light square, dark square
        
        # Draw the squares
        for row in range(8):
            for col in range(8):
                color_idx = (row + col) % 2
                x1, y1 = col * square_size, row * square_size
                x2, y2 = x1 + square_size, y1 + square_size
                self.board_canvas.create_rectangle(x1, y1, x2, y2, fill=colors[color_idx], outline="")
                
                # Add row and column labels
                if col == 0:  # File labels (numbers)
                    self.board_canvas.create_text(
                        x1 + 5, y1 + square_size/2, 
                        text=str(8-row), anchor=tk.W, fill="#000000" if color_idx == 0 else "#ffffff"
                    )
                if row == 7:  # Rank labels (letters)
                    self.board_canvas.create_text(
                        x1 + square_size/2, y2 - 10, 
                        text=chr(97 + col), anchor=tk.S, fill="#000000" if color_idx == 0 else "#ffffff"
                    )
        
        # Draw the pieces
        piece_symbols = {
            'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
            'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
        }
        
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                col = chess.square_file(square)
                row = 7 - chess.square_rank(square)  # Flip for display
                x = col * square_size + square_size/2
                y = row * square_size + square_size/2
                
                color = "black" if piece.color == chess.BLACK else "white"
                symbol = piece_symbols[piece.symbol()]
                
                self.board_canvas.create_text(x, y, text=symbol, font=("Arial", 30), fill=color)
    
    def analyze_position(self, board):
        """Analyze the given board position using Stockfish"""
        # Check if engine is initialized
        if not hasattr(self, 'engine'):
            self.status_label.config(text="Waiting for Stockfish to initialize...")
            return []
        
        # Check if the board has any pieces
        if not any(board.piece_map()):
            self.status_label.config(text="No pieces detected on board.")
            return []
        
        try:
            # Get the top 3 moves
            print(f"Analyzing position: {board.fen()}")
            depth = self.depth_var.get()
            time_limit = self.time_var.get()
            
            # Update UI to show we're analyzing
            self.move_label.config(text="Analyzing...", fg="#CC7700")
            self.root.update()
            
            result = self.engine.analyse(board, chess.engine.Limit(time=time_limit, depth=depth), multipv=3)
            self.status_label.config(text=f"Analysis complete (depth {depth}, {time_limit}s)")
            return result
        except chess.engine.EngineTerminatedError:
            # Handle engine crash by restarting it
            self.status_label.config(text="Stockfish engine crashed. Restarting...")
            try:
                # Reinitialize the engine
                self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
                self.status_label.config(text="Stockfish engine restarted. Try analyzing again.")
            except Exception as e:
                self.status_label.config(text=f"Failed to restart Stockfish: {e}")
            return []
        except Exception as e:
            self.status_label.config(text=f"Analysis error: {e}")
            return []
    
    def generate_explanation(self, board, analysis):
        """Generate beginner-friendly explanations for the suggested moves"""
        explanation = "Chess Assistant Analysis:\n\n"
        
        if not analysis:
            return "No analysis available. Try adjusting the analysis settings or check if Stockfish is initialized."
        
        # Top move
        top_move = analysis[0]["pv"][0]
        score = analysis[0]["score"].white().score(mate_score=10000) / 100.0
        
        # Add the top move
        explanation += f"Best move: {board.san(top_move)}\n"
        
        # Format the evaluation in a beginner-friendly way
        if analysis[0]["score"].is_mate():
            mate_in = analysis[0]["score"].mate()
            explanation += f"Evaluation: Checkmate in {abs(mate_in)} for {'white' if mate_in > 0 else 'black'}\n\n"
        else:
            if score > 3:
                status = "strongly winning for white"
            elif score > 1:
                status = "better for white"
            elif score > 0.3:
                status = "slightly better for white"
            elif score > -0.3:
                status = "roughly equal"
            elif score > -1:
                status = "slightly better for black"
            elif score > -3:
                status = "better for black"
            else:
                status = "strongly winning for black"
            
            explanation += f"Evaluation: {score:.2f} ({status})\n\n"
        
        # Explain the move in beginner terms
        moving_piece = board.piece_at(top_move.from_square)
        piece_name = self.get_piece_name(moving_piece)
        
        # Check if it's a capture
        target_piece = board.piece_at(top_move.to_square)
        is_capture = target_piece is not None
        
        if is_capture:
            target_name = self.get_piece_name(target_piece)
            explanation += f"This move {piece_name} captures {target_name}.\n"
        else:
            explanation += f"This move improves the position of your {piece_name}.\n"
        
        # Add move details
        from_square = chess.square_name(top_move.from_square)
        to_square = chess.square_name(top_move.to_square)
        explanation += f"Move details: {from_square} → {to_square}\n\n"
        
        # Add alternative moves
        if len(analysis) > 1:
            explanation += "Alternative moves:\n"
            for i in range(1, min(3, len(analysis))):
                alt_move = analysis[i]["pv"][0]
                alt_score = analysis[i]["score"].white().score(mate_score=10000) / 100.0
                diff = alt_score - score
                
                # More nuanced evaluation of alternative moves
                if abs(diff) < 0.2:
                    quality = "almost equally good"
                elif abs(diff) < 0.5:
                    quality = "slightly worse"
                elif abs(diff) < 1.0:
                    quality = "noticeably worse"
                else:
                    quality = "significantly worse"
                
                explanation += f"• {board.san(alt_move)} ({quality}, {alt_score:.2f})\n"
        
        explanation += "\n"
        
        # Add some general principles based on the position
        explanation += "Chess principles to consider:\n"
        
        if board.is_check():
            explanation += "• You are in check! You must address this threat.\n"
        
        if board.is_checkmate():
            explanation += "• Checkmate! The game is over.\n"
        elif board.is_stalemate():
            explanation += "• Stalemate! The game is a draw.\n"
        
        # Phase of the game advice
        material = sum(len(board.pieces(piece_type, color)) 
                        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]
                        for color in [chess.WHITE, chess.BLACK])
        
        if material > 28:  # Most pieces still on board
            explanation += "• In the opening, focus on developing pieces and controlling the center.\n"
            explanation += "• Try to castle early to protect your king.\n"
            explanation += "• Avoid moving the same piece multiple times in the opening.\n"
        elif material > 15:  # Middlegame
            explanation += "• In the middlegame, look for tactical opportunities and strategic advantages.\n"
            explanation += "• Control open files with your rooks.\n"
            explanation += "• Look for ways to improve your worst-placed piece.\n"
        else:  # Endgame
            explanation += "• In the endgame, activate your king and push pawns when safe.\n"
            explanation += "• Connected passed pawns are very strong in the endgame.\n"
            explanation += "• Trade pieces (but not pawns) when ahead in material.\n"
        
        return explanation
    
    def generate_detailed_analysis(self, board, analysis):
        """Generate detailed analysis information"""
        if not analysis:
            return "No analysis available."
        
        detailed = "Detailed Analysis:\n\n"
        
        # Add all available moves from the analysis
        for i, info in enumerate(analysis):
            move = info["pv"][0]
            score = info["score"].white().score(mate_score=10000) / 100.0
            san = board.san(move)
            
            # Format the text
            prefix = "►" if i == 0 else " "
            if info["score"].is_mate():
                score_text = f"Mate in {abs(info['score'].mate())}"
            else:
                score_text = f"{score:.2f}"
            
            detailed += f"{prefix} {i+1}. {san} ({score_text})\n"
            
            # Add the full line if available
            if len(info["pv"]) > 1:
                test_board = board.copy()
                line = []
                move_num = test_board.fullmove_number
                is_white_to_move = test_board.turn == chess.WHITE
                
                # Process each move in the principal variation
                for j, m in enumerate(info["pv"]):
                    try:
                        # Format with move numbers
                        if j == 0:
                            test_board.push(m)
                            continue  # Skip the first move as we've already displayed it
                        
                        # Add move number when it's white's turn
                        if is_white_to_move:
                            line.append(f"{move_num}.")
                        
                        # Add the move
                        line.append(test_board.san(m))
                        test_board.push(m)
                        
                        # Update move counter
                        if not is_white_to_move:
                            move_num += 1
                        is_white_to_move = not is_white_to_move
                        
                    except Exception as e:
                        print(f"Error in line processing: {e}")
                        break  # Stop if we encounter an invalid move
                
                if line:
                    detailed += f"   Line: {' '.join(line)}\n"
            
            detailed += "\n"
        
        # Add position assessment
        detailed += "Position Assessment:\n"
        
        # Material count
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
        
        # Detailed material breakdown
        detailed += f"• Material breakdown:\n"
        detailed += f"  White: {w_queens}Q, {w_rooks}R, {w_bishops}B, {w_knights}N, {w_pawns}P\n"
        detailed += f"  Black: {b_queens}Q, {b_rooks}R, {b_bishops}B, {b_knights}N, {b_pawns}P\n"
        
        # Calculate material score using standard piece values
        material_score = w_pawns - b_pawns + 3*(w_knights - b_knights) + 3*(w_bishops - b_bishops) + 5*(w_rooks - b_rooks) + 9*(w_queens - b_queens)
        
        detailed += f"• Material balance: {'White +' if material_score > 0 else 'Black +' if material_score < 0 else 'Equal'} {abs(material_score)}\n\n"
        
        # King safety
        w_king_square = board.king(chess.WHITE) if board.king(chess.WHITE) is not None else -1
        b_king_square = board.king(chess.BLACK) if board.king(chess.BLACK) is not None else -1
        
        if w_king_square != -1 and b_king_square != -1:
            w_king_attackers = len(board.attackers(chess.BLACK, w_king_square))
            b_king_attackers = len(board.attackers(chess.WHITE, b_king_square))
            
            # Calculate squares around kings
            w_king_danger = 0
            b_king_danger = 0
            
            for offset in [-9, -8, -7, -1, 1, 7, 8, 9]:
                # Check squares around white king
                if 0 <= w_king_square + offset < 64:
                    w_sq = w_king_square + offset
                    if board.is_attacked_by(chess.BLACK, w_sq):
                        w_king_danger += 1
                
                # Check squares around black king
                if 0 <= b_king_square + offset < 64:
                    b_sq = b_king_square + offset
                    if board.is_attacked_by(chess.WHITE, b_sq):
                        b_king_danger += 1
            
            detailed += f"• King safety:\n"
            detailed += f"  White king: {w_king_attackers} direct attacker(s), {w_king_danger} threatened squares around king\n"
            detailed += f"  Black king: {b_king_attackers} direct attacker(s), {b_king_danger} threatened squares around king\n\n"
        
        # Piece activity and control
        center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
        w_center = sum(1 for sq in center_squares if board.is_attacked_by(chess.WHITE, sq))
        b_center = sum(1 for sq in center_squares if board.is_attacked_by(chess.BLACK, sq))
        
        # Count attacked squares as a measure of piece activity
        w_control = sum(1 for sq in chess.SQUARES if board.is_attacked_by(chess.WHITE, sq))
        b_control = sum(1 for sq in chess.SQUARES if board.is_attacked_by(chess.BLACK, sq))
        
        detailed += f"• Board control:\n"
        detailed += f"  Center control: White {w_center}/4, Black {b_center}/4\n"
        detailed += f"  Total squares attacked: White {w_control}, Black {b_control}\n\n"
        
        # Pawn structure
        w_isolated = 0
        b_isolated = 0
        w_doubled = 0
        b_doubled = 0
        
        # Check for isolated pawns (no friendly pawns on adjacent files)
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
            
            # Count doubled pawns
            if w_pawns_in_file > 1:
                w_doubled += w_pawns_in_file - 1
            if b_pawns_in_file > 1:
                b_doubled += b_pawns_in_file - 1
            
            # Check for isolated pawns
            has_adjacent_w_pawn = False
            has_adjacent_b_pawn = False
            
            # Check adjacent files for pawns
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
            
            # If we have pawns on this file but no adjacent pawns, they're isolated
            if w_pawns_in_file > 0 and not has_adjacent_w_pawn:
                w_isolated += w_pawns_in_file
            if b_pawns_in_file > 0 and not has_adjacent_b_pawn:
                b_isolated += b_pawns_in_file
        
        detailed += f"• Pawn structure:\n"
        detailed += f"  White: {w_isolated} isolated pawn(s), {w_doubled} doubled pawn(s)\n"
        detailed += f"  Black: {b_isolated} isolated pawn(s), {b_doubled} doubled pawn(s)\n"
        
        return detailed
    
    def get_piece_name(self, piece):
        """Convert a chess.Piece to a beginner-friendly name"""
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
        """Analyze the current position"""
        # Check if we should update the board from the FEN entry
        current_fen = self.fen_entry.get().split()[0]  # Get board part of FEN
        board_fen = self.board.board_fen()
        
        if current_fen != board_fen:
            self.load_fen()
        
        # Check whose turn it is if not specified in FEN
        if len(self.fen_entry.get().split()) < 2:
            turn = chess.WHITE if self.turn_var.get() == "White" else chess.BLACK
            self.board.turn = turn
        
        # Update the FEN entry with the full FEN
        self.fen_entry.delete(0, tk.END)
        self.fen_entry.insert(0, self.board.fen())
        
        # Draw the board
        self.draw_board()
        
        # Update status
        self.status_label.config(text="Analyzing position...")
        
        # Analyze the position
        analysis = self.analyze_position(self.board)
        
        # Generate explanations
        basic_explanation = self.generate_explanation(self.board, analysis)
        detailed_explanation = self.generate_detailed_analysis(self.board, analysis)
        
        # Update the UI
        if analysis and len(analysis) > 0:
            top_move = analysis[0]["pv"][0]
            self.move_label.config(text=f"Suggested Move: {self.board.san(top_move)}")
        else:
            self.move_label.config(text="No move found")
        
        self.explanation_text.delete(1.0, tk.END)
        self.explanation_text.insert(tk.END, basic_explanation)
        
        self.detailed_text.delete(1.0, tk.END)
        self.detailed_text.insert(tk.END, detailed_explanation)
    
    def __del__(self):
        """Clean up resources"""
        if hasattr(self, 'engine'):
            try:
                self.engine.quit()
            except:
                pass

if __name__ == "__main__":
    app = ChessAssistant()