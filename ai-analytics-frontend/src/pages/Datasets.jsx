import { useEffect, useState } from "react";
import { getDatasets, deleteDataset } from "../api";

const t = {
  ru: {
    title: "Датасеты",
    empty: "Нет загруженных датасетов. Загрузи CSV сначала.",
    confirmDelete: "Удалить этот датасет?",
    errorPrefix: "Ошибка: ",
    rows: "строк",
    columns: "колонок",
    dateLocale: "ru-RU"
  },
  en: {
    title: "Datasets",
    empty: "No datasets uploaded yet. Please upload a CSV first.",
    confirmDelete: "Are you sure you want to delete this dataset?",
    errorPrefix: "Error: ",
    rows: "rows",
    columns: "columns",
    dateLocale: "en-US"
  }
};

export default function Datasets({ onSelect, lang = "ru" }) {
  const currentText = t[lang] || t.ru;
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = () => {
    getDatasets()
      .then((r) => setDatasets(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm(currentText.confirmDelete)) return;

    console.log("Попытка удалить ID:", id);

    try {
      const response = await deleteDataset(id);
      console.log("Ответ сервера:", response.data);
      
      setDatasets(prev => prev.filter(d => d.id !== id));
    } catch (err) {
      console.error("ПОЛНАЯ ОШИБКА:", err);
      console.error("ДЕТАЛИ ОТВЕТА:", err.response?.data);
      
      alert(`${currentText.errorPrefix}${err.response?.data?.detail || err.message}`);
    }
  };

  if (loading) return <div className="spinner" />;

  return (
    <div>
      <h1>{currentText.title}</h1>

      {datasets.length === 0 ? (
        <div className="empty">{currentText.empty}</div>
      ) : (
        datasets.map((d) => (
          <div
            key={d.id}
            className="dataset-item"
            onClick={() => onSelect(d)}
            style={{ position: 'relative' }}
          >
            <div>
              <div className="ds-name">{d.name}</div>
              <div className="ds-meta">
                {d.row_count} {currentText.rows} · {d.columns?.length} {currentText.columns} ·{" "}
                {new Date(d.created_at).toLocaleDateString(currentText.dateLocale)}
              </div>
              <div style={{ marginTop: 6 }}>
                {d.columns?.slice(0, 5).map((col) => (
                  <span key={col} className="tag">{col}</span>
                ))}
                {d.columns?.length > 5 && (
                  <span className="tag">+{d.columns.length - 5}</span>
                )}
              </div>
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
              <button 
                onClick={(e) => handleDelete(e, d.id)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '18px',
                  color: '#ef4444',
                  padding: '5px'
                }}
              >
                🗑️
              </button>
              <span className="badge">#{d.display_number}</span>
            </div>
          </div>
        ))
      )}
    </div>
  );
}