import { Component, signal } from '@angular/core';
import { Card } from 'primeng/card';
import { NgClass } from '@angular/common';


@Component({
  templateUrl: 'admin-dashboard.page.html',
  imports: [Card, NgClass],
})
export class AdminDashboardPage {
  statusAi = signal<boolean>(true);

  getStatus(): string {
    if (this.statusAi()) {
      return 'Active';
    }

    return 'Not Active';
  }
}
