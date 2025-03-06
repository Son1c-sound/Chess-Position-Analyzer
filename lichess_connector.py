import threading
import time
import requests
from config import LICHESS_SERVER_URL, LICHESS_USERNAME

class LichessConnector:
    
    def __init__(self, username=LICHESS_USERNAME):
        self.username = username
        self.polling_active = False
        self.polling_thread = None
        self.game_active = False
        self.current_game_id = None
        self.last_fen = None
        
        self.on_status_change = None
        self.on_board_update = None
        self.on_game_state_change = None
    
    def start_connection(self):
        if self.polling_active:
            return True
            
        try:
            response = requests.post(f"{LICHESS_SERVER_URL}/api/start-polling?username={self.username}")
            if response.status_code == 200:
                self.polling_active = True
                
                if self.on_status_change:
                    self.on_status_change(f"Connected to Lichess as {self.username}")
                
                self.polling_thread = threading.Thread(target=self._check_for_game_updates)
                self.polling_thread.daemon = True
                self.polling_thread.start()
                return True
            else:
                error_msg = f"Failed to connect to Lichess: {response.json().get('error', 'Unknown error')}"
                
                if self.on_status_change:
                    self.on_status_change(error_msg)
                    
                return False
        except Exception as e:
            error_msg = f"Error connecting to Lichess server: {e}"
            print(error_msg)
            
            if self.on_status_change:
                self.on_status_change(error_msg)
                
            return False
    
    def stop_connection(self):
        if not self.polling_active:
            return True
            
        try:
            response = requests.post(f"{LICHESS_SERVER_URL}/api/stop-polling")
            
            self.polling_active = False
            
            if self.on_status_change:
                self.on_status_change("Disconnected from Lichess")
                
            return True
        except Exception as e:
            error_msg = f"Error disconnecting from Lichess: {e}"
            print(error_msg)
            
            if self.on_status_change:
                self.on_status_change(error_msg)
                
            return False
    
    def _check_for_game_updates(self):
        while self.polling_active:
            try:
                response = requests.get(f"{LICHESS_SERVER_URL}/api/polling-status")
                if response.status_code == 200:
                    status_data = response.json()
                    
                    is_my_turn = status_data.get("isMyTurn", False)
                    current_fen = status_data.get("lastFen")
                    current_game_id = status_data.get("currentGameId")
                    board_updated = status_data.get("boardUpdated", False)
                    
                    if current_game_id:
                        if not self.game_active or current_game_id != self.current_game_id:
                            self.game_active = True
                            self.current_game_id = current_game_id
                            
                            if self.on_game_state_change:
                                self.on_game_state_change(True, current_game_id)
                        
                        if current_fen and current_fen != self.last_fen and board_updated:
                            self.last_fen = current_fen
                            print(f"Board updated with FEN: {current_fen}, My turn: {is_my_turn}")
                            
                            if self.on_board_update:
                                self.on_board_update(current_fen, is_my_turn)
                    else:
                        if self.game_active:
                            self.game_active = False
                            self.current_game_id = None
                            
                            if self.on_game_state_change:
                                self.on_game_state_change(False, None)
                                
                        self.last_fen = None
                else:
                    print(f"Error getting polling status: {response.status_code}")
                    if self.game_active:
                        self.game_active = False
                        self.current_game_id = None
                        
                        if self.on_game_state_change:
                            self.on_game_state_change(False, None)
                        
            except Exception as e:
                print(f"Error checking game updates: {e}")
            
            time.sleep(1)