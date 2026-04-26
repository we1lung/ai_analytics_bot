from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Dataset, DatasetData, Report
from app.services import generate_report, format_averages, format_categories, format_missing
import pandas as pd
import os
from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_REGULAR = os.path.join(BASE_DIR, "fonts", "DejaVuSans.ttf")
FONT_BOLD    = os.path.join(BASE_DIR, "fonts", "DejaVuSans-Bold.ttf")

router = APIRouter(prefix="/reports", tags=["Reports"])


def build_summary(dataset, df) -> dict:
    """Собирает summary датасета для передачи в AI"""
    averages = {}
    for col in df.select_dtypes(include="number").columns:
        averages[col] = {
            "mean": round(float(df[col].mean()), 2),
            "min":  round(float(df[col].min()), 2),
            "max":  round(float(df[col].max()), 2),
        }

    categories = {}
    for col in df.select_dtypes(include="object").columns:
        top = df[col].value_counts().head(5)
        categories[col] = [{"value": str(v), "count": int(c)} for v, c in top.items()]

    missing = {}
    for col in df.columns:
        cnt = int(df[col].isnull().sum())
        missing[col] = {
            "missing_count": cnt,
            "missing_percent": round(cnt / len(df) * 100, 2),
        }

    return {
        "name": dataset.name,
        "row_count": dataset.row_count,
        "column_count": len(dataset.columns) if dataset.columns else 0,
        "columns": dataset.columns or [],
        "averages": averages,
        "top_categories": categories,
        "missing_values": missing,
    }


@router.post("/{dataset_id}/generate")
def generate(dataset_id: int, db: Session = Depends(get_db)):
    """Генерирует AI отчёт и сохраняет в БД"""

    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Датасет не найден")

    rows = db.query(DatasetData).filter(DatasetData.dataset_id == dataset_id).all()
    if not rows:
        raise HTTPException(status_code=404, detail="Данные пустые")

    df = pd.DataFrame([r.row_data for r in rows])
    dataset_summary = build_summary(dataset, df)

    try:
        result = generate_report(dataset_summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка AI: {str(e)}")

    report = Report(
        dataset_id=dataset_id,
        title=result.get("title", "Отчёт"),
        summary=result.get("summary"),
        findings=result.get("findings", []),
        recommendations=result.get("recommendations", []),
        risks=result.get("risks", []),
        raw_text=result.get("raw_text"),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "report_id": report.id,
        "title": report.title,
        "summary": report.summary,
        "findings": report.findings,
        "recommendations": report.recommendations,
        "risks": report.risks,
        "created_at": report.created_at,
    }


@router.get("/{dataset_id}")
def get_reports(dataset_id: int, db: Session = Depends(get_db)):
    """Список всех отчётов по датасету"""
    reports = (
        db.query(Report)
        .filter(Report.dataset_id == dataset_id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return [
        {
            "report_id": r.id,
            "title": r.title,
            "summary": r.summary,
            "findings": r.findings,
            "recommendations": r.recommendations,
            "risks": r.risks,
            "created_at": r.created_at,
        }
        for r in reports
    ]


@router.get("/{dataset_id}/{report_id}/download/pdf")
def download_pdf(dataset_id: int, report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.dataset_id == dataset_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Отчёт не найден")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_font("DejaVu", "", FONT_REGULAR)
    pdf.add_font("DejaVu", "B", FONT_BOLD)

    # заголовок
    pdf.set_font("DejaVu", "B", 18)
    pdf.cell(0, 12, report.title, ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 8, f"Сгенерировано: {report.created_at.strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    def section(title, items, is_list=True):
        pdf.set_font("DejaVu", "B", 13)
        pdf.set_fill_color(240, 240, 255)
        pdf.set_x(pdf.l_margin)
        pdf.cell(0, 10, title, ln=True, fill=True)
        pdf.ln(2)
        pdf.set_font("DejaVu", "", 11)
        w = pdf.w - pdf.l_margin - pdf.r_margin
        if is_list:
            for i, item in enumerate(items or [], 1):
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(w, 7, f"{i}. {item}", new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(w, 7, items or "", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    section("Summary", report.summary, is_list=False)
    section("Findings", report.findings)
    section("Recommendations", report.recommendations)
    section("Risks", report.risks)

    os.makedirs("/tmp/reports", exist_ok=True)
    path = f"/tmp/reports/report_{report_id}.pdf"
    pdf.output(path)

    return FileResponse(path, media_type="application/pdf", filename=f"report_{report_id}.pdf")

@router.get("/{dataset_id}/{report_id}/download/txt")
def download_txt(dataset_id: int, report_id: int, db: Session = Depends(get_db)):
    """Скачивает отчёт в формате .txt"""

    report = db.query(Report).filter(
        Report.id == report_id,
        Report.dataset_id == dataset_id
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Отчёт не найден")

    lines = [
        report.title,
        "=" * 60,
        "",
        "SUMMARY",
        "-" * 40,
        report.summary or "",
        "",
        "FINDINGS",
        "-" * 40,
    ]
    for i, f in enumerate(report.findings or [], 1):
        lines.append(f"{i}. {f}")

    lines += ["", "RECOMMENDATIONS", "-" * 40]
    for i, r in enumerate(report.recommendations or [], 1):
        lines.append(f"{i}. {r}")

    lines += ["", "RISKS", "-" * 40]
    for i, r in enumerate(report.risks or [], 1):
        lines.append(f"{i}. {r}")

    lines += ["", f"Generated: {report.created_at.strftime('%d.%m.%Y %H:%M')}"]

    os.makedirs("/tmp/reports", exist_ok=True)
    path = f"/tmp/reports/report_{report_id}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return FileResponse(
        path,
        media_type="text/plain",
        filename=f"report_{report_id}.txt",
    )

@router.delete("/{dataset_id}/{report_id}")
def delete_report(dataset_id: int, report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.dataset_id == dataset_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    db.delete(report)
    db.commit()
    return {"message": "Удалён"}