import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { environment } from '../../../../environment/environment';
import { RegisterPayload } from '../models/RegisterPayload';
import { AuthResponse } from '../models/AuthResponse';
import { firstValueFrom } from 'rxjs';
import { LoginPayload } from '../models/LoginPayload';
import { RefreshResponse } from '../models/RefreshResponse';
import { User } from '../models/user';

const TOKEN_KEY = 'hpa.access_token';
const REFRESH_KEY = 'hpa.refresh_token';
const USER_KEY = 'hpa.user';

@Injectable({providedIn: "root"})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly baseUrl = `${environment.baseApiUrl}/users/auth`;

  async register(payload: RegisterPayload): Promise<AuthResponse> {
    const res = await firstValueFrom(this.http.post<AuthResponse>(`${this.baseUrl}/register/`, payload));

    this.persistAuth(res);
    return res;
  }

  async login(payload: LoginPayload): Promise<AuthResponse> {
    const res = await firstValueFrom(
      this.http.post<AuthResponse>(`${this.baseUrl}/login/`, payload),
    );
    this.persistAuth(res);
    return res;
  }

    async refresh(): Promise<RefreshResponse> {
      const refresh_token = this.getRefreshToken();
      if (!refresh_token) {
        throw new Error('No refresh token available');
      }
      const res = await firstValueFrom(
        this.http.post<RefreshResponse>(`${this.baseUrl}/refresh/`, { refresh_token }),
      );
      this.persistTokens(res);
      return res;
    }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    this.router.navigate(['/']);
  }

  getAccessToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  }

  getUser(): User | null {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  }

  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  private persistAuth(res: AuthResponse): void {
    this.persistTokens(res);
    localStorage.setItem(USER_KEY, JSON.stringify(res.user));
  }

  private persistTokens(res: RefreshResponse): void {
    localStorage.setItem(TOKEN_KEY, res.access_token);
    localStorage.setItem(REFRESH_KEY, res.refresh_token);
  }

}
