"""
Система машинного обучения для WORDWEAVE
"""

import json
import os
from datetime import datetime
from collections import defaultdict
import math

class AILearningSystem:
    def __init__(self, data_file='ai_learning_data.json'):
        self.data_file = data_file
        self.word_associations = {}
        self.successful_paths = []
        self.word_categories = defaultdict(set)
        self.games_played = 0
        self.total_guesses = 0
        
        self.load_data()
    
    def load_data(self):
        """Загружает обученные данные"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.word_associations = data.get('associations', {})
                    self.successful_paths = data.get('paths', [])
                    
                    categories_data = data.get('categories', {})
                    self.word_categories = defaultdict(set)
                    for k, v in categories_data.items():
                        self.word_categories[k] = set(v) if isinstance(v, list) else set()
                    
                    self.games_played = data.get('games_played', 0)
                    self.total_guesses = data.get('total_guesses', 0)
                    print(f"✓ AI данные загружены: {self.games_played} игр, {len(self.word_associations)} связей")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки AI данных: {e}")
                self.word_categories = defaultdict(set)
        else:
            print("📝 Создана новая система обучения AI")
    
    def save_data(self):
        """Сохраняет обученные данные"""
        try:
            categories_serializable = {}
            for key, value in self.word_categories.items():
                if isinstance(value, set):
                    categories_serializable[key] = list(value)
                else:
                    categories_serializable[key] = list(value) if hasattr(value, '__iter__') else []
            
            data = {
                'associations': self.word_associations,
                'paths': self.successful_paths[-1000:],
                'categories': categories_serializable,
                'games_played': self.games_played,
                'total_guesses': self.total_guesses,
                'last_update': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ AI данные сохранены")
        except Exception as e:
            print(f"❌ Ошибка сохранения AI данных: {e}")
            import traceback
            traceback.print_exc()
    
    def learn_from_guess(self, guess_word, target_word, similarity, rank, is_correct):
        """Обучается на каждой попытке"""
        try:
            guess_word = guess_word.lower()
            target_word = target_word.lower()
            
            if target_word not in self.word_associations:
                self.word_associations[target_word] = {}
            
            current_strength = self.word_associations[target_word].get(guess_word, 0)
            
            if is_correct:
                new_strength = 1.0
            else:
                learning_rate = 0.1
                rank_factor = 1.0 / (1 + math.log10(rank + 1))
                new_strength = current_strength + learning_rate * rank_factor
                new_strength = min(new_strength, 0.95)
            
            self.word_associations[target_word][guess_word] = new_strength
            
            if guess_word not in self.word_associations:
                self.word_associations[guess_word] = {}
            self.word_associations[guess_word][target_word] = new_strength * 0.8
            
            self.total_guesses += 1
        
        except Exception as e:
            print(f"⚠️ Ошибка обучения на попытке: {e}")
    
    def learn_from_game(self, target_word, guess_history, attempts, won):
        """Обучается на всей игре"""
        try:
            self.games_played += 1
            
            if won and guess_history:
                path = {
                    'target': target_word,
                    'guesses': [g['word'] for g in guess_history if isinstance(g, dict) and 'word' in g],
                    'attempts': attempts,
                    'timestamp': datetime.now().isoformat()
                }
                self.successful_paths.append(path)
                
                self._analyze_categories(target_word, guess_history)
            
            if self.games_played % 10 == 0:
                self.save_data()
        
        except Exception as e:
            print(f"⚠️ Ошибка обучения на игре: {e}")
    
    def _analyze_categories(self, target_word, guess_history):
        """Анализирует категории слов"""
        try:
            related_words = []
            for g in guess_history:
                if isinstance(g, dict) and 'word' in g and 'similarity' in g:
                    if g.get('similarity', 0) > 0.5:
                        related_words.append(g['word'])
            
            if related_words:
                category_key = target_word
                
                if category_key not in self.word_categories:
                    self.word_categories[category_key] = set()
                elif not isinstance(self.word_categories[category_key], set):
                    self.word_categories[category_key] = set(self.word_categories[category_key])
                
                self.word_categories[category_key].update(related_words)
                self.word_categories[category_key].add(target_word)
        
        except Exception as e:
            print(f"⚠️ Ошибка анализа категорий: {e}")
    
    def get_learned_similarity(self, word1, word2):
        """Возвращает выученную похожесть"""
        word1 = word1.lower()
        word2 = word2.lower()
        
        if word1 in self.word_associations and word2 in self.word_associations[word1]:
            return self.word_associations[word1][word2]
        
        if word2 in self.word_associations and word1 in self.word_associations[word2]:
            return self.word_associations[word2][word1]
        
        for category, words in self.word_categories.items():
            if word1 in words and word2 in words:
                return 0.6
        
        return 0.0
    
    def get_best_associations(self, target_word, top_n=10):
        """Возвращает лучшие ассоциации"""
        target_word = target_word.lower()
        
        if target_word not in self.word_associations:
            return []
        
        associations = self.word_associations[target_word]
        sorted_assoc = sorted(associations.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_assoc[:top_n]
    
    def get_hint(self, target_word):
        """Дает подсказку"""
        best_assoc = self.get_best_associations(target_word, top_n=5)
        
        if best_assoc:
            return f"Попробуйте слова связанные с: {', '.join([w for w, s in best_assoc[:3]])}"
        else:
            return "Подсказок пока нет, но AI учится!"
