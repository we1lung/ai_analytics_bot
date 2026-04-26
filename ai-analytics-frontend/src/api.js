import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

// датасеты
export const uploadCSV = (file) => {
  const form = new FormData();
  form.append("file", file);
  return API.post("/datasets/upload", form);
};

export const getDatasets = () => API.get("/datasets/");
export const getDataset = (id) => API.get(`/datasets/${id}`);

// аналитика
export const getFullReport = (id) => API.get(`/analytics/${id}/full-report`);

// чат
export const sendMessage = (dataset_id, question) =>
  API.post("/chat/", { dataset_id, question });

export const getChatHistory = (id) => API.get(`/chat/${id}/history`);
export const clearHistory = (id) => API.delete(`/chat/${id}/history`);

// отчёты
export const generateReport  = (id)           => API.post(`/reports/${id}/generate`);
export const getReports       = (id)           => API.get(`/reports/${id}`);
export const downloadReportPDF = (datasetId, reportId) =>
  API.get(`/reports/${datasetId}/${reportId}/download/pdf`, { responseType: "blob" });
export const downloadReportTXT = (datasetId, reportId) =>
  API.get(`/reports/${datasetId}/${reportId}/download/txt`, { responseType: "blob" });
export const deleteDataset = (id) => API.delete(`/datasets/${id}`);
export const deleteReport = (datasetId, reportId) =>
  API.delete(`/reports/${datasetId}/${reportId}`);