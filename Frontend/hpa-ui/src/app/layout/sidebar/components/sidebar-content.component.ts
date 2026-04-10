import { Component } from '@angular/core';

@Component({
  selector: "app-sidebar-content",
  template: `
    <div class="flex min-h-0 flex-1 flex-col gap-2 overflow-auto px-2">
      <ng-content />
    </div>
  `,
})

export class SidebarContentComponent {}
