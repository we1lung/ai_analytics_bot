const t = {
  ru: {
    welcome: "Привет",
    subtitle: "Добро пожаловать в панель бизнес-аналитики на базе искусственного интеллекта",
    uploaded: "Датасетов загружено",
    autoAnalysis: "Автоматический анализ",
    charts: "Графики",
    interactive: "Интерактивные диаграммы",
    quickStart: "Быстрый start",
    instructions: "Чтобы начать работу с системой, перейдите во вкладку «Загрузить CSV» в левом меню и добавьте ваш первый файл с данными."
  },
  en: {
    welcome: "Hello",
    subtitle: "Welcome to the AI-powered business analytics dashboard",
    uploaded: "Datasets uploaded",
    autoAnalysis: "Automated analysis",
    charts: "Charts",
    interactive: "Interactive diagrams",
    quickStart: "Quick Start",
    instructions: "To start working with the system, go to the 'Upload CSV' tab in the left menu and add your first data file."
  }
};

export default function Dashboard({ datasets = [], user, lang = "ru" }) {
  const currentText = t[lang] || t.ru;
  const userName = user?.username || "User";

  return (
    <div style={{ padding: "20px", maxWidth: "1000px", margin: "0 auto" }}>
      <div style={{ textAlign: "center", marginBottom: "40px" }}>
        <h1 style={{ fontSize: "32px", fontWeight: "600", marginBottom: "10px" }}>
          {currentText.welcome}, {userName}! 👋
        </h1>
        <p style={{ color: "var(--text2)", fontSize: "16px" }}>
          {currentText.subtitle}
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "20px", marginBottom: "40px" }}>
        <div className="card" style={{ textAlign: "center", padding: "24px" }}>
          <div style={{ fontSize: "28px", marginBottom: "8px" }}>📁</div>
          <div style={{ fontSize: "24px", fontWeight: "600", marginBottom: "4px" }}>{datasets.length}</div>
          <div style={{ color: "var(--text2)", fontSize: "14px" }}>{currentText.uploaded}</div>
        </div>

        <div className="card" style={{ textAlign: "center", padding: "24px" }}>
          <div style={{ fontSize: "28px", marginBottom: "8px" }}>⚡</div>
          <div style={{ fontSize: "24px", fontWeight: "600", marginBottom: "4px" }}>AI</div>
          <div style={{ color: "var(--text2)", fontSize: "14px" }}>{currentText.autoAnalysis}</div>
        </div>

        <div className="card" style={{ textAlign: "center", padding: "24px" }}>
          <div style={{ fontSize: "28px", marginBottom: "8px" }}>📊</div>
          <div style={{ fontSize: "24px", fontWeight: "600", marginBottom: "4px" }}>{currentText.charts}</div>
          <div style={{ color: "var(--text2)", fontSize: "14px" }}>{currentText.interactive}</div>
        </div>
      </div>

      <div className="card" style={{ padding: "32px", textAlign: "center" }}>
        <div style={{ fontSize: "32px", marginBottom: "12px" }}>🚀</div>
        <h3 style={{ fontSize: "20px", fontWeight: "600", marginBottom: "12px" }}>{currentText.quickStart}</h3>
        <p style={{ color: "var(--text2)", fontSize: "15px", lineHeight: "1.6", maxWidth: "500px", margin: "0 auto" }}>
          {currentText.instructions}
        </p>
      </div>
    </div>
  );
}