import client from './client.js';

export const logsApi = {
  /**
   * Fetch paginated log history with optional filters.
   * Maps directly to GET /logs with query params.
   *
   * @param {{
   *   page?: number,
   *   limit?: number,
   *   from?: string,       // ISO timestamp
   *   to?: string,         // ISO timestamp
   *   protocol?: string,
   *   src_ip?: string,
   *   country_code?: string,
   *   anomaly_only?: boolean,
   * }} params
   */
  getLogs: (params = {}) =>
    client.get('/logs', { params }).then((r) => r.data),

  /**
   * Fetch a single log entry including raw_payload.
   * @param {string|number} id
   */
  getLog: (id) => client.get(`/logs/${id}`).then((r) => r.data),

  /**
   * Bulk delete logs within a time range.
   * @param {{ from: string, to: string }} params
   */
  deleteLogs: (params) =>
    client.delete('/logs', { params }).then((r) => r.data),
};