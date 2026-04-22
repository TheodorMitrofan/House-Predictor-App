import { inject, Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environment/environment';
import { User } from '../../pages/auth/models/User';
import { firstValueFrom } from 'rxjs';

@Injectable({providedIn: "root"})
export class UserService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.baseApiUrl}/users`;

  readonly currentUser = signal<User | null>(null);

  async getUsers(): Promise<User[]> {
    return firstValueFrom(this.http.get<User[]>(this.baseUrl));
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

}
