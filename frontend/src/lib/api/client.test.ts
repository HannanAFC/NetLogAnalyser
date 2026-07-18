import { refreshCallCount, setRefreshShouldFail, VALID_EMAIL } from '#/../test/mocks/handlers';
import { createTestQueryClient } from '#/../test/test-utils';
import { apiClient } from '#/lib/api/client';
import { sessionQueryKey } from '#/lib/auth/session-key';
import { tokenStore } from '#/lib/auth/token-store';
import { waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

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