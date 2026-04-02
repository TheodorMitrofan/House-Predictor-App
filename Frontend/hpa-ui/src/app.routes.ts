import { Routes } from '@angular/router';
import { LoginPage } from './app/pages/auth/login/login.page';
import { RegisterPage } from './app/pages/auth/register/register.page';

export const routes: Routes = [
  {path: "", component: LoginPage },
  {path: "register", component: RegisterPage }
];
