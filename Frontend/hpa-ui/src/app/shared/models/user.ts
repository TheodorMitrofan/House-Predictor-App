export interface User {
  id: number;
  fullname: string;
  email: string;
  role: 'user' | 'admin';
  prediction: number;
  is_active: boolean;
  created_date: string;
}
