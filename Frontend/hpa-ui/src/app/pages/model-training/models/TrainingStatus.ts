export type TrainingStatusValue = 'idle' | 'running' | 'complete' | 'failed';

export interface TrainingStatus {
  status: TrainingStatusValue;
  progress: number;
  current_run_id: string | null;
  started_at: string | null;
  ended_at: string | null;
  error: string | null;
  logs: string[];
}
