import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: "app-sidebar-menu-item",
  imports: [CommonModule, RouterModule],
  template: `
    <li>
      <a
        [routerLink]="route()"
        class="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors cursor-pointer"
        [ngClass]="{
          'bg-blue-50 text-blue-700': isActive(),
          'text-gray-600 hover:bg-gray-50 hover:text-gray-900': !isActive()
        }"
      >
        <ng-content select="[icon]" />
        <span class="flex-1 truncate">{{ label() }}</span>
        <ng-content select="[suffix]" />
      </a>
    </li>
  `,
})
export class SidebarMenuItemComponent {
  label = input.required<string>();
  route = input<string>('/');
  isActive = input(false);
}
