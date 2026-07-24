import { tokenStore } from '#/lib/auth/token-store';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { forgotPasswordRequest, loginRequest, logoutRequest, registerRequest, resendVerificationRequest, resetPasswordRequest, verifyEmailRequest } from './api';
import { sessionQueryKey, sessionQueryOptions } from './queries';
import type { ForgotPasswordPayload, LoginPayload, RegisterRequestBody, ResendVerificationPayload, ResetPasswordPayload } from './schemas';

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
		onSuccess: ( { access_token, user } ) =>
		{
			tokenStore.set( access_token );
			queryClient.setQueryData( sessionQueryKey, user );
		}
	} );
}

export function useRegister( )
{
	return useMutation(
	{
		mutationFn: ( payload: RegisterRequestBody ) => registerRequest( payload )
	} );
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
	} );
}

export function useForgotPassword( )
{
	return useMutation(
	{
		mutationFn: ( payload: ForgotPasswordPayload ) => forgotPasswordRequest( payload )
	} );
}

export function useResetPassword( )
{
	return useMutation(
	{
		mutationFn: ( payload: ResetPasswordPayload ) => resetPasswordRequest( payload )
	} );
}

export function useVerifyEmail( )
{
	return useMutation(
	{
		mutationFn: ( token: string ) => verifyEmailRequest( token )
	} );
}

export function useResendVerification( )
{
	return useMutation(
	{
		mutationFn: ( payload: ResendVerificationPayload ) => resendVerificationRequest( payload )
	} );
}