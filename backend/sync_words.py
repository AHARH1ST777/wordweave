"""
Скрипт синхронизации - гарантирует что все слова везде одинаковые
"""

from word_categories import WORD_CATEGORIES

def get_all_categorized_words():
    """Получает ВСЕ слова из категорий"""
    words = set()
    for word in WORD_CATEGORIES.keys():
        words.add(word)
    return sorted(list(words))

def print_all_words():
    """Выводит все слова для копирования в game_logic.py"""
    words = get_all_categorized_words()
    print(f"# ВСЕГО СЛОВ: {len(words)}\n")
    print("ALL_WORDS = [")
    for i, word in enumerate(words):
        if i % 5 == 0:
            print('    "' + word + '",', end="")
        else:
            print(f' "{word}",', end="")
        if (i + 1) % 5 == 0:
            print()
    print("\n]")
    
    return words

if __name__ == "__main__":
    words = print_all_words()
    print(f"\n✓ Скопируйте этот список в backend/game_logic.py!")
