import { useState, useEffect } from "react";
import "./App.css";
import Upload    from "./pages/Upload";
import Datasets  from "./pages/Datasets";
import Chat      from "./pages/Chat";
import Analytics from "./pages/Analytics";
import Reports   from "./pages/Reports";
import { getDatasets } from "./api";

const PAGES = [
  { id: "upload",    label: "Загрузить CSV", icon: "📂" },
  { id: "datasets",  label: "Датасеты",      icon: "🗄️" },
  { id: "analytics", label: "Аналитика",     icon: "📊" },
  { id: "chat",      label: "Чат с AI",      icon: "💬" },
  { id: "reports",   label: "Отчёты",        icon: "📄" },
];

export default function App() {
  const [page, setPage]                = useState("upload");
  const [selectedDataset, setSelected] = useState(null);
  const [datasets, setDatasets]        = useState([]);
  const [theme, setTheme]              = useState(() =>
    localStorage.getItem("theme") || "light"
  );

  // применяем тему на <html>
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () =>
    setTheme((t) => (t === "light" ? "dark" : "light"));

  const loadDatasets = () => {
    getDatasets().then((r) => setDatasets(r.data)).catch(console.error);
  };

  useEffect(() => { loadDatasets(); }, []);

  const handleSelectDataset = (ds) => {
    setSelected(ds);
    setPage("analytics");
  };

  const handleUploaded = () => {
    loadDatasets();
    setPage("datasets");
  };

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span /> AI ANALYTICS
        </div>

        {PAGES.map((p) => (
          <button
            key={p.id}
            className={`nav-btn ${page === p.id ? "active" : ""}`}
            onClick={() => setPage(p.id)}
          >
            {p.icon} {p.label}
          </button>
        ))}

        <div className="sidebar-footer">
          {selectedDataset && (
            <div className="ds-chip">
              <div className="chip-label">Выбран датасет</div>
              <div className="chip-name">{selectedDataset.name}</div>
              <div className="chip-meta">{selectedDataset.row_count} строк</div>
            </div>
          )}
          <button className="theme-toggle" onClick={toggleTheme}>
            {theme === "light" ? "🌙 Тёмная тема" : "☀️ Светлая тема"}
          </button>
        </div>
      </aside>

      <main className="main">
        {page === "upload"    && <Upload onUploaded={handleUploaded} />}
        {page === "datasets"  && <Datasets onSelect={handleSelectDataset} />}
        {page === "analytics" && <Analytics dataset={selectedDataset} />}
        {page === "chat"      && <Chat dataset={selectedDataset} />}
        {page === "reports"   && <Reports dataset={selectedDataset} />}
      </main>
    </div>
  );
}