import { useInitialLogs, useLogHistory } from '#/features/logs/hooks';
import { wrapperFor } from '#/lib/api/test-utils';
import { createTestQueryClient } from '#/../test/test-utils';
import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

describe( 'useInitialLogs', ( ) =>
{
	it( 'returns entries on success', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useInitialLogs( ), { wrapper: wrapperFor( queryClient ) } );

		await waitFor( ( ) =>
		{
			expect( result.current.isLoading ).toBe( false );
		} );

		expect( result.current.isError ).toBe( false );
		expect( result.current.entries.length ).toBeGreaterThan( 0 );
		expect( result.current.entries[ 0 ] ).toHaveProperty( 'src_ip' );
	} );

	it( 'returns the requested number of entries', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useInitialLogs( 5 ), { wrapper: wrapperFor( queryClient ) } );

		await waitFor( ( ) =>
		{
			expect( result.current.isLoading ).toBe( false );
		} );

		expect( result.current.entries ).toHaveLength( 5 );
	} );

	it( 'defaults to 20 entries when no limit is passed', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useInitialLogs( ), { wrapper: wrapperFor( queryClient ) } );

		await waitFor( ( ) =>
		{
			expect( result.current.isLoading ).toBe( false );
		} );

		expect( result.current.entries ).toHaveLength( 20 );
	} );
} );

describe( 'useLogHistory', ( ) =>
{
	it( 'returns entries on initial page load', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useLogHistory( ), { wrapper: wrapperFor( queryClient ) } );

		await waitFor( ( ) =>
		{
			expect( result.current.isLoading ).toBe( false );
		} );

		expect( result.current.isError ).toBe( false );
		expect( result.current.entries.length ).toBeGreaterThan( 0 );
	} );

	it( 'supports fetching the next page', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useLogHistory( 2 ), { wrapper: wrapperFor( queryClient ) } );

		await waitFor( ( ) =>
		{
			expect( result.current.isLoading ).toBe( false );
		} );

		const firstPageCount = result.current.entries.length;

		await act( async( ) =>
		{
			await result.current.fetchNextPage( );
		} );

		await waitFor( ( ) =>
		{
			expect( result.current.entries.length ).toBeGreaterThan( firstPageCount );
		} );
	} );

	it( 'reports hasNextPage correctly when more pages exist', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useLogHistory( 2 ), { wrapper: wrapperFor( queryClient ) } );

		await waitFor( ( ) =>
		{
			expect( result.current.isLoading ).toBe( false );
		} );

		expect( result.current.hasNextPage ).toBe( true );
	} );

	it( 'defaults to 25 entries per page', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useLogHistory( ), { wrapper: wrapperFor( queryClient ) } );

		await waitFor( ( ) =>
		{
			expect( result.current.isLoading ).toBe( false );
		} );

		expect( result.current.entries ).toHaveLength( 25 );
	} );
} );
