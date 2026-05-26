import client from './client.js';

export const apiKeysApi = {
  /** List all keys for the current user (prefix + label only, never plaintext). */
  list: () => client.get('/api-keys').then((r) => r.data),

  /**
   * Generate a new key.
   * Returns { id, label, key_prefix, plaintext_key }.
   * The plaintext_key is returned ONCE and never stored server-side.
   * @param {{ label: string }} body
   */
  create: (body) => client.post('/api-keys', body).then((r) => r.data),

  /**
   * Rename a key.
   * @param {string} keyId
   * @param {{ label: string }} body
   */
  rename: (keyId, body) =>
    client.patch(`/api-keys/${keyId}`, body).then((r) => r.data),

  /**
   * Revoke a key. Any further ingest attempts using it will receive 401.
   * @param {string} keyId
   */
  revoke: (keyId) => client.delete(`/api-keys/${keyId}`).then((r) => r.data),
};