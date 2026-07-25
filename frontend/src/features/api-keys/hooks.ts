import { apiKeysQueryOptions } from '#/features/api-keys/queries';
import type { CreateApiKeyPayload } from '#/features/api-keys/schemas';
import { apiKeysQueryKey } from '#/lib/api-keys/query-key';
import type { ApiKey } from '#/lib/api-keys/types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createApiKeyRequest, getApiKeysRequest, revokeApiKeyRequest } from './api';

export function useApiKeys( )
{
    return useQuery( apiKeysQueryOptions );
}

export function useCreateApiKey( )
{
    const queryClient = useQueryClient( );
    return useMutation(
    {
        mutationFn: ( payload: CreateApiKeyPayload ) => createApiKeyRequest( payload ),
        onSuccess: ( ) =>
        {
            // the returned key contains the raw key, so don't update the cached list with it
            queryClient.invalidateQueries( { queryKey: apiKeysQueryKey } );
        }
    } );
}

export function useGetApiKeys( )
{
    const queryClient = useQueryClient( );
    return useMutation(
    {
        mutationFn: ( ) => getApiKeysRequest( ),
        onSuccess: ( api_keys ) =>
        {
            queryClient.setQueryData( apiKeysQueryKey, api_keys );
        }
    } );
}

export function useRevokeApiKey( )
{
    const queryClient = useQueryClient( );
    return useMutation(
    {
        mutationFn: ( id: string ) => revokeApiKeyRequest( id ),
        onSuccess: ( data, keyId ) =>
        {
            queryClient.setQueryData(
                apiKeysQueryKey,
                ( oldData: ApiKey[ ] | undefined ) =>
                {
                    if ( !oldData ) return undefined;

                    for ( let i = 0; i < oldData.length; i ++ )
                    {
                        if ( oldData[ i ].id === keyId )
                        {
                            const newData      = oldData[ i ];
                            newData.revoked_at = new Date( ).toISOString( );
                            oldData[ i ]       = newData;
                            return oldData;
                        }
                    }
                }
            );
        }
    } );
}