import { Routes } from '@angular/router';
import { LoginPage } from './app/pages/auth/login/login.page';
import { RegisterPage } from './app/pages/auth/register/register.page';
import { AppLayoutComponent } from './app/layout/sidebar/app-layout.component';
import { AdminDashboardPage } from './app/pages/dashboard/admin/admin-dashboard.page';
import { UserDashboardPage } from './app/pages/dashboard/user/user-dashboard.page';
import { ProfilePage } from './app/pages/profile/profile.page';
import { DataManagementPage } from './app/pages/data-management/data-management.page';
import { ModelTrainingPage } from './app/pages/model-training/model-training.page';
import { NewPredictionPage } from './app/pages/prediction/new-prediction/new-prediction.page';
import { PredictionResultPage } from './app/pages/prediction/prediction-result/prediction-result.page';
import { authGuard } from './app/shared/guards/auth.guard';
import { adminGuard } from './app/shared/guards/admin.guard';

export const routes: Routes = [
  { path: "", component: LoginPage },
  { path: "register", component: RegisterPage },
  {
    path: "dashboard",
    component: AppLayoutComponent,
    canActivate: [authGuard],
    children: [
      { path: "admin", component: AdminDashboardPage, canActivate: [adminGuard] },
      { path: "user", component: UserDashboardPage },
      { path: "profile", component: ProfilePage },
      { path: "data-management", component: DataManagementPage, canActivate: [adminGuard] },
      { path: "model-training", component: ModelTrainingPage, canActivate: [adminGuard] },
      { path: "predict", component: NewPredictionPage },
      { path: "predict/result/:id", component: PredictionResultPage },
    ],
  },
];
