import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { UserService } from '../services/user.service';

export const adminGuard: CanActivateFn = async () => {
  const userService = inject(UserService);
  const router = inject(Router);

  if (!userService.currentUser()) {
    try {
      await userService.load();
    } catch {
      return router.createUrlTree(['/']);
    }
  }

  return userService.currentUser()?.role === 'admin'
    ? true
    : router.createUrlTree(['/dashboard/user']);
};
