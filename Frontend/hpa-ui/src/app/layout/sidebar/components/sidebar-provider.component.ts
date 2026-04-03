import { Component } from '@angular/core';

@Component({
  selector: "app-sidebar-provider",
  template: `
    <div class="flex min-h-screen w-full">
      <ng-content />
    </div>
  `,
})
export class SidebarProviderComponent {}
