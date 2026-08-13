import {
	anomaliesInfiniteQueryOptions,
	geoQueryOptions,
	protocolsQueryOptions,
	summaryQueryOptions,
	timeseriesQueryOptions,
	topTalkersQueryOptions
} from '#/features/analytics/queries';
import { FAKE_GEO, FAKE_PROTOCOLS, FAKE_SUMMARY, FAKE_TIMESERIES, FAKE_TOP_TALKERS } from '#/../test/mocks/handlers';
import { createTestQueryClient } from '#/../test/test-utils';
import { describe, expect, it } from 'vitest';

const START = new Date( '2024-01-01T00:00:00Z' );
const END   = new Date( '2024-01-02T00:00:00Z' );

describe( 'summaryQueryOptions', ( ) =>
{
	it( 'uses the analytics summary query key', ( ) =>
	{
		const params = { start: START, end: END };
		const options = summaryQueryOptions( params );

		expect( options.queryKey ).toEqual( [ 'analytics', 'summary', params ] );
	} );

	it( 'sets staleTime to 30 seconds', ( ) =>
	{
		expect( summaryQueryOptions( { start: START, end: END } ).staleTime ).toBe( 30_000 );
	} );

	it( 'resolves summary data from the mock endpoint', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const data = await queryClient.ensureQueryData( summaryQueryOptions( { start: START, end: END } ) );

		expect( data ).toEqual( FAKE_SUMMARY );
	} );
} );

describe( 'timeseriesQueryOptions', ( ) =>
{
	it( 'uses the analytics timeseries query key', ( ) =>
	{
		const params = { start: START, end: END, bucket: 'hour' as const };
		const options = timeseriesQueryOptions( params );

		expect( options.queryKey ).toEqual( [ 'analytics', 'timeseries', params ] );
	} );

	it( 'sets staleTime to 30 seconds', ( ) =>
	{
		expect( timeseriesQueryOptions( { start: START, end: END } ).staleTime ).toBe( 30_000 );
	} );

	it( 'resolves timeseries data from the mock endpoint', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const data = await queryClient.ensureQueryData( timeseriesQueryOptions( { start: START, end: END, bucket: 'hour' } ) );

		expect( data ).toEqual( FAKE_TIMESERIES );
	} );
} );

describe( 'topTalkersQueryOptions', ( ) =>
{
	it( 'uses the analytics top-talkers query key', ( ) =>
	{
		const params = { start: START, end: END, direction: 'src' as const, metric: 'packets' as const, limit: 10 };
		const options = topTalkersQueryOptions( params );

		expect( options.queryKey ).toEqual( [ 'analytics', 'top-talkers', params ] );
	} );

	it( 'resolves top talkers data from the mock endpoint', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const data = await queryClient.ensureQueryData( topTalkersQueryOptions( { start: START, end: END, direction: 'src', metric: 'packets', limit: 10 } ) );

		expect( data ).toEqual( FAKE_TOP_TALKERS );
	} );
} );

describe( 'protocolsQueryOptions', ( ) =>
{
	it( 'uses the analytics protocols query key', ( ) =>
	{
		const params = { start: START, end: END };
		const options = protocolsQueryOptions( params );

		expect( options.queryKey ).toEqual( [ 'analytics', 'protocols', params ] );
	} );

	it( 'resolves protocol data from the mock endpoint', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const data = await queryClient.ensureQueryData( protocolsQueryOptions( { start: START, end: END } ) );

		expect( data ).toEqual( FAKE_PROTOCOLS );
	} );
} );

describe( 'geoQueryOptions', ( ) =>
{
	it( 'uses the analytics geo query key', ( ) =>
	{
		const params = { start: START, end: END, direction: 'src' as const, limit: 25 };
		const options = geoQueryOptions( params );

		expect( options.queryKey ).toEqual( [ 'analytics', 'geo', params ] );
	} );

	it( 'resolves geo data from the mock endpoint', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const data = await queryClient.ensureQueryData( geoQueryOptions( { start: START, end: END, direction: 'src', limit: 25 } ) );

		expect( data ).toEqual( FAKE_GEO );
	} );
} );

describe( 'anomaliesInfiniteQueryOptions', ( ) =>
{
	const params = { start: START, end: END, min_score: 0.5, limit: 25 };

	it( 'uses the analytics anomalies query key', ( ) =>
	{
		const options = anomaliesInfiniteQueryOptions( params );

		expect( options.queryKey ).toEqual( [ 'analytics', 'anomalies', params ] );
	} );

	it( 'uses undefined as initialPageParam', ( ) =>
	{
		expect( anomaliesInfiniteQueryOptions( params ).initialPageParam ).toBeUndefined( );
	} );

	it( 'getNextPageParam returns undefined when has_more is false', ( ) =>
	{
		const options = anomaliesInfiniteQueryOptions( params );

		const result = options.getNextPageParam(
			{ rows: [ ], next_cursor: null, has_more: false },
			[ ],
			undefined,
			[ ]
		);

		expect( result ).toBeUndefined( );
	} );

	it( 'getNextPageParam returns next_cursor when has_more is true', ( ) =>
	{
		const options = anomaliesInfiniteQueryOptions( params );

		const result = options.getNextPageParam(
			{ rows: [ ], next_cursor: 'cursor-abc', has_more: true },
			[ ],
			undefined,
			[ ]
		);

		expect( result ).toBe( 'cursor-abc' );
	} );

	it( 'fetches pages correctly', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const data = await queryClient.fetchInfiniteQuery( anomaliesInfiniteQueryOptions( params ) );

		expect( data.pages ).toBeDefined( );
		expect( data.pages.length ).toBeGreaterThan( 0 );
		expect( data.pages[ 0 ]?.rows.length ).toBeGreaterThan( 0 );
	} );
} );
