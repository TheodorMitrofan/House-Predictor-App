export interface RunHistory {
  id: string;
  date: string;
  duration: string | null;
  accuracy: number;
  rmse: number | null;
  dataset_size: number;
  success: boolean;
  is_active: boolean;
  version: string | null;
  model_path: string | null;
  error_message: string | null;
}
