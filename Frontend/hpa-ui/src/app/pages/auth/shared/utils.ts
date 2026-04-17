import { HttpErrorResponse } from '@angular/common/http';
import { AbstractControl } from '@angular/forms';
import { MessageService } from 'primeng/api';

export function handleRegisterError(
  error: unknown,
  emailControl: AbstractControl,
  messages: MessageService,
): void {
  if (error instanceof HttpErrorResponse && error.status === 409) {
    emailControl.setErrors({ duplicate: true });
    return;
  }
  messages.add({
    severity: 'error',
    summary: 'Registration failed',
    detail: extractDetail(error, 'Unexpected error. Please try again.'),
  });
}

export function handleLoginError(error: unknown, messages: MessageService): void {
  if (error instanceof HttpErrorResponse && error.status === 401) {
    messages.add({
      severity: 'error',
      summary: 'Login failed',
      detail: 'Invalid email or password.',
    });
    return;
  }
  messages.add({
    severity: 'error',
    summary: 'Login failed',
    detail: extractDetail(error, 'Unexpected error. Please try again.'),
  });
}

function extractDetail(error: unknown, fallback: string): string {
  return error instanceof HttpErrorResponse
    ? (error.error?.detail ?? fallback)
    : fallback;
}