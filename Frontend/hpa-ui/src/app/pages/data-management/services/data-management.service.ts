import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environment/environment';
import { TrainingData } from '../models/TrainingData';
import { PagedResult } from '../../../shared/models/paged-result';
import { SearchDTO } from '../../../shared/models/search-dto';

export type TrainingDataField =
  | 'id' | 'price' | 'yr_built' | 'grade' | 'bedrooms' | 'sqft_living'
  | 'zipcode' | 'condition' | 'waterfront';

@Injectable({ providedIn: 'root' })
export class DataManagementService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.baseApiUrl}/training/data`;

  async search(dto: SearchDTO<TrainingDataField>): Promise<PagedResult<TrainingData>> {
    return firstValueFrom(
      this.http.post<PagedResult<TrainingData>>(`${this.baseUrl}/search/`, dto),
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
