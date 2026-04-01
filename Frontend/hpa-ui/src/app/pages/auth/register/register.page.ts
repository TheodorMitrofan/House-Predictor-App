import { Component, signal } from '@angular/core';
import { ILustrationPanel } from '../shared/ilustration-panel';
import {
  AbstractControl,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  ValidatorFn,
  Validators
} from '@angular/forms';
import { RouterLink } from '@angular/router';

@Component({
  templateUrl: 'register.page.html',
  imports: [ILustrationPanel, ReactiveFormsModule, RouterLink],
})
export class RegisterPage {
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

  public handleSubmit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
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
