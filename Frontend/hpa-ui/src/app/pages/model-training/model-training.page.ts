import { AfterViewChecked, Component, ElementRef, inject, OnDestroy, OnInit, signal, ViewChild } from '@angular/core';
import { NgClass } from '@angular/common';
import { Card } from 'primeng/card';
import { ProgressBar } from 'primeng/progressbar';
import { TableLazyLoadEvent, TableModule } from 'primeng/table';
import { MessageService } from 'primeng/api';
import { ModelTrainingService, RunHistoryField } from './services/model-training.service';
import { ActiveModel } from './models/ActiveModel';
import { RunHistory } from './models/RunHistory';
import { TrainingStatus } from './models/TrainingStatus';
import { SearchDTO } from '../../shared/models/search-dto';

const POLL_INTERVAL_MS = 1500;
const PAGE_SIZE = 10;

interface ComparisonSnapshot {
  newRun: RunHistory;
  previous: RunHistory | null;
  activated: boolean;
}

@Component({
  templateUrl: 'model-training.page.html',
  imports: [Card, NgClass, ProgressBar, TableModule],
})
export class ModelTrainingPage implements OnInit, OnDestroy, AfterViewChecked {
  private readonly service = inject(ModelTrainingService);
  private readonly messages = inject(MessageService);

  @ViewChild('logBox') logBox?: ElementRef<HTMLDivElement>;

  readonly pageSize = PAGE_SIZE;

  active = signal<ActiveModel | null>(null);
  status = signal<TrainingStatus>({
    status: 'idle',
    progress: 0,
    current_run_id: null,
    started_at: null,
    ended_at: null,
    error: null,
    logs: [],
  });

  history = signal<RunHistory[]>([]);
  totalRuns = signal<number>(0);
  first = signal<number>(0);
  loadingHistory = signal<boolean>(false);

  comparison = signal<ComparisonSnapshot | null>(null);
  retraining = signal<boolean>(false);

  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private lastLogCount = 0;

  async ngOnInit(): Promise<void> {
    await this.refreshActive();
    const initial = await this.service.getStatus();
    this.status.set(initial);
    if (initial.status === 'running') {
      this.retraining.set(true);
      this.startPolling();
    }
  }

  ngOnDestroy(): void {
    this.stopPolling();
  }

  ngAfterViewChecked(): void {
    const logs = this.status().logs;
    if (logs.length !== this.lastLogCount && this.logBox?.nativeElement) {
      this.lastLogCount = logs.length;
      this.logBox.nativeElement.scrollTop = this.logBox.nativeElement.scrollHeight;
    }
  }

  // ── Actions ───────────────────────────────────────────────────────

  async onRetrain(): Promise<void> {
    if (this.retraining()) return;
    this.retraining.set(true);
    this.comparison.set(null);
    try {
      const res = await this.service.retrain();
      this.messages.add({ severity: 'info', summary: 'Reantrenare pornită', detail: res.message });
      this.startPolling();
    } catch (err: any) {
      this.retraining.set(false);
      const detail = err?.error?.error || err?.error?.detail || 'Could not start retraining.';
      this.messages.add({ severity: 'error', summary: 'Retrain failed', detail });
    }
  }

  onReset(): void {
    if (this.retraining()) return;
    this.comparison.set(null);
    this.status.update(s => ({ ...s, status: 'idle', progress: 0, logs: [] }));
    this.lastLogCount = 0;
  }

  async onLazyLoad(event: TableLazyLoadEvent): Promise<void> {
    const first = event.first ?? 0;
    const rows = event.rows ?? this.pageSize;
    this.first.set(first);
    await this.loadHistory(first, rows, event);
  }

  // ── Polling ───────────────────────────────────────────────────────

  private startPolling(): void {
    this.stopPolling();
    this.pollTimer = setInterval(() => this.tick(), POLL_INTERVAL_MS);
  }

  private stopPolling(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  private async tick(): Promise<void> {
    try {
      const next = await this.service.getStatus();
      this.status.set(next);
      if (next.status === 'complete' || next.status === 'failed') {
        this.stopPolling();
        this.retraining.set(false);
        await this.refreshActive();
        await this.loadHistory(0, this.pageSize);
        this.first.set(0);
        await this.buildComparison(next.status === 'complete');

        if (next.status === 'complete') {
          this.messages.add({ severity: 'success', summary: 'Training complete' });
        } else {
          this.messages.add({
            severity: 'error',
            summary: 'Training failed',
            detail: next.error || 'Unknown error',
          });
        }
      }
    } catch {
      // Transient errors — keep polling.
    }
  }

  private async buildComparison(success: boolean): Promise<void> {
    const dto: SearchDTO<RunHistoryField> = {
      filters: [],
      sorters: [{ field: 'date', direction: 'desc' }],
      pagination: { page: 1, pageSize: 2 },
    };
    const res = await this.service.searchHistory(dto);
    if (!success || !res.results.length) return;
    const [latest, previous] = res.results;
    this.comparison.set({
      newRun: latest,
      previous: previous ?? null,
      activated: latest.is_active,
    });
  }

  // ── Data loaders ──────────────────────────────────────────────────

  private async refreshActive(): Promise<void> {
    this.active.set(await this.service.getActiveModel());
  }

  private async loadHistory(first: number, rows: number, event?: TableLazyLoadEvent): Promise<void> {
    const page = Math.floor(first / rows) + 1;
    const sorters = this.extractSorters(event);

    const dto: SearchDTO<RunHistoryField> = {
      filters: [],
      sorters,
      pagination: { page, pageSize: rows },
    };

    this.loadingHistory.set(true);
    try {
      const res = await this.service.searchHistory(dto);
      this.history.set(res.results);
      this.totalRuns.set(res.pagination.totalElements);
    } catch {
      this.messages.add({
        severity: 'error',
        summary: 'Load failed',
        detail: 'Could not load training history.',
      });
    } finally {
      this.loadingHistory.set(false);
    }
  }

  private extractSorters(event?: TableLazyLoadEvent): { field: RunHistoryField; direction: 'asc' | 'desc' }[] {
    if (!event?.sortField) return [{ field: 'date', direction: 'desc' }];
    const field = event.sortField as RunHistoryField;
    return [{ field, direction: event.sortOrder === 1 ? 'asc' : 'desc' }];
  }

  // ── Display helpers ───────────────────────────────────────────────

  accuracyPct(value: number | null | undefined): string {
    if (value === null || value === undefined) return '—';
    return `${(value * 100).toFixed(1)}%`;
  }

  formatNumber(value: number | null | undefined): string {
    if (value === null || value === undefined) return '—';
    return value.toLocaleString('en-US');
  }

  formatRmse(value: number | null | undefined): string {
    if (value === null || value === undefined) return '—';
    return value.toLocaleString('en-US', { maximumFractionDigits: 0 });
  }

  formatDate(value: string | null | undefined): string {
    if (!value) return '—';
    return new Date(value).toLocaleString('en-GB');
  }

  formatDuration(value: string | null | undefined): string {
    if (!value) return '—';
    // Postgres "interval" comes back as "HH:MM:SS.ms" or "P0DT...". Show the seconds part.
    const match = value.match(/(\d+):(\d{2}):(\d{2})/);
    if (match) {
      const m = parseInt(match[2], 10);
      const s = parseInt(match[3], 10);
      return m > 0 ? `${m}m ${s}s` : `${s}s`;
    }
    return value;
  }

  formatVersion(): string {
    return this.active()?.version ? `v${this.active()!.version}` : '—';
  }

  lastTrainedRelative(): string {
    const d = this.active()?.date;
    if (!d) return '—';
    const diff = Date.now() - new Date(d).getTime();
    if (diff < 60_000) return 'Just now';
    const mins = Math.floor(diff / 60_000);
    if (mins < 60) return `${mins} min ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }

  shortRunId(id: string): string {
    return 'run-' + id.slice(0, 6);
  }

  isInProgress(): boolean {
    return this.status().status === 'running';
  }

  progressLabel(): string {
    const s = this.status().status;
    if (s === 'running') return `Training... ${this.status().progress}%`;
    if (s === 'complete') return 'Training complete';
    if (s === 'failed') return 'Training failed';
    return 'Idle';
  }
}
