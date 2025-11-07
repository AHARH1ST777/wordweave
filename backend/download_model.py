import gensim.downloader as api

print("Загрузка модели RusVectōrēs...")
model = api.load("word2vec-ruscorpora")
print("✓ Модель загружена и сохранена!")