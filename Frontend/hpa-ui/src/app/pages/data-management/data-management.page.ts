import { Component, inject, signal } from '@angular/core';
import { TableLazyLoadEvent, TableModule } from 'primeng/table';
import { MessageService } from 'primeng/api';
import { TrainingData } from './models/TrainingData';
import { DataManagementService, TrainingDataField } from './services/data-management.service';
import { SearchDTO } from '../../shared/models/search-dto';

interface EntryForm {
  zipcode: number;
  bedrooms: number;
  bathrooms: number;
  sqft_living: number;
  floors: number;
  yr_built: number;
  grade: number;
  price: number;
}

const PAGE_SIZE = 20;

const DEFAULT_FORM: EntryForm = {
  zipcode: 98000,
  bedrooms: 3,
  bathrooms: 2,
  sqft_living: 1500,
  floors: 1,
  yr_built: 2010,
  grade: 7,
  price: 500000,
};

@Component({
  templateUrl: 'data-management.page.html',
  imports: [TableModule],
})
export class DataManagementPage {
  private readonly dataService = inject(DataManagementService);
  private readonly messages = inject(MessageService);

  readonly headers = ['Zipcode', 'Bedrooms', 'Bathrooms', 'Sqft Living', 'Floors', 'Year Built', 'Grade', 'Price', 'Actions'];
  readonly pageSize = PAGE_SIZE;

  data = signal<TrainingData[]>([]);
  totalCount = signal<number>(0);
  loading = signal<boolean>(false);
  first = signal<number>(0);

  showModal = signal<boolean>(false);
  editEntry = signal<TrainingData | null>(null);
  deleteConfirm = signal<number | null>(null);
  saving = signal<boolean>(false);

  form = signal<EntryForm>({ ...DEFAULT_FORM });

  public async onLazyLoad(event: TableLazyLoadEvent): Promise<void> {
    const first = event.first ?? 0;
    const rows = event.rows ?? this.pageSize;
    this.first.set(first);
    await this.loadData(first, rows);
  }

  private async loadData(first: number, rows: number): Promise<void> {
    this.loading.set(true);
    const page = Math.floor(first / rows) + 1;
    const dto: SearchDTO<TrainingDataField> = {
      filters: [],
      sorters: [],
      pagination: { page, pageSize: rows },
    };
    try {
      const res = await this.dataService.search(dto);
      this.data.set(res.results);
      this.totalCount.set(res.pagination.totalElements);
    } catch {
      this.messages.add({
        severity: 'error',
        summary: 'Load failed',
        detail: 'Could not load training data.',
      });
    } finally {
      this.loading.set(false);
    }
  }

  private async reloadCurrent(): Promise<void> {
    await this.loadData(this.first(), this.pageSize);
  }

  public openAddModal(): void {
    this.editEntry.set(null);
    this.form.set({ ...DEFAULT_FORM });
    this.showModal.set(true);
  }

  public openEditModal(entry: TrainingData): void {
    this.editEntry.set(entry);
    this.form.set({
      zipcode: entry.zipcode,
      bedrooms: entry.bedrooms,
      bathrooms: entry.bathrooms,
      sqft_living: entry.sqft_living,
      floors: entry.floors,
      yr_built: entry.yr_built,
      grade: entry.grade,
      price: entry.price,
    });
    this.showModal.set(true);
  }

  public closeModal(): void {
    this.showModal.set(false);
    this.editEntry.set(null);
  }

  public setField(key: keyof EntryForm, event: Event): void {
    const value = Number((event.target as HTMLInputElement).value);
    this.form.update((f) => ({ ...f, [key]: value }));
  }

  public async save(): Promise<void> {
    if (this.saving()) return;
    this.saving.set(true);

    const f = this.form();
    const editing = this.editEntry();

    try {
      if (editing) {
        await this.dataService.update(editing.id, f);
        this.messages.add({ severity: 'success', summary: 'Entry updated' });
      } else {
        const payload: Partial<TrainingData> = {
          ...f,
          sqft_lot: 0,
          waterfront: false,
          view: 0,
          condition: 3,
          sqft_above: f.sqft_living,
          sqft_basement: 0,
          yr_renovated: 0,
          lat: 0,
          long: 0,
          sqft_living15: 0,
          sqft_lot15: 0,
        };
        await this.dataService.create(payload);
        this.messages.add({ severity: 'success', summary: 'Entry added' });
      }
      this.closeModal();
      await this.reloadCurrent();
    } catch {
      this.messages.add({
        severity: 'error',
        summary: 'Save failed',
        detail: 'Could not save the entry.',
      });
    } finally {
      this.saving.set(false);
    }
  }

  public askDelete(id: number): void {
    this.deleteConfirm.set(id);
  }

  public cancelDelete(): void {
    this.deleteConfirm.set(null);
  }

  public async confirmDelete(id: number): Promise<void> {
    try {
      await this.dataService.delete(id);
      this.deleteConfirm.set(null);
      await this.reloadCurrent();
      // If the deleted row was the last one on a non-first page, step back
      if (this.data().length === 0 && this.first() >= this.pageSize) {
        this.first.set(this.first() - this.pageSize);
        await this.reloadCurrent();
      }
    } catch {
      this.deleteConfirm.set(null);
      this.messages.add({
        severity: 'error',
        summary: 'Delete failed',
        detail: 'Could not delete the entry.',
      });
    }
  }

  public formatPrice(price: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(price);
  }
}