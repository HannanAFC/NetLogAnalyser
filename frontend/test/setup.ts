import '@testing-library/jest-dom/vitest';
import { afterAll, afterEach, beforeAll } from 'vitest';

import { tokenStore } from '#/lib/auth/token-store';

import { resetAnalyticsCallCounts, resetApiKeysCallCounts, resetGetLogsCallCount, resetRefreshCallCount, setRefreshShouldFail } from './mocks/handlers';
import { server } from './mocks/server';


window.__ENV__ =
{
	API_BASE_URL: 'http://localhost:8000',
	WS_BASE_URL:  'ws://localhost:8000/ws'
};

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
	resetApiKeysCallCounts( );
	resetGetLogsCallCount( );
	resetAnalyticsCallCounts( );
} );

afterAll( ( ) =>
{
	server.close( );
} );
