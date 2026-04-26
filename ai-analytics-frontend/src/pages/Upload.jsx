import { useState, useRef } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

export default function Upload({ onUploaded }) {
  const [file, setFile]         = useState(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus]     = useState(null); // "uploading" | "success" | "error"
  const [error, setError]       = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef                = useRef();

  const handleFile = (f) => {
    if (!f) return;
    if (!f.name.endsWith(".csv")) {
      setError("Только .csv файлы");
      return;
    }
    setFile(f);
    setError(null);
    setStatus(null);
    setProgress(0);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);

    setStatus("uploading");
    setProgress(0);
    setError(null);

    try {
      await axios.post(`${API_URL}/datasets/upload`, form, {
        onUploadProgress: (e) => {
          const pct = Math.round((e.loaded * 100) / (e.total || 1));
          setProgress(pct);
        },
      });
      setStatus("success");
      setProgress(100);
      setTimeout(() => onUploaded(), 800);
    } catch (e) {
      setStatus("error");
      setError(e.response?.data?.detail || "Ошибка загрузки");
    }
  };

  return (
    <div>
      <h1>Загрузить CSV</h1>

      {/* Зона drag & drop */}
      <div
        className={`upload-zone ${dragOver ? "drag-over" : ""}`}
        onClick={() => inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <div className="upload-icon">📂</div>
        {file ? (
          <>
            <p><strong>{file.name}</strong></p>
            <p style={{ marginTop: 4 }}>{(file.size / 1024).toFixed(1)} KB</p>
          </>
        ) : (
          <>
            <p><strong>Перетащи CSV</strong> или нажми для выбора</p>
            <p style={{ marginTop: 6, fontSize: 12 }}>Поддерживается только формат .csv</p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          style={{ display: "none" }}
          onChange={(e) => handleFile(e.target.files[0])}
        />
      </div>

      {/* Прогресс-бар */}
      {status === "uploading" && (
        <div style={{ marginTop: 16 }}>
          <div className="progress-wrap">
            <div className="progress-bar" style={{ width: `${progress}%` }} />
          </div>
          <div className="progress-label">Загрузка... {progress}%</div>
        </div>
      )}

      {/* Успех */}
      {status === "success" && (
        <div className="alert alert-success" style={{ marginTop: 16 }}>
          ✅ Файл загружен! Переходим к датасетам...
        </div>
      )}

      {/* Ошибка */}
      {error && (
        <div className="alert alert-error" style={{ marginTop: 16 }}>
          {error}
        </div>
      )}

      {/* Кнопка */}
      {file && status !== "success" && (
        <button
          className="btn btn-primary"
          style={{ marginTop: 20, width: "100%" }}
          onClick={handleUpload}
          disabled={status === "uploading"}
        >
          {status === "uploading" ? `Загружаю... ${progress}%` : "Загрузить"}
        </button>
      )}
    </div>
  );
}