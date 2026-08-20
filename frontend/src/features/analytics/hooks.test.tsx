import { useAnomalies, useGeo, useProtocols, useSummary, useTimeseries, useTopTalkers } from '#/features/analytics/hooks';
import { createTestQueryClient } from '#/../test/test-utils';
import { wrapperFor } from '#/lib/api/test-utils';
import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

const START = new Date( '2024-01-01T00:00:00Z' );
const END   = new Date( '2024-01-02T00:00:00Z' );

describe( 'useSummary', ( ) =>
{
	it( 'returns summary data on success', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useSummary( { start: START, end: END } ), { wrapper: wrapperFor( queryClient ) } );

		await waitFor( ( ) =>
		{
			expect( result.current.isSuccess ).toBe( true );
		} );

		expect( result.current.data?.total_packets ).toBe( 1000 );
		expect( result.current.data?.unique_src_ips ).toBe( 42 );
	} );
} );

describe( 'useTimeseries', ( ) =>
{
	it( 'returns timeseries data on success', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useTimeseries( { start: START, end: END, bucket: 'hour' } ), { wrapper: wrapperFor( queryClient ) } );

		await waitFor( ( ) =>
		{
			expect( result.current.isSuccess ).toBe( true );
		} );

		expect( result.current.data?.bucket ).toBe( 'hour' );
		expect( result.current.data?.points.length ).toBeGreaterThan( 0 );
	} );
} );

describe( 'useTopTalkers', ( ) =>
{
	it( 'returns top talkers on success', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook(
			( ) => useTopTalkers( { start: START, end: END, direction: 'src', metric: 'packets', limit: 10 } ),
			{ wrapper: wrapperFor( queryClient ) }
		);

		await waitFor( ( ) =>
		{
			expect( result.current.isSuccess ).toBe( true );
		} );

		expect( result.current.data?.rows.length ).toBeGreaterThan( 0 );
	} );
} );

describe( 'useProtocols', ( ) =>
{
	it( 'returns protocol breakdown on success', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useProtocols( { start: START, end: END } ), { wrapper: wrapperFor( queryClient ) } );

		await waitFor( ( ) =>
		{
			expect( result.current.isSuccess ).toBe( true );
		} );

		expect( result.current.data?.by_protocol.length ).toBeGreaterThan( 0 );
		expect( result.current.data?.top_dst_ports.length ).toBeGreaterThan( 0 );
	} );
} );

describe( 'useGeo', ( ) =>
{
	it( 'returns geo distribution on success', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook(
			( ) => useGeo( { start: START, end: END, direction: 'src', limit: 50 } ),
			{ wrapper: wrapperFor( queryClient ) }
		);

		await waitFor( ( ) =>
		{
			expect( result.current.isSuccess ).toBe( true );
		} );

		expect( result.current.data?.rows.length ).toBeGreaterThan( 0 );
	} );
} );

describe( 'useAnomalies', ( ) =>
{
	it( 'returns anomaly pages on initial load', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook(
			( ) => useAnomalies( { start: START, end: END, min_score: 0.5, limit: 25 } ),
			{ wrapper: wrapperFor( queryClient ) }
		);

		await waitFor( ( ) =>
		{
			expect( result.current.isLoading ).toBe( false );
		} );

		expect( result.current.isError ).toBe( false );
		expect( result.current.pages ).toHaveLength( 1 );
		expect( result.current.pages[ 0 ]?.rows.length ).toBeGreaterThan( 0 );
	} );

	it( 'reports hasNextServerPage when more pages exist', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook(
			( ) => useAnomalies( { start: START, end: END, min_score: 0.5, limit: 10 } ),
			{ wrapper: wrapperFor( queryClient ) }
		);

		await waitFor( ( ) =>
		{
			expect( result.current.isLoading ).toBe( false );
		} );

		expect( result.current.hasNextServerPage ).toBe( true );
	} );

	it( 'supports fetching the next page', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook(
			( ) => useAnomalies( { start: START, end: END, min_score: 0.5, limit: 10 } ),
			{ wrapper: wrapperFor( queryClient ) }
		);

		await waitFor( ( ) =>
		{
			expect( result.current.isLoading ).toBe( false );
		} );

		const firstPageCount = result.current.pages.length;

		await act( async( ) =>
		{
			await result.current.fetchNextPage( );
		} );

		await waitFor( ( ) =>
		{
			expect( result.current.pages.length ).toBeGreaterThan( firstPageCount );
		} );
	} );
} );
