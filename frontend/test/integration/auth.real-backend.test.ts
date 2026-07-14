import axios from 'axios';
import { describe, expect, it } from 'vitest';

const BASE_URL = 'http://localhost:8000';

const client = axios.create(
{
    baseURL: BASE_URL,
	withCredentials: true,
	validateStatus: ( ) => true
});

function uniqueTestEmail( )
{
	return `integration-test-${ Date.now() }-${ Math.random( ).toString( 36 ).slice( 2 ) }@example.com`;
}

function uniqueTestDisplayName( )
{
    return `integration-test-${ Date.now() }-${ Math.random( ).toString( 36 ).slice( 2 ) }`;
}

const TEST_PASSWORD = 'Correct-Horse-Battery-Staple-9!';

// TODO: maybe verify response shapes exactly match what is expected?

describe.runIf( process.env.RUN_INTEGRATION_TESTS === '1' )( 'real backend: auth flow', ( ) =>
{
	it( 'health check responds ok', async ( ) =>
	{
		const response = await client.get( '/health' );

		expect( response.status ).toBe( 200 );
		expect( response.data ).toMatchObject( { database: 'ok' } );
	});

	it( 'registers a new user and returns the expected shape', async ( ) =>
	{
		const email       = uniqueTestEmail( );
        const displayName = uniqueTestDisplayName( );

		const response = await client.post( '/auth/register',
        {
			email,
            display_name:     displayName,
			password:         TEST_PASSWORD,
            confirm_password: TEST_PASSWORD
		});

		expect( response.status ).toBe( 201 );
		expect( response.data ).toMatchObject(
        {
			user: { email }
		});
		
		expect( JSON.stringify( response.data ) ).not.toContain( TEST_PASSWORD );
	});

	it( 'logs in with the registered user and receives a real access token', async ( ) =>
	{
		const email       = uniqueTestEmail( );
        const displayName = uniqueTestDisplayName( );
		await client.post( '/auth/register', { email, display_name: displayName, password: TEST_PASSWORD, confirm_password: TEST_PASSWORD } );

		const response = await client.post( '/auth/login', { email, password: TEST_PASSWORD } );

		expect( response.status ).toBe( 200 );
		expect( response.data.access_token ).toBeTypeOf( 'string' );
		expect( response.data.user ).toMatchObject( { email } );

		
		const setCookie = response.headers[ 'set-cookie' ] ?? [ ];
		const refreshCookie = setCookie.find( ( c: string ) => c.includes( 'refresh_token' ) );

		expect( refreshCookie ).toBeDefined( );
		expect( refreshCookie?.toLowerCase() ).toContain( 'httponly' );
		expect( refreshCookie?.toLowerCase() ).toContain( 'path=/auth' );
	});

	it( 'rejects login for a nonexistent email with the same response as a wrong password', async ( ) =>
	{
		const email       = uniqueTestEmail( );
        const displayName = uniqueTestDisplayName( );
		await client.post( '/auth/register', { email, display_name: displayName, password: TEST_PASSWORD, confirm_password: TEST_PASSWORD } );

		const wrongPassword = await client.post( '/auth/login',
        {
			email,
			password: 'definitely-wrong',
		});
		const nonexistentEmail = await client.post( '/auth/login',
        {
			email: uniqueTestEmail( ),
			password: TEST_PASSWORD,
		});

		expect( wrongPassword.status ).toBe( nonexistentEmail.status );
		expect( wrongPassword.data ).toEqual( nonexistentEmail.data );
	});

	it( 'rejects a request to /users/me without a token', async ( ) =>
	{
		const response = await client.get( '/users/me' );

		expect( response.status ).toBe( 401 );
	});
});