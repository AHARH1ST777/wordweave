from enum import Enum
from typing import List, Dict, Optional
import random
from datetime import datetime
from word_categories import WORD_CATEGORIES

class GameMode(Enum):
    """Режимы игры"""
    SOLO = "solo"
    MULTIPLAYER = "multiplayer"

class GameSession:
    """Класс для управления игровой сессией"""
    
    # ========== АВТОМАТИЧЕСКАЯ СИНХРОНИЗАЦИЯ ИЗ КАТЕГОРИЙ ==========
    ALL_WORDS = sorted(list(WORD_CATEGORIES.keys()))
    
    def __init__(self, game_id: str, mode: GameMode, similarity_engine, players: List[str] = None):
        self.game_id = game_id
        self.mode = mode
        self.similarity_engine = similarity_engine
        self.players = players or ["player"]
        self.target_word = self._select_random_word()
        self.attempts: Dict[str, int] = {p: 0 for p in self.players}
        self.history: Dict[str, List[Dict]] = {p: [] for p in self.players}
        self.winner: Optional[str] = None
        self.start_time = datetime.now()
        self.current_turn = self.players[0] if len(self.players) > 1 else None
        
        print(f"✓ Игра начата #{self.game_id}")
        print(f"✓ Загадано слово: {self.target_word}")
        print(f"✓ Всего слов в игре: {len(self.ALL_WORDS)}")
    
    def _select_random_word(self) -> str:
        """Выбирает случайное слово из синхронизированного списка"""
        if not self.ALL_WORDS:
            print("⚠️ КРИТИЧЕСКАЯ ОШИБКА: Список слов пуст!")
            return "ошибка"
        
        word = random.choice(self.ALL_WORDS)
        
        # Проверяем что слово есть в категориях
        if word not in WORD_CATEGORIES:
            print(f"⚠️ ОШИБКА: Слово '{word}' не в категориях!")
        
        return word
    
    def make_guess(self, player_id: str, word: str) -> Dict:
        """Обрабатывает попытку угадывания"""
        word = word.lower().strip()
        
        # Проверяем валидность слова
        validation = self.similarity_engine.validate_word(word)
        
        if not validation["valid"]:
            return {
                "error": validation["message"],
                "is_correct": False
            }
        
        if player_id not in self.players:
            return {"error": "Игрок не найден"}
        
        self.attempts[player_id] += 1
        similarity = self.similarity_engine.get_similarity(word, self.target_word)
        rank = self.similarity_engine.get_rank(word, self.target_word)
        
        # Если ранг = 0, это означает точное совпадение (победа)
        is_correct = rank == 0 or word == self.target_word
        
        if is_correct and not self.winner:
            self.winner = player_id
        
        guess_data = {
            "word": word,
            "similarity": round(similarity, 4),
            "rank": rank,
            "attempt": self.attempts[player_id]
        }
        self.history[player_id].append(guess_data)
        
        # Исключаем точные совпадения из истории и сортируем по рангу
        sorted_history = sorted(
            [h for h in self.history[player_id] if h["rank"] != 0],
            key=lambda x: x["rank"]
        )
        
        return {
            "word": word,
            "similarity": round(similarity, 4),
            "rank": rank if rank != 0 else "✓ ТОЧНОЕ СОВПАДЕНИЕ",
            "attempts": self.attempts[player_id],
            "is_correct": is_correct,
            "history": sorted_history,
            "winner": self.winner,
            "target_word": self.target_word if is_correct else None
        }
    
    def get_opponent(self, player_id: str) -> Optional[str]:
        """Возвращает ID соперника"""
        if self.mode != GameMode.MULTIPLAYER or len(self.players) < 2:
            return None
        for p in self.players:
            if p != player_id:
                return p
        return None
    
    def get_game_state(self, player_id: str) -> Dict:
        """Возвращает текущее состояние игры"""
        return {
            "game_id": self.game_id,
            "mode": self.mode.value,
            "target_word": self.target_word,
            "player_id": player_id,
            "attempts": self.attempts.get(player_id, 0),
            "history": self.history.get(player_id, []),
            "winner": self.winner,
            "elapsed_time": (datetime.now() - self.start_time).total_seconds()
        }
    
    def get_leaderboard(self) -> List[Dict]:
        """Возвращает лидерборд"""
        leaderboard = []
        for player in self.players:
            leaderboard.append({
                "player_id": player,
                "attempts": self.attempts.get(player, 0),
                "is_winner": player == self.winner
            })
        return sorted(leaderboard, key=lambda x: (x["is_winner"] == False, x["attempts"]))
    
    def reset_game(self):
        """Сбрасывает игру"""
        self.target_word = self._select_random_word()
        self.attempts = {p: 0 for p in self.players}
        self.history = {p: [] for p in self.players}
        self.winner = None
        self.start_time = datetime.now()
    
    def is_game_over(self) -> bool:
        """Проверяет, закончилась ли игра"""
        return self.winner is not None
    
    @staticmethod
    def validate_all_words():
        """Проверяет что все слова в категориях"""
        missing = []
        for word in GameSession.ALL_WORDS:
            if word not in WORD_CATEGORIES:
                missing.append(word)
        
        if missing:
            print(f"❌ ОШИБКА: {len(missing)} слов не в категориях: {missing}")
            return False
        
        print(f"✅ ВСЕ {len(GameSession.ALL_WORDS)} СЛОВ СИНХРОНИЗИРОВАНЫ!")
        return True
