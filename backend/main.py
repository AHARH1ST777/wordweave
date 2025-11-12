from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
from typing import Dict
from game_logic import GameSession, GameMode
from word_similarity import WordSimilarityEngine
from ai_learning import AILearningSystem

app = FastAPI(title="WORDWEAVE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🚀 Запуск сервера WORDWEAVE...")
print("=" * 60)

# Инициализация AI системы обучения
try:
    ai_system = AILearningSystem(data_file='ai_learning_data.json')
    print("✓ AI система инициализирована")
except Exception as e:
    print(f"⚠️ Ошибка инициализации AI: {e}")
    ai_system = None

# Инициализация движка похожести с AI
try:
    similarity_engine = WordSimilarityEngine(
        database_path='word_database.json',
        ai_system=ai_system
    )
    print("✓ Движок похожести инициализирован")
except Exception as e:
    print(f"❌ Ошибка инициализации движка: {e}")
    import sys
    sys.exit(1)

print("=" * 60)

# Показываем статистику AI если доступна
if ai_system:
    try:
        ai_stats = ai_system.get_stats()
        print(f"🧠 AI Статистика:")
        for key, value in ai_stats.items():
            print(f"   - {key}: {value}")
    except Exception as e:
        print(f"⚠️ Не удалось получить статистику AI: {e}")

print("=" * 60)

active_games: Dict[str, GameSession] = {}
waiting_players: Dict[str, WebSocket] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"✓ Подключен: {client_id}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"✗ Отключен: {client_id}")
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(message))

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            action = message.get('action')
            
            print(f"📨 {client_id}: {action}")
            
            if action == 'start_solo':
                game_id = str(uuid.uuid4())
                game = GameSession(
                    game_id=game_id,
                    mode=GameMode.SOLO,
                    similarity_engine=similarity_engine,
                    players=[client_id]
                )
                active_games[game_id] = game
                
                await manager.send_personal_message({
                    'type': 'game_started',
                    'game_id': game_id,
                    'mode': 'solo'
                }, client_id)
            
            elif action == 'start_multiplayer':
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
                    
                    await manager.send_personal_message({
                        'type': 'game_started',
                        'game_id': game_id,
                        'mode': 'multiplayer',
                        'opponent': opponent_id
                    }, client_id)
                    
                    await manager.send_personal_message({
                        'type': 'game_started',
                        'game_id': game_id,
                        'mode': 'multiplayer',
                        'opponent': client_id
                    }, opponent_id)
                else:
                    waiting_players[client_id] = websocket
                    await manager.send_personal_message({
                        'type': 'waiting_for_opponent'
                    }, client_id)
            
            elif action == 'guess':
                game_id = message.get('game_id')
                word = message.get('word')
                
                if game_id in active_games:
                    game = active_games[game_id]
                    result = game.make_guess(client_id, word)
                    
                    await manager.send_personal_message({
                        'type': 'guess_result',
                        **result
                    }, client_id)
                    
                    if game.mode == GameMode.MULTIPLAYER:
                        opponent = game.get_opponent(client_id)
                        if opponent:
                            await manager.send_personal_message({
                                'type': 'opponent_guess',
                                'attempts': game.attempts[client_id],
                                'last_word': word
                            }, opponent)
                    
                    if result.get('is_correct'):
                        if game.mode == GameMode.MULTIPLAYER:
                            opponent = game.get_opponent(client_id)
                            if opponent:
                                await manager.send_personal_message({
                                    'type': 'game_over',
                                    'winner': client_id,
                                    'word': game.target_word
                                }, opponent)
                else:
                    await manager.send_personal_message({
                        'type': 'error',
                        'message': 'Игра не найдена'
                    }, client_id)
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        if client_id in waiting_players:
            del waiting_players[client_id]

@app.get("/")
async def root():
    stats = {
        "app": "WORDWEAVE",
        "version": "2.0",
        "words_count": len(similarity_engine.get_all_words()),
        "status": "running"
    }
    
    if ai_system:
        try:
            stats["ai_stats"] = ai_system.get_stats()
        except:
            stats["ai_stats"] = "unavailable"
    
    return stats

@app.get("/api/stats")
async def get_stats():
    stats = {
        "total_words": len(similarity_engine.get_all_words()),
        "active_games": len(active_games),
        "waiting_players": len(waiting_players)
    }
    
    if ai_system:
        try:
            stats["ai"] = ai_system.get_stats()
        except:
            stats["ai"] = {"error": "AI stats unavailable"}
    
    return stats

@app.on_event("shutdown")
async def shutdown_event():
    """Сохраняем AI данные при остановке"""
    print("💾 Сохранение AI данных...")
    if ai_system:
        try:
            ai_system.save_data()
            print("✓ AI данные сохранены")
        except Exception as e:
            print(f"⚠️ Ошибка сохранения: {e}")
    print("✓ Сервер остановлен")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("✅ Сервер запущен!")
    print("=" * 60)
    print("🌐 Backend:  http://localhost:8000")
    print("🎮 Frontend: http://localhost:5173")
    print("📊 Слов в базе:", len(similarity_engine.get_all_words()))
    
    if ai_system:
        try:
            print("🧠 AI игр сыграно:", ai_system.games_played)
        except:
            print("🧠 AI: новая система")
    
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
