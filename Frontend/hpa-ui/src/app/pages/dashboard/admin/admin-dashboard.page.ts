import { Component, inject, OnInit, signal } from '@angular/core';
import { Card } from 'primeng/card';
import { NgClass } from '@angular/common';
import { UIChart } from 'primeng/chart';
import { IconField } from 'primeng/iconfield';
import { InputIcon } from 'primeng/inputicon';
import { TableModule } from 'primeng/table';
import { InputText } from 'primeng/inputtext';
import { User } from '../../auth/models/user';
import { AdminStatisticsService } from '../services/admin-statistics.service';
import { AdminStatistics } from '../models/AdminStatistics';
import { UserService } from '../../../shared/services/user.service';

@Component({
  templateUrl: 'admin-dashboard.page.html',
  imports: [Card, NgClass, UIChart, IconField, InputIcon, TableModule, InputText],
})
export class AdminDashboardPage implements OnInit {

  private readonly adminStatisticsService = inject(AdminStatisticsService);
  private readonly userService = inject(UserService);
  //TODO update in sprint 3 with real values
  statusAi = signal<boolean>(true);
  versionAi = signal<string>('1.0.0');
  lastTrainedDateAi = signal<string>('10-04-2026');
  totalPredictions = signal<number>(420);
  newPredictionsThisMonth = signal<number>(69);
  datasetSize = signal<number>(20000);
  newRecordsThisMonth = signal<number>(100);
  modelAccuracy = signal<number>(95);
  accuracyDelta = signal<number>(0.67);
  activeFilter = signal<'All' | 'User' | 'Admin'>('All');

  adminStatistics = signal<AdminStatistics | null>(null);
  users = signal<User[]>([
    {
      id: '1',
      full_name: 'Alex Johnson',
      email: 'user@example.com',
      role: 'user',
      prediction: 24,
      is_active: true,
      created_date: '2024-06-15',
    },
    {
      id: '2',
      full_name: 'Sarah Mitchell',
      email: 'admin@example.com',
      role: 'admin',
      prediction: 57,
      is_active: true,
      created_date: '2024-01-10',
    },
    {
      id: '3',
      full_name: 'Marcus Chen',
      email: 'm.chen@example.com',
      role: 'user',
      prediction: 12,
      is_active: true,
      created_date: '2026-03-08',
    },
    {
      id: '4',
      full_name: 'Laura Perez',
      email: 'l.perez@example.com',
      role: 'user',
      prediction: 38,
      is_active: true,
      created_date: '2025-04-22',
    },
    {
      id: '5',
      full_name: 'James Walker',
      email: 'j.walker@example.com',
      role: 'admin',
      prediction: 91,
      is_active: true,
      created_date: '2023-11-03',
    },
    {
      id: '6',
      full_name: 'Emily Nguyen',
      email: 'e.nguyen@example.com',
      role: 'user',
      prediction: 5,
      is_active: false,
      created_date: '2025-09-17',
    },
    {
      id: '7',
      full_name: 'David Kim',
      email: 'd.kim@example.com',
      role: 'user',
      prediction: 63,
      is_active: true,
      created_date: '2024-08-30',
    },
    {
      id: '8',
      full_name: 'Sophia Brown',
      email: 's.brown@example.com',
      role: 'user',
      prediction: 17,
      is_active: true,
      created_date: '2025-02-14',
    },
  ]);

  async ngOnInit(): Promise<void> {
    const data = await this.adminStatisticsService.getStatistics();
    this.adminStatistics.set(data);

    const data_users = await this.userService.getUsers();
    console.log(data_users);
  }

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

  getStatus(): string {
    if (this.statusAi()) {
      return 'Active';
    }

    return 'Not Active';
  }

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

  onAddUser(): void {
    console.log('Add User clicked');
  }

  onSearch(value: string): void {
    console.log('Search:', value);
  }

  onFilterChange(f: string): void {
    this.activeFilter.set(f as 'All' | 'User' | 'Admin');
    console.log('Filter changed:', f);
  }
}
