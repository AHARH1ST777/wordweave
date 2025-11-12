"""
Скрипт для загрузки и обработки словарей русских слов
Источники:
1. danakt/russian-words - все слова
2. Harrix/Russian-Nouns - существительные
"""

import requests
import json
import re
from typing import List, Set

def download_all_russian_words() -> Set[str]:
    """Загружает базу всех русских слов (1.5M)"""
    print("📥 Загрузка базы russian-words (1.5M слов)...")
    
    url = "https://raw.githubusercontent.com/danakt/russian-words/master/russian.txt"
    
    try:
        response = requests.get(url, timeout=30)
        response.encoding = 'utf-8'
        
        words = set()
        for line in response.text.split('\n'):
            word = line.strip().lower()
            # Фильтруем: только русские буквы, длина 3-20 символов
            if word and re.match(r'^[а-яё]{3,20}$', word):
                words.add(word)
        
        print(f"✓ Загружено {len(words)} слов из russian-words")
        return words
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return set()

def download_russian_nouns() -> Set[str]:
    """Загружает существительные (125K)"""
    print("📥 Загрузка существительных Russian-Nouns...")
    
    url = "https://raw.githubusercontent.com/Harrix/Russian-Nouns/master/dist/russian_nouns.txt"
    
    try:
        response = requests.get(url, timeout=30)
        response.encoding = 'utf-8'
        
        nouns = set()
        for line in response.text.split('\n'):
            word = line.strip().lower()
            if word and re.match(r'^[а-яё]{3,20}$', word):
                nouns.add(word)
        
        print(f"✓ Загружено {len(nouns)} существительных")
        return nouns
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return set()

def merge_dictionaries(all_words: Set[str], nouns: Set[str]) -> List[str]:
    """Объединяет словари с нормализацией ё → е"""
    print("🔄 Объединение словарей...")
    
    # Нормализуем все слова (ё → е)
    normalized_nouns = set()
    for word in nouns:
        normalized = word.replace('ё', 'е')
        normalized_nouns.add(normalized)
    
    final_words = set(normalized_nouns)
    
    noun_like_endings = ['а', 'я', 'о', 'е', 'ь', 'й', 'ие', 'ия', 'ка', 'ок', 'ек', 'ик']
    
    for word in all_words:
        normalized = word.replace('ё', 'е')
        if any(normalized.endswith(ending) for ending in noun_like_endings):
            if not (normalized.endswith('ть') or normalized.endswith('ти')):
                final_words.add(normalized)
    
    result = sorted(list(final_words))
    print(f"✓ Итого слов: {len(result)}")
    return result


def create_word_database(words: List[str]) -> dict:
    """Создает структурированную базу данных слов"""
    print("📦 Создание базы данных...")
    
    word_db = {}
    
    for idx, word in enumerate(words):
        word_db[word] = {
            'id': idx,
            'word': word,
            'length': len(word),
            'first_letter': word[0],
            'last_letter': word[-1],
            'rank': 99999,  # Начальный ранг для незнакомых слов
            'frequency': 0,  # Будет обновляться в процессе игры
            'times_guessed': 0,
            'times_used_as_target': 0
        }
    
    print(f"✓ База данных создана: {len(word_db)} слов")
    return word_db

def save_database(word_db: dict, filename: str = 'word_database.json'):
    """Сохраняет базу в JSON"""
    print(f"💾 Сохранение в {filename}...")
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(word_db, f, ensure_ascii=False, indent=2)
    
    file_size = len(json.dumps(word_db)) / 1024 / 1024
    print(f"✓ База сохранена! Размер: {file_size:.2f} MB")

def create_compact_version(word_db: dict, filename: str = 'words_compact.json'):
    """Создает компактную версию (только список слов)"""
    print(f"💾 Создание компактной версии...")
    
    words_list = list(word_db.keys())
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(words_list, f, ensure_ascii=False)
    
    print(f"✓ Компактная версия создана: {len(words_list)} слов")

def main():
    """Главная функция"""
    print("=" * 60)
    print("🎮 WORDWEAVE - Создание базы слов")
    print("=" * 60)
    
    # Шаг 1: Загружаем оба словаря
    all_words = download_all_russian_words()
    nouns = download_russian_nouns()
    
    if not all_words and not nouns:
        print("❌ ОШИБКА: Не удалось загрузить словари!")
        return
    
    # Шаг 2: Объединяем
    final_words = merge_dictionaries(all_words, nouns)
    
    # Шаг 3: Создаем базу данных
    word_db = create_word_database(final_words)
    
    # Шаг 4: Сохраняем
    save_database(word_db, 'word_database.json')
    create_compact_version(word_db, 'words_compact.json')
    
    print("\n" + "=" * 60)
    print("✅ ГОТОВО!")
    print("=" * 60)
    print(f"📊 Статистика:")
    print(f"   - Всего слов: {len(word_db)}")
    print(f"   - Файл базы: word_database.json")
    print(f"   - Компактный: words_compact.json")
    print("=" * 60)

if __name__ == "__main__":
    main()
