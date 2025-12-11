# Telegram-бот аналитики видео по естественному языку

Бот принимает запросы на русском языке и возвращает одно число - результат сложных аналитических запросов по статистике видео.

## Технологии
- Python + aiogram
- PostgreSQL
- Groq + Llama
- Docker + docker-compose

## Как запустить локально 

git clone 

### 1. Создай .env файл в корне проекта 
     TELEGRAM_TOKEN=XXXX
     GROQ_API_KEY=XXXX
     DATABASE_URL=postgresql://postgres:postgres@db:5432/video_analytics

### 2. Скачай JSON с данными - положи в папку data/videos.json

### 3. Вставь свои токены в .env:
     - TELEGRAM_TOKEN - получи у @BotFather
     - GROQ_API_KEY - бесплатно на https://console.groq.com/keys

### 4. Запусти всё одной командой
docker compose up --build -d

### 5. Загрузи данные в базу
docker exec -it tz5-bot-1 python load_data.py

## Архитектура и подход к NLP to SQL
Используем LLM (Llama Groq) 
System промпт с few shot примерами
Температура = 0 - модель не галлюцинирует
После генерации SQL сразу выполняем его через asyncpg и возвращаем одно число

Почему это работает:

На таком маленьком домене (2 таблицы) даже Llama с температурой 0 и хорошими примерами выдаёт корректный SQL
Groq даёт скорость примерно 600 токенов/сек - ответ за 100–200 мс
Всё в одном промпте
Ключевой файл: llm.py — там промпт
