import { apiClient } from '../../lib/api/client';
import type { AuthTokenResponse, RefreshResponse, User } from '../../lib/auth/types';
import type { LoginPayload, RegisterRequestBody } from './schemas';

export async function loginRequest( payload: LoginPayload ): Promise< AuthTokenResponse >
{
	const { data } = await apiClient.post< AuthTokenResponse >( '/auth/login', payload );
	return data;
}

export async function registerRequest( payload: RegisterRequestBody ): Promise< AuthTokenResponse >
{
	const { data } = await apiClient.post< AuthTokenResponse >( '/auth/register', payload );
	return data;
}

export async function refreshRequest( ): Promise< RefreshResponse >
{
	const { data } = await apiClient.post< RefreshResponse >( '/auth/refresh' );
	return data;
}

export async function logoutRequest( ): Promise< void >
{
	await apiClient.post( '/auth/logout' );
}

export async function getMe( ): Promise< User >
{
	const { data } = await apiClient.get< User >( '/users/me' );
	return data;
}
