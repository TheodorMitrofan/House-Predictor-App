import { Component } from '@angular/core';

@Component({
  selector: "app-sidebar-header",
  template: `
    <div class="flex flex-col gap-2 p-4">
      <ng-content />
    </div>
  `,
})

export class SidebarHeaderComponent {}
