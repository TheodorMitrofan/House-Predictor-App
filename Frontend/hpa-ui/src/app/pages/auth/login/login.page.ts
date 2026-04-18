import { Component, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ILustrationPanel } from '../shared/ilustration-panel';
import { AuthService } from '../services/auth.service';
import { MessageService } from 'primeng/api';
import { handleLoginError } from '../shared/utils';

@Component({
  templateUrl: 'login.page.html',
  imports: [
    ReactiveFormsModule,
    RouterLink,
    ILustrationPanel
  ],
})
export class LoginPage {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly messages = inject(MessageService);

  showPassword = signal<boolean>(false);
  loading = signal<boolean>(false);

  form = new FormGroup({
    email: new FormControl('', [Validators.required, Validators.email]),
    password: new FormControl('', [Validators.required]),
  });

  public changePasswordVisibility(): void {
    this.showPassword.set(!this.showPassword());
  }

  async handleSubmit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);

    try {
      await this.authService.login({
        email: this.form.controls.email.value!,
        password: this.form.controls.password.value!,
      })
      const role = this.authService.getRoleFromToken();
      this.router.navigate([role === 'admin' ? '/dashboard/admin' : '/dashboard/user']);
    } catch (error) {
      handleLoginError(error, this.messages);
    } finally {
      this.loading.set(false);
    }
  }
}
