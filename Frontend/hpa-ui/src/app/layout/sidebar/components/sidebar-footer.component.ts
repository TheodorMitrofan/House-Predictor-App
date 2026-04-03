import { Component } from '@angular/core';

@Component({
  selector: "app-sidebar-footer",
  host: { class: "mt-auto" },
  template: `
    <div class="flex flex-col gap-2 p-2 border-t border-gray-100">
      <ng-content />
    </div>
  `,
})

export class SidebarFooterComponent {}
