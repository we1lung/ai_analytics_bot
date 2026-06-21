import { useEffect, useState } from "react";

export default function Toast() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    const handler = (e) => {
      if (e.detail) {
        const id = Date.now();
        setToasts((t) => [...t, { id, ...e.detail }]);
        setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3000);
      }
    };
    window.addEventListener("toast", handler);
    return () => window.removeEventListener("toast", handler);
  }, []);

  return (
    <div style={{ position: "fixed", bottom: 20, right: 20, zIndex: 9999, display: "flex", flexDirection: "column", gap: 10 }}>
      {toasts.map((t) => (
        <div
          key={t.id}
          style={{
            padding: "12px 16px",
            borderRadius: 8,
            color: "#fff",
            fontSize: 14,
            fontWeight: 500,
            animation: "slideIn 0.3s ease",
            background: t.type === "error" ? "#ef4444" : t.type === "success" ? "#10b981" : "#3b82f6",
            boxShadow: "0 10px 25px rgba(0,0,0,0.2)",
          }}
        >
          {t.message}
        </div>
      ))}
      <style>{`
        @keyframes slideIn {
          from { transform: translateX(400px); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

// Помощник для вызова тоста
export const showToast = (message, type = "info") => {
  window.dispatchEvent(new CustomEvent("toast", { detail: { message, type } }));
};