from groq import Groq
from dotenv import load_dotenv
import os
import json
import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Dataset, DatasetData, ChatHistory

load_dotenv()
print("GROQ KEY LOADED:", bool(os.getenv("GROQ_API_KEY")), os.getenv("GROQ_API_KEY")[:8] if os.getenv("GROQ_API_KEY") else None)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SQL_KEYWORDS = [
    "сколько строк", "сколько колонок", "среднее", "средняя", "минимум", "максимум",
    "мин", "макс", "сумма", "количество", "count", "average", "mean",
    "max", "min", "sum", "total", "пропуски", "пустые", "missing",
    "топ", "top", "категории", "уникальные", "unique",
]

SQL_PATTERNS = [
    r"(сколько|сколько|count|количество)\s+(строк|колонок|записей)",
    r"(пропуск|пуст|missing|null)\w*",
    r"(уникаль|unique|distinct)",
    r"(средн|avg|average|mean|сумм|sum|total|минимум|min|максимум|max)",
    r"(топ|top|лидер|самый\s+(част|популяр)|групп|group)",
    r"(больше|меньше|выше|ниже|равно|равны|>=|<=|>|<)",
    r"(сравн|compare|vs|по\s+(столб|колонк)",
]


def should_use_sql(question: str) -> bool:
    q = question.lower()

    sql_keywords = {
        'count': ['строк', 'колонок', 'записей', 'count'],
        'missing': ['пропуск', 'пуст', 'null', 'missing', 'nan'],
        'stats': ['средн', 'сумм', 'мин', 'макс', 'avg', 'sum', 'min', 'max'],
        'top': ['топ', 'лидер', 'самый част', 'group by'],
        'unique': ['тип', 'типов', 'типы', 'категор', 'вид', 'видов', 'уникаль', 'unique', 'distinct'],
    }

    for category, words in sql_keywords.items():
        if any(word in q for word in words):
            return True

    if re.search(r'\d+\s*(%|процент|>|>=|<|<=|равно|больше|меньше)', q):
        return True

    column_ops = ['по', 'в', 'для', 'где', 'из', 'среди']
    if any(op in q for op in column_ops) and len(q.split()) > 4:
        return True

    word_count = len(q.split())
    if 5 <= word_count <= 12:
        return word_count % 3 == 0

    return False


def answer_with_sql(question: str, db: Session, dataset_id: int) -> str:
    q = question.lower()
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    columns = dataset.columns or []

    if any(kw in q for kw in ["сколько строк", "count", "количество строк"]):
        row_count = db.query(DatasetData).filter(DatasetData.dataset_id == dataset_id).count()
        return f"В датасете **{row_count} строк**."

    if any(kw in q for kw in ["сколько колонок", "количество колонок"]):
        return f"В датасете **{len(columns)} колонок**: {', '.join(columns)}."

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
            return "Пропущенных значений нет во всех колонках."
        return "Пропуски:\n" + "\n".join(missing_lines)

    if any(kw in q for kw in ["уникальные", "unique"]):
        lines = []
        for col in columns[:5]:
            result = db.execute(text("""
                SELECT COUNT(DISTINCT row_data->>:col) as unique_count
                FROM dataset_data
                WHERE dataset_id = :dataset_id AND row_data->>:col IS NOT NULL
            """), {"dataset_id": dataset_id, "col": col}).scalar()
            lines.append(f"`{col}`: **{result}** уникальных")
        return "Уникальные значения:\n" + "\n".join(lines)

    if any(kw in q for kw in ["топ", "top", "категории"]):
        lines = []
        for col in columns[:3]:
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
        return "Топ значения:\n" + "\n".join(lines)

    numeric_results = {}
    for col in columns:
        try:
            agg = db.execute(text("""
                SELECT
                    AVG((row_data->>:col)::numeric) as avg_val,
                    MIN((row_data->>:col)::numeric) as min_val,
                    MAX((row_data->>:col)::numeric) as max_val,
                    SUM((row_data->>:col)::numeric) as sum_val
                FROM dataset_data
                WHERE dataset_id = :dataset_id
                AND row_data->>:col ~ '^[0-9.+-]+$'
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
            return "Средние значения:\n" + "\n".join(lines)
        elif any(kw in q for kw in ["максимум", "макс", "max"]):
            lines = [f"`{col}`: **{data['max']}**" for col, data in numeric_results.items()]
            return "Максимумы:\n" + "\n".join(lines)
        elif any(kw in q for kw in ["минимум", "мин", "min"]):
            lines = [f"`{col}`: **{data['min']}**" for col, data in numeric_results.items()]
            return "Минимумы:\n" + "\n".join(lines)
        elif any(kw in q for kw in ["сумма", "sum", "total"]):
            lines = [f"`{col}`: **{data['sum']}**" for col, data in numeric_results.items()]
            return "Суммы:\n" + "\n".join(lines)
        lines = []
        for col, data in numeric_results.items():
            lines.append(f"`{col}`: avg={data['avg']}, min={data['min']}, max={data['max']}")
        return "Полная статистика:\n" + "\n".join(lines)

    return f"Датасет: **{dataset.name}**\nСтрок: {dataset.row_count}\nКолонки: {', '.join(columns[:5])}..."


def answer_with_ai(
    user_question: str,
    dataset_summary: dict,
    chat_history: list,
) -> str:
    has_system = chat_history and chat_history[0].get("role") == "system"
    lang_instruction = chat_history[0]["content"] if has_system else (
        "You are an expert AI data analyst. ALWAYS answer in Russian."
    )
    history_rest = chat_history[1:] if has_system else chat_history

    system_prompt = (
        lang_instruction +
        "\n\nAnswer questions based ONLY on the dataset data below. "
        "Be clear and concise. Remember the context of previous messages. "
        "NEVER use Chinese, Japanese, or any other language characters. Only use the detected language."
    )

    dataset_context = (
        f"Датасет: {dataset_summary.get('name')}\n"
        f"Строк: {dataset_summary.get('row_count')}\n"
        f"Колонок: {dataset_summary.get('column_count')}\n"
        f"Колонки: {', '.join(dataset_summary.get('columns', []))}\n\n"
        f"Числовая статистика:\n{format_averages(dataset_summary.get('averages', {}))}\n\n"
        f"Топ категорий:\n{format_categories(dataset_summary.get('top_categories', {}))}\n"
    )

    messages = [
        {"role": "system", "content": system_prompt + "\n\nДанные:\n" + dataset_context}
    ]

    for msg in history_rest[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

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
        lines.append(f"  {col}: среднее={stats.get('mean')}, мин={stats.get('min')}, макс={stats.get('max')}")
    return "\n".join(lines)


def format_categories(categories: dict) -> str:
    if not categories:
        return "нет текстовых данных"
    lines = []
    for col, values in categories.items():
        top = ", ".join([f"{v['value']}({v['count']})" for v in values[:3]])
        lines.append(f"  {col}: {top}")
    return "\n".join(lines)


def generate_report(dataset_summary: dict, lang: str = "ru") -> dict:
    lang_name = "Russian" if lang == "ru" else "English"
    system_prompt = (
        f"You are a professional business analyst.\n"
        f"You are given dataset statistics. Generate a business report.\n"
        f"ALWAYS write all text content (title, summary, findings, recommendations, risks) in {lang_name}.\n\n"
        f"Respond ONLY with valid JSON, no markdown, no explanations. Format:\n"
        '{{\n'
        '  "title": "report title",\n'
        '  "summary": "brief 2-3 sentence summary",\n'
        '  "findings": ["finding 1", "finding 2", "finding 3"],\n'
        '  "recommendations": ["recommendation 1", "recommendation 2"],\n'
        '  "risks": ["risk 1", "risk 2"]\n'
        '}}'
    )

    dataset_context = (
        f"Датасет: {dataset_summary.get('name')}\n"
        f"Строк: {dataset_summary.get('row_count')}\n"
        f"Колонок: {dataset_summary.get('column_count')}\n"
        f"Колонки: {', '.join(dataset_summary.get('columns', []))}\n\n"
        f"Числовая статистика:\n{format_averages(dataset_summary.get('averages', {}))}\n\n"
        f"Топ категорий:\n{format_categories(dataset_summary.get('top_categories', {}))}\n\n"
        f"Пропущенные значения:\n{format_missing(dataset_summary.get('missing_values', {}))}\n"
    )

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

    try:
        clean = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(clean)
    except Exception:
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
        for col in columns[:8]:
            try:
                cnt = db.execute(text("""
                    SELECT COUNT(*) FROM dataset_data
                    WHERE dataset_id = :id AND (row_data->>:col IS NULL OR row_data->>:col = '' OR row_data->>:col = 'null')
                """), {"id": dataset_id, "col": col}).scalar()
                if cnt > 0:
                    missing[col] = int(cnt)
            except Exception:
                db.rollback()
                continue
        if missing:
            result["data"]["missing_values"] = missing
            return result

    # Unique types / categories
    if any(kw in q for kw in ["тип", "типов", "типы", "категор", "вид", "видов", "уникаль", "unique", "distinct"]):
        unique_values = {}
        for col in columns:
            try:
                rows = db.execute(text("""
                    SELECT DISTINCT row_data->>:col as val
                    FROM dataset_data
                    WHERE dataset_id = :id AND row_data->>:col IS NOT NULL
                    ORDER BY val
                    LIMIT 50
                """), {"id": dataset_id, "col": col}).fetchall()
                if rows:
                    vals = [r.val for r in rows if r.val]
                    non_numeric = [v for v in vals if not v.replace('.', '').replace('-', '').isdigit()]
                    if non_numeric:
                        unique_values[col] = {
                            "count": len(vals),
                            "values": non_numeric[:20]
                        }
            except Exception:
                db.rollback()
                continue
        if unique_values:
            result["data"]["unique_values"] = unique_values
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
        except Exception:
            db.rollback()
            continue

    if numeric_stats:
        result["data"]["numeric_stats"] = numeric_stats
        return result

    return None


def answer_with_ai_explain(question: str, sql_data: dict, dataset_summary: dict, chat_history: list) -> str:
    """AI explains raw SQL results naturally."""
    sql_context = (
        f"SQL Results: {question}\n"
        f"{json.dumps(sql_data['data'], indent=2, ensure_ascii=False)}\n"
    )

    has_system = chat_history and chat_history[0].get("role") == "system"
    lang_instruction = chat_history[0]["content"] if has_system else (
        "You are an expert AI data analyst. ALWAYS answer in Russian."
    )
    history_rest = chat_history[1:] if has_system else chat_history

    system_prompt = (
        lang_instruction +
        "\n\nExplain the SQL results below in plain language. "
        "Use **bold** for important numbers. Be concise and natural. "
        "NEVER use Chinese, Japanese, or any other language characters. Only use the detected language.\n\n"
        f"Dataset: {dataset_summary['name']} ({dataset_summary['row_count']} rows)\n"
        f"{sql_context}"
    )

    messages = [{"role": "system", "content": system_prompt}]

    for msg in history_rest[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=400,
        temperature=0.1
    )

    return response.choices[0].message.content