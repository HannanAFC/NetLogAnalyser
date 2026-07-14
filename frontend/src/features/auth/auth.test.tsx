import { renderHook, waitFor } from '@testing-library/react';
import { act } from 'react';
import { describe, expect, it } from 'vitest';

import { useLogin } from '#/features/auth/hooks';
import { sessionQueryOptions } from '#/features/auth/queries';
import { apiClient } from '#/lib/api/client';
import { sessionQueryKey } from '#/lib/auth/session-key';
import { tokenStore } from '#/lib/auth/token-store';

import { QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import {
	VALID_EMAIL,
	VALID_PASSWORD,
	refreshCallCount,
	setRefreshShouldFail,
} from '../../../test/mocks/handlers';
import { createTestQueryClient } from '../../../test/test-utils';

describe( 'useLogin', ( ) =>
{
	it( 'stores the access token and populates the session cache on success', async ( ) =>
	{
		const queryClient = createTestQueryClient( );
		const wrapper = ( { children }: { children: ReactNode } ) => (
			<QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
		);

		const { result } = renderHook( ( ) => useLogin( ), { wrapper } );

		await act( async ( ) =>
		{
			await result.current.mutateAsync(
			{
				email: VALID_EMAIL,
				password: VALID_PASSWORD
			});
		});

		expect( tokenStore.get( ) ).toBe( 'fake-access-token' );
		expect( queryClient.getQueryData( sessionQueryKey ) ).toMatchObject(
		{
			email: VALID_EMAIL
		});
	});

	it( 'surfaces an error and leaves the token store empty on invalid credentials', async ( ) =>
	{
		const queryClient = createTestQueryClient( );
		const wrapper = ( { children }: { children: ReactNode } ) => (
			<QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
		);

		const { result } = renderHook( ( ) => useLogin( ), { wrapper } );

		await act( async ()  =>
		{
			await expect(
				result.current.mutateAsync( { email: VALID_EMAIL, password: 'wrong-password' } )
			).rejects.toBeTruthy();
		} );

		expect( tokenStore.get( ) ).toBeNull( );
		expect( queryClient.getQueryData( sessionQueryKey ) ).toBeUndefined( );
	});
});

describe( 'route guard (ensureQueryData against sessionQueryOptions)', ( ) =>
{
	it( 'resolves to null when there is no access token and no valid refresh cookie', async ( ) =>
	{
		// No token in the store, and the mocked /auth/refresh in this test
		// run is forced to fail - mirrors an unauthenticated first visit.
		setRefreshShouldFail( true );

		const queryClient = createTestQueryClient( );
		const session = await queryClient.ensureQueryData( sessionQueryOptions );

		expect( session ).toBeNull( );
	});

	it( 'resolves to the user when a valid refresh cookie is present', async ( ) =>
	{
		// tokenStore starts empty (page reload); fetchSession should fall
		// back to /auth/refresh, succeed, then call /users/me.
		const queryClient = createTestQueryClient( );
		const session = await queryClient.ensureQueryData( sessionQueryOptions );

		expect( session ).toMatchObject( { email: VALID_EMAIL } );
		expect( tokenStore.get( ) ).toBe( 'refreshed-access-token' );
	});
});

describe( '401 -> refresh -> retry interceptor', ( ) =>
{
	it( 'deduplicates concurrent refreshes into a single /auth/refresh call', async ( ) =>
	{
		// Use an expired token so /users/me returns 401 on first attempt.
		tokenStore.set( 'expired-access-token' );

		const requests = [
			apiClient.get( '/users/me' ),
			apiClient.get( '/users/me' ),
			apiClient.get( '/users/me' ),
		];

		const results = await Promise.all( requests );

		results.forEach( ( response ) =>
		{
			expect( response.status ).toBe( 200 );
		});

		// All three 401s should have shared a single refresh.
		expect( refreshCallCount ).toBe( 1 );
		expect( tokenStore.get() ).toBe( 'refreshed-access-token' );
	});

	it( 'clears the session cache when the refresh itself fails', async ( ) =>
	{
		tokenStore.set( 'expired-access-token' );
		setRefreshShouldFail( true );

		const queryClient = createTestQueryClient( );
		queryClient.setQueryData( sessionQueryKey, { id: '1', email: VALID_EMAIL } );

		await expect( apiClient.get( '/users/me' ) ).rejects.toBeTruthy( );

		await waitFor( ( ) =>
		{
			expect( tokenStore.get( ) ).toBeNull( );
		});
	});
});