import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environment/environment';
import { Prediction, PredictionRequest } from '../models/Prediction';

@Injectable({ providedIn: 'root' })
export class PredictionService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.baseApiUrl}/predictions`;

  async create(payload: PredictionRequest): Promise<Prediction> {
    return firstValueFrom(
      this.http.post<Prediction>(`${this.baseUrl}/`, payload),
    );
  }

  async getById(id: string): Promise<Prediction> {
    return firstValueFrom(
      this.http.get<Prediction>(`${this.baseUrl}/${id}/`),
    );
  }

  async history(search?: string, type?: string): Promise<Prediction[]> {
    const params: Record<string, string> = {};
    if (search) params['search'] = search;
    if (type && type !== 'All') params['type'] = type;
    return firstValueFrom(
      this.http.get<Prediction[]>(`${this.baseUrl}/history/`, { params }),
    );
  }
}
