import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environment/environment';
import { TrainingData } from '../models/TrainingData';
import { PaginatedResponse } from '../../../shared/models/PaginatedResponse';

@Injectable({ providedIn: 'root' })
export class DataManagementService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.baseApiUrl}/training/data`;

  async list(page: number = 1, pageSize: number = 20, search?: string): Promise<PaginatedResponse<TrainingData>> {
    const params: Record<string, string> = {
      page: String(page),
      page_size: String(pageSize),
    };
    if (search) {
      params['search'] = search;
    }
    return firstValueFrom(
      this.http.get<PaginatedResponse<TrainingData>>(`${this.baseUrl}/`, { params }),
    );
  }

  async create(payload: Partial<TrainingData>): Promise<TrainingData> {
    return firstValueFrom(
      this.http.post<TrainingData>(`${this.baseUrl}/`, payload),
    );
  }

  async update(id: number, payload: Partial<TrainingData>): Promise<TrainingData> {
    return firstValueFrom(
      this.http.patch<TrainingData>(`${this.baseUrl}/${id}/`, payload),
    );
  }

  async delete(id: number): Promise<void> {
    await firstValueFrom(this.http.delete(`${this.baseUrl}/${id}/`));
  }
}