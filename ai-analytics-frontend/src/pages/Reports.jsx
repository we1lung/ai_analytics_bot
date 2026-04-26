import { useEffect, useState } from "react";
import { generateReport, getReports, downloadReportPDF, downloadReportTXT, deleteReport } from "../api";

export default function Reports({ dataset }) {
  const [reports, setReports]   = useState([]);
  const [loading, setLoading]   = useState(false);
  const [generating, setGen]    = useState(false);
  const [selected, setSelected] = useState(null);
  const [error, setError]       = useState(null);

  useEffect(() => {
    if (!dataset) return;
    loadReports();
  }, [dataset]);

  const loadReports = () => {
    setLoading(true);
    getReports(dataset.id)
      .then((r) => setReports(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const handleDelete = async (e, reportId) => {
    e.stopPropagation();
    if (!window.confirm("Удалить этот отчёт?")) return;
    try {
      await deleteReport(dataset.id, reportId);
      setReports((prev) => prev.filter((r) => r.report_id !== reportId));
      if (selected?.report_id === reportId) setSelected(null);
    } catch {
      setError("Ошибка при удалении отчёта");
    }
  };

  const handleGenerate = async () => {
    setGen(true);
    setError(null);
    try {
      const r = await generateReport(dataset.id);
      setReports((prev) => [r.data, ...prev]);
      setSelected(r.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Ошибка генерации");
    } finally {
      setGen(false);
    }
  };

  const handleDownload = async (type) => {
    try {
      const fn = type === "pdf" ? downloadReportPDF : downloadReportTXT;
      const res = await fn(dataset.id, selected.report_id);
      const url = URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `report_${selected.report_id}.${type}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("Ошибка скачивания");
    }
  };

  if (!dataset) return <div className="empty">Выбери датасет из списка</div>;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h1>Отчёты: {dataset.name}</h1>
        <button className="btn btn-primary" onClick={handleGenerate} disabled={generating}>
          {generating ? "Генерирую..." : "Создать отчёт"}
        </button>
      </div>

      {generating && <div className="alert alert-success">AI анализирует данные... подожди 10-20 секунд</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: 20 }}>

        {/* список отчётов */}
        <div>
          {loading && <div className="spinner" />}
          {reports.length === 0 && !loading && (
            <div className="empty" style={{ padding: 20 }}>Нет отчётов</div>
          )}
          {reports.map((r) => (
            <div
              key={r.report_id}
              className={`report-card ${selected?.report_id === r.report_id ? "active" : ""}`}
              onClick={() => setSelected(r)}
            >
              <div className="rc-title">{r.title}</div>
              <div className="rc-date">{new Date(r.created_at).toLocaleString("ru-RU")}</div>
              <button className="rc-del" onClick={(e) => handleDelete(e, r.report_id)}>
                Удалить
              </button>
            </div>
          ))}
        </div>

        {/* детали отчёта */}
        {selected ? (
          <div className="card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
              <h2 style={{ fontSize: 18, fontWeight: 600 }}>{selected.title}</h2>
              <div style={{ display: "flex", gap: 8 }}>
                <button className="btn btn-ghost" onClick={() => handleDownload("txt")}>Скачать TXT</button>
                <button className="btn btn-primary" onClick={() => handleDownload("pdf")}>Скачать PDF</button>
              </div>
            </div>

            <div className="report-summary">
              <div className="section-label">SUMMARY</div>
              <p>{selected.summary}</p>
            </div>

            <div className="report-section findings">
              <div className="section-label">Findings</div>
              {selected.findings?.map((item, i) => (
                <div key={i} className="section-item">
                  <span className="section-num">{i + 1}</span>
                  <p>{item}</p>
                </div>
              ))}
            </div>

            <div className="report-section recommend">
              <div className="section-label">Recommendations</div>
              {selected.recommendations?.map((item, i) => (
                <div key={i} className="section-item">
                  <span className="section-num">{i + 1}</span>
                  <p>{item}</p>
                </div>
              ))}
            </div>

            <div className="report-section risks">
              <div className="section-label">Risks</div>
              {selected.risks?.map((item, i) => (
                <div key={i} className="section-item">
                  <span className="section-num">{i + 1}</span>
                  <p>{item}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="empty">Выбери отчёт из списка или создай новый</div>
        )}
      </div>
    </div>
  );
}