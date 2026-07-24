import {
    createApiKeyCallCount,
    FAKE_API_KEY_ID_1,
    FAKE_API_KEY_ID_2,
    getApiKeysCallCount,
    lastCreateApiKeyLabel,
    revokeApiKeyCallCount
} from '#/../test/mocks/handlers';
import { createTestQueryClient } from '#/../test/test-utils';
import { apiKeysQueryKey } from '#/lib/api-keys/query-key';
import type { ApiKey } from '#/lib/api-keys/types';
import { wrapperFor } from '#/lib/api/test-utils';
import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { useApiKeys, useCreateApiKey, useGetApiKeys, useRevokeApiKey } from './hooks';

describe( 'useApiKeys', ( ) =>
{
	it( 'fetches and returns the list of API keys', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useApiKeys( ), { wrapper: wrapperFor( queryClient ) } );

		await waitFor( ( ) =>
		{
			expect( result.current.isSuccess ).toBe( true );
		} );

		expect( result.current.data ).toHaveLength( 2 );
		expect( queryClient.getQueryData( apiKeysQueryKey ) ).toHaveLength( 2 );
	} );

	it( 'seeds the query cache so subsequent ensureQueryData calls are instant', async( ) =>
	{
		const queryClient = createTestQueryClient( );
		const { result } = renderHook( ( ) => useApiKeys( ), { wrapper: wrapperFor( queryClient ) } );

		await waitFor( ( ) =>
		{
			expect( result.current.isSuccess ).toBe( true );
		} );

		// After the hook populates the cache, ensureQueryData should resolve
		// synchronously without another network round-trip.
		const cached = queryClient.getQueryData( apiKeysQueryKey );
		expect( cached ).toHaveLength( 2 );
	} );
} );

describe( 'useCreateApiKey', ( ) =>
{
	it( 'creates a key, invalidates the cache, and tracks the label', async( ) =>
	{
		const queryClient = createTestQueryClient( );

		// Seed the cache first so we can verify invalidation
		queryClient.setQueryData( apiKeysQueryKey, [
			{ id: FAKE_API_KEY_ID_1, label: 'Existing', key_prefix: 'nl_xx', created_at: '', last_used_at: null, revoked_at: null }
		] );

		const { result } = renderHook( ( ) => useCreateApiKey( ), { wrapper: wrapperFor( queryClient ) } );

		await act( async( ) =>
		{
			await result.current.mutateAsync( { label: 'test-label@example.com' } );
		} );

		await waitFor( ( ) =>
		{
			expect( result.current.isSuccess ).toBe( true );
		} );

		expect( createApiKeyCallCount ).toBe( 1 );
		expect( lastCreateApiKeyLabel ).toBe( 'test-label@example.com' );
	} );
} );

describe( 'useGetApiKeys', ( ) =>
{
	it( 'fetches keys and populates the query cache', async( ) =>
	{
		const queryClient = createTestQueryClient( );

		const { result } = renderHook( ( ) => useGetApiKeys( ), { wrapper: wrapperFor( queryClient ) } );

		await act( async( ) =>
		{
			await result.current.mutateAsync( );
		} );

		await waitFor( ( ) =>
		{
			expect( result.current.isSuccess ).toBe( true );
		} );

		const cache = queryClient.getQueryData( apiKeysQueryKey ) as ApiKey[ ];
		expect( cache ).toHaveLength( 2 );
		expect( getApiKeysCallCount ).toBe( 1 );
	} );
} );

describe( 'useRevokeApiKey', ( ) =>
{
	it( 'revokes an active key and marks it revoked in the cache', async( ) =>
	{
		const queryClient = createTestQueryClient( );

		// Seed the cache with an active key
		const activeKey: ApiKey = {
			id: FAKE_API_KEY_ID_1,
			label: 'Active Key',
			key_prefix: 'nl_abc123',
			created_at: '2024-01-01T00:00:00Z',
			last_used_at: null,
			revoked_at: null
		};

		queryClient.setQueryData( apiKeysQueryKey, [ activeKey ] );

		const { result } = renderHook( ( ) => useRevokeApiKey( ), { wrapper: wrapperFor( queryClient ) } );

		await act( async( ) =>
		{
			await result.current.mutateAsync( FAKE_API_KEY_ID_1 );
		} );

		await waitFor( ( ) =>
		{
			expect( result.current.isSuccess ).toBe( true );
		} );

		expect( revokeApiKeyCallCount ).toBe( 1 );

		const cache = queryClient.getQueryData( apiKeysQueryKey ) as ApiKey[ ];
		expect( cache ).toHaveLength( 1 );
		expect( cache[ 0 ].id ).toBe( FAKE_API_KEY_ID_1 );
		expect( cache[ 0 ].revoked_at ).toBeTruthy( );
	} );

	it( 'rejects for an already revoked key', async( ) =>
	{
		const queryClient = createTestQueryClient( );

		queryClient.setQueryData( apiKeysQueryKey, [
			{
				id: FAKE_API_KEY_ID_2,
				label: 'Revoked Key',
				key_prefix: 'nl_def456',
				created_at: '2024-01-02T00:00:00Z',
				last_used_at: '2024-01-15T00:00:00Z',
				revoked_at: '2024-02-01T00:00:00Z'
			}
		] );

		const { result } = renderHook( ( ) => useRevokeApiKey( ), { wrapper: wrapperFor( queryClient ) } );

		await act( async( ) =>
		{
			await expect( result.current.mutateAsync( FAKE_API_KEY_ID_2 ) ).rejects.toBeTruthy( );
		} );
	} );

	it( 'rejects for a non-existent key id', async( ) =>
	{
		const queryClient = createTestQueryClient( );

		const { result } = renderHook( ( ) => useRevokeApiKey( ), { wrapper: wrapperFor( queryClient ) } );

		await act( async( ) =>
		{
			await expect(
				result.current.mutateAsync( 'non-existent-id' )
			).rejects.toBeTruthy( );
		} );
	} );
} );
