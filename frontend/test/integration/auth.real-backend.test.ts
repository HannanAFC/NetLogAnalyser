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

async function getLatestTestToken(
	email: string,
	tokenType: 'verification' | 'reset'
): Promise<string>
{
	const response = await client.get( '/test-only/last-token',
	{
		params: { email: email, token_type: tokenType },
		headers: { 'X-Test-Endpoint-Key': process.env.TEST_ENDPOINT_KEY ?? '' },
	});

	if ( response.status !== 200 )
	{
		throw new Error(
			`Could not fetch test token (status ${ response.status }) - is ENABLE_TEST_ENDPOINTS ` +
			`and TEST_ENDPOINT_KEY set for the backend this suite is running against?`
		);
	}

	return response.data.token;
}

const TEST_PASSWORD = 'Correct-Horse-Battery-Staple-9!';

// TODO: maybe verify response shapes exactly match what is expected?

describe.runIf( process.env.RUN_INTEGRATION_TESTS === '1' )( 'real backend auth flow', ( ) =>
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

	it( 'logs in with the registered and verified user and receives a real access token', async ( ) =>
	{
		const email       = uniqueTestEmail( );
        const displayName = uniqueTestDisplayName( );
		await client.post( '/auth/register', { email, display_name: displayName, password: TEST_PASSWORD, confirm_password: TEST_PASSWORD } );

		const token = await getLatestTestToken( email, 'verification' );

		const verifyResponse = await client.get( '/auth/verify-email', { params: { token } } );
		expect( verifyResponse.status ).toBe( 200 );

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

	it( 'resends a valid verification link and expires the old one', async ( ) =>
	{
		const email       = uniqueTestEmail( );
        const displayName = uniqueTestDisplayName( );
		await client.post( '/auth/register', { email, display_name: displayName, password: TEST_PASSWORD, confirm_password: TEST_PASSWORD } );
		const oldToken = await getLatestTestToken( email, 'verification' );

		await client.post( '/auth/resend-verification', { email } );
		const newToken = await getLatestTestToken( email, 'verification' );
		expect( newToken ).not.toBe( oldToken );

		const oldResult = await client.get( '/auth/verify-email', { params: { token: oldToken } } );
		expect( oldResult.status ).toBe( 400 );

		const newResult = await client.get( '/auth/verify-email', { params: { token: newToken } } );
		expect( newResult.status ).toBe( 200 );
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

describe.runIf( process.env.RUN_INTEGRATION_TESTS === '1' )( 'real backend full password reset loop', ( ) =>
{
	it( 'completes forgot-password -> reset -> login with the new password', async ( ) =>
	{
		const email       = uniqueTestEmail( );
        const displayName = uniqueTestDisplayName( );
		await client.post( '/auth/register', { email, display_name: displayName, password: TEST_PASSWORD, confirm_password: TEST_PASSWORD } );
		const verifyToken = await getLatestTestToken( email, 'verification' );
		await client.get( '/auth/verify-email', { params: { token: verifyToken } } );

		await client.post( '/auth/forgot-password', { email } );
		const resetToken = await getLatestTestToken( email, 'reset' );

		const newPassword = 'A-Brand-New-Password-7!';
		const resetResponse = await client.post( '/auth/reset-password', { token: resetToken, password: newPassword, confirm_password: newPassword } );
		expect( resetResponse.status ).toBe( 200 );

		const oldPasswordLogin = await client.post( '/auth/login', { email, password: TEST_PASSWORD } );
		expect( oldPasswordLogin.status ).toBe( 401 );

		const newPasswordLogin = await client.post( '/auth/login', { email, password: newPassword } );
		expect( newPasswordLogin.status ).toBe( 200 );
	});
});