## Telegram bot (Replit)

### Что умеет

- Проверяет подписку на канал (через `getChatMember`)
- Главное меню с кнопками:
  - **ℹ️ Информация**
  - **✅ Проверить подписку**

### Важно

Чтобы бот мог проверять подписку, добавь **бота в канал администратором**. Иначе Telegram API не даст получить статус участника.

### Запуск на Replit

1. Создай Repl (Python) и загрузи сюда файлы проекта (или импортируй из GitHub).
2. В Replit открой **Secrets / Environment variables** и добавь:
   - `BOT_TOKEN`
   - `CHANNEL_ID` (например `@my_channel` или `-100...`)
   - (опционально) `CHANNEL_LINK` (например `https://t.me/my_channel`)
3. Нажми **Run**.

### Локальный запуск (Windows PowerShell)

```powershell
cd "c:\Users\pickk\OneDrive\Рабочий стол\tgbot"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
notepad .env
python bot.py
```

Содержимое `.env`:

```
BOT_TOKEN=123456789:ABC...
CHANNEL_ID=@your_channel_username
CHANNEL_LINK=https://t.me/your_channel_username
```

