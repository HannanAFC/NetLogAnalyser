import type { ForgotPasswordPayload, LoginPayload, RegisterRequestBody, ResendVerificationPayload, ResetPasswordPayload } from '#/features/auth/schemas';
import { apiClient } from '#/lib/api/client';
import type { AuthTokenResponse, RefreshResponse, RegisterResponse, User } from '#/lib/auth/types';

export async function loginRequest( payload: LoginPayload ): Promise< AuthTokenResponse >
{
	const { data } = await apiClient.post< AuthTokenResponse >( '/auth/login', payload );
	return data;
}

export async function registerRequest( payload: RegisterRequestBody ): Promise< RegisterResponse >
{
	const { data } = await apiClient.post< RegisterResponse >( '/auth/register', payload );
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

export async function verifyEmailRequest( token: string ): Promise< void >
{
	await apiClient.get( '/auth/verify-email', { params: { token } } );
}

export async function resendVerificationRequest( payload: ResendVerificationPayload ): Promise< void >
{
	await apiClient.post( '/auth/resend-verification', payload );
}

export async function forgotPasswordRequest( payload: ForgotPasswordPayload ): Promise< void >
{
	await apiClient.post( '/auth/forgot-password', payload );
}

export async function resetPasswordRequest( payload: ResetPasswordPayload ): Promise< void >
{
	await apiClient.post( '/auth/reset-password', payload );
}