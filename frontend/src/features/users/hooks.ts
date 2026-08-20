import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { ChangeUserDetailsPayload, ChangeUserPasswordPayload, DeleteUserPayload } from './schemas';
import { changeUserDetailsRequest, changeUserPasswordRequest, deleteUserRequest } from './api';
import { sessionQueryKey } from '#/lib/auth/session-key';
import { tokenStore } from '#/lib/auth/token-store';

export function useChangeUserDetails( )
{
    const queryClient = useQueryClient( );
    return useMutation(
    {
        mutationFn: ( payload: ChangeUserDetailsPayload ) => changeUserDetailsRequest( payload ),
        onSuccess: ( user ) =>
        {
            queryClient.setQueryData( sessionQueryKey, user );
        }
    } );
}

export function useChangeUserPassword( )
{
    const queryClient = useQueryClient( );
    return useMutation(
    {
        mutationFn: ( payload: ChangeUserPasswordPayload ) => changeUserPasswordRequest( payload ),
        onSuccess: ( ) =>
        {
            setTimeout( ( ) =>
            {
                tokenStore.set( null );
                queryClient.setQueryData( sessionQueryKey, null );
            }, 5000 );
        }
    } );
}

export function useDeleteUser( )
{
    const queryClient = useQueryClient( );
    return useMutation(
    {
        mutationFn: ( payload: DeleteUserPayload ) => deleteUserRequest( payload ),
        onSuccess: ( ) =>
        {
            setTimeout( ( ) =>
            {
                tokenStore.set( null );
                queryClient.setQueryData( sessionQueryKey, null );
            }, 5000 );
        }
    } );
}