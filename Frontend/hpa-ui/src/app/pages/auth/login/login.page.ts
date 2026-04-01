import { Component, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ILustrationPanel } from '../shared/ilustration-panel';

@Component({
  templateUrl: 'login.page.html',
  imports: [
    ReactiveFormsModule,
    RouterLink,
    ILustrationPanel
  ],
})
export class LoginPage {
  showPassword = signal<boolean>(false);
  loading = signal<boolean>(false);

  form = new FormGroup({
    email: new FormControl('', [Validators.required, Validators.email]),
    password: new FormControl('', [Validators.required]),
  });

  public changePasswordVisibility(): void {
    this.showPassword.set(!this.showPassword());
  }

  public handleSubmit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
  }
}
