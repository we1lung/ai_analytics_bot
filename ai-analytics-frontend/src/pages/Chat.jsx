import { useEffect, useRef, useState } from "react";
import { sendMessage, getChatHistory, clearHistory } from "../api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function Chat({ dataset }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput]       = useState("");
  const [loading, setLoading]   = useState(false);
  const bottomRef               = useRef(null);

  // загружаем историю при открытии
  useEffect(() => {
    if (!dataset) return;
    getChatHistory(dataset.id)
      .then((r) => setMessages(r.data))
      .catch(console.error);
  }, [dataset]);

  // автоскролл вниз
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");

    // сразу показываем вопрос пользователя
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const res = await sendMessage(dataset.id, question);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: res.data.answer,
          answered_by: res.data.answered_by,
        },
      ]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Ошибка: " + (e.response?.data?.detail || "неизвестная ошибка") },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    await clearHistory(dataset.id);
    setMessages([]);
  };

  if (!dataset) return <div className="empty">Выбери датасет из списка</div>;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1>Чат: {dataset.name}</h1>
        <button className="btn btn-ghost" onClick={handleClear}>Очистить историю</button>
      </div>

      <div className="chat-box">
        {messages.length === 0 && (
          <div className="empty">Задай вопрос по данным</div>
        )}

        {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
                <div className="msg-content">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {m.content}
                </ReactMarkdown>
                </div>

                {m.answered_by && (
                <div className="msg-meta">отвечено через {m.answered_by}</div>
                )}
            </div>
        ))}

        {loading && (
          <div className="msg assistant" style={{ color: "#9ca3af" }}>
            Думаю...
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="chat-input-row">
        <input
          type="text"
          placeholder="Задай вопрос по данным..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          disabled={loading}
        />
        <button
          className="btn btn-primary"
          onClick={handleSend}
          disabled={!input.trim() || loading}
        >
          Отправить
        </button>
      </div>
    </div>
  );
}