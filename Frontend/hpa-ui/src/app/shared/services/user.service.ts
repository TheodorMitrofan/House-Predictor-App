import { inject, Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environment/environment';
import { User } from '../../pages/auth/models/User';
import { firstValueFrom } from 'rxjs';

export interface AdminCreateUserPayload {
  full_name: string;
  email: string;
  password: string;
  role: 'user' | 'admin';
}

export interface AdminUpdateUserPayload {
  full_name?: string;
  role?: string;
  is_active?: boolean;
}

@Injectable({providedIn: "root"})
export class UserService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.baseApiUrl}/users`;

  readonly currentUser = signal<User | null>(null);

  async getUsers(search?: string, role?: string): Promise<User[]> {
    const params: Record<string, string> = {};
    if (search) params['search'] = search;
    if (role && role !== 'All') params['role'] = role.toLowerCase();
    return firstValueFrom(this.http.get<User[]>(this.baseUrl, { params }));
  }

  async getUser(): Promise<User> {
    return firstValueFrom(this.http.get<User>(`${this.baseUrl}/me`));
  }

  async load(): Promise<User> {
    const user = await this.getUser();
    this.currentUser.set(user);
    return user;
  }

  async updateMe(payload: Partial<Pick<User, 'full_name' | 'location' | 'description'>>): Promise<User> {
    const updated = await firstValueFrom(
      this.http.patch<User>(`${this.baseUrl}/me/`, payload)
    );
    this.currentUser.set(updated);
    return updated;
  }

  async createUser(payload: AdminCreateUserPayload): Promise<User> {
    return firstValueFrom(
      this.http.post<User>(`${this.baseUrl}/create/`, payload)
    );
  }

  async updateUser(userId: string, payload: AdminUpdateUserPayload): Promise<User> {
    return firstValueFrom(
      this.http.patch<User>(`${this.baseUrl}/${userId}/`, payload)
    );
  }

  async deleteUser(userId: string): Promise<void> {
    await firstValueFrom(this.http.delete(`${this.baseUrl}/${userId}/`));
  }

}

