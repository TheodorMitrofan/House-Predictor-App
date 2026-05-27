import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environment/environment';
import { PagedResult } from '../../../shared/models/paged-result';
import { SearchDTO } from '../../../shared/models/search-dto';
import { ActiveModel } from '../models/ActiveModel';
import { RunHistory } from '../models/RunHistory';
import { TrainingStatus } from '../models/TrainingStatus';

export type RunHistoryField = 'date' | 'accuracy' | 'dataset_size' | 'version' | 'is_active' | 'success';

@Injectable({ providedIn: 'root' })
export class ModelTrainingService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.baseApiUrl}/training`;

  async getActiveModel(): Promise<ActiveModel | null> {
    try {
      return await firstValueFrom(this.http.get<ActiveModel>(`${this.baseUrl}/active-model/`));
    } catch {
      return null;
    }
  }

  async retrain(): Promise<{ message: string }> {
    return firstValueFrom(this.http.post<{ message: string }>(`${this.baseUrl}/retrain/`, {}));
  }

  async getStatus(): Promise<TrainingStatus> {
    return firstValueFrom(this.http.get<TrainingStatus>(`${this.baseUrl}/status/`));
  }

  async searchHistory(dto: SearchDTO<RunHistoryField>): Promise<PagedResult<RunHistory>> {
    return firstValueFrom(
      this.http.post<PagedResult<RunHistory>>(`${this.baseUrl}/run-history/search/`, dto),
    );
  }
}
