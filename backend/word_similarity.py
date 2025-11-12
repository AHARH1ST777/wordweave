import gensim
from gensim.models import KeyedVectors
import os
import json
from difflib import SequenceMatcher

class WordSimilarityEngine:
    def __init__(self, database_path='word_database.json', ai_system=None):
        """Инициализация с AI системой"""
        self.model = None
        self.word_database = {}
        self.ai_system = ai_system
        
        self.load_database(database_path)
        self.load_model()
    
    def load_database(self, database_path):
        """Загружает базу слов"""
        if os.path.exists(database_path):
            print(f"📖 Загрузка базы слов...")
            with open(database_path, 'r', encoding='utf-8') as f:
                self.word_database = json.load(f)
            print(f"✓ Загружено {len(self.word_database)} слов")
        else:
            print(f"⚠️ База слов не найдена")
    
    def load_model(self):
        """Загружает Word2Vec модель"""
        model_path = "ruscorpora_upos_skipgram_300_2_2019.bin"
        
        if os.path.exists(model_path):
            try:
                print("📦 Загрузка Word2Vec модели...")
                self.model = KeyedVectors.load_word2vec_format(
                    model_path,
                    binary=True
                )
                print("✓ Word2Vec модель загружена!")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки модели: {e}")
                self.model = None
        else:
            print("⚠️ Word2Vec модель не найдена")
            self.model = None
    
    def normalize_word(self, word: str) -> str:
        """Нормализация слова с заменой ё → е"""
        word = word.lower().strip()
        word = word.replace('ё', 'е')
        return word
    
    def validate_word(self, word: str) -> dict:
        """Проверяет валидность слова с поддержкой ё/е"""
        word_normalized = self.normalize_word(word)
        
        if not word_normalized:
            return {"valid": False, "message": "Пустое слово"}
        
        if word_normalized in self.word_database:
            return {"valid": True, "word": word_normalized}
        
        word_original = word.lower().strip()
        if word_original in self.word_database:
            return {"valid": True, "word": word_original}
        
        return {
            "valid": False,
            "message": f"Слово '{word}' не найдено в словаре"
        }
    
    def get_synonyms(self, word: str, top_n: int = 20) -> list:
        """Получает синонимы через Word2Vec"""
        if not self.model:
            return []
        
        word = self.normalize_word(word)
        
        try:
            variants = [f"{word}_NOUN", f"{word}_ADJ", word]
            
            for variant in variants:
                if variant in self.model:
                    similar = self.model.most_similar(variant, topn=top_n)
                    synonyms = []
                    for w, score in similar:
                        clean_word = self.normalize_word(w.split('_')[0])
                        if clean_word in self.word_database and score > 0.4:
                            synonyms.append((clean_word, score))
                    return synonyms
            
            return []
        except Exception as e:
            return []
    
    def get_similarity(self, word1: str, word2: str) -> float:
        """Вычисляет похожесть с уменьшенным весом AI"""
        word1 = self.normalize_word(word1)
        word2 = self.normalize_word(word2)
        
        if word1 == word2:
            return 1.0
        
        similarities = []
        
        # 1. AI обучение (15% веса)
        if self.ai_system:
            ai_sim = self.ai_system.get_learned_similarity(word1, word2)
            if ai_sim > 0:
                similarities.append(('ai', ai_sim, 0.15))
        
        # 2. Word2Vec (70% веса)
        if self.model:
            try:
                variants1 = [f"{word1}_NOUN", word1]
                variants2 = [f"{word2}_NOUN", word2]
                
                for v1 in variants1:
                    for v2 in variants2:
                        if v1 in self.model and v2 in self.model:
                            w2v_sim = float(self.model.similarity(v1, v2))
                            similarities.append(('w2v', w2v_sim, 0.70))
                            break
                    if similarities and similarities[-1][0] == 'w2v':
                        break
            except:
                pass
        
        # 3. Фонетическая (15% веса)
        phonetic_sim = SequenceMatcher(None, word1, word2).ratio()
        similarities.append(('phonetic', phonetic_sim, 0.15))
        
        if similarities:
            total_weight = sum(w for _, _, w in similarities)
            weighted_sum = sum(sim * w for _, sim, w in similarities)
            final_similarity = weighted_sum / total_weight
            return min(final_similarity, 1.0)
        
        return 0.0
    
    def get_rank(self, guess_word: str, target_word: str) -> int:
        """Вычисляет ранг БЕЗ AI (для одинакового ранга у всех)"""
        guess_word = self.normalize_word(guess_word)
        target_word = self.normalize_word(target_word)
        
        if guess_word == target_word:
            return 0
        
        # Синонимы через Word2Vec
        synonyms = self.get_synonyms(target_word, top_n=100)
        for idx, (syn_word, score) in enumerate(synonyms):
            if syn_word == guess_word:
                rank = int(idx / score) + 1
                return min(rank, 200)
        
        # По похожести
        similarity = self.get_similarity(guess_word, target_word)
        
        if similarity >= 0.85:
            return int((1 - similarity) * 200) + 10
        elif similarity >= 0.70:
            return int((1 - similarity) * 800) + 50
        elif similarity >= 0.55:
            return int((1 - similarity) * 2000) + 300
        elif similarity >= 0.40:
            return int((1 - similarity) * 5000) + 1200
        elif similarity >= 0.25:
            return int((1 - similarity) * 15000) + 4200
        elif similarity >= 0.10:
            return int((1 - similarity) * 30000) + 15700
        else:
            return int((1 - similarity) * 63000) + 36000
    
    def get_all_words(self) -> list:
        """Возвращает все слова"""
        return list(self.word_database.keys())
    
    def get_word_info(self, word: str) -> dict:
        """Информация о слове"""
        word = self.normalize_word(word)
        return self.word_database.get(word, {})
