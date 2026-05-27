import { Component, inject, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { TableLazyLoadEvent, TableModule } from 'primeng/table';
import { Card } from 'primeng/card';
import { MessageService } from 'primeng/api';
import { PredictionService, PredictionField } from '../services/prediction.service';
import { Prediction, PropertyType } from '../models/Prediction';
import { SearchDTO, Filter, Sorter } from '../../../shared/models/search-dto';

const PAGE_SIZE = 10;

@Component({
  selector: 'app-prediction-history',
  templateUrl: 'history.page.html',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    TableModule,
    Card,
    DecimalPipe,
  ],
})
export class HistoryPage {
  private readonly predictionService = inject(PredictionService);
  private readonly router = inject(Router);
  private readonly messages = inject(MessageService);

  readonly pageSize = PAGE_SIZE;
  readonly propertyTypes: ('All' | PropertyType)[] = ['All', 'Apartment', 'House', 'Villa'];

  predictions = signal<Prediction[]>([]);
  totalCount = signal<number>(0);
  loading = signal<boolean>(false);
  first = signal<number>(0);

  searchTerm = signal<string>('');
  selectedPropertyType = signal<'All' | PropertyType>('All');
  currentSorters = signal<Sorter<PredictionField>[]>([{ field: 'created_at', direction: 'desc' }]);

  public async onLazyLoad(event: TableLazyLoadEvent): Promise<void> {
    const first = event.first ?? 0;
    const rows = event.rows ?? this.pageSize;
    this.first.set(first);

    // Extract sorters
    if (event.sortField) {
      const field = event.sortField as PredictionField;
      const direction = event.sortOrder === 1 ? 'asc' : 'desc';
      this.currentSorters.set([{ field, direction }]);
    } else {
      this.currentSorters.set([{ field: 'created_at', direction: 'desc' }]);
    }

    await this.loadHistory();
  }

  public async loadHistory(): Promise<void> {
    this.loading.set(true);
    const page = Math.floor(this.first() / this.pageSize) + 1;

    // Build filters
    const filters: Filter<PredictionField>[] = [];
    
    const searchVal = this.searchTerm().trim();
    if (searchVal) {
      filters.push({
        field: 'location',
        operator: 'contains',
        value: searchVal,
      });
    }

    const typeVal = this.selectedPropertyType();
    if (typeVal !== 'All') {
      filters.push({
        field: 'property_type',
        operator: 'eq',
        value: typeVal,
      });
    }

    const dto: SearchDTO<PredictionField> = {
      filters,
      sorters: this.currentSorters(),
      pagination: { page, pageSize: this.pageSize },
    };

    try {
      const res = await this.predictionService.search(dto);
      this.predictions.set(res.results);
      this.totalCount.set(res.pagination.totalElements);
    } catch (error) {
      this.messages.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Could not load prediction history. Please try again.',
      });
    } finally {
      this.loading.set(false);
    }
  }

  public onSearchChange(newVal: string): void {
    this.searchTerm.set(newVal);
    this.first.set(0);
    this.loadHistory();
  }

  public selectPropertyType(type: 'All' | PropertyType): void {
    this.selectedPropertyType.set(type);
    this.first.set(0);
    this.loadHistory();
  }

  public async viewDetails(id: string): Promise<void> {
    await this.router.navigate(['/dashboard/predict/result', id]);
  }

  // ── Formatter Helpers ──────────────────────────────────────────────

  public formatDate(dateStr: string): string {
    if (!dateStr) return '—';
    return dateStr.slice(0, 10);
  }

  public formatPrice(price: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(price);
  }

  public confidenceBadgeClass(conf: number): string {
    if (conf >= 0.90) {
      return 'bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-full text-xs font-semibold inline-flex items-center gap-1.5 border border-emerald-100';
    }
    if (conf >= 0.80) {
      return 'bg-amber-50 text-amber-700 px-2.5 py-1 rounded-full text-xs font-semibold inline-flex items-center gap-1.5 border border-amber-100';
    }
    return 'bg-rose-50 text-rose-700 px-2.5 py-1 rounded-full text-xs font-semibold inline-flex items-center gap-1.5 border border-rose-100';
  }

  public confidenceDotClass(conf: number): string {
    if (conf >= 0.90) return 'w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse';
    if (conf >= 0.80) return 'w-1.5 h-1.5 rounded-full bg-amber-500';
    return 'w-1.5 h-1.5 rounded-full bg-rose-500';
  }
}
