import client from './client.js';

export const analyticsApi = {
  /**
   * Traffic volume over a rolling window.
   * @param {{ interval?: '1m'|'5m'|'1h', from?: string, to?: string }} params
   */
  getTraffic: (params = {}) =>
    client.get('/analytics/traffic', { params }).then((r) => r.data),

  /**
   * Protocol breakdown as counts and percentages.
   * @param {{ from?: string, to?: string }} params
   */
  getProtocols: (params = {}) =>
    client.get('/analytics/protocols', { params }).then((r) => r.data),

  /**
   * Source IP counts grouped by country_code for the geo map.
   * @param {{ from?: string, to?: string }} params
   */
  getGeo: (params = {}) =>
    client.get('/analytics/geo', { params }).then((r) => r.data),

  /**
   * Most active source/destination IPs by packet volume.
   * @param {{ limit?: number, from?: string, to?: string }} params
   */
  getTopTalkers: (params = {}) =>
    client.get('/analytics/top-talkers', { params }).then((r) => r.data),

  /**
   * Recent log entries above the anomaly_score threshold.
   * @param {{ threshold?: number, limit?: number }} params
   */
  getAnomalies: (params = {}) =>
    client.get('/analytics/anomalies', { params }).then((r) => r.data),
};