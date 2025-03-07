# Chess Position Monitor - run on ur conputer easy

<a href='https://www.youtube.com/watch?v=46zSw3E4_zg&t=11s' target='_self'>Watch Demo</a> 

<h1>follow these easy steps and you will have chess analyzer running</h1>

1) get api from lichess.org and attach to server in express-serverless/api

2) after adding api run the server node game-fen.js

3) make post request to this url to start pooling http://localhost:3000/api/start-polling?username=ur username in lechess

4) running server should  already display game status - game found or not 

6) run python main.py

if game is started u will see live updates in GUI.


=========================================================

why node and not flask? 

serverless express more comfortable to build servers (for me) and cost effective to host on vercel

future vision to move this all into web so why not

that it :) sign: sonic
