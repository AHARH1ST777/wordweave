import gensim
from gensim.models import KeyedVectors
import os
from difflib import SequenceMatcher
from word_categories import WORD_CATEGORIES

class WordSimilarityEngine:
    def __init__(self):
        """Инициализация движка"""
        self.model = None
        self.load_model()
        self.word_categories = WORD_CATEGORIES
    
    def load_model(self):
        """Загрузка модели"""
        model_path = "ruscorpora_upos_skipgram_300_2_2019.bin"
        
        if os.path.exists(model_path):
            try:
                print("Загрузка модели... (может занять 1-2 минуты)")
                self.model = KeyedVectors.load_word2vec_format(
                    model_path, 
                    binary=True
                )
                print("✓ Модель загружена успешно!")
            except Exception as e:
                print(f"❌ Ошибка загрузки модели: {e}")
                self.model = None
        else:
            print("⚠ Модель не найдена, используется режим с категориями")
            self.model = None
    
    def normalize_word(self, word: str) -> str:
        """Нормализация слова"""
        return word.lower().strip()
    
    def string_similarity(self, a: str, b: str) -> float:
        """Фонетическая похожесть"""
        return SequenceMatcher(None, a, b).ratio()
    
    def validate_word(self, word: str) -> dict:
        """Проверка валидности"""
        word = self.normalize_word(word)
        
        if not word:
            return {"valid": False, "message": "Слово не может быть пустым"}
        
        if not self.model:
            return {"valid": True, "message": "OK"}
        
        word_noun = f"{word}_NOUN"
        
        if word_noun not in self.model:
            found = False
            for form in [f"{word}_NOUN", f"{word}_VERB", f"{word}_ADJ", f"{word}_ADV"]:
                if form in self.model:
                    found = True
                    break
            
            if not found:
                return {"valid": False, "message": f"Слово '{word}' не найдено"}
            else:
                return {"valid": False, "message": f"'{word}' - пожалуйста вводите существительные"}
        
        return {"valid": True, "message": "OK"}
    
    def get_category_similarity(self, word: str, target: str) -> float:
        """Похожесть через категории"""
        word = self.normalize_word(word)
        target = self.normalize_word(target)
        
        if target in self.word_categories:
            if word in self.word_categories[target]:
                return 0.65
        
        if word in self.word_categories:
            if target in self.word_categories[word]:
                return 0.5
        
        return None
    
    def get_similarity(self, word1: str, word2: str) -> float:
        """Комбинированная похожесть"""
        word1 = self.normalize_word(word1)
        word2 = self.normalize_word(word2)
        
        if word1 == word2:
            return 1.0
        
        category_sim = self.get_category_similarity(word1, word2)
        
        if not self.model:
            if category_sim is not None:
                return category_sim
            phon_sim = self.string_similarity(word1, word2)
            if phon_sim > 0.5:
                return phon_sim * 0.4
            return 0.0
        
        try:
            word1_tagged = f"{word1}_NOUN"
            word2_tagged = f"{word2}_NOUN"
            
            model_sim = 0.0
            if word1_tagged in self.model and word2_tagged in self.model:
                model_sim = max(0.0, float(self.model.similarity(word1_tagged, word2_tagged)))
            
            if category_sim is not None:
                return (model_sim * 0.7) + (category_sim * 0.3)
            
            return model_sim
        except:
            if category_sim is not None:
                return category_sim
            return 0.0
    
    def get_rank(self, word: str, target: str) -> int:
        """Вычисляет ранг"""
        word = self.normalize_word(word)
        target = self.normalize_word(target)
        
        if word == target:
            return 0
        
        category_sim = self.get_category_similarity(word, target)
        if category_sim is not None:
            rank = int(100 * (1 - category_sim)) // 5
            return max(2, rank)
        
        if not self.model:
            phon_sim = self.string_similarity(word, target)
            if phon_sim > 0.5:
                rank = int(200 * (1 - phon_sim))
                return max(2, min(1000, rank))
            return 9999
        
        try:
            target_tagged = f"{target}_NOUN"
            word_tagged = f"{word}_NOUN"
            
            if target_tagged not in self.model:
                phon_sim = self.string_similarity(word, target)
                if phon_sim > 0.55:
                    rank = int(150 * (1 - phon_sim))
                    return max(2, min(500, rank))
                return 9999
            
            similar_words = self.model.most_similar(target_tagged, topn=2000)
            
            rank = 0
            for idx, (similar_word, _) in enumerate(similar_words):
                similar_word_clean = similar_word.split('_')[0]
                if similar_word_clean == target:
                    continue
                rank += 1
                if similar_word_clean == word:
                    return rank
            
            return 9999
        except:
            return 9999
