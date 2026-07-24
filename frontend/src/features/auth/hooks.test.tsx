import { lastForgotPasswordEmail, lastResendVerificationEmail, refreshCallCount, setRefreshShouldFail, UNVERIFIED_EMAIL, VALID_EMAIL, VALID_PASSWORD, VALID_RESET_TOKEN, VALID_VERIFICATION_TOKEN } from '#/../test/mocks/handlers';
import { createTestQueryClient } from '#/../test/test-utils';
import { wrapperFor } from '#/lib/api/test-utils';
import { tokenStore } from '#/lib/auth/token-store';
import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { useForgotPassword, useLogin, useResendVerification, useResetPassword, useVerifyEmail } from './hooks';
import { sessionQueryKey, sessionQueryOptions } from './queries';

describe( 'useLogin', ( ) =>
{
	it( 'stores the access token and populates the session cache on success', async( ) =>
	{
		const queryClient = createTestQueryClient( );

		const { result } = renderHook( ( ) => useLogin( ), { wrapper: wrapperFor( queryClient ) } );

		await act( async( ) =>
		{
			await result.current.mutateAsync(
				{
					email: VALID_EMAIL,
					password: VALID_PASSWORD
				} );
		} );

		expect( tokenStore.get( ) ).toBe( 'fake-access-token' );
		expect( queryClient.getQueryData( sessionQueryKey ) ).toMatchObject(
			{
				email: VALID_EMAIL
			} );
	} );

	it( 'surfaces an error and leaves the token store empty on invalid credentials', async( ) =>
	{
		const queryClient = createTestQueryClient( );

		const { result } = renderHook( ( ) => useLogin( ), { wrapper: wrapperFor( queryClient ) } );

		await act( async() =>
		{
			await expect(
				result.current.mutateAsync( { email: VALID_EMAIL, password: 'wrong-password' } )
			).rejects.toBeTruthy();
		} );

		expect( tokenStore.get( ) ).toBeNull( );
		expect( queryClient.getQueryData( sessionQueryKey ) ).toBeUndefined( );
	} );
} );

describe( 'route guard (ensureQueryData against sessionQueryOptions)', ( ) =>
{
	it( 'resolves to null when there is no access token and no valid refresh cookie', async( ) =>
	{
		// No token in the store, and the mocked /auth/refresh in this test
		// run is forced to fail - mirrors an unauthenticated first visit.
		setRefreshShouldFail( true );

		const queryClient = createTestQueryClient( );
		const session = await queryClient.ensureQueryData( sessionQueryOptions );

		expect( session ).toBeNull( );
	} );

	it( 'resolves to the user when a valid refresh cookie is present', async( ) =>
	{
		// tokenStore starts empty (page reload); fetchSession should fall
		// back to /auth/refresh, succeed, then call /users/me.
		const queryClient = createTestQueryClient( );
		const session = await queryClient.ensureQueryData( sessionQueryOptions );

		expect( session ).toMatchObject( { email: VALID_EMAIL } );
		expect( tokenStore.get( ) ).toBe( 'refreshed-access-token' );
	} );
} );

describe( 'useVerifyEmail', ( ) =>
{
	it( 'resolves for a valid token', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useVerifyEmail( ), { wrapper: wrapperFor( queryClient ) } );

		await act( async( ) =>
		{
			await result.current.mutateAsync( VALID_VERIFICATION_TOKEN );
		} );

		await waitFor( ( ) =>
		{
			expect( result.current.isSuccess ).toBe( true );
		} );
	} );

	it( 'rejects for an invalid or expired token', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useVerifyEmail( ), { wrapper: wrapperFor( queryClient ) } );

		await act( async( ) =>
		{
			await expect( result.current.mutateAsync( 'stale-token' ) ).rejects.toBeTruthy( );
		} );
	} );
} );

describe( 'useResendVerification', ( ) =>
{
	it( 'sends the email address and resolves regardless of what the backend actually did with it', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useResendVerification( ), { wrapper: wrapperFor( queryClient ) } );

		await act( async( ) =>
		{
			await result.current.mutateAsync( { email: 'someone@example.com' } );
		} );

		await waitFor( ( ) =>
		{
			expect( result.current.isSuccess ).toBe( true );
		} );
		expect( lastResendVerificationEmail ).toBe( 'someone@example.com' );
	} );
} );

describe( 'useForgotPassword', ( ) =>
{
	it( 'sends the email address and resolves', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useForgotPassword( ), { wrapper: wrapperFor( queryClient ) } );

		await act( async( ) =>
		{
			await result.current.mutateAsync( { email: 'someone@example.com' } );
		} );

		await waitFor( ( ) =>
		{
			expect( result.current.isSuccess ).toBe( true );
		} );
		expect( lastForgotPasswordEmail ).toBe( 'someone@example.com' );
	} );
} );

describe( 'useResetPassword', ( ) =>
{
	it( 'resolves for a valid token', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useResetPassword( ), { wrapper: wrapperFor( queryClient ) } );

		await act( async( ) =>
		{
			await result.current.mutateAsync( { token: VALID_RESET_TOKEN, password: 'new-long-password&', confirm_password: 'new-long-password&' } );
		} );

		await waitFor( ( ) =>
		{
			expect( result.current.isSuccess ).toBe( true );
		} );
	} );

	it( 'rejects for an invalid or expired token', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useResetPassword( ), { wrapper: wrapperFor( queryClient ) } );

		await act( async( ) =>
		{
			await expect(
				result.current.mutateAsync( { token: 'stale-token', password: 'new-long-password&', confirm_password: 'new-long-password&' } )
			).rejects.toBeTruthy( );
		} );
	} );
} );

describe( 'login with an unverified email', ( ) =>
{
	it( 'surfaces the 403 without going through the 401 refresh interceptor', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useLogin( ), { wrapper: wrapperFor( queryClient ) } );

		const refreshCallsBefore = refreshCallCount;

		await act( async( ) =>
		{
			await expect(
				result.current.mutateAsync( { email: UNVERIFIED_EMAIL, password: VALID_PASSWORD } )
			).rejects.toBeTruthy( );
		} );

		expect( refreshCallCount ).toBe( refreshCallsBefore );
		expect( tokenStore.get( ) ).toBeNull( );
	} );
} );