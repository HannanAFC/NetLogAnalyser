import { apiClient } from '#/lib/api/client';
import type { ChangeUserPasswordResponse, User } from '#/lib/users/types';
import type { ChangeUserPasswordPayload, ChangeUserDetailsPayload, DeleteUserPayload } from './schemas';

export async function getMe( ): Promise< User >
{
    const { data } = await apiClient.get< User >( '/users/me' );
    return data;
}

export async function changeUserDetailsRequest( payload: ChangeUserDetailsPayload ): Promise< User >
{
    const { data } = await apiClient.patch< User >( '/users/me', payload );
    return data;
}

export async function changeUserPasswordRequest( payload: ChangeUserPasswordPayload ): Promise< ChangeUserPasswordResponse >
{
    const { data } = await apiClient.patch< ChangeUserPasswordResponse >( '/users/me/change-password', payload );
    return data;
}

export async function deleteUserRequest( payload: DeleteUserPayload ): Promise< null >
{
    const { data } = await apiClient.post< null >( '/users/me', payload );
    return data;
}