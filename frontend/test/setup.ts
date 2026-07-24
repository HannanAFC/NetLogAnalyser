import '@testing-library/jest-dom/vitest';
import { afterAll, afterEach, beforeAll } from 'vitest';

import { tokenStore } from '#/lib/auth/token-store';

import { resetRefreshCallCount, setRefreshShouldFail } from './mocks/handlers';
import { server } from './mocks/server';

beforeAll( ( ) =>
{
	server.listen( { onUnhandledRequest: 'error' } );
} );

afterEach( () =>
{
	server.resetHandlers( );
	tokenStore.set( null );
	resetRefreshCallCount( );
	setRefreshShouldFail( false );
} );

afterAll( ( ) =>
{
	server.close( );
} );
