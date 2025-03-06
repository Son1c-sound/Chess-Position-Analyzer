import express from 'express';
import fetch from 'node-fetch';

const app = express();
const PORT = 3000;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const gameState = {
  currentGameId: null,
  isMyTurn: false,
  username: null,
  pollingInterval: null,
  lastFen: null,
  lastCheckTime: null,
  boardUpdated: false 
};

const POLLING_INTERVAL = 2000; 

async function fetchCurrentGame(username) {
  try {
    const response = await fetch(`https://lichess.org/api/account/playing`, {
      headers: {
        'Authorization': 'Bearer lip_cEHrREJPDi4Q0u1fdx7B',
        'Accept': 'application/json'
      }
    });
    
    if (!response.ok) {
      console.log('OAuth authentication failed, trying public endpoint...');
      
      const publicResponse = await fetch(`https://lichess.org/api/user/${username}/current-games?nb=1`, {
        headers: {
          'Accept': 'application/json'
        }
      });
      
      if (!publicResponse.ok) {
        throw new Error(`Lichess API returned status: ${publicResponse.status}`);
      }
      
      const publicData = await publicResponse.json();
      
      if (!publicData.nowPlaying || publicData.nowPlaying.length === 0) {
        return null; 
      }
      
      return publicData.nowPlaying[0];
    }
    
    const data = await response.json();
    
    if (!data.nowPlaying || data.nowPlaying.length === 0) {
      return null; 
    }
    
    return data.nowPlaying[0];
  } catch (error) {
    console.error('Error fetching game:', error);
    return null;
  }
}

function processGameData(gameData) {
  if (!gameData) return null;
  
  return { 
    game_id: gameData.gameId,
    fen: gameData.fen,
    last_move: gameData.lastMove,
    color: gameData.color,
    opponent: {
      username: gameData.opponent.username,
      rating: gameData.opponent.rating
    },
    is_my_turn: gameData.isMyTurn,
    time_left: gameData.secondsLeft,
    variant: gameData.variant,
    speed: gameData.speed,
    game_url: `https://lichess.org/${gameData.gameId}`
  };
}

function startPolling(username) {
  if (gameState.pollingInterval) {
    clearInterval(gameState.pollingInterval);
  }
  
  gameState.username = username;
  gameState.isMyTurn = false;
  gameState.lastFen = null;
  gameState.boardUpdated = false;
  
  checkGameState();
  
  gameState.pollingInterval = setInterval(checkGameState, POLLING_INTERVAL);
  
  console.log(`Started polling for ${username}'s game state every ${POLLING_INTERVAL/1000} seconds`);
  return true;
}

function stopPolling() {
  if (gameState.pollingInterval) {
    clearInterval(gameState.pollingInterval);
    gameState.pollingInterval = null;
    console.log('Stopped polling for moves');
    return true;
  }
  return false;
}

async function checkGameState() {
  if (!gameState.username) return;
  
  const gameData = await fetchCurrentGame(gameState.username);
  const processedGame = processGameData(gameData);
  
  if (!processedGame) {
    console.log('No active game found');
    if (gameState.currentGameId) {
      gameState.currentGameId = null;
      gameState.lastFen = null;
      gameState.isMyTurn = false;
    }
    return;
  }
  
  gameState.currentGameId = processedGame.game_id;
  
  const wasPreviouslyMyTurn = gameState.isMyTurn;
  const isNowMyTurn = processedGame.is_my_turn;
  
  if (gameState.lastFen !== processedGame.fen) {
    console.log(`Board position updated: ${processedGame.fen}`);
    console.log(`Turn: ${isNowMyTurn ? 'Your turn' : 'Opponent\'s turn'}`);
    
    gameState.lastFen = processedGame.fen;
    gameState.lastCheckTime = new Date();
    gameState.boardUpdated = true;
  } else {
    gameState.boardUpdated = false;
  }
  
  if (wasPreviouslyMyTurn !== isNowMyTurn) {
    if (isNowMyTurn) {
      console.log(`It's now your turn in game ${processedGame.game_id}!`);
    } else {
      console.log(`It's now your opponent's turn`);
    }
    gameState.isMyTurn = isNowMyTurn;
  }
}

app.get('/api/current-game', async (req, res) => {
  const { username } = req.query;
  if (!username) return res.status(400).json({ error: 'Username is required' });

  try {
    const gameData = await fetchCurrentGame(username);
    
    if (!gameData) {
      return res.status(404).json({ error: 'No ongoing games found for this user' });
    }
    
    const processedGame = processGameData(gameData);
    res.json(processedGame);
  } catch (error) {
    console.error('Server error:', error);
    res.status(500).json({ error: 'Internal server error', details: error.message });
  }
});

app.route('/api/start-polling')
  .get((req, res) => {
    const { username } = req.query;
    
    if (!username) {
      return res.status(400).json({ error: 'Username is required' });
    }
    
    const success = startPolling(username);
    
    if (success) {
      res.json({ 
        message: `Started polling for ${username}'s game state`, 
        interval: POLLING_INTERVAL/1000
      });
    } else {
      res.status(500).json({ error: 'Failed to start polling' });
    }
  })
  .post((req, res) => {
    const { username } = req.query;
    
    if (!username) {
      return res.status(400).json({ error: 'Username is required' });
    }
    
    const success = startPolling(username);
    
    if (success) {
      res.json({ 
        message: `Started polling for ${username}'s game state`, 
        interval: POLLING_INTERVAL/1000
      });
    } else {
      res.status(500).json({ error: 'Failed to start polling' });
    }
  });

app.route('/api/stop-polling')
  .get((req, res) => {
    const success = stopPolling();
    
    if (success) {
      res.json({ message: 'Stopped polling for moves' });
    } else {
      res.status(400).json({ error: 'Polling was not active' });
    }
  })
  .post((req, res) => {
    const success = stopPolling();
    
    if (success) {
      res.json({ message: 'Stopped polling for moves' });
    } else {
      res.status(400).json({ error: 'Polling was not active' });
    }
  });

app.get('/api/polling-status', (req, res) => {
  const now = new Date();
  const lastChecked = gameState.lastCheckTime ? 
    Math.round((now - gameState.lastCheckTime) / 1000) + " seconds ago" : 
    "never";
  
  res.json({
    active: !!gameState.pollingInterval,
    username: gameState.username || null,
    currentGameId: gameState.currentGameId || null,
    isMyTurn: gameState.isMyTurn || false,
    lastFen: gameState.lastFen || null,
    boardUpdated: gameState.boardUpdated || false,
    lastChecked: lastChecked,
    pollingInterval: POLLING_INTERVAL/1000
  });
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`Get current game: http://localhost:${PORT}/api/current-game?username=YOUR_LICHESS_USERNAME`);
  console.log(`Start polling: http://localhost:${PORT}/api/start-polling?username=YOUR_LICHESS_USERNAME`);
  console.log(`Stop polling: http://localhost:${PORT}/api/stop-polling`);
  console.log(`Check polling status: http://localhost:${PORT}/api/polling-status`);
});

export default app;