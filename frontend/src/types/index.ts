export type MachineStatus = 'Healthy' | 'Warning' | 'Critical';
export type TicketPriority = 'High' | 'Medium' | 'Low';
export type TicketStatus = 'Pending' | 'In Progress' | 'Completed';

export interface Machine {
  id: number;
  machine_code: string;
  machine_name: string;
  department?: string;
  manufacturer?: string;
  installation_date?: string;
  status: MachineStatus;
  created_at?: string;
}

export interface MachineCreateInput {
  machine_code: string;
  machine_name: string;
  department?: string;
  manufacturer?: string;
  installation_date?: string;
  status?: string;
}

export interface MachineUpdateInput {
  machine_code?: string;
  machine_name?: string;
  department?: string;
  manufacturer?: string;
  installation_date?: string;
  status?: string;
}

export interface PredictionRunInput {
  machine_id: number;
  air_temperature: number;
  process_temperature: number;
  rotational_speed: number;
  torque: number;
  tool_wear: number;
}

export interface AnalysisTableRow {
  parameter: string;
  current: string;
  normal: string;
  status: string;
  effect: string;
}

export interface PredictionResult {
  id: number;
  machine_id: number;
  machine_code: string;
  machine_name: string;
  prediction: string;
  is_failure: boolean;
  failure_probability: number;
  machine_health: number;
  risk_level: 'Low' | 'Medium' | 'High';
  suggested_machine_status: MachineStatus;
  ticket_created: boolean;
  ticket_priority?: TicketPriority;
  root_cause_analysis: {
    risk_score: number;
    diagnosis: string;
    causes: string[];
    components: string[];
    maintenance: string[];
    analysis_table: AnalysisTableRow[];
  };
  predicted_at: string;
}

export interface PredictionHistoryItem {
  id: number;
  machine_id: number;
  machine_code?: string;
  machine_name?: string;
  air_temperature: number;
  process_temperature: number;
  rotational_speed: number;
  torque: number;
  tool_wear: number;
  prediction: string;
  probability: number;
  confidence?: number;
  predicted_at: string;
}

export interface MaintenanceTicket {
  id: number;
  machine_id: number;
  machine_code?: string;
  machine_name?: string;
  prediction_id?: number;
  priority: TicketPriority;
  status: TicketStatus;
  remarks?: string;
  created_at: string;
}

export interface DashboardSummary {
  total_machines: number;
  healthy: number;
  warning: number;
  critical: number;
  total_predictions: number;
  normal_predictions: number;
  failure_predictions: number;
  pending_maintenance: number;
  avg_health: number;
  avg_failure: number;
  recent_predictions: PredictionHistoryItem[];
  recent_machines: Machine[];
}

export interface ReportsSummary {
  total_predictions: number;
  normal_predictions: number;
  failure_predictions: number;
  pending_tickets: number;
  in_progress_tickets: number;
  completed_tickets: number;
  total_machines: number;
  healthy_machines: number;
  warning_machines: number;
  critical_machines: number;
  avg_failure: number;
  avg_health: number;
  highest_failure: number;
  lowest_failure: number;
  model_metrics: {
    model_name: string;
    benchmark_dataset: string;
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
    roc_auc: number;
  };
}

export interface SystemHealth {
  status: string;
  version: string;
  database: string;
  ml_engine: string;
}
