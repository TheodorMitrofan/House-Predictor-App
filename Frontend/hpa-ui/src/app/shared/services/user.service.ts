import { inject, Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environment/environment';
import { User } from '../../pages/auth/models/User';
import { firstValueFrom } from 'rxjs';
import { SearchDTO } from '../models/search-dto';
import { PagedResult } from '../models/paged-result';

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

export type UserField =
  | 'role' | 'is_active' | 'email' | 'full_name' | 'created_date';

@Injectable({providedIn: "root"})
export class UserService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.baseApiUrl}/users`;

  readonly currentUser = signal<User | null>(null);

  async searchUsers(dto: SearchDTO<UserField>): Promise<PagedResult<User>> {
    return firstValueFrom(
      this.http.post<PagedResult<User>>(`${this.baseUrl}/search/`, dto),
    );
  }

  async getUser(): Promise<User> {
    return firstValueFrom(this.http.get<User>(`${this.baseUrl}/me/`));
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
