import { Component } from '@angular/core';

@Component({
  selector: "app-sidebar-menu",
  template: `
    <ul class="flex w-full min-w-0 flex-col gap-1 px-1">
      <ng-content />
    </ul>
  `,
})

export class SidebarMenuComponent {}
