# AI File Analytics Bot

Full-stack платформа бизнес-аналитики с AI-чатом: загрузка данных, продвинутая аналитика и общение с LLM на естественном языке для получения инсайтов.

🔗 **Демо:** [ai-analytics-chat-bot.netlify.app](https://ai-analytics-chat-bot.netlify.app)

---

## Возможности

- 📊 Загрузка и обработка CSV/данных, визуализация через интерактивные графики (Recharts)
- 🤖 AI-чат по данным на базе LLM (Groq API, LLaMA 3.3 70B) — вопросы на естественном языке
- 🔍 Продвинутая аналитика: корреляционные тепловые карты, детекция аномалий (Isolation Forest), трендовый анализ
- 🔐 JWT-аутентификация и ролевой доступ (RBAC)
- 📄 Генерация отчётов

## Стек

| Слой | Технологии |
|---|---|
| Backend | FastAPI, SQLAlchemy, PostgreSQL |
| Frontend | React, Recharts |
| AI | Groq API (LLaMA 3.3 70B) |
| Deploy | Railway (backend), Netlify (frontend) |

## Архитектура

```
Frontend (React, Netlify)
        │
        ▼
Backend (FastAPI, Railway)
        │
   ┌────┴────┐
   ▼         ▼
PostgreSQL   Groq API (LLaMA 3.3)
```

## Запуск локально

```bash
# Backend
git clone https://github.com/we1lung/ai_analytics_bot.git
cd ai_analytics_bot/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# заполнить .env: DATABASE_URL, GROQ_API_KEY, JWT_SECRET
uvicorn main:app --reload

# Frontend
cd ../frontend
npm install
npm run dev
```

## Переменные окружения

```
DATABASE_URL=postgresql://user:pass@host:port/dbname
GROQ_API_KEY=your_groq_api_key
JWT_SECRET=your_secret_key
```

## Скриншоты

*(вставь сюда 2-3 скриншота дашборда и AI-чата — это самое важное для README)*

## Автор

Айдар Бу — [GitHub](https://github.com/we1lung) · [LinkedIn](https://www.linkedin.com/in/veilung-aidar-bu-4306b7362/)
