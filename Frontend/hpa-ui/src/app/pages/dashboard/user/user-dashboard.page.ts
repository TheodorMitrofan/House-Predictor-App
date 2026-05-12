import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { Card } from 'primeng/card';
import { NgClass } from '@angular/common';
import { UIChart } from 'primeng/chart';
import { TableModule } from 'primeng/table';
import { UserService } from '../../../shared/services/user.service';
import { Router } from '@angular/router';

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

  user = this.userService.currentUser;

  greeting = computed(() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  });

  // ── Hardcoded stats ───────────────────────────────────────────────
  totalPredictions = signal<number>(24);
  lastPredictedPrice = signal<number>(875000);
  lastPredictedLocation = signal<string>('New York, NY');
  averagePredictedValue = signal<number>(586000);
  newThisWeek = signal<number>(3);

  // ── Model info ────────────────────────────────────────────────────
  modelAccuracy = signal<number>(94.2);
  modelVersion = signal<string>('v3.2.1');
  modelStatus = signal<boolean>(true);

  // ── Recent predictions (hardcoded) ────────────────────────────────
  recentPredictions = signal<RecentPrediction[]>([
    { id: '1', location: 'New York, NY',  property: 'Apartment · 3br · 120m²',  predictedPrice: 875000,  confidence: 92, date: '2026-03-10' },
    { id: '2', location: 'Austin, TX',    property: 'House · 4br · 210m²',      predictedPrice: 620000,  confidence: 88, date: '2026-03-07' },
    { id: '3', location: 'Miami, FL',     property: 'Condo · 2br · 85m²',       predictedPrice: 410000,  confidence: 79, date: '2026-02-28' },
    { id: '4', location: 'Seattle, WA',   property: 'Townhouse · 3br · 160m²',  predictedPrice: 730000,  confidence: 85, date: '2026-02-20' },
    { id: '5', location: 'Denver, CO',    property: 'House · 3br · 175m²',      predictedPrice: 540000,  confidence: 91, date: '2026-02-15' },
  ]);

  // ── Chart ─────────────────────────────────────────────────────────
  predictionTrendData = {
    labels: ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
    datasets: [
      {
        label: 'Predicted Price',
        data: [250000, 350000, 280000, 720000, 650000, 950000],
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
