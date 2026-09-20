import axios from 'axios';
import type {
  Machine,
  MachineCreateInput,
  MachineUpdateInput,
  PredictionResult,
  PredictionRunInput,
  PredictionHistoryItem,
  MaintenanceTicket,
  DashboardSummary,
  ReportsSummary,
  SystemHealth,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// System Health
export const checkSystemHealth = async (): Promise<SystemHealth> => {
  const res = await apiClient.get<SystemHealth>('/health');
  return res.data;
};

// Dashboard
export const getDashboardSummary = async (): Promise<DashboardSummary> => {
  const res = await apiClient.get<DashboardSummary>('/dashboard/summary');
  return res.data;
};

// Machines
export const getMachines = async (params?: { search?: string; department?: string; status?: string }): Promise<Machine[]> => {
  const res = await apiClient.get<Machine[]>('/machines', { params });
  return res.data;
};

export const createMachine = async (data: MachineCreateInput): Promise<Machine> => {
  const res = await apiClient.post<Machine>('/machines', data);
  return res.data;
};

export const updateMachine = async (id: number, data: MachineUpdateInput): Promise<Machine> => {
  const res = await apiClient.put<Machine>(`/machines/${id}`, data);
  return res.data;
};

export const deleteMachine = async (id: number): Promise<void> => {
  await apiClient.delete(`/machines/${id}`);
};

// Predictions
export const runPrediction = async (data: PredictionRunInput): Promise<PredictionResult> => {
  const res = await apiClient.post<PredictionResult>('/predictions/run', data);
  return res.data;
};

export const getPredictionHistory = async (params?: { machine_id?: number; limit?: number; offset?: number }): Promise<PredictionHistoryItem[]> => {
  const res = await apiClient.get<PredictionHistoryItem[]>('/predictions/history', { params });
  return res.data;
};

export const deletePredictionHistoryItem = async (id: number): Promise<void> => {
  await apiClient.delete(`/predictions/history/${id}`);
};

// Maintenance
export const getMaintenanceTickets = async (params?: { status?: string; priority?: string }): Promise<MaintenanceTicket[]> => {
  const res = await apiClient.get<MaintenanceTicket[]>('/maintenance', { params });
  return res.data;
};

export const updateMaintenanceTicket = async (id: number, data: { status: string; remarks?: string }): Promise<MaintenanceTicket> => {
  const res = await apiClient.put<MaintenanceTicket>(`/maintenance/${id}`, data);
  return res.data;
};

export const deleteMaintenanceTicket = async (id: number): Promise<void> => {
  await apiClient.delete(`/maintenance/${id}`);
};

// Reports
export const getReportsSummary = async (): Promise<ReportsSummary> => {
  const res = await apiClient.get<ReportsSummary>('/reports/summary');
  return res.data;
};

export const getPdfExportUrl = () => `${API_BASE_URL}/reports/pdf`;
export const getExcelExportUrl = () => `${API_BASE_URL}/reports/excel`;
