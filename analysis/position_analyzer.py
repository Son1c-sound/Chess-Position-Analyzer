import chess
from chess_engine import ChessEngine
from .evaluation import Evaluator

class PositionAnalyzer:
    def __init__(self, status_callback=None):
        self.status_callback = status_callback
        self.engine = ChessEngine(on_init_callback=self._on_engine_init)
        self.evaluator = Evaluator()
        self.depth = 15
        self.time_limit = 1.0
        self.multipv = 3
    
    def _on_engine_init(self, message):
        if self.status_callback:
            self.status_callback(message)
    
    def initialize_engine(self):
        return self.engine.initialize()
    
    def set_analysis_params(self, depth=None, time_limit=None, multipv=None):
        if depth is not None:
            self.depth = depth
        if time_limit is not None:
            self.time_limit = time_limit
        if multipv is not None:
            self.multipv = multipv
    
    def analyze_position(self, board, on_move_found=None, on_analysis_complete=None):
        if self.status_callback:
            self.status_callback("Analyzing position...")
        
        if not any(board.piece_map()):
            if self.status_callback:
                self.status_callback("No pieces detected on board")
            return "", ""
        
        analysis = self.engine.analyze_position(
            board, 
            depth=self.depth, 
            time_limit=self.time_limit, 
            multipv=self.multipv
        )
        
        if not analysis:
            if self.status_callback:
                self.status_callback("Analysis failed")
            return "", ""
        
        if self.status_callback:
            self.status_callback(f"Analysis complete (depth {self.depth}, {self.time_limit}s)")
        
        basic_explanation = self.evaluator.generate_explanation(board, analysis)
        detailed_explanation = self.evaluator.generate_detailed_analysis(board, analysis)
        
        if analysis and len(analysis) > 0 and on_move_found:
            top_move = analysis[0]["pv"][0]
            on_move_found(board.san(top_move))
        
        if on_analysis_complete:
            on_analysis_complete(basic_explanation, detailed_explanation)
        
        return basic_explanation, detailed_explanation
    
    def restart_engine(self):
        if self.status_callback:
            self.status_callback("Restarting engine...")
        return self.engine.restart()
    
    def quit(self):
        self.engine.quit()