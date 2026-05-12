export interface AdminStatistics {
  total_number: number | null;
  number_of_admins: number | null;
  number_of_active: number | null;
  new_users_this_month: number | null;
  total_predictions: number | null;
  new_predictions_this_month: number | null;
  dataset_size: number | null;
  model_accuracy: number | null;
  model_version: string | null;
  last_trained_date: string | null;
}
