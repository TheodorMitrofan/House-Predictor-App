import { Component } from '@angular/core';

@Component({
  selector: "app-sidebar-group-label",
  template: `
    <div class="flex h-8 shrink-0 items-center px-3 text-xs font-semibold text-blue-600 uppercase tracking-wider">
      <ng-content />
    </div>
  `,
})

export class SidebarGroupLabelComponent {}
