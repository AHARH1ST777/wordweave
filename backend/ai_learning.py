"""
AI модуль, который учится из каждой игры и совершенствуется
"""

import json
import os
from typing import Dict, List, Tuple
from collections import defaultdict
from datetime import datetime

class AILearningEngine:
    """Механизм обучения AI из игр"""
    
    def __init__(self, learning_file: str = "backend/ai_learning_data.json"):
        self.learning_file = learning_file
        self.learning_data = self._load_learning_data()
        self.game_statistics = self._load_statistics()
    
    def _load_learning_data(self) -> Dict:
        """Загружает данные обучения"""
        if os.path.exists(self.learning_file):
            try:
                with open(self.learning_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._initialize_learning_data()
        return self._initialize_learning_data()
    
    def _initialize_learning_data(self) -> Dict:
        """Инициализирует пустые данные обучения"""
        return {
            "word_associations": {},  # Слово -> список слов которые часто угадывают
            "patterns": {},  # Шаблоны - как люди угадывают
            "difficulty_levels": {},  # Насколько сложно угадать слово
            "games_played": 0,
            "total_attempts": 0,
            "average_attempts": 0,
            "ai_improvements": []
        }
    
    def _load_statistics(self) -> Dict:
        """Загружает статистику"""
        return {
            "total_games": 0,
            "successful_games": 0,
            "average_win_rate": 0.0,
            "hardest_words": [],
            "easiest_words": []
        }
    
    def record_game(self, target_word: str, guesses: List[Dict], winner: str = None, attempts: int = 0) -> Dict:
        """Записывает прошедшую игру в память AI"""
        
        # Обновляем статистику слова
        if target_word not in self.learning_data["word_associations"]:
            self.learning_data["word_associations"][target_word] = {
                "times_guessed": 0,
                "related_words": defaultdict(int),
                "average_attempts": 0,
                "difficulty_score": 0.0
            }
        
        word_data = self.learning_data["word_associations"][target_word]
        
        # Анализируем все попытки
        for guess in guesses:
            guessed_word = guess.get("word", "")
            rank = guess.get("rank", 9999)
            
            # Если слово часто угадывают, увеличиваем связь
            if rank <= 50:  # Близкие слова
                word_data["related_words"][guessed_word] += 1
        
        # Обновляем попытки
        word_data["times_guessed"] += 1
        if attempts > 0:
            word_data["average_attempts"] = (
                (word_data["average_attempts"] * (word_data["times_guessed"] - 1) + attempts) 
                / word_data["times_guessed"]
            )
        
        # Вычисляем сложность (больше попыток = сложнее)
        word_data["difficulty_score"] = word_data["average_attempts"] / 10.0
        
        # Обновляем общую статистику
        self.learning_data["games_played"] += 1
        self.learning_data["total_attempts"] += attempts if attempts > 0 else len(guesses)
        self.learning_data["average_attempts"] = (
            self.learning_data["total_attempts"] / self.learning_data["games_played"]
        )
        
        if winner:
            self.game_statistics["successful_games"] += 1
        
        self.game_statistics["total_games"] += 1
        self.game_statistics["average_win_rate"] = (
            self.game_statistics["successful_games"] / self.game_statistics["total_games"]
        )
        
        # Сохраняем данные
        self._save_learning_data()
        
        return {
            "status": "recorded",
            "word": target_word,
            "attempts": attempts,
            "difficulty": word_data["difficulty_score"]
        }
    
    def get_ai_suggestions(self, target_word: str, current_guesses: List[str] = None) -> List[Tuple[str, float]]:
        """Возвращает AI рекомендации на основе обучения"""
        current_guesses = current_guesses or []
        
        if target_word not in self.learning_data["word_associations"]:
            return []
        
        word_data = self.learning_data["word_associations"][target_word]
        related_words = word_data["related_words"]
        
        # Сортируем по количеству появлений (популярность)
        suggestions = sorted(
            [(word, score) for word, score in related_words.items() 
             if word not in current_guesses],
            key=lambda x: x[1],
            reverse=True
        )
        
        return suggestions[:5]  # Топ 5 предложений
    
    def get_word_difficulty(self, word: str) -> float:
        """Возвращает сложность слова (0.0 - 1.0)"""
        if word not in self.learning_data["word_associations"]:
            return 0.5  # Средняя сложность для неизвестных слов
        
        return min(1.0, self.learning_data["word_associations"][word]["difficulty_score"])
    
    def get_ai_insight(self) -> Dict:
        """Возвращает инсайты о том, что AI научилось"""
        hardest = max(
            self.learning_data["word_associations"].items(),
            key=lambda x: x[1]["difficulty_score"],
            default=("unknown", {"difficulty_score": 0})
        )
        
        easiest = min(
            self.learning_data["word_associations"].items(),
            key=lambda x: x[1]["difficulty_score"],
            default=("unknown", {"difficulty_score": 0})
        )
        
        return {
            "total_games_analyzed": self.learning_data["games_played"],
            "average_attempts_per_game": round(self.learning_data["average_attempts"], 2),
            "hardest_word": hardest[0],
            "hardest_difficulty": round(hardest[1]["difficulty_score"], 2),
            "easiest_word": easiest[0],
            "easiest_difficulty": round(easiest[1]["difficulty_score"], 2),
            "win_rate": round(self.game_statistics["average_win_rate"] * 100, 1),
            "total_unique_words": len(self.learning_data["word_associations"])
        }
    
    def _save_learning_data(self):
        """Сохраняет данные обучения"""
        try:
            # Конвертируем defaultdict в обычный dict
            learning_data_copy = self.learning_data.copy()
            learning_data_copy["word_associations"] = {
                word: {
                    **data,
                    "related_words": dict(data["related_words"])
                }
                for word, data in learning_data_copy["word_associations"].items()
            }
            
            with open(self.learning_file, 'w', encoding='utf-8') as f:
                json.dump(learning_data_copy, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения данных обучения: {e}")
    
    def export_learning_stats(self) -> str:
        """Экспортирует статистику обучения"""
        insight = self.get_ai_insight()
        stats = f"""
=== AI LEARNING STATISTICS ===
Всего игр проанализировано: {insight['total_games_analyzed']}
Среднее попыток на игру: {insight['average_attempts_per_game']}
Коэффициент побед: {insight['win_rate']}%
Всего уникальных слов: {insight['total_unique_words']}

Сложнейшее слово: "{insight['hardest_word']}" (сложность: {insight['hardest_difficulty']})
Легчайшее слово: "{insight['easiest_word']}" (сложность: {insight['easiest_difficulty']})
===========================
        """
        return stats.strip()
