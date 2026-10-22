import { describe, expect, it } from 'vitest';

import { sessionQueryOptions } from '#/features/auth/queries';
import { setSessionHint } from '#/lib/auth/session-hint';
import { tokenStore } from '#/lib/auth/token-store';

import { VALID_EMAIL, setRefreshShouldFail } from '#/../test/mocks/handlers';
import { createTestQueryClient } from '#/../test/test-utils';

describe( 'route guard (ensureQueryData against sessionQueryOptions)', ( ) =>
{
	it( 'resolves to null when there is no access token and no valid refresh cookie', async( ) =>
	{
		setRefreshShouldFail( true );

		const queryClient = createTestQueryClient( );
		const session = await queryClient.query( sessionQueryOptions );

		expect( session ).toBeNull( );
	} );

	it( 'resolves to the user when a valid refresh cookie is present', async( ) =>
	{
		setSessionHint( true );
		const queryClient = createTestQueryClient( );
		const session = await queryClient.query( sessionQueryOptions );

		expect( session ).toMatchObject( { email: VALID_EMAIL } );
		expect( tokenStore.get( ) ).toBe( 'refreshed-access-token' );
	} );
} );