import os
import chess
import chess.engine
from config import STOCKFISH_PATH

class ChessEngine:
    
    def __init__(self, on_init_callback=None):
        self.engine = None
        self.on_init_callback = on_init_callback
        self.verify_path()
        
    def verify_path(self):
        if not os.path.exists(STOCKFISH_PATH):
            print(f"Error: Could not find Stockfish at {os.path.abspath(STOCKFISH_PATH)}")
            print("Please make sure the path points to the stockfish.exe file")
            raise FileNotFoundError(f"Stockfish not found at {STOCKFISH_PATH}")
        else:
            print(f"Found Stockfish at {os.path.abspath(STOCKFISH_PATH)}")
    
    def initialize(self):
        try:
            print(f"Attempting to initialize Stockfish at: {STOCKFISH_PATH}")
            self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
            self.engine.configure({"Threads": 4, "Hash": 128})
            print("Stockfish engine initialized successfully")
            
            if self.on_init_callback:
                self.on_init_callback("Stockfish engine initialized successfully")
                
            return True
        except Exception as e:
            error_msg = f"Error initializing Stockfish: {e}"
            print(error_msg)
            
            if self.on_init_callback:
                self.on_init_callback(error_msg)
                
            return False
    
    def analyze_position(self, board, depth=15, time_limit=1.0, multipv=3):
       
        if not self.engine:
            print("Engine not initialized. Initialize first.")
            return []
        
        if not any(board.piece_map()):
            print("No pieces detected on board.")
            return []
        
        try:
            print(f"Analyzing position: {board.fen()}")
            
            result = self.engine.analyse(
                board, 
                chess.engine.Limit(time=time_limit, depth=depth), 
                multipv=multipv
            )
            return result
        except chess.engine.EngineTerminatedError:
            print("Stockfish engine crashed. Attempting to restart...")
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
                print("Stockfish engine restarted. Try analyzing again.")
            except Exception as e:
                print(f"Failed to restart Stockfish: {e}")
            return []
        except Exception as e:
            print(f"Analysis error: {e}")
            return []
    
    def restart(self):
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass
        
        return self.initialize()
    
    def quit(self):
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass