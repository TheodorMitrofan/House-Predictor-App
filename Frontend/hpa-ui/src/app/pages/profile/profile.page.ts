import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { TableLazyLoadEvent, TableModule } from 'primeng/table';
import { MessageService } from 'primeng/api';
import { UserService } from '../../shared/services/user.service';
import { PredictionService, PredictionField } from '../prediction/services/prediction.service';
import { Prediction, PropertyType } from '../prediction/models/Prediction';
import { SearchDTO, Filter, Sorter } from '../../shared/models/search-dto';

interface ProfileForm {
  name: string;
  email: string;
  location: string;
  bio: string;
}

interface ActivityStat {
  label: string;
  value: string;
  icon: string;
  color: string;
  bg: string;
}

@Component({
  templateUrl: 'profile.page.html',
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    TableModule,
    DecimalPipe,
  ],
})
export class ProfilePage implements OnInit {
  private readonly userService = inject(UserService);
  private readonly predictionService = inject(PredictionService);
  private readonly messages = inject(MessageService);

  saving = signal<boolean>(false);
  user = this.userService.currentUser;
  editing = signal<boolean>(false);
  touched = signal<Record<'name' | 'location' | 'bio', boolean>>({
    name: false,
    location: false,
    bio: false,
  });

  form = signal<ProfileForm>({
    name: this.user()?.full_name ?? '',
    email: this.user()?.email ?? '',
    location: this.user()?.location ?? '',
    bio: this.user()?.description ?? '',
  });

  readonly isFormValid = computed<boolean>(() => {
    const f = this.form();
    return f.name.trim().length > 0
      && f.location.trim().length > 0
      && f.bio.trim().length > 0;
  });

  // ── Dynamic Prediction Stats ──────────────────────────────────────
  totalPredictions = signal<number>(0);
  avgPredictedPrice = signal<number>(0);
  avgConfidence = signal<number>(0);

  readonly activityStats = computed<ActivityStat[]>(() => [
    { label: 'Total Predictions', value: this.totalPredictions().toString(), icon: 'pi-chart-bar', color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Avg. Predicted Price', value: this.formatPrice(this.avgPredictedPrice()), icon: 'pi-chart-line', color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { label: 'Avg. Confidence', value: `${this.avgConfidence()}%`, icon: 'pi-bolt', color: 'text-violet-600', bg: 'bg-violet-50' },
    { label: 'Member Since', value: this.formatJoinDate(this.user()?.created_date), icon: 'pi-calendar', color: 'text-orange-600', bg: 'bg-orange-50' },
  ]);

  // ── Pagination, Search & Sorting State ────────────────────────────
  predictions = signal<Prediction[]>([]);
  totalCount = signal<number>(0);
  loading = signal<boolean>(false);
  first = signal<number>(0);
  readonly pageSize = 5; // Compact size for profile page list

  searchTerm = signal<string>('');
  selectedPropertyType = signal<'All' | PropertyType>('All');
  readonly propertyTypes: ('All' | PropertyType)[] = ['All', 'Apartment', 'House', 'Villa'];
  currentSorters = signal<Sorter<PredictionField>[]>([{ field: 'created_at', direction: 'desc' }]);

  async ngOnInit() {
    if (!this.user()) {
      await this.userService.load();
    }
    const u = this.user();
    if (u) {
      this.form.set({
        name: u.full_name,
        email: u.email,
        location: u.location ?? '',
        bio: u.description ?? '',
      });
    }
    await this.loadStats();
  }

  // ── Load Stats Dynamically ────────────────────────────────────────
  private async loadStats(): Promise<void> {
    try {
      const dto: SearchDTO<PredictionField> = {
        filters: [],
        sorters: [],
        pagination: { page: 1, pageSize: 100 },
      };
      const res = await this.predictionService.search(dto);
      this.totalPredictions.set(res.pagination.totalElements);
      
      const results = res.results;
      if (results.length > 0) {
        const priceSum = results.reduce((acc, p) => acc + p.prediction_value, 0);
        this.avgPredictedPrice.set(Math.round(priceSum / results.length));
        
        const confSum = results.reduce((acc, p) => acc + p.confidence, 0);
        this.avgConfidence.set(Math.round((confSum / results.length) * 100));
      } else {
        this.avgPredictedPrice.set(0);
        this.avgConfidence.set(0);
      }
    } catch {
      // Fallback in case prediction list fails to load
    }
  }

  // ── Lazy Load prediction history with filtering/sorting ───────────
  public async onLazyLoad(event: TableLazyLoadEvent): Promise<void> {
    const first = event.first ?? 0;
    const rows = event.rows ?? this.pageSize;
    this.first.set(first);

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

    const filters: Filter<PredictionField>[] = [];
    const searchVal = this.searchTerm().trim();
    if (searchVal) {
      filters.push({ field: 'location', operator: 'contains', value: searchVal });
    }
    const typeVal = this.selectedPropertyType();
    if (typeVal !== 'All') {
      filters.push({ field: 'property_type', operator: 'eq', value: typeVal });
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
    } catch {
      this.messages.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Could not load prediction history.',
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

  // ── Helpers & Formatting ──────────────────────────────────────────
  private formatJoinDate(iso?: string): string {
    if (!iso) return '—';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return '—';
    return d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  }

  public initials(): String {
    return this.user()!.full_name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase();
  }

  public formatPrice(price: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(price);
  }

  // ── Confidence Class Mappers ──────────────────────────────────────
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

  // ── Form Input & Edit profile handlers ─────────────────────────────
  public onFieldChange(key: keyof ProfileForm, event: Event): void {
    const value = (event.target as HTMLInputElement | HTMLTextAreaElement).value;
    this.form.update((f) => ({ ...f, [key]: value }));
  }

  public markTouched(key: 'name' | 'location' | 'bio'): void {
    this.touched.update((t) => ({ ...t, [key]: true }));
  }

  public fieldError(key: 'name' | 'location' | 'bio'): string | null {
    const value = this.form()[key];
    if (!this.touched()[key]) return null;
    if (value.trim().length === 0) {
      const labels = { name: 'Name', location: 'Location', bio: 'Bio' };
      return `${labels[key]} is required.`;
    }
    return null;
  }

  async save() {
    if (this.saving()) return;
    if (!this.isFormValid()) {
      this.touched.set({ name: true, location: true, bio: true });
      this.messages.add({
        severity: 'warn',
        summary: 'Missing fields',
        detail: 'Name, location and bio cannot be empty.',
      });
      return;
    }
    this.saving.set(true);
    try {
      const f = this.form();
      await this.userService.updateMe({
        full_name: f.name.trim(),
        location: f.location.trim(),
        description: f.bio.trim(),
      });
      await this.userService.load();
      this.messages.add({
        severity: 'success',
        summary: 'Profile updated',
        detail: 'Your changes have been saved.',
      });
      this.editing.set(false);
    } catch (err) {
      this.messages.add({
        severity: 'error',
        summary: 'Update failed',
        detail: 'Could not save your profile. Please try again.',
      });
    } finally {
      this.saving.set(false);
    }
  }

  public startEdit(): void {
    const u = this.user();
    if (u) {
      this.form.set({
        name: u.full_name,
        email: u.email,
        location: u.location ?? '',
        bio: u.description ?? '',
      });
    }
    this.touched.set({ name: false, location: false, bio: false });
    this.editing.set(true);
  }

  public cancelEdit(): void {
    this.touched.set({ name: false, location: false, bio: false });
    this.editing.set(false);
  }
}
