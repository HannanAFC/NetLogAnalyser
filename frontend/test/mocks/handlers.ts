import { http, HttpResponse } from 'msw';

export const VALID_EMAIL = 'jane@example.com';
export const VALID_PASSWORD = 'correct-horse-battery-staple';

const FAKE_USER =
{
	id: '11111111-1111-1111-1111-111111111111',
	email: VALID_EMAIL
};

// Tracks how many times /auth/refresh was actually called, so tests can
// assert the 401 -> refresh -> retry interceptor deduplicates concurrent
// refresh calls instead of firing one per failed request.
export let refreshCallCount = 0;

export function resetRefreshCallCount()
{
	refreshCallCount = 0;
}

// Toggle this from a test with `server.use(...)` overrides rather than
// mutating it directly where possible - kept simple here for clarity.
export let refreshShouldFail = false;

export function setRefreshShouldFail( value: boolean )
{
	refreshShouldFail = value;
}

export const handlers = [
	http.post( '*/auth/login', async ( { request } ) =>
	{
		const body = ( await request.json() ) as { email: string; password: string };

		if ( body.email !== VALID_EMAIL || body.password !== VALID_PASSWORD )
		{
			return HttpResponse.json(
				{ detail: 'Incorrect email or password' },
				{ status: 401 }
			);
		}

		return HttpResponse.json(
		{
			access_token: 'fake-access-token',
			user: FAKE_USER
		});
	}),

	http.post( '*/auth/refresh', async () =>
	{
		refreshCallCount += 1;

		if ( refreshShouldFail )
		{
			return HttpResponse.json( { detail: 'Invalid refresh token' }, { status: 401 } );
		}

		// Simulate a small delay so concurrent 401s actually race and
		// exercise the dedup logic in the Axios interceptor.
		await new Promise( ( resolve ) => setTimeout( resolve, 20 ) );

		return HttpResponse.json(
		{
			access_token: 'refreshed-access-token',
			user: FAKE_USER
		});
	}),

	http.get( '*/users/me', ( { request } ) =>
	{
		const auth = request.headers.get( 'authorization' );

		if ( !auth || auth === 'Bearer expired-access-token' )
		{
			return HttpResponse.json( { detail: 'Not authenticated' }, { status: 401 } );
		}

		return HttpResponse.json( FAKE_USER );
	}),

	http.post( '*/auth/logout', ( ) => new HttpResponse( null, { status: 204 } ) )
];