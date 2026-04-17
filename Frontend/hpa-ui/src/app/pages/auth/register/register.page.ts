import { Component, inject, signal } from '@angular/core';
import { ILustrationPanel } from '../shared/ilustration-panel';
import {
  AbstractControl,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { MessageService } from 'primeng/api';
import { handleRegisterError } from '../shared/utils';

@Component({
  templateUrl: 'register.page.html',
  imports: [ILustrationPanel, ReactiveFormsModule, RouterLink],
})
export class RegisterPage {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly messages = inject(MessageService);

  showPassword = signal<boolean>(false);
  showConfirmedPassword = signal<boolean>(false);
  loading = signal<boolean>(false);

  form = new FormGroup(
    {
      fullName: new FormControl('', [Validators.required]),
      email: new FormControl('', [Validators.required, Validators.email]),
      password: new FormControl('', [Validators.required, Validators.minLength(6)]),
      confirmPassword: new FormControl('', [Validators.required, Validators.minLength(6)]),
    },
    { validators: this.matchPasswords() },
  );

  public changePasswordVisibility(): void {
    this.showPassword.set(!this.showPassword());
  }

  public changeConfirmedPasswordVisibility(): void {
    this.showConfirmedPassword.set(!this.showConfirmedPassword());
  }

  async handleSubmit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);

    try {
      await this.authService.register({
        full_name: this.form.controls.fullName.value!,
        email: this.form.controls.email.value!,
        password: this.form.controls.password.value!,
      });
      this.router.navigate(['/dashboard']);
    } catch (error) {
      handleRegisterError(error, this.form.controls.email, this.messages);
    } finally {
      this.loading.set(false);
    }
  }

  private matchPasswords(): ValidatorFn {
    return (group: AbstractControl): ValidationErrors | null => {
      const password = group.get('password')?.value;
      const confirmPassword = group.get('confirmPassword')?.value;
      return password === confirmPassword ? null : { passwordMismatch: true };
    };
  }
}
