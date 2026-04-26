import { useEffect, useState } from "react";
import { getFullReport } from "../api";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell, Legend,
} from "recharts";

const COLORS = ["#4f46e5", "#7c3aed", "#a855f7", "#ec4899", "#f59e0b", "#10b981", "#3b82f6"];

export default function Analytics({ dataset }) {
  const [report, setReport]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    if (!dataset) return;
    setLoading(true);
    setError(null);
    getFullReport(dataset.id)
      .then((r) => setReport(r.data))
      .catch(() => setError("Ошибка загрузки аналитики"))
      .finally(() => setLoading(false));
  }, [dataset]);

  if (!dataset) return <div className="empty">Выбери датасет из списка</div>;
  if (loading)  return <div className="spinner" />;
  if (error)    return <div className="alert alert-error">{error}</div>;

  const { summary, missing_values, averages, top_categories } = report;

  const barData = Object.entries(averages).map(([col, s]) => ({
    name: col,
    Среднее: s.mean,
    Мин: s.min,
    Макс: s.max,
  }));

  const missingPieData = Object.entries(missing_values)
    .filter(([, m]) => m.missing_count > 0)
    .map(([col, m]) => ({ name: col, value: m.missing_count }));

  const noMissingCount = Object.values(missing_values).filter(
    (m) => m.missing_count === 0
  ).length;

  const missingPieFull =
    missingPieData.length > 0
      ? [...missingPieData, { name: "Без пропусков", value: noMissingCount }]
      : null;

  return (
    <div>
      <h1>Аналитика: {summary.name}</h1>

      {/* сводка */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="label">Строк</div>
          <div className="value">{summary.row_count}</div>
        </div>
        <div className="stat-card">
          <div className="label">Колонок</div>
          <div className="value">{summary.column_count}</div>
        </div>
        <div className="stat-card">
          <div className="label">Числовых</div>
          <div className="value">{Object.keys(averages).length}</div>
        </div>
        <div className="stat-card">
          <div className="label">Текстовых</div>
          <div className="value">{Object.keys(top_categories).length}</div>
        </div>
      </div>

      {/* BAR CHART */}
      {barData.length > 0 && (
        <div className="card">
          <p style={{ fontWeight: 500, marginBottom: 20 }}>
            Среднее / Мин / Макс по числовым колонкам
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 24 }}>
            {barData.map((col) => (
              <div key={col.name}>
                <p style={{ fontSize: 13, color: "var(--text2)", marginBottom: 8, textAlign: "center" }}>
                  {col.name}
                </p>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={[col]} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Макс"    fill="#7c3aed" radius={[4,4,0,0]} />
                    <Bar dataKey="Среднее" fill="#4f46e5" radius={[4,4,0,0]} />
                    <Bar dataKey="Мин"     fill="#a5b4fc" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* PIE CHARTS — топ категорий */}
      {Object.keys(top_categories).length > 0 && (
        <div className="card">
          <p style={{ fontWeight: 500, marginBottom: 20 }}>Топ категорий</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 24 }}>
            {Object.entries(top_categories).map(([col, vals]) => {
              const pieData = vals.map((v) => ({ name: v.value, value: v.count }));
              return (
                <div key={col}>
                  <p style={{ fontSize: 13, color: "var(--text2)", marginBottom: 8, textAlign: "center" }}>
                    {col}
                  </p>
                  <ResponsiveContainer width="100%" height={240}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="45%"
                        innerRadius={45}
                        outerRadius={75}
                        paddingAngle={3}
                        dataKey="value"
                      >
                        {pieData.map((_, i) => (
                          <Cell key={i} fill={COLORS[i % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(val, name) => [`${val} записей`, name]} />
                      <Legend
                        iconType="circle"
                        iconSize={8}
                        formatter={(value) =>
                          value.length > 14 ? value.slice(0, 14) + "…" : value
                        }
                        wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* PIE CHART — пропуски */}
      {missingPieFull && (
        <div className="card">
          <p style={{ fontWeight: 500, marginBottom: 20 }}>Пропущенные значения</p>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={missingPieFull}
                cx="50%"
                cy="45%"
                outerRadius={80}
                paddingAngle={2}
                dataKey="value"
              >
                {missingPieFull.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={entry.name === "Без пропусков" ? "#10b981" : COLORS[i % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip formatter={(val) => [`${val} колонок`]} />
              <Legend
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* таблица статистики */}
      {Object.keys(averages).length > 0 && (
        <div className="card">
          <p style={{ fontWeight: 500, marginBottom: 16 }}>Детальная статистика</p>
          <table className="stats-table">
            <thead>
              <tr>
                {["Колонка", "Среднее", "Мин", "Макс"].map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.entries(averages).map(([col, s]) => (
                <tr key={col}>
                  <td style={{ fontWeight: 500 }}>{col}</td>
                  <td>{s.mean}</td>
                  <td>{s.min}</td>
                  <td>{s.max}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}