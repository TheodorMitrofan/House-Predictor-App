import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environment/environment';
import { User } from '../../pages/auth/models/user';
import { firstValueFrom } from 'rxjs';


@Injectable({providedIn: "root"})
export class UserService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.baseApiUrl}/users`;

  async getUsers(): Promise<User[]> {
    return firstValueFrom(this.http.get<User[]>(this.baseUrl));
  }

}
