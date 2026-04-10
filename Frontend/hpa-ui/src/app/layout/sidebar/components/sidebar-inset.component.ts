import { Component } from '@angular/core';

@Component({
  selector: "app-sidebar-inset",
  host: { class: "flex-1 min-w-0" },
  template: `
    <main class="relative flex w-full flex-col bg-gray-50 min-h-screen">
      <ng-content />
    </main>
  `,
})

export class SidebarInsetComponent {}
