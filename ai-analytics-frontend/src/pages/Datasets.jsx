import { useEffect, useState } from "react";
import { getDatasets, deleteDataset } from "../api"; // 1. Добавили импорт

export default function Datasets({ onSelect }) {
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

  // 2. Функция удаления
  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm("Удалить этот датасет?")) return;

    console.log("Попытка удалить ID:", id); // Проверим, передается ли ID

    try {
      const response = await deleteDataset(id);
      console.log("Ответ сервера:", response.data);
      
      // Обновляем список локально
      setDatasets(prev => prev.filter(d => d.id !== id));
    } catch (err) {
      // ВЫВОДИМ РЕАЛЬНУЮ ОШИБКУ В КОНСОЛЬ
      console.error("ПОЛНАЯ ОШИБКА:", err);
      console.error("ДЕТАЛИ ОТВЕТА:", err.response?.data);
      
      alert(`Ошибка: ${err.response?.data?.detail || err.message}`);
    }
  };

  if (loading) return <div className="spinner" />;

  return (
    <div>
      <h1>Датасеты</h1>

      {datasets.length === 0 ? (
        <div className="empty">Нет загруженных датасетов. Загрузи CSV сначала.</div>
      ) : (
        datasets.map((d) => (
          <div
            key={d.id}
            className="dataset-item"
            onClick={() => onSelect(d)}
            style={{ position: 'relative' }} // Нужно для позиционирования кнопки
          >
            <div>
              <div className="ds-name">{d.name}</div>
              <div className="ds-meta">
                {d.row_count} строк · {d.columns?.length} колонок ·{" "}
                {new Date(d.created_at).toLocaleDateString("ru-RU")}
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
            
            {/* 3. Кнопка удаления */}
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
              <span className="badge">#{d.id}</span>
            </div>
          </div>
        ))
      )}
    </div>
  );
}