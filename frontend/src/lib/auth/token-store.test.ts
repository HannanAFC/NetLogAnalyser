// lib/auth/token-store.test.ts
import { beforeEach, describe, expect, it } from 'vitest';
import { tokenStore } from './token-store';

describe( 'tokenStore', ( ) =>
{
	beforeEach( ( ) => tokenStore.set( null ) );

	it( 'returns null when nothing has been set', ( ) =>
	{
		expect( tokenStore.get( ) ).toBeNull( );
	} );

	it( 'stores and returns a token', ( ) =>
	{
		tokenStore.set( 'abc123' );
		expect( tokenStore.get( ) ).toBe( 'abc123' );
	} );

	it( 'clears back to null', ( ) =>
	{
		tokenStore.set( 'abc123' );
		tokenStore.set( null );
		expect( tokenStore.get( ) ).toBeNull( );
	} );
} );