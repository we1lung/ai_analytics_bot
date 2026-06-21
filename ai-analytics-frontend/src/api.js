import axios from "axios";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000",
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---------------- AUTH ----------------
export const register = (username, email, password) =>
  API.post("/auth/register", { username, email, password });

export const login = (email, password) =>
  API.post("/auth/login", { email, password });

export const getCurrentUser = () => API.get("/auth/me");

// ---------------- DATASETS ----------------
export const uploadCSV = (file) => {
  const form = new FormData();
  form.append("file", file);
  return API.post("/datasets/upload", form);
};

export const uploadDataset = uploadCSV;

export const getDatasets = () => API.get("/datasets/");
export const getDataset = (id) => API.get(`/datasets/${id}`);
export const deleteDataset = (id) => API.delete(`/datasets/${id}`);

// ---------------- ADMIN ----------------
export const getUsers = () => API.get("/admin/users");
export const getUserDatasets = (userId) =>
  API.get(`/admin/users/${userId}/datasets`);

export const deleteUser = (userId) =>
  API.delete(`/admin/users/${userId}`);

// ---------------- ANALYTICS ----------------
export const getFullReport = (id) =>
  API.get(`/analytics/${id}/full-report`);

export const sendMessage = (datasetId, message, lang = "ru") =>
  API.post(`/chat/`, {
    dataset_id: datasetId,
    question: message,
    lang,
  });

export const getChatHistory = (datasetId) =>
  API.get(`/chat/${datasetId}/history`);

export const clearChatHistory = (datasetId) =>
  API.delete(`/chat/${datasetId}/history`);

// ---------------- REPORTS ----------------
export const generateReport = (datasetId, lang = "ru") =>
  API.post(`/reports/${datasetId}/generate?lang=${lang}`);

export const getReports = (datasetId) =>
  API.get(`/reports/${datasetId}`);

export const deleteReport = (datasetId, reportId) =>
  API.delete(`/reports/${datasetId}/${reportId}`);

export const downloadReportPDF = (datasetId, reportId) =>
  API.get(`/reports/${datasetId}/${reportId}/download/pdf`, {
    responseType: "blob",
  });

export const downloadReportTXT = (datasetId, reportId) =>
  API.get(`/reports/${datasetId}/${reportId}/download/txt`, {
    responseType: "blob",
  });



// ---------------- ADVANCED ANALYTICS ----------------
export const getCorrelation = (datasetId) =>
  API.get(`/analytics/${datasetId}/correlation`);

export const getAnomalies = (datasetId, contamination = 0.05) =>
  API.get(`/analytics/${datasetId}/anomalies?contamination=${contamination}`);

export const getTrend = (datasetId) =>
  API.get(`/analytics/${datasetId}/trend`);

export const compareDatasets = (datasetIdA, datasetIdB) =>
  API.get(`/analytics/compare?dataset_id_a=${datasetIdA}&dataset_id_b=${datasetIdB}`);