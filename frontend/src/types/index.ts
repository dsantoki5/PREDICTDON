export type MachineStatus = 'Healthy' | 'Warning' | 'Critical';

export interface Machine {
  id: number;
  machine_code: string;
  machine_name: string;
  department?: string;
  manufacturer?: string;
  installation_date?: string;
  status: MachineStatus;
  updated_at?: string;
}

export interface PredictionResult {
  id?: number;
  machine_id: number;
  prediction: string;
  is_failure: boolean;
  failure_probability: number;
  machine_health: number;
  risk_level: 'Low' | 'Medium' | 'High';
  suggested_machine_status: MachineStatus;
  ticket_created?: boolean;
  ticket_priority?: 'Low' | 'Medium' | 'High';
  root_cause_analysis: {
    risk_score: number;
    diagnosis: string;
    causes: string[];
    components: string[];
    maintenance: string[];
    analysis_table: Array<{
      parameter: string;
      current: string;
      normal: string;
      status: string;
      effect: string;
    }>;
  };
}

export interface MaintenanceTicket {
  id: number;
  machine_id: number;
  machine_code?: string;
  machine_name?: string;
  priority: 'Low' | 'Medium' | 'High';
  status: 'Pending' | 'In Progress' | 'Completed';
  remarks?: string;
  created_at: string;
}

export interface SystemHealth {
  status: string;
  version: string;
  database: string;
  ml_engine: string;
}
