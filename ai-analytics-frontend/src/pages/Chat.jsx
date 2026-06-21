import { useState, useEffect, useRef } from "react";
import { sendMessage, getChatHistory, clearChatHistory } from "../api";

const t = {
  ru: {
    selectDataset: "Выбери датасет из списка, чтобы начать чат",
    clearBtn: "Очистить историю",
    inputPlaceholder: "Задай вопрос о данных...",
    sendBtn: "Отправить",
    errorLoad: "Ошибка при загрузке истории чата",
    errorSend: "Ошибка при отправке сообщения"
  },
  en: {
    selectDataset: "Select a dataset from the list to start a chat",
    clearBtn: "Clear History",
    inputPlaceholder: "Ask a question about data...",
    sendBtn: "Send",
    errorLoad: "Error loading chat history",
    errorSend: "Error sending message"
  }
};

export default function Chat({ dataset, lang = "ru" }) {
  const currentText = t[lang] || t.ru;

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    if (!dataset) return;
    loadHistory();
  }, [dataset]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadHistory = async () => {
    try {
      const res = await getChatHistory(dataset.id);

      console.log("CHAT HISTORY:", res.data);

      if (Array.isArray(res.data)) {
        setMessages(res.data);
      } else if (Array.isArray(res.data.messages)) {
        setMessages(res.data.messages);
      } else if (Array.isArray(res.data.history)) {
        setMessages(res.data.history);
      } else {
        setMessages([]);
        console.error("Unexpected chat history format:", res.data);
      }

      setError(null);
    } catch {
      setError(currentText.errorLoad);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      // 🚀 Передаем lang на бэкенд, чтобы ИИ отвечал на выбранном языке
      const res = await sendMessage(dataset.id, input, lang);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.data.answer }
      ]);
    } catch {
      setError(currentText.errorSend);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    if (!window.confirm(lang === "ru" ? "Очистить историю чата?" : "Clear chat history?")) return;
    try {
      await clearChatHistory(dataset.id);
      setMessages([]);
      setError(null);
    } catch {
      setError(lang === "ru" ? "Не удалось очистить историю" : "Failed to clear history");
    }
  };

  if (!dataset) return <div className="empty">{currentText.selectDataset}</div>;

  return (
    <div className="chat-container" style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 40px)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2>Chat: {dataset.name}</h2>
        {messages.length > 0 && (
          <button className="btn btn-ghost" onClick={handleClear}>
            {currentText.clearBtn}
          </button>
        )}
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: 12 }}>{error}</div>}

      <div className="chat-box" style={{ flex: 1 }}>
        {messages.map((msg, i) => (
          <div key={i} className={`msg ${msg.role === "user" ? "user" : "assistant"}`}>
            <div className="msg-content">
              <p style={{ whiteSpace: "pre-line" }}>{msg.content}</p>
            </div>
            {msg.role === "assistant" && <div className="msg-meta">answered via ai</div>}
          </div>
        ))}
        {loading && (
          <div className="msg assistant">
            <div className="spinner" style={{ margin: 0, width: 18, height: 18 }} />
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <form onSubmit={handleSend} className="chat-input-row">
        <input
          type="text"
          placeholder={currentText.inputPlaceholder}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="btn btn-primary" disabled={loading || !input.trim()}>
          {currentText.sendBtn}
        </button>
      </form>
    </div>
  );
}