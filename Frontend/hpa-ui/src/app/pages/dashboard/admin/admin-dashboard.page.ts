import { Component, inject, OnInit, signal } from '@angular/core';
import { Card } from 'primeng/card';
import { NgClass } from '@angular/common';
import { UIChart } from 'primeng/chart';
import { IconField } from 'primeng/iconfield';
import { InputIcon } from 'primeng/inputicon';
import { TableLazyLoadEvent, TableModule } from 'primeng/table';
import { InputText } from 'primeng/inputtext';
import { MessageService } from 'primeng/api';
import { User } from '../../auth/models/User';
import { AdminStatisticsService } from '../services/admin-statistics.service';
import { AdminStatistics } from '../models/AdminStatistics';
import { UserService, UserField } from '../../../shared/services/user.service';
import { Filter, SearchDTO } from '../../../shared/models/search-dto';

interface UserForm {
  full_name: string;
  email: string;
  password: string;
  role: 'user' | 'admin';
  is_active: boolean;
}

const DEFAULT_FORM: UserForm = {
  full_name: '',
  email: '',
  password: '',
  role: 'user',
  is_active: true,
};

@Component({
  templateUrl: 'admin-dashboard.page.html',
  imports: [Card, NgClass, UIChart, IconField, InputIcon, TableModule, InputText],
})
export class AdminDashboardPage implements OnInit {

  private readonly adminStatisticsService = inject(AdminStatisticsService);
  private readonly userService = inject(UserService);
  private readonly messages = inject(MessageService);

  adminStatistics = signal<AdminStatistics | null>(null);
  users = signal<User[]>([]);

  activeFilter = signal<'All' | 'User' | 'Admin'>('All');
  searchQuery = signal<string>('');

  // Pagination state
  readonly pageSize = 20;
  totalUsers = signal<number>(0);
  first = signal<number>(0);
  loadingUsers = signal<boolean>(false);

  // Modal state
  showModal = signal<boolean>(false);
  editingUser = signal<User | null>(null);
  form = signal<UserForm>({ ...DEFAULT_FORM });
  saving = signal<boolean>(false);
  deleteConfirmId = signal<string | null>(null);

  private searchTimeout: ReturnType<typeof setTimeout> | null = null;

  async ngOnInit(): Promise<void> {
    const data = await this.adminStatisticsService.getStatistics();
    this.adminStatistics.set(data);
    // Initial users load is triggered by PrimeNG's lazy table via onLazyLoad.
  }

  async onLazyLoad(event: TableLazyLoadEvent): Promise<void> {
    const first = event.first ?? 0;
    const rows = event.rows ?? this.pageSize;
    this.first.set(first);
    await this.loadUsers(first, rows);
  }

  private async loadUsers(first?: number, rows?: number): Promise<void> {
    const pageFirst = first ?? this.first();
    const pageRows = rows ?? this.pageSize;

    const filters: Filter<UserField>[] = [];
    if (this.activeFilter() !== 'All') {
      filters.push({ field: 'role', operator: 'eq', value: this.activeFilter().toLowerCase() });
    }
    if (this.searchQuery()) {
      filters.push({ field: 'full_name', operator: 'contains', value: this.searchQuery() });
    }

    const dto: SearchDTO<UserField> = {
      filters,
      sorters: [],
      pagination: { page: Math.floor(pageFirst / pageRows) + 1, pageSize: pageRows },
    };

    this.loadingUsers.set(true);
    try {
      const res = await this.userService.searchUsers(dto);
      this.users.set(res.results.map(u => ({ ...u, prediction: u.prediction ?? 0 })));
      this.totalUsers.set(res.pagination.totalElements);
    } finally {
      this.loadingUsers.set(false);
    }
  }

  private reloadFromStart(): void {
    this.first.set(0);
    this.loadUsers(0, this.pageSize);
  }

  // ── Stats helpers ─────────────────────────────────────────────────

  statusAi(): boolean {
    return !!this.adminStatistics()?.model_version;
  }

  getStatus(): string {
    return this.statusAi() ? 'Active' : 'Not Active';
  }

  versionAi(): string {
    return this.adminStatistics()?.model_version ?? '—';
  }

  lastTrainedDateAi(): string {
    const d = this.adminStatistics()?.last_trained_date;
    if (!d) return '—';
    return new Date(d).toLocaleDateString('en-GB');
  }

  totalPredictions(): number {
    return this.adminStatistics()?.total_predictions ?? 0;
  }

  newPredictionsThisMonth(): number {
    return this.adminStatistics()?.new_predictions_this_month ?? 0;
  }

  datasetSize(): number {
    return this.adminStatistics()?.dataset_size ?? 0;
  }

  modelAccuracy(): string {
    const acc = this.adminStatistics()?.model_accuracy;
    if (acc === null || acc === undefined) return '0.00';
    // If the accuracy is already formatted as a percentage (> 1), just format it,
    // otherwise multiply by 100 to convert fraction to percentage.
    const percentage = acc <= 1 ? acc * 100 : acc;
    return percentage.toFixed(2);
  }

  // ── Charts ────────────────────────────────────────────────────────

  platformActivityData = {
    labels: ['Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
    datasets: [
      {
        label: 'Predictions',
        data: [620, 850, 1050, 1200, 1450, 1700, 1870],
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
        borderWidth: 2,
        pointRadius: 0,
      },
      {
        label: 'New Users',
        data: [10, 20, 30, 45, 60, 90, 130],
        borderColor: '#a855f7',
        backgroundColor: 'transparent',
        borderDash: [6, 4],
        fill: false,
        tension: 0.4,
        borderWidth: 2,
        pointRadius: 0,
      },
    ],
  };
  platformActivityOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
    },
    scales: {
      x: {
        grid: { color: 'rgba(0,0,0,0.06)', borderDash: [4, 4] },
        border: { display: false },
        ticks: { color: '#9ca3af' },
      },
      y: {
        grid: { color: 'rgba(0,0,0,0.06)', borderDash: [4, 4] },
        border: { display: false },
        ticks: { color: '#9ca3af' },
      },
    },
  };
  modelAccuracyData = {
    labels: ['Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
    datasets: [
      {
        label: 'Accuracy %',
        data: [89, 91, 91, 90, 92, 93.5, 94.2],
        backgroundColor: '#3b82f6',
        borderRadius: 4,
        borderSkipped: false,
      },
    ],
  };
  modelAccuracyOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
    },
    scales: {
      x: {
        grid: { display: false },
        border: { display: false },
        ticks: { color: '#9ca3af' },
      },
      y: {
        min: 85,
        max: 100,
        grid: { color: 'rgba(0,0,0,0.06)' },
        border: { display: false },
        ticks: {
          color: '#9ca3af',
          callback: (value: number) => value + '%',
        },
      },
    },
  };

  // ── Helpers ───────────────────────────────────────────────────────

  getInitials(fullname: string): string {
    return fullname
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase();
  }

  getAvatarColor(id: string): string {
    const colors = [
      'bg-blue-500',
      'bg-purple-500',
      'bg-blue-600',
      'bg-green-500',
      'bg-purple-600',
      'bg-pink-500',
      'bg-orange-500',
      'bg-teal-500',
    ];
    return colors[id.charCodeAt(0) % colors.length];
  }

  // ── Search & Filter ───────────────────────────────────────────────

  onSearch(value: string): void {
    this.searchQuery.set(value);
    if (this.searchTimeout) clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(() => this.reloadFromStart(), 300);
  }

  onFilterChange(f: string): void {
    this.activeFilter.set(f as 'All' | 'User' | 'Admin');
    this.reloadFromStart();
  }

  // ── Add User ──────────────────────────────────────────────────────

  onAddUser(): void {
    this.editingUser.set(null);
    this.form.set({ ...DEFAULT_FORM });
    this.showModal.set(true);
  }

  // ── Edit User ─────────────────────────────────────────────────────

  onEditUser(user: User): void {
    this.editingUser.set(user);
    this.form.set({
      full_name: user.full_name,
      email: user.email,
      password: '',
      role: user.role as 'user' | 'admin',
      is_active: user.is_active,
    });
    this.showModal.set(true);
  }

  // ── Modal ─────────────────────────────────────────────────────────

  closeModal(): void {
    this.showModal.set(false);
    this.editingUser.set(null);
  }

  setField(key: keyof UserForm, event: Event): void {
    const el = event.target as HTMLInputElement | HTMLSelectElement;
    if (key === 'is_active') {
      this.form.update((f) => ({ ...f, is_active: (el as HTMLInputElement).checked }));
    } else {
      this.form.update((f) => ({ ...f, [key]: el.value }));
    }
  }

  setRole(value: string): void {
    this.form.update((f) => ({ ...f, role: value as 'user' | 'admin' }));
  }

  async saveUser(): Promise<void> {
    if (this.saving()) return;
    this.saving.set(true);

    const f = this.form();
    const editing = this.editingUser();

    try {
      if (editing) {
        await this.userService.updateUser(editing.id, {
          full_name: f.full_name,
          role: f.role,
          is_active: f.is_active,
        });
        this.messages.add({ severity: 'success', summary: 'User updated' });
      } else {
        await this.userService.createUser({
          full_name: f.full_name,
          email: f.email,
          password: f.password,
          role: f.role,
        });
        this.messages.add({ severity: 'success', summary: 'User created' });
      }
      this.closeModal();
      await this.loadUsers();
      // Refresh statistics
      const stats = await this.adminStatisticsService.getStatistics();
      this.adminStatistics.set(stats);
    } catch (err: any) {
      const detail = err?.error?.email || err?.error?.detail || 'Could not save user.';
      this.messages.add({ severity: 'error', summary: 'Save failed', detail });
    } finally {
      this.saving.set(false);
    }
  }

  // ── Delete User ───────────────────────────────────────────────────

  askDelete(userId: string): void {
    this.deleteConfirmId.set(userId);
  }

  cancelDelete(): void {
    this.deleteConfirmId.set(null);
  }

  async confirmDelete(userId: string): Promise<void> {
    try {
      await this.userService.deleteUser(userId);
      this.deleteConfirmId.set(null);
      this.messages.add({ severity: 'success', summary: 'User deleted' });
      await this.loadUsers();
      const stats = await this.adminStatisticsService.getStatistics();
      this.adminStatistics.set(stats);
    } catch (err: any) {
      this.deleteConfirmId.set(null);
      const detail = err?.error?.error || 'Could not delete user.';
      this.messages.add({ severity: 'error', summary: 'Delete failed', detail });
    }
  }
}
