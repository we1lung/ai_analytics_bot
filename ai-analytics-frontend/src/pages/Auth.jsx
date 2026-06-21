import { useState } from "react";
import axios from "axios";

const API = axios.create({ baseURL: "http://127.0.0.1:8000" });

export default function Auth() {
  const [mode, setMode] = useState("login"); // login | register
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const url = mode === "login" ? "/auth/login" : "/auth/register";
      const data = mode === "login"
        ? { email, password }
        : { username, email, password };

      const res = await API.post(url, data);
      
      localStorage.setItem("token", res.data.access_token);
      localStorage.setItem("user", JSON.stringify({
        id: res.data.user_id,
        username: res.data.username,
        role: res.data.role,
      }));

      window.location.reload();
    } catch (err) {
      setError(err.response?.data?.detail || "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg)" }}>
      <div className="card" style={{ width: "100%", maxWidth: 400, padding: 32 }}>
        <h1 style={{ textAlign: "center", marginBottom: 24, fontSize: 24, fontWeight: 700 }}>
          {mode === "login" ? "Вход" : "Регистрация"}
        </h1>

        {error && (
          <div style={{ padding: 12, background: "#fee", color: "#c33", borderRadius: 8, marginBottom: 16, fontSize: 14 }}>
            ❌ {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {mode === "register" && (
            <input
              type="text"
              placeholder="Имя пользователя"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              style={{
                padding: "10px 12px",
                border: "1px solid var(--border)",
                borderRadius: 8,
                background: "var(--bg2)",
                color: "var(--text)",
                fontSize: 14,
              }}
            />
          )}

          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{
              padding: "10px 12px",
              border: "1px solid var(--border)",
              borderRadius: 8,
              background: "var(--bg2)",
              color: "var(--text)",
              fontSize: 14,
            }}
          />

          <input
            type="password"
            placeholder="Пароль"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{
              padding: "10px 12px",
              border: "1px solid var(--border)",
              borderRadius: 8,
              background: "var(--bg2)",
              color: "var(--text)",
              fontSize: 14,
            }}
          />

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: "10px 16px",
              background: loading ? "#999" : "var(--primary)",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              fontSize: 14,
            }}
          >
            {loading ? "Подождите..." : mode === "login" ? "Войти" : "Зарегистрироваться"}
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: 16, fontSize: 14 }}>
          {mode === "login" ? (
            <>
              Нет аккаунта?{" "}
              <button
                onClick={() => { setMode("register"); setError(null); }}
                style={{ background: "none", border: "none", color: "var(--primary)", cursor: "pointer", fontWeight: 600 }}
              >
                Создать
              </button>
            </>
          ) : (
            <>
              Уже есть аккаунт?{" "}
              <button
                onClick={() => { setMode("login"); setError(null); }}
                style={{ background: "none", border: "none", color: "var(--primary)", cursor: "pointer", fontWeight: 600 }}
              >
                Войти
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}