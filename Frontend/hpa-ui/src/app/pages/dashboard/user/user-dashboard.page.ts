import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { Card } from 'primeng/card';
import { NgClass } from '@angular/common';
import { UIChart } from 'primeng/chart';
import { TableModule } from 'primeng/table';
import { UserService } from '../../../shared/services/user.service';
import { Router } from '@angular/router';
import { PredictionService, PredictionField } from '../../prediction/services/prediction.service';
import { ModelTrainingService } from '../../model-training/services/model-training.service';
import { SearchDTO } from '../../../shared/models/search-dto';

interface RecentPrediction {
  id: string;
  location: string;
  property: string;
  predictedPrice: number;
  confidence: number;
  date: string;
}

@Component({
  templateUrl: 'user-dashboard.page.html',
  imports: [Card, NgClass, UIChart, TableModule],
})
export class UserDashboardPage implements OnInit {

  private readonly userService = inject(UserService);
  private readonly router = inject(Router);
  private readonly predictionService = inject(PredictionService);
  private readonly trainingService = inject(ModelTrainingService);

  user = this.userService.currentUser;

  greeting = computed(() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  });

  // ── Dynamic stats ─────────────────────────────────────────────────
  totalPredictions = signal<number>(0);
  lastPredictedPrice = signal<number>(0);
  lastPredictedLocation = signal<string>('No predictions yet');
  averagePredictedValue = signal<number>(0);
  newThisWeek = signal<number>(0);

  // ── Model info ────────────────────────────────────────────────────
  modelAccuracy = signal<string>('0.00');
  modelVersion = signal<string>('v1.0.0');
  modelStatus = signal<boolean>(false);

  // ── Recent predictions ────────────────────────────────────────────
  recentPredictions = signal<RecentPrediction[]>([]);

  // ── Chart ─────────────────────────────────────────────────────────
  predictionTrendData = {
    labels: ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
    datasets: [
      {
        label: 'Predicted Price',
        data: [0, 0, 0, 0, 0, 0],
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.08)',
        fill: true,
        tension: 0.4,
        borderWidth: 2,
        pointRadius: 5,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
      },
    ],
  };

  predictionTrendOptions = {
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
        grid: { color: 'rgba(0,0,0,0.06)', borderDash: [4, 4] },
        border: { display: false },
        ticks: {
          color: '#9ca3af',
          callback: (value: number) => {
            if (value >= 1000000) return '$' + (value / 1000000).toFixed(0) + 'M';
            if (value >= 1000) return '$' + (value / 1000).toFixed(0) + 'k';
            return '$' + value;
          },
        },
      },
    },
  };

  async ngOnInit(): Promise<void> {
    if (!this.user()) {
      await this.userService.load();
    }
    await this.loadDashboardData();
  }

  async loadDashboardData(): Promise<void> {
    try {
      // 1. Fetch recent predictions (last 100 to compute stats and chart)
      const dto: SearchDTO<PredictionField> = {
        filters: [],
        sorters: [{ field: 'created_at', direction: 'desc' }],
        pagination: { page: 1, pageSize: 100 }
      };
      
      const res = await this.predictionService.search(dto);
      const results = res.results;
      
      this.totalPredictions.set(res.pagination.totalElements);
      
      // Calculate "new this week"
      const oneWeekAgo = new Date();
      oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
      const recentCount = results.filter(p => new Date(p.created_at) >= oneWeekAgo).length;
      this.newThisWeek.set(recentCount);

      if (results.length > 0) {
        this.lastPredictedPrice.set(results[0].prediction_value);
        this.lastPredictedLocation.set(results[0].location);
        
        const sum = results.reduce((acc, curr) => acc + curr.prediction_value, 0);
        this.averagePredictedValue.set(Math.round(sum / results.length));
        
        // Map to recentPredictions UI model (top 5 recent)
        const recent = results.slice(0, 5).map(p => ({
          id: p.id,
          location: p.location,
          property: `${p.property_type} · ${Math.round(p.bedrooms)} bed · ${Math.round(p.floor_area)}m²`,
          predictedPrice: p.prediction_value,
          confidence: Math.round(p.confidence * 100),
          date: p.created_at.slice(0, 10)
        }));
        this.recentPredictions.set(recent);
        
        // Update Chart with last 6 predictions trend
        const chartPredictions = [...results].slice(0, 6).reverse();
        const labels = chartPredictions.map(p => {
          const d = new Date(p.created_at);
          return d.toLocaleString('en-US', { month: 'short', day: 'numeric' });
        });
        const data = chartPredictions.map(p => p.prediction_value);
        
        this.predictionTrendData = {
          labels,
          datasets: [
            {
              ...this.predictionTrendData.datasets[0],
              data
            }
          ]
        };
      } else {
        this.lastPredictedPrice.set(0);
        this.lastPredictedLocation.set('No predictions yet');
        this.averagePredictedValue.set(0);
        this.recentPredictions.set([]);
      }
      
      // 2. Fetch active model info
      const activeModel = await this.trainingService.getActiveModel();
      if (activeModel) {
        const acc = activeModel.accuracy;
        const percentage = acc <= 1 ? acc * 100 : acc;
        this.modelAccuracy.set(percentage.toFixed(2));
        this.modelVersion.set(activeModel.version ? `v${activeModel.version}` : 'v1.0.0');
        this.modelStatus.set(activeModel.success);
      }
    } catch (e) {
      console.error('Could not load user dashboard statistics', e);
    }
  }

  formatPrice(price: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(price);
  }

  getConfidenceColor(confidence: number): string {
    if (confidence >= 90) return 'text-green-600 bg-green-50';
    if (confidence >= 80) return 'text-blue-600 bg-blue-50';
    return 'text-orange-600 bg-orange-50';
  }

  navigateTo(path: string): void {
    this.router.navigate([path]);
  }
}
