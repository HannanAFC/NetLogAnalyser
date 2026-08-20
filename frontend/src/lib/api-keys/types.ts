export interface ApiKey
{
    id: string;
    label: string;
    key_prefix: string;
    created_at: string;
    last_used_at: string | null;
    revoked_at: string | null;
}

export interface CreatedApiKey
{
    id: string;
    label: string;
    key_prefix: string;
    api_key: string;
    created_at: string;
}

export interface CreateApiKeyResponse extends CreatedApiKey {};
export interface GetApiKeysResponse extends Array< ApiKey > {};