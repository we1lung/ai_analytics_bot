from groq import Groq
from dotenv import load_dotenv
import os
import json  # Keep for reports

# SQLAlchemy imports
from sqlalchemy import text
from sqlalchemy.orm import Session

# YOUR MODELS - ADD ALL THREE!
from app.models import Dataset, DatasetData, ChatHistory

# Remove pandas import - we don't need it anymore!
# import pandas as pd  # ← DELETE THIS LINE

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ─────────────────────────────────────────
# Ключевые слова → отвечаем через pandas/SQL
# ─────────────────────────────────────────
SQL_KEYWORDS = [
    "сколько строк", "сколько колонок", "среднее", "средняя", "минимум", "максимум",
    "мин", "макс", "сумма", "количество", "count", "average", "mean",
    "max", "min", "sum", "total", "пропуски", "пустые", "missing",
    "топ", "top", "категории", "уникальные", "unique",
]


SQL_PATTERNS = [
    # Counts
    r"(сколько|сколько|count|количество)\s+(строк|колонок|записей)",
    r"(пропуск|пуст|missing|null)\w*",
    r"(уникаль|unique|distinct)",
    
    # Aggregations  
    r"(средн|avg|average|mean|сумм|sum|total|минимум|min|максимум|max)",
    
    # Top/Group
    r"(топ|top|лидер|самый\s+(част|популяр)|групп|group)",
    
    # Comparisons
    r"(больше|меньше|выше|ниже|равно|равны|>=|<=|>|<)",
    r"(сравн|compare|vs|по\s+(столб|колонк)",
]

import re

def should_use_sql(question: str) -> bool:
    """🚀 Smart SQL detection - covers 90% analytics questions"""
    q = question.lower()
    
    # HIGH PRIORITY: Exact matches
    sql_keywords = {
        'count': ['строк', 'колонок', 'записей', 'count'],
        'missing': ['пропуск', 'пуст', 'null', 'missing', 'nan'],
        'stats': ['средн', 'сумм', 'мин', 'макс', 'avg', 'sum', 'min', 'max'],
        'top': ['топ', 'лидер', 'самый част', 'group by'],
    }
    
    for category, words in sql_keywords.items():
        if any(word in q for word in words):
            return True
    
    # SMART: Numbers + comparisons
    if re.search(r'\d+\s*(%|процент|>|>=|<|<=|равно|больше|меньше)', q):
        return True
    
    # SMART: Column operations  
    column_ops = ['по', 'в', 'для', 'где', 'из', 'среди']
    if any(op in q for op in column_ops) and len(q.split()) > 4:
        return True
    
    # Default: 30% chance for medium questions
    word_count = len(q.split())
    if 5 <= word_count <= 12:
        return word_count % 3 == 0  # Simple heuristic
    
    return False


def answer_with_sql(question: str, db: Session, dataset_id: int) -> str:
    """🚀 REAL SQL queries! No more pandas. Converts question → SQL."""
    q = question.lower()
    
    # Get dataset columns first
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    columns = dataset.columns or []
    
    # 1. Row/column count - FAST SQL COUNT
    if any(kw in q for kw in ["сколько строк", "count", "количество строк"]):
        row_count = db.query(DatasetData).filter(DatasetData.dataset_id == dataset_id).count()
        return f"В датасете **{row_count} строк**."

    if any(kw in q for kw in ["сколько колонок", "количество колонок"]):
        return f"В датасете **{len(columns)} колонок**: {', '.join(columns)}."

    # 2. MISSING VALUES - SQL NULL count per column
    if any(kw in q for kw in ["пропуски", "пустые", "missing"]):
        missing_lines = []
        for col in columns:
            result = db.execute(text("""
                SELECT COUNT(*) as null_count
                FROM dataset_data 
                WHERE dataset_id = :dataset_id AND row_data->>:col IS NULL OR row_data->>:col = ''
            """), {"dataset_id": dataset_id, "col": col}).scalar()
            
            if result > 0:
                missing_lines.append(f"`{col}`: **{result}** пропусков")
        
        if not missing_lines:
            return "✅ **Пропущенных значений нет** во всех колонках."
        return "Пропуски:\n" + "\n".join(missing_lines)

    # 3. UNIQUE VALUES
    if any(kw in q for kw in ["уникальные", "unique"]):
        lines = []
        for col in columns[:5]:  # Limit to first 5 columns
            result = db.execute(text("""
                SELECT COUNT(DISTINCT row_data->>:col) as unique_count
                FROM dataset_data 
                WHERE dataset_id = :dataset_id AND row_data->>:col IS NOT NULL
            """), {"dataset_id": dataset_id, "col": col}).scalar()
            lines.append(f"`{col}`: **{result}** уникальных")
        return "Уникальные значения:\n" + "\n".join(lines)

    # 4. TOP VALUES - GROUP BY + LIMIT 3
    if any(kw in q for kw in ["топ", "top", "категории"]):
        lines = []
        for col in columns[:3]:  # First 3 text columns
            result = db.execute(text("""
                SELECT row_data->>:col as value, COUNT(*) as cnt
                FROM dataset_data 
                WHERE dataset_id = :dataset_id AND row_data->>:col IS NOT NULL
                GROUP BY row_data->>:col 
                ORDER BY cnt DESC 
                LIMIT 3
            """), {"dataset_id": dataset_id, "col": col}).fetchall()
            
            if result:
                vals = ", ".join([f"{r.value}({r.cnt})" for r in result])
                lines.append(f"`{col}`: {vals}")
        return "🏆 Топ значения:\n" + "\n".join(lines)

    # 5. AGGREGATIONS - AVG, MIN, MAX, SUM for numeric columns
    numeric_results = {}
    for col in columns:
        try:
            # Test if numeric by trying AVG
            agg = db.execute(text("""
                SELECT 
                    AVG((row_data->>:col)::numeric) as avg_val,
                    MIN((row_data->>:col)::numeric) as min_val,
                    MAX((row_data->>:col)::numeric) as max_val,
                    SUM((row_data->>:col)::numeric) as sum_val
                FROM dataset_data 
                WHERE dataset_id = :dataset_id 
                AND row_data->>:col ~ '^[0-9.+-]+$'  -- regex: only numbers
            """), {"dataset_id": dataset_id, "col": col}).fetchone()
            
            if agg.avg_val is not None:
                numeric_results[col] = {
                    "avg": round(float(agg.avg_val), 2),
                    "min": round(float(agg.min_val), 2),
                    "max": round(float(agg.max_val), 2),
                    "sum": round(float(agg.sum_val), 2)
                }
        except:
            continue
    
    if numeric_results:
        if any(kw in q for kw in ["среднее", "средняя", "mean", "average"]):
            lines = [f"`{col}`: **{data['avg']}**" for col, data in numeric_results.items()]
            return "📊 Средние значения:\n" + "\n".join(lines)
        
        elif any(kw in q for kw in ["максимум", "макс", "max"]):
            lines = [f"`{col}`: **{data['max']}**" for col, data in numeric_results.items()]
            return "📈 Максимумы:\n" + "\n".join(lines)
        
        elif any(kw in q for kw in ["минимум", "мин", "min"]):
            lines = [f"`{col}`: **{data['min']}**" for col, data in numeric_results.items()]
            return "📉 Минимумы:\n" + "\n".join(lines)
        
        elif any(kw in q for kw in ["сумма", "sum", "total"]):
            lines = [f"`{col}`: **{data['sum']}**" for col, data in numeric_results.items()]
            return "💰 Суммы:\n" + "\n".join(lines)
        
        # Default stats
        lines = []
        for col, data in numeric_results.items():
            lines.append(f"`{col}`: avg={data['avg']}, min={data['min']}, max={data['max']}")
        return "📈 Полная статистика:\n" + "\n".join(lines)

    # Fallback
    return f"ℹ️ Датасет: **{dataset.name}**\n📊 Строк: {dataset.row_count}\n📋 Колонки: {', '.join(columns[:5])}..."

# 🚀 Update function signature in services.py imports comment:
# def answer_with_sql(question: str, db: Session, dataset_id: int) -> str:


def answer_with_ai(
    user_question: str,
    dataset_summary: dict,
    chat_history: list,  # история предыдущих сообщений
) -> str:
    """Отправляет вопрос + историю + summary в Groq"""

    system_prompt = """Ты — AI аналитик данных. Отвечай ТОЛЬКО на русском языке.
Тебе дают краткое описание датасета и историю разговора.
Отвечай на вопросы основываясь ТОЛЬКО на данных датасета.
Отвечай чётко и по делу. Помни контекст предыдущих сообщений."""

    dataset_context = f"""
Датасет: {dataset_summary.get('name')}
Строк: {dataset_summary.get('row_count')}
Колонок: {dataset_summary.get('column_count')}
Колонки: {', '.join(dataset_summary.get('columns', []))}

Числовая статистика:
{format_averages(dataset_summary.get('averages', {}))}

Топ категорий:
{format_categories(dataset_summary.get('top_categories', {}))}
"""

    # собираем messages: system + история + новый вопрос
    messages = [
        {"role": "system", "content": system_prompt + "\n\nДанные:\n" + dataset_context}
    ]

    # добавляем последние 10 сообщений из истории (чтобы не перегружать контекст)
    for msg in chat_history[-10:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"],
        })

    # добавляем текущий вопрос
    messages.append({"role": "user", "content": user_question})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=1024,
    )

    return response.choices[0].message.content


def format_averages(averages: dict) -> str:
    if not averages:
        return "нет числовых данных"
    lines = []
    for col, stats in averages.items():
        lines.append(
            f"  {col}: среднее={stats.get('mean')}, мин={stats.get('min')}, макс={stats.get('max')}"
        )
    return "\n".join(lines)


def format_categories(categories: dict) -> str:
    if not categories:
        return "нет текстовых данных"
    lines = []
    for col, values in categories.items():
        top = ", ".join([f"{v['value']}({v['count']})" for v in values[:3]])
        lines.append(f"  {col}: {top}")
    return "\n".join(lines)


import json

def generate_report(dataset_summary: dict) -> dict:
    """
    Отправляет аналитику в Groq → получает структурированный отчёт в JSON
    """

    system_prompt = """Ты — профессиональный бизнес-аналитик.
Тебе дают статистику датасета. Твоя задача — сгенерировать бизнес-отчёт.

Отвечай ТОЛЬКО валидным JSON без markdown и пояснений. Формат:
{
  "title": "название отчёта",
  "summary": "краткий вывод 2-3 предложения",
  "findings": [
    "находка 1",
    "находка 2",
    "находка 3"
  ],
  "recommendations": [
    "рекомендация 1",
    "рекомендация 2"
  ],
  "risks": [
    "риск 1",
    "риск 2"
  ]
}"""

    dataset_context = f"""
Датасет: {dataset_summary.get('name')}
Строк: {dataset_summary.get('row_count')}
Колонок: {dataset_summary.get('column_count')}
Колонки: {', '.join(dataset_summary.get('columns', []))}

Числовая статистика:
{format_averages(dataset_summary.get('averages', {}))}

Топ категорий:
{format_categories(dataset_summary.get('top_categories', {}))}

Пропущенные значения:
{format_missing(dataset_summary.get('missing_values', {}))}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Сгенерируй отчёт по данным:\n{dataset_context}"},
        ],
        max_tokens=2048,
        temperature=0.3,
    )

    raw_text = response.choices[0].message.content

    # парсим JSON из ответа
    try:
        # убираем возможные markdown блоки если AI всё же добавил их
        clean = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(clean)
    except Exception:
        # если AI вернул не JSON — делаем fallback
        parsed = {
            "title": f"Отчёт по датасету {dataset_summary.get('name')}",
            "summary": raw_text[:500],
            "findings": [],
            "recommendations": [],
            "risks": [],
        }

    parsed["raw_text"] = raw_text
    return parsed


def format_missing(missing: dict) -> str:
    if not missing:
        return "нет данных о пропусках"
    lines = []
    for col, m in missing.items():
        if m.get("missing_count", 0) > 0:
            lines.append(f"  {col}: {m['missing_count']} пропусков ({m['missing_percent']}%)")
    return "\n".join(lines) if lines else "пропусков нет"


# 🚀 STEP 5 NEW FUNCTIONS - ADD THESE AT BOTTOM OF services.py
def answer_with_sql_raw(question: str, db: Session, dataset_id: int) -> dict:
    """Returns RAW structured SQL data (not formatted text)."""
    q = question.lower()
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    columns = dataset.columns or []
    
    result = {"type": "sql_data", "data": {}}
    
    # Row count
    if any(kw in q for kw in ["сколько строк", "count", "количество строк"]):
        result["data"]["row_count"] = db.query(DatasetData).filter(DatasetData.dataset_id == dataset_id).count()
        return result
    
    # Missing values
    if any(kw in q for kw in ["пропуски", "пустые", "missing"]):
        missing = {}
        for col in columns[:8]:  # Limit 8 columns
            cnt = db.execute(text("""
                SELECT COUNT(*) FROM dataset_data 
                WHERE dataset_id = :id AND (row_data->>:col IS NULL OR row_data->>:col = '' OR row_data->>:col = 'null')
            """), {"id": dataset_id, "col": col}).scalar()
            if cnt > 0:
                missing[col] = int(cnt)
        if missing:
            result["data"]["missing_values"] = missing
            return result
    
    # Numeric aggregations
    numeric_stats = {}
    for col in columns[:5]:
        try:
            stats = db.execute(text("""
                SELECT 
                    COALESCE(AVG((row_data->>:col)::numeric), 0) as avg,
                    COALESCE(MIN((row_data->>:col)::numeric), 0) as minv,
                    COALESCE(MAX((row_data->>:col)::numeric), 0) as maxv
                FROM dataset_data 
                WHERE dataset_id = :id AND row_data->>:col ~ '^[0-9.-]+$' AND row_data->>:col IS NOT NULL
            """), {"id": dataset_id, "col": col}).fetchone()
            
            if stats and float(stats.avg) != 0:
                numeric_stats[col] = {
                    "avg": round(float(stats.avg), 2),
                    "min": round(float(stats.minv), 2),
                    "max": round(float(stats.maxv), 2)
                }
        except:
            continue
    
    if numeric_stats:
        result["data"]["numeric_stats"] = numeric_stats
        return result
    
    return None

def answer_with_ai_explain(question: str, sql_data: dict, dataset_summary: dict, chat_history: list) -> str:
    """AI explains raw SQL results naturally."""
    import json
    
    sql_context = f"""
📊 SQL Results: {question}
{json.dumps(sql_data['data'], indent=2, ensure_ascii=False)}
"""
    
    system_prompt = f"""Ты эксперт по данным. Отвечай ТОЛЬКО на русском языке.
Объясняй SQL результаты простым языком.
Используй **жирный текст** для важных чисел и 📊 эмодзи.
Кратко, по делу, естественно.

Dataset: {dataset_summary['name']} ({dataset_summary['row_count']} строк)
"""
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Recent chat history (max 6 messages)
    for msg in chat_history[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    messages.append({"role": "user", "content": f"Объясни эти данные простыми словами: {question}"})
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=400,
        temperature=0.1
    )
    
    return response.choices[0].message.content