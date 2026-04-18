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

@Injectable({providedIn: "root"})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly baseUrl = `${environment.baseApiUrl}/users/auth`;

  async register(payload: RegisterPayload): Promise<AuthResponse> {
    const res = await firstValueFrom(this.http.post<AuthResponse>(`${this.baseUrl}/register/`, payload));

    this.persistTokens(res);
    return res;
  }

  async login(payload: LoginPayload): Promise<AuthResponse> {
    const res = await firstValueFrom(
      this.http.post<AuthResponse>(`${this.baseUrl}/login/`, payload),
    );
    this.persistTokens(res);
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
    this.router.navigate(['/']);
  }

  getAccessToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  }

  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  getRoleFromToken(): 'admin' | 'user' | null {
    const token = this.getAccessToken();
    if (!token) return null;
    try {
      const part = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      const padded = part + '='.repeat((4 - part.length % 4) % 4);
      const payload = JSON.parse(atob(padded));
      const roles: string[] = payload.realm_access?.roles ?? [];
      return roles.includes('admin') ? 'admin' : 'user';
    } catch {
      return null;
    }
  }

  private persistTokens(res: RefreshResponse): void {
    localStorage.setItem(TOKEN_KEY, res.access_token);
    localStorage.setItem(REFRESH_KEY, res.refresh_token);
  }

}
