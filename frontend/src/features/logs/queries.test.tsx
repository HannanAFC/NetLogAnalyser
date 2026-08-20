import { initialLogsQueryOptions, logsInfiniteQueryOptions } from '#/features/logs/queries';
import { createTestQueryClient } from '#/../test/test-utils';
import { describe, expect, it } from 'vitest';

describe( 'initialLogsQueryOptions', ( ) =>
{
	it( 'returns a queryOptions object with the correct queryKey', ( ) =>
	{
		const options = initialLogsQueryOptions( 20 );

		expect( options.queryKey ).toEqual( [ 'logs', 20, 'initial' ] );
	} );

	it( 'uses the provided limit in the query key', ( ) =>
	{
		const options = initialLogsQueryOptions( 50 );

		expect( options.queryKey ).toEqual( [ 'logs', 50, 'initial' ] );
	} );

	it( 'sets staleTime to Infinity', ( ) =>
	{
		const options = initialLogsQueryOptions( );

		expect( options.staleTime ).toBe( Infinity );
	} );

	it( 'sets retry to false', ( ) =>
	{
		const options = initialLogsQueryOptions( );

		expect( options.retry ).toBe( false );
	} );

	it( 'resolves entries from the mock logs endpoint', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const data = await queryClient.ensureQueryData( initialLogsQueryOptions( 20 ) );

		expect( data.entries ).toBeDefined( );
		expect( data.entries.length ).toBeGreaterThan( 0 );
		expect( data.entries[ 0 ] ).toHaveProperty( 'src_ip' );
	} );
} );

describe( 'logsInfiniteQueryOptions', ( ) =>
{
	it( 'returns infiniteQueryOptions with the correct queryKey', ( ) =>
	{
		const options = logsInfiniteQueryOptions( 25 );

		expect( options.queryKey ).toEqual( [ 'logs', 25 ] );
	} );

	it( 'uses undefined as initialPageParam', ( ) =>
	{
		const options = logsInfiniteQueryOptions( );

		expect( options.initialPageParam ).toBeUndefined( );
	} );

	it( 'getNextPageParam returns undefined when has_more is false', ( ) =>
	{
		const options = logsInfiniteQueryOptions( );

		const result = options.getNextPageParam(
			{ entries: [ ], next_cursor: null, has_more: false },
			[ ],
			undefined,
			[ ]
		);

		expect( result ).toBeUndefined( );
	} );

	it( 'getNextPageParam returns next_cursor when has_more is true', ( ) =>
	{
		const options = logsInfiniteQueryOptions( );

		const result = options.getNextPageParam(
			{ entries: [ ], next_cursor: 'cursor-abc', has_more: true },
			[ ],
			undefined,
			[ ]
		);

		expect( result ).toBe( 'cursor-abc' );
	} );

	it( 'fetches pages correctly', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const data = await queryClient.fetchInfiniteQuery( logsInfiniteQueryOptions( 25 ) );

		expect( data.pages ).toBeDefined( );
		expect( data.pages.length ).toBeGreaterThan( 0 );
		expect( data.pages[ 0 ].entries.length ).toBeGreaterThan( 0 );
	} );
} );
