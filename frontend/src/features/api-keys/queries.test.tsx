import { describe, expect, it } from 'vitest';

import { apiKeysQueryOptions } from '#/features/api-keys/queries';

import { FAKE_API_KEY_ID_1, FAKE_API_KEY_ID_2 } from '#/../test/mocks/handlers';
import { createTestQueryClient } from '#/../test/test-utils';

describe( 'apiKeysQueryOptions', ( ) =>
{
	it( 'resolves to the list of API keys', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const keys = await queryClient.ensureQueryData( apiKeysQueryOptions );

		expect( keys ).toHaveLength( 2 );
		expect( keys[ 0 ].id ).toBe( FAKE_API_KEY_ID_1 );
		expect( keys[ 0 ].label ).toBe( 'My API Key' );
		expect( keys[ 1 ].id ).toBe( FAKE_API_KEY_ID_2 );
		expect( keys[ 1 ].revoked_at ).toBeTruthy( );
	} );

	it( 'includes both active and revoked keys', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const keys = await queryClient.ensureQueryData( apiKeysQueryOptions );

		const active  = keys.filter( ( k ) => !k.revoked_at );
		const revoked = keys.filter( ( k ) => k.revoked_at );

		expect( active ).toHaveLength( 1 );
		expect( revoked ).toHaveLength( 1 );
	} );
} );
