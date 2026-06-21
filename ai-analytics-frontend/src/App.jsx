import { useState, useEffect } from "react";
import "./App.css";
import Upload from "./pages/Upload";
import Datasets from "./pages/Datasets";
import Chat from "./pages/Chat";
import Analytics from "./pages/Analytics";
import Reports from "./pages/Reports";
import Dashboard from "./pages/Dashboard";
import Auth from "./pages/Auth";
import { getDatasets } from "./api";
import Toast from "./components/Toast";
import { translations } from "./utils/translations";

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [selectedDataset, setSelected] = useState(null);
  const [datasets, setDatasets] = useState([]);
  const [theme, setTheme] = useState(() =>
    localStorage.getItem("theme") || "light"
  );

  const [lang, setLang] = useState(() => localStorage.getItem("lang") || "ru");

  const toggleLang = () => {
    const nextLang = lang === "ru" ? "en" : "ru";
    setLang(nextLang);
    localStorage.setItem("lang", nextLang);
  };

  const t = translations[lang] || translations.ru;

  const PAGES = [
    { id: "dashboard", label: t.dashboard, icon: "🏠" },
    { id: "upload", label: t.upload, icon: "📂" },
    { id: "datasets", label: t.datasets, icon: "🗄️" },
    { id: "analytics", label: t.analytics, icon: "📊" },
    { id: "chat", label: t.chat, icon: "💬" },
    { id: "reports", label: t.reports, icon: "📄" }
  ];

  const [isAuth, setIsAuth] = useState(() => !!localStorage.getItem("token"));
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("user") || "null");
    } catch {
      return null;
    }
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    const token = localStorage.getItem("token");
    setIsAuth(!!token);
    if (token) {
      setCurrentUser(JSON.parse(localStorage.getItem("user") || "null"));
    }
  }, []);

  const toggleTheme = () =>
    setTheme((t) => (t === "light" ? "dark" : "light"));

  const loadDatasets = () => {
    getDatasets()
      .then((r) => setDatasets(r.data))
      .catch(console.error);
  };

  useEffect(() => {
    if (isAuth) {
      loadDatasets();
    }
  }, [isAuth]);

  const handleSelectDataset = (ds) => {
    setSelected(ds);
    setPage("analytics");
  };

  const handleUploaded = () => {
    loadDatasets();
    setPage("datasets");
  };

  const handleAuthSuccess = () => {
    setIsAuth(true);
    setCurrentUser(JSON.parse(localStorage.getItem("user") || "null"));
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setSelected(null);
    setDatasets([]);
    setCurrentUser(null);
    setIsAuth(false);
  };

  if (!isAuth) {
    return <Auth onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <div className="layout">
      <div
  className={`sidebar-overlay ${sidebarOpen ? "visible" : ""}`}
  onClick={() => setSidebarOpen(false)}
/>
<div className="mobile-topbar">
  <button className="burger-btn" onClick={() => setSidebarOpen(true)}>☰</button>
  <span className="topbar-title">AI ANALYTICS</span>
</div>
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-logo">
          <span /> AI ANALYTICS
        </div>
        <Toast />

        <div className="sidebar-nav">
          {PAGES.map((p) => (
            <button
              key={p.id}
              className={`nav-btn ${page === p.id ? "active" : ""}`}
              onClick={() => { setPage(p.id); setSidebarOpen(false); }}
            >
              {p.icon} {p.label}
            </button>
          ))}
        </div>

        <div className="sidebar-footer">
          {selectedDataset && (
            <div className="ds-chip">
              <div className="chip-label">{lang === "ru" ? "Выбран датасет" : "Dataset selected"}</div>
              <div className="chip-name">{selectedDataset.name}</div>
              <div className="chip-meta">{selectedDataset.row_count} {lang === "ru" ? "строк" : "rows"}</div>
            </div>
          )}

          <button
            className="theme-toggle lang-btn"
            onClick={toggleLang}
            style={{
              marginBottom: "6px",
              width: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "flex-start",
              padding: "10px 16px"
            }}
          >
            {t.langBtn}
          </button>

          <button
            className="theme-toggle"
            onClick={toggleTheme}
            style={{
              marginBottom: "6px",
              width: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "flex-start",
              padding: "10px 16px"
            }}
          >
            {theme === "light" ? `🌙 ${t.themeDark}` : `☀️ ${t.themeLight}`}
          </button>

          <button
            className="theme-toggle logout-btn"
            onClick={handleLogout}
            style={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "flex-start",
              padding: "10px 16px"
            }}
          >
               ⛔ {t.logout}
          </button>
        </div>
      </aside>

      <main className="main">
        {/* 🚀 Теперь проп lang корректно передается во все компоненты */}
        {page === "upload" && <Upload onUploaded={handleUploaded} lang={lang} />}
        {page === "datasets" && <Datasets onSelect={handleSelectDataset} datasets={datasets} onRefresh={loadDatasets} lang={lang} />}
        {page === "analytics" && <Analytics dataset={selectedDataset} lang={lang} />}
        {page === "chat" && <Chat dataset={selectedDataset} lang={lang} />}
        {page === "reports" && <Reports dataset={selectedDataset} lang={lang} />}
        {page === "dashboard" && <Dashboard datasets={datasets} user={currentUser} lang={lang} />}
      </main>
    </div>
  );
}