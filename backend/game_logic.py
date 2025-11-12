from enum import Enum
from typing import List, Dict, Optional
import random
from datetime import datetime
from popular_words import get_popular_words

class GameMode(Enum):
    SOLO = "solo"
    MULTIPLAYER = "multiplayer"

class GameSession:
    """Игровая сессия БЕЗ блокировки повторов"""
    
    def __init__(self, game_id: str, mode: GameMode, similarity_engine, players: List[str] = None):
        self.game_id = game_id
        self.mode = mode
        self.similarity_engine = similarity_engine
        self.players = players or ["player"]
        
        # Выбираем простое слово
        popular_words = get_popular_words()
        available_popular = [w for w in popular_words if w in similarity_engine.word_database]
        
        if available_popular:
            self.target_word = random.choice(available_popular)
            print(f"✓ Игра #{game_id}: загадано ПРОСТОЕ слово '{self.target_word}'")
        else:
            all_words = similarity_engine.get_all_words()
            simple_words = [w for w in all_words if 4 <= len(w) <= 7]
            
            if simple_words:
                self.target_word = random.choice(simple_words)
                print(f"✓ Игра #{game_id}: загадано слово '{self.target_word}'")
            else:
                self.target_word = random.choice(all_words) if all_words else "ошибка"
                print(f"⚠️ Игра #{game_id}: загадано '{self.target_word}'")
        
        self.attempts: Dict[str, int] = {p: 0 for p in self.players}
        self.history: Dict[str, List[Dict]] = {p: [] for p in self.players}
        self.winner: Optional[str] = None
        self.start_time = datetime.now()
    
    def make_guess(self, player_id: str, word: str) -> Dict:
        """Обрабатывает попытку (РАЗРЕШЕНЫ ПОВТОРЫ между игроками)"""
        word = word.lower().strip()
        
        # Валидация слова
        validation = self.similarity_engine.validate_word(word)
        
        if not validation["valid"]:
            return {
                "error": validation.get("message", "Неверное слово"),
                "is_correct": False
            }
        
        if player_id not in self.players:
            return {"error": "Игрок не найден"}
        
        # НОВАЯ ПРОВЕРКА: Этот игрок уже вводил это слово?
        player_words = [g['word'] for g in self.history[player_id]]
        if word in player_words:
            return {
                "error": f"Вы уже вводили слово '{word}'! Попробуйте другое.",
                "is_correct": False
            }
        
        self.attempts[player_id] += 1
        similarity = self.similarity_engine.get_similarity(word, self.target_word)
        rank = self.similarity_engine.get_rank(word, self.target_word)
        
        is_correct = rank == 0
        
        # AI обучение
        ai_system = getattr(self.similarity_engine, 'ai_system', None)
        if ai_system:
            ai_system.learn_from_guess(word, self.target_word, similarity, rank, is_correct)
        
        if is_correct and not self.winner:
            self.winner = player_id
            if ai_system:
                ai_system.learn_from_game(
                    self.target_word,
                    self.history[player_id],
                    self.attempts[player_id],
                    True
                )
        
        guess_data = {
            "word": word,
            "similarity": round(similarity, 4),
            "rank": rank,
            "attempt": self.attempts[player_id]
        }
        
        if not is_correct:
            self.history[player_id].append(guess_data)
        
        sorted_history = sorted(
            self.history[player_id],
            key=lambda x: x["rank"]
        )
        
        return {
            "word": word,
            "similarity": round(similarity, 4),
            "rank": rank,
            "attempts": self.attempts[player_id],
            "is_correct": is_correct,
            "history": sorted_history,
            "winner": self.winner,
            "target_word": self.target_word if is_correct else None
        }
    
    def get_opponent(self, player_id: str) -> Optional[str]:
        """Возвращает соперника"""
        if self.mode != GameMode.MULTIPLAYER or len(self.players) < 2:
            return None
        for p in self.players:
            if p != player_id:
                return p
        return None
