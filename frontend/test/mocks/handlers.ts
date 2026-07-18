import { http, HttpResponse } from 'msw';

export const VALID_EMAIL = 'jane@example.com';
export const VALID_PASSWORD = 'correct-horse-battery-staple';
export const UNVERIFIED_EMAIL = 'unverified@example.com';
export const VALID_VERIFICATION_TOKEN = 'valid-verification-token';
export const VALID_RESET_TOKEN = 'valid-reset-token';

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

export let verifyEmailCallCount                       = 0;
export let resendVerificationCallCount                = 0;
export let forgotPasswordCallCount                    = 0;
export let resetPasswordCallCount                     = 0;
export let lastResendVerificationEmail: string | null = null;
export let lastForgotPasswordEmail: string | null     = null;

export function resetEmailVerificationCounters( )
{
	verifyEmailCallCount        = 0;
	resendVerificationCallCount = 0;
	forgotPasswordCallCount     = 0;
	resetPasswordCallCount      = 0;
	lastResendVerificationEmail = null;
	lastForgotPasswordEmail     = null;
}

export const handlers = [
	http.post( '*/auth/login', async ( { request } ) =>
	{
		const body = ( await request.json() ) as { email: string; password: string };

		if ( body.email === UNVERIFIED_EMAIL && body.password === VALID_PASSWORD )
		{
			return HttpResponse.json( { detail: 'Email has not been verified.' }, { status: 403 } );
		}

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

	http.post( '*/auth/logout', ( ) => new HttpResponse( null, { status: 204 } ) ),

	http.get( '*/auth/verify-email', ( { request } ) =>
	{
		verifyEmailCallCount += 1;
		const url = new URL( request.url );
		const token = url.searchParams.get( 'token' );

		if ( token !== VALID_VERIFICATION_TOKEN )
		{
			return HttpResponse.json( { detail: 'Invalid or expired verification link' }, { status: 400 } );
		}

		return HttpResponse.json( { detail: 'Email verified successfully' } );
	}),

	http.post( '*/auth/resend-verification', async ( { request } ) =>
	{
		resendVerificationCallCount += 1;
		const body = ( await request.json( ) ) as { email: string };
		lastResendVerificationEmail = body.email;

		// Enumeration-safe: identical response regardless of whether the email
		// exists or is already verified, matching the real backend.
		return HttpResponse.json(
		{
			detail: 'If an account with that email exists and is unverified, a new link has been sent'
		});
	}),

	http.post( '*/auth/forgot-password', async ( { request } ) =>
	{
		forgotPasswordCallCount += 1;
		const body = ( await request.json( ) ) as { email: string };
		lastForgotPasswordEmail = body.email;

		return HttpResponse.json(
		{
			detail: "If an account with that email exists, we've sent a link to reset your password"
		});
	}),

	http.post( '*/auth/reset-password', async ( { request } ) =>
	{
		resetPasswordCallCount += 1;
		const body = ( await request.json( ) ) as { token: string; password: string };

		if ( body.token !== VALID_RESET_TOKEN )
		{
			return HttpResponse.json( { detail: 'Invalid or expired reset link' }, { status: 400 } );
		}

		return HttpResponse.json( { detail: 'Password reset successfully' } );
	})
];