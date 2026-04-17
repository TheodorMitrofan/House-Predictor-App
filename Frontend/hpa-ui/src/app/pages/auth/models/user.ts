export interface User {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
  location?: string | null;
  role: string;
  prediction: number;
  description?: string | null;
  created_date: string;
}
