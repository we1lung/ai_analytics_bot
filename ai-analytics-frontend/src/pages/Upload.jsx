import { useState, useRef } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

// Текстовые переводы без изменения структуры
const t = {
  ru: {
    title: "Загрузить датасет",
    dragText: "Перетащи файл",
    clickText: "или нажми для выбора",
    formats: "CSV, TXT или PDF",
    uploadingLabel: "Загрузка...",
    successAlert: "✅ Файл загружен! Переходим к датасетам...",
    btnUpload: "Загрузить",
    btnUploading: "Загружаю...",
    validationError: "Только файлы следующих форматов: ",
    defaultError: "Ошибка загрузки"
  },
  en: {
    title: "Upload Dataset",
    dragText: "Drag & drop a file here",
    clickText: "or click to select",
    formats: "CSV, TXT or PDF",
    uploadingLabel: "Uploading...",
    successAlert: "✅ File uploaded! Moving to datasets...",
    btnUpload: "Upload",
    btnUploading: "Uploading...",
    validationError: "Only the following formats are allowed: ",
    defaultError: "Upload failed"
  }
};

export default function Upload({ onUploaded, lang = "ru" }) {
  const currentText = t[lang] || t.ru;

  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef();

  const ALLOWED = [".csv", ".txt", ".pdf"];

  const handleFile = (f) => {
    if (!f) return;
    const ext = f.name.toLowerCase().slice(f.name.lastIndexOf("."));
    if (!ALLOWED.includes(ext)) {
      setError(`${currentText.validationError}${ALLOWED.join(", ")}`);
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
      const token = localStorage.getItem("token");
      await axios.post(`${API_URL}/datasets/upload`, form, {
        headers: { Authorization: `Bearer ${token}` },
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
      setError(e.response?.data?.detail || currentText.defaultError);
    }
  };

  return (
    <div>
      <h1>{currentText.title}</h1>

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
            <p><strong>{currentText.dragText}</strong> {currentText.clickText}</p>
            <p style={{ marginTop: 6, fontSize: 12 }}>{currentText.formats}</p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.txt,.pdf"
          style={{ display: "none" }}
          onChange={(e) => handleFile(e.target.files[0])}
        />
      </div>

      {status === "uploading" && (
        <div style={{ marginTop: 16 }}>
          <div className="progress-wrap">
            <div className="progress-bar" style={{ width: `${progress}%` }} />
          </div>
          <div className="progress-label">{currentText.uploadingLabel} {progress}%</div>
        </div>
      )}

      {status === "success" && (
        <div className="alert alert-success" style={{ marginTop: 16 }}>
          {currentText.successAlert}
        </div>
      )}

      {error && (
        <div className="alert alert-error" style={{ marginTop: 16 }}>
          {error}
        </div>
      )}

      {file && status !== "success" && (
        <button
          className="btn btn-primary"
          style={{ marginTop: 20, width: "100%" }}
          onClick={handleUpload}
          disabled={status === "uploading"}
        >
          {status === "uploading" ? `${currentText.btnUploading} ${progress}%` : currentText.btnUpload}
        </button>
      )}
    </div>
  );
}