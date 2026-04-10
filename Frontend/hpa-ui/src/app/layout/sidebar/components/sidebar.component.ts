import { Component } from '@angular/core';

@Component({
  selector: "app-sidebar",
  template: `
    <aside class="fixed inset-y-0 left-0 z-10 flex h-screen w-64 flex-col border-r border-gray-200 bg-white">
      <ng-content />
    </aside>
    <div class="w-64 shrink-0"></div>
  `,
})

export class SidebarComponent {}
