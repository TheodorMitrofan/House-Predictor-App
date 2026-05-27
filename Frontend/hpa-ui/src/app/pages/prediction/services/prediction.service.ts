import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environment/environment';
import { AiTipsResponse, Prediction, PredictionRequest } from '../models/Prediction';
import { SearchDTO } from '../../../shared/models/search-dto';
import { PagedResult } from '../../../shared/models/paged-result';

export type PredictionField =
  | 'property_type' | 'location' | 'bedrooms' | 'bathrooms'
  | 'has_parking' | 'has_pool' | 'has_balcony' | 'has_elevator'
  | 'created_at' | 'prediction_value' | 'floor_area' | 'year_built' | 'confidence';

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

  async search(dto: SearchDTO<PredictionField>): Promise<PagedResult<Prediction>> {
    return firstValueFrom(
      this.http.post<PagedResult<Prediction>>(`${this.baseUrl}/search/`, dto),
    );
  }

  async generateAIExplanation(id: string): Promise<{ explanation: string }> {
    return firstValueFrom(
      this.http.post<{ explanation: string }>(`${this.baseUrl}/${id}/ai-explain/`, {}),
    );
  }

  async generateAITips(id: string): Promise<AiTipsResponse> {
    return firstValueFrom(
      this.http.post<AiTipsResponse>(`${this.baseUrl}/${id}/ai-tips/`, {}),
    );
  }
}
