import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environment/environment';
import { AdminStatistics } from '../models/AdminStatistics';
import { firstValueFrom } from 'rxjs';


@Injectable({providedIn: "root"})
export class AdminStatisticsService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.baseApiUrl}/users/statistics`;

  async getStatistics(): Promise<AdminStatistics> {
    return firstValueFrom(this.http.get<AdminStatistics>(this.baseUrl));
  }
}
