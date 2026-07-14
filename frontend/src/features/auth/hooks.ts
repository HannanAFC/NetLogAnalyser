import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { tokenStore } from '../../lib/auth/token-store';
import { loginRequest, logoutRequest, registerRequest } from './api';
import { sessionQueryKey, sessionQueryOptions } from './queries';
import type { LoginPayload, RegisterRequestBody } from './schemas';

/** Read the current session. Cheap after first load - served from cache. */
export function useSession( )
{
  return useQuery( sessionQueryOptions );
}

export function useLogin( )
{
    const queryClient = useQueryClient( );
    return useMutation(
    {
        mutationFn: ( payload: LoginPayload ) => loginRequest( payload ),
        onSuccess:  ( { access_token, user } ) =>
        {
            tokenStore.set( access_token );
            queryClient.setQueryData( sessionQueryKey, user );
        }
    });
}

export function useRegister( )
{
    const queryClient = useQueryClient( );
    return useMutation(
    {
        mutationFn: ( payload: RegisterRequestBody ) => registerRequest( payload ),
        onSuccess: ( { access_token, user } ) =>
        {
            tokenStore.set( access_token );
            queryClient.setQueryData( sessionQueryKey, user) ;
        }
    });
}

export function useLogout( )
{
    const queryClient = useQueryClient( );
    return useMutation(
        {
            mutationFn: logoutRequest,
            // Clear local state even if the network call fails - an expired
            // or already-revoked refresh token shouldn't trap the user logged in.
            onSettled: ( ) =>
            {
                tokenStore.set( null );
                queryClient.setQueryData( sessionQueryKey, null );
            }
    });
}
