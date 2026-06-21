import { useEffect, useState } from "react";
import {
  getFullReport, getCorrelation, getAnomalies, getTrend,
  compareDatasets, getDatasets,
} from "../api";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell, Legend, LineChart, Line,
} from "recharts";

const COLORS = ["#4f46e5", "#7c3aed", "#a855f7", "#ec4899", "#f59e0b", "#10b981", "#3b82f6"];

const t = {
  ru: {
    empty: "Выбери датасет из списка",
    error: "Ошибка загрузки аналитики",
    title: "Аналитика:",
    rows: "Строк",
    columns: "Колонок",
    numeric: "Числовых",
    text: "Текстовых",
    barTitle: "Среднее / Мин / Макс по числовым колонкам",
    barMean: "Среднее",
    barMin: "Мин",
    barMax: "Макс",
    topCategories: "Топ категорий",
    pieRecords: "записей",
    missingValues: "Пропущенные значения",
    noMissing: "Без пропусков",
    pieColumns: "колонок",
    tableTitle: "Детальная статистика",
    thCol: "Колонка",
    thMean: "Среднее",
    thMin: "Мин",
    thMax: "Макс",
    tabOverview: "Обзор",
    tabCorrelation: "Корреляция",
    tabAnomalies: "Аномалии",
    tabTrend: "Тренд",
    tabCompare: "Сравнение",
    corrNotEnough: "Недостаточно числовых колонок для корреляции",
    anomalyNone: "Числовых колонок нет",
    anomalyTooFew: "Слишком мало строк (нужно минимум 10)",
    anomalyFound: "Найдено аномалий",
    anomalyOf: "из",
    anomalyRow: "Строка",
    trendNoDate: "Дата-колонка не найдена",
    trendNoNumeric: "Числовых колонок для тренда нет",
    compareSelect: "Выбери второй датасет для сравнения",
    compareNoCommon: "Нет общих числовых колонок",
    compareMetric: "Метрика",
    compareA: "Датасет A",
    compareB: "Датасет B",
    compareDiff: "Разница, %",
    loadError: "Не удалось загрузить",
  },
  en: {
    empty: "Select a dataset from the list",
    error: "Error loading analytics",
    title: "Analytics:",
    rows: "Rows",
    columns: "Columns",
    numeric: "Numeric",
    text: "Text",
    barTitle: "Mean / Min / Max for numeric columns",
    barMean: "Mean",
    barMin: "Min",
    barMax: "Max",
    topCategories: "Top Categories",
    pieRecords: "records",
    missingValues: "Missing Values",
    noMissing: "No Missing",
    pieColumns: "columns",
    tableTitle: "Detailed Statistics",
    thCol: "Column",
    thMean: "Mean",
    thMin: "Min",
    thMax: "Max",
    tabOverview: "Overview",
    tabCorrelation: "Correlation",
    tabAnomalies: "Anomalies",
    tabTrend: "Trend",
    tabCompare: "Compare",
    corrNotEnough: "Not enough numeric columns for correlation",
    anomalyNone: "No numeric columns",
    anomalyTooFew: "Too few rows (need at least 10)",
    anomalyFound: "Anomalies found",
    anomalyOf: "of",
    anomalyRow: "Row",
    trendNoDate: "No date column found",
    trendNoNumeric: "No numeric columns for trend",
    compareSelect: "Select a second dataset to compare",
    compareNoCommon: "No common numeric columns",
    compareMetric: "Metric",
    compareA: "Dataset A",
    compareB: "Dataset B",
    compareDiff: "Diff, %",
    loadError: "Failed to load",
  }
};

function corrColor(value) {
  if (value === null || value === undefined) return "var(--bg3)";
  if (value >= 0) {
    const alpha = Math.abs(value);
    return `rgba(79, 70, 229, ${alpha})`;
  }
  const alpha = Math.abs(value);
  return `rgba(239, 68, 68, ${alpha})`;
}

function CorrelationTab({ dataset, lang }) {
  const tt = t[lang] || t.ru;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getCorrelation(dataset.id)
      .then((r) => setData(r.data))
      .catch(() => setError(tt.loadError))
      .finally(() => setLoading(false));
  }, [dataset.id, lang]);

  if (loading) return <div className="spinner" />;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!data || !data.columns || data.columns.length < 2) {
    return <div className="empty">{data?.message || tt.corrNotEnough}</div>;
  }

  const { columns, cells } = data;
  const cellMap = {};
  cells.forEach((c) => { cellMap[`${c.y}|${c.x}`] = c.value; });
  const cellSize = Math.max(48, Math.min(90, 560 / columns.length));

  return (
    <div className="card" style={{ overflowX: "auto" }}>
      <div style={{ display: "inline-block" }}>
        <div style={{ display: "flex" }}>
          <div style={{ width: 120, flexShrink: 0 }} />
          {columns.map((col) => (
            <div
              key={col}
              style={{
                width: cellSize, flexShrink: 0, fontSize: 11, color: "var(--text2)",
                textAlign: "center", padding: "4px 2px", writingMode: "vertical-rl",
                transform: "rotate(180deg)", height: 80,
              }}
              title={col}
            >
              {col}
            </div>
          ))}
        </div>
        {columns.map((rowCol) => (
          <div key={rowCol} style={{ display: "flex" }}>
            <div
              style={{
                width: 120, flexShrink: 0, fontSize: 12, color: "var(--text2)",
                display: "flex", alignItems: "center", padding: "0 8px",
                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
              }}
              title={rowCol}
            >
              {rowCol}
            </div>
            {columns.map((colCol) => {
              const val = cellMap[`${rowCol}|${colCol}`];
              return (
                <div
                  key={colCol}
                  title={`${rowCol} x ${colCol}: ${val ?? "-"}`}
                  style={{
                    width: cellSize, height: cellSize, flexShrink: 0,
                    background: corrColor(val), display: "flex",
                    alignItems: "center", justifyContent: "center",
                    fontSize: 11, fontWeight: 500,
                    color: Math.abs(val ?? 0) > 0.5 ? "#fff" : "var(--text)",
                    border: "1px solid var(--bg)",
                  }}
                >
                  {val !== null && val !== undefined ? val.toFixed(2) : "-"}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

function AnomaliesTab({ dataset, lang }) {
  const tt = t[lang] || t.ru;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getAnomalies(dataset.id)
      .then((r) => setData(r.data))
      .catch(() => setError(tt.loadError))
      .finally(() => setLoading(false));
  }, [dataset.id, lang]);

  if (loading) return <div className="spinner" />;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!data || data.anomaly_count === undefined) {
    return <div className="empty">{data?.message || tt.anomalyNone}</div>;
  }
  if (data.message) return <div className="empty">{data.message}</div>;

  return (
    <div>
      <div className="stat-grid" style={{ marginBottom: 16 }}>
        <div className="stat-card">
          <div className="label">{tt.anomalyFound}</div>
          <div className="value">{data.anomaly_count} {tt.anomalyOf} {data.total_rows}</div>
        </div>
      </div>
      {data.anomalies.map((a) => (
        <div key={a.row_index} className="card" style={{ marginBottom: 10, padding: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
            <span style={{ fontWeight: 500, fontSize: 13 }}>
              {tt.anomalyRow} #{a.row_index}
            </span>
            <span className="badge">score: {a.anomaly_score}</span>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {Object.entries(a.row_data).slice(0, 8).map(([k, v]) => (
              <span key={k} className="tag">{k}: {String(v)}</span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function TrendTab({ dataset, lang }) {
  const tt = t[lang] || t.ru;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getTrend(dataset.id)
      .then((r) => setData(r.data))
      .catch(() => setError(tt.loadError))
      .finally(() => setLoading(false));
  }, [dataset.id, lang]);

  if (loading) return <div className="spinner" />;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!data || !data.trend || data.trend.length === 0) {
    return <div className="empty">{data?.message || tt.trendNoDate}</div>;
  }

  return (
    <div className="card">
      <p style={{ fontWeight: 500, marginBottom: 16 }}>
        {data.date_column} - {data.metrics.join(", ")}
      </p>
      <ResponsiveContainer width="100%" height={340}>
        <LineChart data={data.trend} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          {data.metrics.map((m, i) => (
            <Line
              key={m}
              type="monotone"
              dataKey={m}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function CompareTab({ dataset, lang, allDatasets }) {
  const tt = t[lang] || t.ru;
  const [otherId, setOtherId] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const options = allDatasets.filter((d) => d.id !== dataset.id);

  useEffect(() => {
    if (!otherId) { setData(null); return; }
    setLoading(true);
    setError(null);
    compareDatasets(dataset.id, otherId)
      .then((r) => setData(r.data))
      .catch(() => setError(tt.loadError))
      .finally(() => setLoading(false));
  }, [otherId, dataset.id, lang]);

  return (
    <div>
      <div className="card" style={{ marginBottom: 16 }}>
        <p style={{ fontWeight: 500, marginBottom: 10 }}>{tt.compareSelect}</p>
        <select
          value={otherId}
          onChange={(e) => setOtherId(e.target.value)}
          style={{
            width: "100%", padding: "10px 14px", borderRadius: 8,
            border: "1px solid var(--border)", background: "var(--bg2)",
            color: "var(--text)", fontSize: 14,
          }}
        >
          <option value="">-</option>
          {options.map((d) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
      </div>

      {loading && <div className="spinner" />}
      {error && <div className="alert alert-error">{error}</div>}

      {data && data.message && <div className="empty">{data.message}</div>}

      {data && data.common_columns && data.common_columns.length > 0 && (
        <>
          <div className="card">
            <p style={{ fontWeight: 500, marginBottom: 16 }}>
              {data.dataset_a.name} ({data.dataset_a.row_count}) vs {data.dataset_b.name} ({data.dataset_b.row_count})
            </p>
            <ResponsiveContainer width="100%" height={Math.max(240, data.common_columns.length * 60)}>
              <BarChart
                layout="vertical"
                data={data.common_columns.map((col) => ({
                  name: col,
                  [tt.compareA]: data.comparison[col].dataset_a.mean,
                  [tt.compareB]: data.comparison[col].dataset_b.mean,
                }))}
                margin={{ top: 5, right: 20, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={120} />
                <Tooltip />
                <Legend />
                <Bar dataKey={tt.compareA} fill="#4f46e5" radius={[0, 4, 4, 0]} />
                <Bar dataKey={tt.compareB} fill="#7c3aed" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <table className="stats-table">
              <thead>
                <tr>
                  <th>{tt.compareMetric}</th>
                  <th>{tt.compareA}</th>
                  <th>{tt.compareB}</th>
                  <th>{tt.compareDiff}</th>
                </tr>
              </thead>
              <tbody>
                {data.common_columns.map((col) => {
                  const c = data.comparison[col];
                  return (
                    <tr key={col}>
                      <td style={{ fontWeight: 500 }}>{col}</td>
                      <td>{c.dataset_a.mean}</td>
                      <td>{c.dataset_b.mean}</td>
                      <td style={{ color: c.diff_percent > 0 ? "#10b981" : c.diff_percent < 0 ? "#ef4444" : "var(--text2)" }}>
                        {c.diff_percent !== null ? `${c.diff_percent > 0 ? "+" : ""}${c.diff_percent}%` : "-"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function OverviewTab({ dataset, lang }) {
  const currentText = t[lang] || t.ru;
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getFullReport(dataset.id)
      .then((r) => setReport(r.data))
      .catch(() => setError(currentText.error))
      .finally(() => setLoading(false));
  }, [dataset.id, lang]);

  if (loading) return <div className="spinner" />;
  if (error) return <div className="alert alert-error">{error}</div>;

  const { summary, missing_values, averages, top_categories } = report;

  const barData = Object.entries(averages).map(([col, s]) => ({
    name: col,
    [currentText.barMean]: s.mean,
    [currentText.barMin]: s.min,
    [currentText.barMax]: s.max,
  }));

  const missingPieData = Object.entries(missing_values)
    .filter(([, m]) => m.missing_count > 0)
    .map(([col, m]) => ({ name: col, value: m.missing_count }));

  const noMissingCount = Object.values(missing_values).filter(
    (m) => m.missing_count === 0
  ).length;

  const missingPieFull =
    missingPieData.length > 0
      ? [...missingPieData, { name: currentText.noMissing, value: noMissingCount }]
      : null;

  return (
    <div>
      <div className="stat-grid">
        <div className="stat-card">
          <div className="label">{currentText.rows}</div>
          <div className="value">{summary.row_count}</div>
        </div>
        <div className="stat-card">
          <div className="label">{currentText.columns}</div>
          <div className="value">{summary.column_count}</div>
        </div>
        <div className="stat-card">
          <div className="label">{currentText.numeric}</div>
          <div className="value">{Object.keys(averages).length}</div>
        </div>
        <div className="stat-card">
          <div className="label">{currentText.text}</div>
          <div className="value">{Object.keys(top_categories).length}</div>
        </div>
      </div>

      {barData.length > 0 && (
        <div className="card">
          <p style={{ fontWeight: 500, marginBottom: 20 }}>
            {currentText.barTitle}
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
                    <Bar dataKey={currentText.barMax}  fill="#7c3aed" radius={[4,4,0,0]} />
                    <Bar dataKey={currentText.barMean} fill="#4f46e5" radius={[4,4,0,0]} />
                    <Bar dataKey={currentText.barMin}  fill="#a5b4fc" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ))}
          </div>
        </div>
      )}

      {Object.keys(top_categories).length > 0 && (
        <div className="card">
          <p style={{ fontWeight: 500, marginBottom: 20 }}>{currentText.topCategories}</p>
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
                      <Tooltip formatter={(val, name) => [`${val} ${currentText.pieRecords}`, name]} />
                      <Legend
                        iconType="circle"
                        iconSize={8}
                        formatter={(value) =>
                          value.length > 14 ? value.slice(0, 14) + "..." : value
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

      {missingPieFull && (
        <div className="card">
          <p style={{ fontWeight: 500, marginBottom: 20 }}>{currentText.missingValues}</p>
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
                    fill={entry.name === currentText.noMissing ? "#10b981" : COLORS[i % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip formatter={(val) => [`${val} ${currentText.pieColumns}`]} />
              <Legend
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      {Object.keys(averages).length > 0 && (
        <div className="card">
          <p style={{ fontWeight: 500, marginBottom: 16 }}>{currentText.tableTitle}</p>
          <table className="stats-table">
            <thead>
              <tr>
                {[currentText.thCol, currentText.thMean, currentText.thMin, currentText.thMax].map((h) => (
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

export default function Analytics({ dataset, lang = "ru" }) {
  const currentText = t[lang] || t.ru;
  const [tab, setTab] = useState("overview");
  const [allDatasets, setAllDatasets] = useState([]);

  useEffect(() => {
    if (tab !== "compare") return;
    getDatasets().then((r) => setAllDatasets(r.data)).catch(() => {});
  }, [tab]);

  if (!dataset) return <div className="empty">{currentText.empty}</div>;

  const tabs = [
    { id: "overview", label: currentText.tabOverview },
    { id: "correlation", label: currentText.tabCorrelation },
    { id: "anomalies", label: currentText.tabAnomalies },
    { id: "trend", label: currentText.tabTrend },
    { id: "compare", label: currentText.tabCompare },
  ];

  return (
    <div>
      <h1>{currentText.title} {dataset.name}</h1>

      <div style={{ display: "flex", gap: 6, marginBottom: 20, flexWrap: "wrap" }}>
        {tabs.map((tb) => (
          <button
            key={tb.id}
            className={`btn ${tab === tb.id ? "btn-primary" : "btn-ghost"}`}
            onClick={() => setTab(tb.id)}
            style={{ padding: "8px 16px", fontSize: 13 }}
          >
            {tb.label}
          </button>
        ))}
      </div>

      {tab === "overview" && <OverviewTab dataset={dataset} lang={lang} />}
      {tab === "correlation" && <CorrelationTab dataset={dataset} lang={lang} />}
      {tab === "anomalies" && <AnomaliesTab dataset={dataset} lang={lang} />}
      {tab === "trend" && <TrendTab dataset={dataset} lang={lang} />}
      {tab === "compare" && <CompareTab dataset={dataset} lang={lang} allDatasets={allDatasets} />}
    </div>
  );
}