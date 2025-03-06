import express from 'express';
import fetch from 'node-fetch';
import { Chess } from 'chess.js';

const app = express();

app.get('/api/game-fen', async (req, res) => {
    const { username } = req.query;
    if (!username) return res.status(400).json({ error: 'Username is required' });

    try {
        // Fetch the latest game PGN from Chess.com
        const response = await fetch(`https://api.chess.com/pub/player/${username}/games/archives`);
        const archives = await response.json();
        const latestArchive = archives.archives.pop();
        const gameResponse = await fetch(latestArchive);
        const games = await gameResponse.json();
        
        if (!games.games || games.games.length === 0) {
            return res.status(404).json({ error: 'No games found' });
        }

        const latestGame = games.games[games.games.length - 1];
        const pgn = latestGame.pgn;
        
        if (!pgn) return res.status(404).json({ error: 'PGN not found' });

        // Convert PGN to FEN
        const chess = new Chess();
        const fenList = [];
        
        chess.loadPgn(pgn);
        const history = chess.history({ verbose: true });
        
        history.forEach(move => {
            chess.move(move.san);
            const fen = chess.fen();
            console.log(fen); // Log FEN to console
            fenList.push(fen);
        });

        res.json({ fenList });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

export default app;