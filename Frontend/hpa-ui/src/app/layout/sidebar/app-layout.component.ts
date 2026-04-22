import { SidebarFooterComponent } from './components/sidebar-footer.component';
import { Component, computed, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SidebarProviderComponent } from './components/sidebar-provider.component';
import { SidebarComponent } from './components/sidebar.component';
import { SidebarHeaderComponent } from './components/sidebar-header.component';
import { SidebarContentComponent } from './components/sidebar-content.component';
import { SidebarGroupComponent } from './components/sidebar-group.component';
import { SidebarMenuComponent } from './components/sidebar-menu.component';
import { SidebarMenuItemComponent } from './components/sidebar-menu-item.component';
import { SidebarInsetComponent } from './components/sidebar-inset.component';
import { SidebarGroupLabelComponent } from './components/sidebar-group-label.component';
import { AuthService } from '../../pages/auth/services/auth.service';
import { UserService } from '../../shared/services/user.service';

@Component({
  selector: "app-layout",
  imports: [
    CommonModule,
    RouterModule,
    SidebarProviderComponent,
    SidebarComponent,
    SidebarHeaderComponent,
    SidebarContentComponent,
    SidebarFooterComponent,
    SidebarGroupComponent,
    SidebarGroupLabelComponent,
    SidebarMenuComponent,
    SidebarMenuItemComponent,
    SidebarInsetComponent,
  ],
  template: `
    <app-sidebar-provider>
      <app-sidebar>

        <app-sidebar-header>
          <div class="flex items-center gap-3 px-1">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white">
              <!-- PrimeNG icon here -->
              <i class="pi pi-home text-lg"></i>
            </div>
            <div>
              <div class="text-sm font-bold text-gray-900">ProphetAI</div>
              <div class="text-xs text-gray-500">House Price Intelligence</div>
            </div>
          </div>
        </app-sidebar-header>

        <app-sidebar-content>
          <app-sidebar-group>
            <app-sidebar-group-label>User Panel</app-sidebar-group-label>
            <app-sidebar-menu>

              <app-sidebar-menu-item label="Dashboard" [route]="dashboardRoute()">
                <i icon class="pi pi-th-large"></i>
              </app-sidebar-menu-item>

              <app-sidebar-menu-item label="New Prediction" route="/predict">
                <i icon class="pi pi-plus-circle"></i>
              </app-sidebar-menu-item>

              <app-sidebar-menu-item label="History" route="/history">
                <i icon class="pi pi-history"></i>
              </app-sidebar-menu-item>

              <app-sidebar-menu-item label="Profile" route="/dashboard/profile">
                <i icon class="pi pi-user"></i>
              </app-sidebar-menu-item>

            </app-sidebar-menu>
          </app-sidebar-group>
        </app-sidebar-content>

        <app-sidebar-footer>
          <div class="flex items-center gap-3 px-2 py-2">
            <div class="flex h-9 w-9 items-center justify-center rounded-full bg-blue-600 text-white text-xs font-bold">
              {{ computeInitials() }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-gray-900 truncate">{{ currentUser()!.full_name }}</div>
              <div class="text-xs text-gray-500 truncate">{{ currentUser()!.email }}</div>
            </div>
          </div>
          <button class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
                  (click)="logout()">
            <i class="pi pi-sign-out"></i>
            Sign Out
          </button>
        </app-sidebar-footer>

      </app-sidebar>

      <app-sidebar-inset>
        <router-outlet />
      </app-sidebar-inset>
    </app-sidebar-provider>
  `,
})
export class AppLayoutComponent implements OnInit {
  private readonly authService = inject(AuthService)
  private readonly userService = inject(UserService)

  currentUser = this.userService.currentUser;

  dashboardRoute = computed(() =>
    this.currentUser()?.role === 'admin' ? '/dashboard/admin' : '/dashboard/user'
  );

  async ngOnInit() {
    if (!this.currentUser()) {
      await this.userService.load();
    }
  }

  public computeInitials(): string {
    return (this.currentUser()?.full_name ?? '')
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map(word => word[0]!.toUpperCase())
      .join('');
  }

  public logout(): void {
    this.authService.logout();
  }
}
