import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Toast } from 'primeng/toast';

@Component({
  selector: 'app-root',
  imports: [
    RouterOutlet,
    Toast
  ],
  template: `
    <router-outlet />
    <p-toast position="top-right" />
  `,
})
export class App {}
