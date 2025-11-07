from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
from typing import Dict
from game_logic import GameSession, GameMode
from word_similarity import WordSimilarityEngine

app = FastAPI(title="Word Game API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🚀 Запуск сервера...")
similarity_engine = WordSimilarityEngine()
print("✓ Движок семантического поиска готов")

# ПРОВЕРКА при запуске
print("=" * 50)
if GameSession.validate_all_words():
    print("✅ СИНХРОНИЗАЦИЯ OK - можно играть!")
else:
    print("❌ ЕСТЬ ПРОБЛЕМЫ - исправьте слова!")
print("=" * 50)

active_games: Dict[str, GameSession] = {}
waiting_players: Dict[str, WebSocket] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"✓ Игрок {client_id} подключился")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"✗ Игрок {client_id} отключился")
    
    async def send_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                print(f"Ошибка отправки сообщения игроку {client_id}: {e}")

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "Word Game API", "version": "1.0"}

@app.get("/health")
async def health():
    return {"status": "ok", "active_games": len(active_games)}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "start_solo":
                game_id = str(uuid.uuid4())
                game = GameSession(
                    game_id=game_id,
                    mode=GameMode.SOLO,
                    similarity_engine=similarity_engine,
                    players=[client_id]
                )
                active_games[game_id] = game
                print(f"🎮 Соло игра {game_id} начата. Слово: {game.target_word}")
                
                await manager.send_message({
                    "type": "game_started",
                    "game_id": game_id,
                    "mode": "solo"
                }, client_id)
            
            elif action == "start_multiplayer":
                if waiting_players:
                    opponent_id = list(waiting_players.keys())[0]
                    opponent_ws = waiting_players.pop(opponent_id)
                    
                    game_id = str(uuid.uuid4())
                    game = GameSession(
                        game_id=game_id,
                        mode=GameMode.MULTIPLAYER,
                        similarity_engine=similarity_engine,
                        players=[client_id, opponent_id]
                    )
                    active_games[game_id] = game
                    print(f"🎮 Мультиплеер {game_id}: {client_id} vs {opponent_id}. Слово: {game.target_word}")
                    
                    await manager.send_message({
                        "type": "game_started",
                        "game_id": game_id,
                        "mode": "multiplayer",
                        "opponent": opponent_id
                    }, client_id)
                    
                    await manager.send_message({
                        "type": "game_started",
                        "game_id": game_id,
                        "mode": "multiplayer",
                        "opponent": client_id
                    }, opponent_id)
                else:
                    waiting_players[client_id] = websocket
                    print(f"⏳ Игрок {client_id} ждет соперника")
                    await manager.send_message({"type": "waiting_for_opponent"}, client_id)
            
            elif action == "guess":
                game_id = data.get("game_id")
                word = data.get("word", "").lower().strip()
                
                if not word:
                    await manager.send_message({"type": "error", "message": "Введите слово"}, client_id)
                    continue
                
                if game_id not in active_games:
                    await manager.send_message({"type": "error", "message": "Игра не найдена"}, client_id)
                    continue
                
                game = active_games[game_id]
                result = game.make_guess(client_id, word)
                
                # Проверяем, есть ли ошибка валидации
                if "error" in result:
                    await manager.send_message({
                        "type": "error",
                        "message": result["error"]
                    }, client_id)
                    continue
                
                print(f"   {client_id}: '{word}' → ранг {result['rank']}")
                
                await manager.send_message({"type": "guess_result", **result}, client_id)
                
                if game.mode == GameMode.MULTIPLAYER:
                    opponent_id = game.get_opponent(client_id)
                    if opponent_id:
                        await manager.send_message({
                            "type": "opponent_guess",
                            "attempts": result["attempts"],
                            "last_word": word
                        }, opponent_id)
                        
                        if result["is_correct"]:
                            print(f"🏆 {client_id} победил!")
                            await manager.send_message({
                                "type": "game_over",
                                "winner": client_id,
                                "word": game.target_word
                            }, opponent_id)
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        if client_id in waiting_players:
            del waiting_players[client_id]

if __name__ == "__main__":
    import uvicorn
    print("🎮 Сервер запускается на http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
