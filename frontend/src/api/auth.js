import client from './client.js';

export const authApi = {
  /**
   * Register a new account.
   * @param {{ email: string, password: string, display_name: string }} body
   */
  register: (body) => client.post('/auth/register', body).then((r) => r.data),

  /**
   * Log in. Returns { access_token, user }.
   * The backend also sets an httpOnly refresh token cookie.
   * @param {{ email: string, password: string }} body
   */
  login: (body) => client.post('/auth/login', body).then((r) => r.data),

  /**
   * Exchange the refresh token cookie for a new access token.
   * Returns { access_token }.
   */
  refresh: () => client.post('/auth/refresh').then((r) => r.data),

  /**
   * Revoke the current refresh token and clear the cookie.
   */
  logout: () => client.post('/auth/logout').then((r) => r.data),
};