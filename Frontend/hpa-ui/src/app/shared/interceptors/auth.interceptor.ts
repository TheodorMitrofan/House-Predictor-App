import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { environment } from '../../../environment/environment';
import { AuthService } from '../../pages/auth/services/auth.service';
import { inject } from '@angular/core';
import { catchError, from, switchMap, throwError } from 'rxjs';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const isApiCall = req.url.startsWith(environment.baseApiUrl);                                                                                                                       const isAuthEndpoint = req.url.includes('/users/auth/');
  const authed = attachToken(req, auth.getAccessToken(), isApiCall);

  return next(authed).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status !== 401 || !isApiCall || isAuthEndpoint || !auth.getRefreshToken()) {
        return throwError(() => err);
      }
      return from(auth.refresh()).pipe(
        switchMap(() => next(attachToken(req, auth.getAccessToken(), isApiCall))),
        catchError(refreshErr => {
          auth.logout();
          return throwError(() => refreshErr);
        }),
      );
    }),
  );
};

function attachToken(
  req: Parameters<HttpInterceptorFn>[0],
  token: string | null,
  isApiCall: boolean,
) {
  if (!token || !isApiCall) return req;
  return req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
}
