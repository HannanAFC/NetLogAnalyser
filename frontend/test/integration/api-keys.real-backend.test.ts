import axios from 'axios';
import { describe, expect, it } from 'vitest';

const BASE_URL = 'http://localhost:8000';

const client = axios.create(
{
    baseURL: BASE_URL,
    withCredentials: true,
    validateStatus: ( ) => true
} );

function uniqueTestEmail( )
{
	return `integration-test-${ Date.now() }-${ Math.random( ).toString( 36 ).slice( 2 ) }@example.com`;
}

function uniqueTestDisplayName( )
{
	return `integration-test-${ Date.now() }-${ Math.random( ).toString( 36 ).slice( 2 ) }`;
}

async function getLatestTestToken(
	email: string,
	tokenType: 'verification' | 'reset'
): Promise<string>
{
	const response = await client.get( '/test-only/last-token',
    {
        params: { email: email, token_type: tokenType },
        headers: { 'X-Test-Endpoint-Key': process.env.TEST_ENDPOINT_KEY ?? '' }
    } );

	if ( response.status !== 200 )
	{
		throw new Error(
			`Could not fetch test token (status ${ response.status }) - is ENABLE_TEST_ENDPOINTS ` +
			'and TEST_ENDPOINT_KEY set for the backend this suite is running against?'
		);
	}

	return response.data.token;
}

const TEST_PASSWORD = 'Correct-Horse-Battery-Staple-9!';

/**
 * Register a user, verify their email, log in, and return the access token
 * and user id so API key tests can call authenticated endpoints.
 */
async function registerAndLogin( email: string, displayName: string )
{
	await client.post( '/auth/register',
    {
        email,
        display_name:     displayName,
        password:         TEST_PASSWORD,
        confirm_password: TEST_PASSWORD
    } );

	const verifyToken = await getLatestTestToken( email, 'verification' );
	await client.get( '/auth/verify-email', { params: { token: verifyToken } } );

	const loginResponse = await client.post( '/auth/login',
    {
        email,
        password: TEST_PASSWORD
    } );

	return {
		accessToken: loginResponse.data.access_token as string,
		userId:      loginResponse.data.user.id as string
	};
}

function authHeader( token: string )
{
	return { Authorization: `Bearer ${ token }` };
}

describe.runIf( process.env.RUN_INTEGRATION_TESTS === '1' )( 'real backend API keys', ( ) =>
{
	it( 'creates an API key and returns the expected shape including the raw key', async( ) =>
	{
		const { accessToken } = await registerAndLogin( uniqueTestEmail( ), uniqueTestDisplayName( ) );

		const response = await client.post( '/api-keys',
			{ label: 'My Integration Test Key' },
			{ headers: authHeader( accessToken ) }
        );

		expect( response.status ).toBe( 201 );

		const data = response.data;
		expect( data ).toHaveProperty( 'id' );
		expect( data ).toHaveProperty( 'label', 'My Integration Test Key' );
		expect( data ).toHaveProperty( 'key_prefix' );
		expect( data ).toHaveProperty( 'api_key' );
		expect( data ).toHaveProperty( 'created_at' );

		// The raw key must be a non-empty string and contain the prefix
		expect( data.api_key ).toBeTypeOf( 'string' );
		expect( data.api_key.length ).toBeGreaterThan( 0 );
		expect( data.api_key ).toContain( data.key_prefix );
		expect( data.api_key ).not.toBe( data.key_prefix ); // longer than prefix
	} );

	it( 'lists API keys for the authenticated user', async( ) =>
	{
		const email = uniqueTestEmail( );
		const { accessToken } = await registerAndLogin( email, uniqueTestDisplayName( ) );

		// Create two keys with distinct labels
		await client.post( '/api-keys',
			{ label: 'First Key' },
			{ headers: authHeader( accessToken ) }
        );
		await client.post( '/api-keys',
			{ label: 'Second Key' },
			{ headers: authHeader( accessToken ) }
        );

		const response = await client.get( '/api-keys',
			{ headers: authHeader( accessToken ) }
        );

		expect( response.status ).toBe( 200 );
		expect( Array.isArray( response.data ) ).toBe( true );
		expect( response.data ).toHaveLength( 2 );

		// Each entry must have the public shape and must NOT expose the raw key
		for ( const key of response.data )
		{
			expect( key ).toHaveProperty( 'id' );
			expect( key ).toHaveProperty( 'label' );
			expect( key ).toHaveProperty( 'key_prefix' );
			expect( key ).toHaveProperty( 'created_at' );
			expect( key ).toHaveProperty( 'last_used_at' );
			expect( key ).toHaveProperty( 'revoked_at' );
			expect( key ).not.toHaveProperty( 'api_key' );
			expect( key ).not.toHaveProperty( 'key_hash' );
		}

		// Keys are ordered newest-first (created_at desc)
		const labels = response.data.map( ( k: { label: string } ) => k.label );
		expect( labels ).toEqual( [ 'Second Key', 'First Key' ] );
	} );

	it( 'revokes an API key and reflects the change in the list', async( ) =>
	{
		const { accessToken } = await registerAndLogin( uniqueTestEmail( ), uniqueTestDisplayName( ) );

		const createResponse = await client.post( '/api-keys',
			{ label: 'To Be Revoked' },
			{ headers: authHeader( accessToken ) }
        );
		const keyId = createResponse.data.id as string;

		// Revoke the key
		const revokeResponse = await client.delete( `/api-keys/${ keyId }`,
			{ headers: authHeader( accessToken ) }
        );
		expect( revokeResponse.status ).toBe( 204 );

		// Listing again must show revoked_at set
		const listResponse = await client.get( '/api-keys',
			{ headers: authHeader( accessToken ) }
        );
		expect( listResponse.status ).toBe( 200 );
		expect( listResponse.data ).toHaveLength( 1 );

		const key = listResponse.data[ 0 ];
		expect( key.id ).toBe( keyId );
		expect( key.revoked_at ).toBeTruthy( );
		expect( key.revoked_at ).toBeTypeOf( 'string' );
	} );

	it( 'returns 404 when revoking a non-existent key id', async( ) =>
	{
		const { accessToken } = await registerAndLogin( uniqueTestEmail( ), uniqueTestDisplayName( ) );

		const response = await client.delete(
			'/api-keys/00000000-0000-0000-0000-000000000000',
			{ headers: authHeader( accessToken ) }
        );

		expect( response.status ).toBe( 404 );
		expect( response.data.detail ).toContain( 'not found' );
	} );

	it( 'returns 409 when revoking an already-revoked key', async( ) =>
	{
		const { accessToken } = await registerAndLogin( uniqueTestEmail( ), uniqueTestDisplayName( ) );

		const createResponse = await client.post( '/api-keys',
			{ label: 'Revoke Twice' },
			{ headers: authHeader( accessToken ) }
        );
		const keyId = createResponse.data.id as string;

		// First revoke
		await client.delete( `/api-keys/${ keyId }`,
			{ headers: authHeader( accessToken ) }
        );

		// Second revoke — must be 409
		const secondRevoke = await client.delete( `/api-keys/${ keyId }`,
			{ headers: authHeader( accessToken ) }
        );
		expect( secondRevoke.status ).toBe( 409 );
		expect( secondRevoke.data.detail ).toContain( 'already been revoked' );
	} );

	it( 'returns 401 when accessing API key endpoints without a token', async( ) =>
	{
		const listResponse = await client.get( '/api-keys' );
		expect( listResponse.status ).toBe( 401 );

		const createResponse = await client.post( '/api-keys', { label: 'Unauthorized' } );
		expect( createResponse.status ).toBe( 401 );

		const revokeResponse = await client.delete(
			'/api-keys/00000000-0000-0000-0000-000000000000' );
		expect( revokeResponse.status ).toBe( 401 );
	} );

	it( 'lists only the keys belonging to the authenticated user', async( ) =>
	{
		// User A creates a key
		const { accessToken: tokenA } = await registerAndLogin( uniqueTestEmail( ), uniqueTestDisplayName( ) );
		await client.post( '/api-keys',
			{ label: 'User A Key' },
			{ headers: authHeader( tokenA ) }
        );

		// User B creates two keys
		const { accessToken: tokenB } = await registerAndLogin( uniqueTestEmail( ), uniqueTestDisplayName( ) );
		await client.post( '/api-keys',
			{ label: 'User B Key 1' },
			{ headers: authHeader( tokenB ) }
        );
		await client.post( '/api-keys',
			{ label: 'User B Key 2' },
			{ headers: authHeader( tokenB ) }
        );

		// User A only sees their own key
		const listA = await client.get( '/api-keys',
			{ headers: authHeader( tokenA ) }
        );
		expect( listA.data ).toHaveLength( 1 );
		expect( listA.data[ 0 ].label ).toBe( 'User A Key' );

		// User B only sees their own keys
		const listB = await client.get( '/api-keys',
			{ headers: authHeader( tokenB ) }
        );
		expect( listB.data ).toHaveLength( 2 );
	} );

	it( 'returns 404 when revoking a key that belongs to another user', async( ) =>
	{
		// User A creates a key
		const { accessToken: tokenA } = await registerAndLogin( uniqueTestEmail( ), uniqueTestDisplayName( ) );
		const createResponse = await client.post( '/api-keys',
			{ label: 'User A Key' },
			{ headers: authHeader( tokenA ) }
        );
		const keyAId = createResponse.data.id as string;

		// User B tries to revoke User A's key
		const { accessToken: tokenB } = await registerAndLogin( uniqueTestEmail( ), uniqueTestDisplayName( ) );
		const response = await client.delete( `/api-keys/${ keyAId }`,
			{ headers: authHeader( tokenB ) }
        );

		expect( response.status ).toBe( 404 );
	} );

	it( 'respects the label length constraints', async( ) =>
	{
		const { accessToken } = await registerAndLogin( uniqueTestEmail( ), uniqueTestDisplayName( ) );

		// Empty label
		const emptyResponse = await client.post( '/api-keys',
			{ label: '' },
			{ headers: authHeader( accessToken ) }
        );
		expect( emptyResponse.status ).toBe( 422 );

		// Label over 100 characters
		const tooLongResponse = await client.post( '/api-keys',
			{ label: 'a'.repeat( 101 ) },
			{ headers: authHeader( accessToken ) }
        );
		expect( tooLongResponse.status ).toBe( 422 );
	} );
} );
