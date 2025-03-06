import chess

class Evaluator:
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
                        break  
                
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