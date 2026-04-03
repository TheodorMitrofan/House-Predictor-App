import { Component } from '@angular/core';

@Component({
  selector: "app-sidebar-group",
  template: `
    <div class="relative flex w-full min-w-0 flex-col py-1">
      <ng-content />
    </div>
  `,
})

export class SidebarGroupComponent {}
