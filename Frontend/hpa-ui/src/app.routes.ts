import { Routes } from '@angular/router';
import { LoginPage } from './app/pages/auth/login/login.page';
import { RegisterPage } from './app/pages/auth/register/register.page';
import { AppLayoutComponent } from './app/layout/sidebar/app-layout.component';
import { AdminDashboardPage } from './app/pages/dashboard/admin/admin-dashboard.page';
import { authGuard } from './app/shared/guards/auth.guard';

export const routes: Routes = [
  { path: "", component: LoginPage },
  { path: "register", component: RegisterPage },
  {
    path: "dashboard",
    component: AppLayoutComponent,
    canActivate: [authGuard],
    children: [
      { path: "", component: AdminDashboardPage },
    ],
  },
];
