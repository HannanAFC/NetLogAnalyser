import type { CreateApiKeyResponse, GetApiKeysResponse } from '#/lib/api-keys/types';
import { apiClient } from '#/lib/api/client';
import type { CreateApiKeyPayload } from './schemas';

export async function getApiKeysRequest( ): Promise< GetApiKeysResponse >
{
    const { data } = await apiClient.get< GetApiKeysResponse >( '/api-keys' );
    return data;
}

export async function createApiKeyRequest( payload: CreateApiKeyPayload ): Promise< CreateApiKeyResponse >
{
    const { data } = await apiClient.post< CreateApiKeyResponse >( '/api-keys', payload );
    return data;
}

export async function revokeApiKeyRequest( id: string ): Promise< void >
{
	await apiClient.delete( `/api-keys/${ id }` );
}