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

// ── API Keys mock data ──────────────────────────────────────────────

export const FAKE_API_KEY_ID_1 = 'aaaaaaaa-1111-1111-1111-111111111111';
export const FAKE_API_KEY_ID_2 = 'bbbbbbbb-2222-2222-2222-222222222222';

const FAKE_API_KEYS = [
	{
		id: FAKE_API_KEY_ID_1,
		label: 'My API Key',
		key_prefix: 'nl_abc123',
		created_at: '2024-01-01T00:00:00Z',
		last_used_at: null,
		revoked_at: null
	},
	{
		id: FAKE_API_KEY_ID_2,
		label: 'Old Key',
		key_prefix: 'nl_def456',
		created_at: '2024-01-02T00:00:00Z',
		last_used_at: '2024-01-15T00:00:00Z',
		revoked_at: '2024-02-01T00:00:00Z'
	}
];

const FAKE_CREATED_KEY = {
	id: 'cccccccc-3333-3333-3333-333333333333',
	label: 'New Key',
	key_prefix: 'nl_ghi789',
	api_key: 'nl_ghi789_this_is_a_raw_secret_key',
	created_at: '2024-03-01T00:00:00Z'
};

/** Call counts so tests can assert requests were (or were not) made. */
export let getApiKeysCallCount = 0;
export let createApiKeyCallCount = 0;
export let revokeApiKeyCallCount = 0;
export let lastCreateApiKeyLabel: string | null = null;

export function resetApiKeysCallCounts( )
{
	getApiKeysCallCount = 0;
	createApiKeyCallCount = 0;
	revokeApiKeyCallCount = 0;
	lastCreateApiKeyLabel = null;
}

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

export let verifyEmailCallCount = 0;
export let resendVerificationCallCount = 0;
export let forgotPasswordCallCount = 0;
export let resetPasswordCallCount = 0;
export let lastResendVerificationEmail: string | null = null;
export let lastForgotPasswordEmail: string | null = null;

export function resetEmailVerificationCounters( )
{
	verifyEmailCallCount = 0;
	resendVerificationCallCount = 0;
	forgotPasswordCallCount = 0;
	resetPasswordCallCount = 0;
	lastResendVerificationEmail = null;
	lastForgotPasswordEmail = null;
}

// ── Logs mock data ──────────────────────────────────────────────────

/** 50 mock log entries sorted newest-first (id 50 → 1). */
const MOCK_LOG_ENTRIES = Array.from( { length: 50 }, ( _, i ) =>
{
	const id = 50 - i;
	const padded = String( id ).padStart( 2, '0' );
	return {
		id,
		src_ip:            `192.168.1.${ id }`,
		dst_ip:            `10.0.0.${ id }`,
		src_port:          443,
		dst_port:          5000 + id,
		protocol:          id % 3 === 0 ? 'UDP' : 'TCP',
		packet_size_bytes: 1500,
		flags:             id % 2 === 0 ? 'SYN,ACK' : null,
		src_country_code:  id % 7 === 0 ? 'US' : null,
		dst_country_code:  id % 5 === 0 ? 'US' : null,
		src_geo_status:    id % 7 === 0 ? 'resolved' : 'private',
		dst_geo_status:    id % 5 === 0 ? 'resolved' : 'private',
		anomaly_score:     id % 7 === 0 ? 0.85 : 0,
		anomaly_reasons:   id % 7 === 0 ? [ { name: 'test_anomaly', score: 0.85, detail: 'Test anomaly detail' } ] : [],
		captured_at:       `2024-01-01T00:00:${ padded }Z`
	};
} );

export let getLogsCallCount = 0;

export function resetGetLogsCallCount( )
{
	getLogsCallCount = 0;
}

// ── Analytics mock data ────────────────────────────────────────────

export const FAKE_SUMMARY =
{
	start:              '2024-01-01T00:00:00Z',
	end:                '2024-01-02T00:00:00Z',
	total_packets:      1000,
	unique_src_ips:     42,
	unique_dst_ips:     57,
	avg_anomaly_score:  0.13,
	high_anomaly_count: 4,
	total_bytes:        1500000
};

export const FAKE_TIMESERIES =
{
	bucket: 'hour',
	points:
	[
		{ ts: '2024-01-01T00:00:00Z', count: 100, avg_anomaly_score: 0.1, total_bytes: 50000 },
		{ ts: '2024-01-01T01:00:00Z', count: 200, avg_anomaly_score: 0.2, total_bytes: 100000 },
		{ ts: '2024-01-01T02:00:00Z', count: 150, avg_anomaly_score: 0.15, total_bytes: 75000 }
	]
};

export const FAKE_TOP_TALKERS =
{
	direction: 'src',
	metric:    'packets',
	rows:
	[
		{ ip: '192.168.1.10', count: 300, avg_anomaly_score: 0.05, total_bytes: 150000 },
		{ ip: '192.168.1.11', count: 200, avg_anomaly_score: 0.1, total_bytes: 100000 }
	]
};

export const FAKE_PROTOCOLS =
{
	by_protocol:
	[
		{ protocol: 'TCP', count: 800, packet_percentage: 0.8 },
		{ protocol: 'UDP', count: 200, packet_percentage: 0.2 }
	],
	top_dst_ports:
	[
		{ port: 443, count: 500 },
		{ port: 80, count: 300 }
	]
};

export const FAKE_GEO =
{
	direction: 'src',
	rows:
	[
		{ country_code: 'US', geo_status: 'resolved', count: 400, packet_percentage: 0.5 },
		{ country_code: null, geo_status: 'private', count: 400, packet_percentage: 0.5 }
	]
};

export let getSummaryCallCount = 0;
export let getTimeseriesCallCount = 0;
export let getTopTalkersCallCount = 0;
export let getProtocolsCallCount = 0;
export let getGeoCallCount = 0;
export let getAnomaliesCallCount = 0;

export function resetAnalyticsCallCounts( )
{
	getSummaryCallCount = 0;
	getTimeseriesCallCount = 0;
	getTopTalkersCallCount = 0;
	getProtocolsCallCount = 0;
	getGeoCallCount = 0;
	getAnomaliesCallCount = 0;
}

export const handlers = [
	http.post( '*/auth/login', async( { request } ) =>
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
			} );
	} ),

	http.post( '*/auth/refresh', async() =>
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
			} );
	} ),

	http.get( '*/users/me', ( { request } ) =>
	{
		const auth = request.headers.get( 'authorization' );

		if ( !auth || auth === 'Bearer expired-access-token' )
		{
			return HttpResponse.json( { detail: 'Not authenticated' }, { status: 401 } );
		}

		return HttpResponse.json( FAKE_USER );
	} ),

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
	} ),

	http.post( '*/auth/resend-verification', async( { request } ) =>
	{
		resendVerificationCallCount += 1;
		const body = ( await request.json( ) ) as { email: string };
		lastResendVerificationEmail = body.email;

		// Enumeration-safe: identical response regardless of whether the email
		// exists or is already verified, matching the real backend.
		return HttpResponse.json(
			{
				detail: 'If an account with that email exists and is unverified, a new link has been sent'
			} );
	} ),

	http.post( '*/auth/forgot-password', async( { request } ) =>
	{
		forgotPasswordCallCount += 1;
		const body = ( await request.json( ) ) as { email: string };
		lastForgotPasswordEmail = body.email;

		return HttpResponse.json(
			{
				detail: "If an account with that email exists, we've sent a link to reset your password"
			} );
	} ),

	http.post( '*/auth/reset-password', async( { request } ) =>
	{
		resetPasswordCallCount += 1;
		const body = ( await request.json( ) ) as { token: string; password: string };

		if ( body.token !== VALID_RESET_TOKEN )
		{
			return HttpResponse.json( { detail: 'Invalid or expired reset link' }, { status: 400 } );
		}

		return HttpResponse.json( { detail: 'Password reset successfully' } );
	} ),

	// ── API Keys ─────────────────────────────────────────────────────

	http.get( '*/api-keys', ( ) =>
	{
		getApiKeysCallCount += 1;
		return HttpResponse.json( FAKE_API_KEYS );
	} ),

	http.post( '*/api-keys', async( { request } ) =>
	{
		createApiKeyCallCount += 1;
		const body = ( await request.json( ) ) as { label: string };
		lastCreateApiKeyLabel = body.label;

		return HttpResponse.json( FAKE_CREATED_KEY, { status: 201 } );
	} ),

	http.delete( '*/api-keys/:id', ( { params } ) =>
	{
		revokeApiKeyCallCount += 1;
		const { id } = params;

		if ( id === FAKE_API_KEY_ID_1 )
		{
			return new HttpResponse( null, { status: 204 } );
		}

		if ( id === FAKE_API_KEY_ID_2 )
		{
			// Already revoked
			return HttpResponse.json( { detail: 'API key has already been revoked.' }, { status: 409 } );
		}

		return HttpResponse.json( { detail: 'API key was not found.' }, { status: 404 } );
	} ),

	// ── WebSocket ticket ─────────────────────────────────────────────

	http.post( '*/ws/ticket', ( ) =>
	{
		return HttpResponse.json(
			{
				ticket:     'fake-ws-ticket',
				expires_in: 30
			}
		);
	} ),

	// ── Logs ─────────────────────────────────────────────────────────

	http.get( '*/logs', ( { request } ) =>
	{
		getLogsCallCount += 1;
		const url = new URL( request.url );
		const rawLimit = url.searchParams.get( 'limit' ) || '20';
		const limit = Math.min( Math.max( parseInt( rawLimit, 10 ) || 20, 1 ), 50 );
		const cursor = url.searchParams.get( 'cursor' );

		let startIndex = 0;
		if ( cursor )
		{
			try
			{
				const decoded = JSON.parse( atob( cursor ) ) as { id: number; captured_at: string };
				const idx = MOCK_LOG_ENTRIES.findIndex(
					( e ) => e.id === decoded.id && e.captured_at === decoded.captured_at
				);
				if ( idx === -1 )
				{
					return HttpResponse.json( { detail: 'Invalid cursor' }, { status: 400 } );
				}
				startIndex = idx + 1;
			}
			catch
			{
				return HttpResponse.json( { detail: 'Invalid cursor' }, { status: 400 } );
			}
		}

		const slice = MOCK_LOG_ENTRIES.slice( startIndex, startIndex + limit + 1 );
		const hasMore = slice.length > limit;
		const entries = hasMore ? slice.slice( 0, limit ) : slice;

		const nextCursor = hasMore && entries.length > 0
			? btoa( JSON.stringify( { id: entries[ entries.length - 1 ].id, captured_at: entries[ entries.length - 1 ].captured_at } ) )
			: null;

		return HttpResponse.json( { entries, next_cursor: nextCursor, has_more: hasMore } );
	} ),

	// ── Analytics ───────────────────────────────────────────────────

	http.get( '*/analytics/summary', ( ) =>
	{
		getSummaryCallCount += 1;
		return HttpResponse.json( FAKE_SUMMARY );
	} ),

	http.get( '*/analytics/timeseries', ( ) =>
	{
		getTimeseriesCallCount += 1;
		return HttpResponse.json( FAKE_TIMESERIES );
	} ),

	http.get( '*/analytics/top-talkers', ( ) =>
	{
		getTopTalkersCallCount += 1;
		return HttpResponse.json( FAKE_TOP_TALKERS );
	} ),

	http.get( '*/analytics/protocols', ( ) =>
	{
		getProtocolsCallCount += 1;
		return HttpResponse.json( FAKE_PROTOCOLS );
	} ),

	http.get( '*/analytics/geo', ( ) =>
	{
		getGeoCallCount += 1;
		return HttpResponse.json( FAKE_GEO );
	} ),

	http.get( '*/analytics/anomalies', ( { request } ) =>
	{
		getAnomaliesCallCount += 1;
		const url = new URL( request.url );
		const rawLimit = url.searchParams.get( 'limit' ) || '25';
		const limit = Math.min( Math.max( parseInt( rawLimit, 10 ) || 25, 1 ), 50 );
		const cursor = url.searchParams.get( 'cursor' );

		let startIndex = 0;
		if ( cursor )
		{
			try
			{
				const decoded = JSON.parse( atob( cursor ) ) as { id: number; captured_at: string };
				const idx = MOCK_LOG_ENTRIES.findIndex(
					( e ) => e.id === decoded.id && e.captured_at === decoded.captured_at
				);
				if ( idx === -1 )
				{
					return HttpResponse.json( { detail: 'Invalid cursor' }, { status: 400 } );
				}
				startIndex = idx + 1;
			}
			catch
			{
				return HttpResponse.json( { detail: 'Invalid cursor' }, { status: 400 } );
			}
		}

		const slice = MOCK_LOG_ENTRIES.slice( startIndex, startIndex + limit + 1 );
		const hasMore = slice.length > limit;
		const rows = hasMore ? slice.slice( 0, limit ) : slice;

		const lastRow = rows[ rows.length - 1 ];
		const nextCursor = hasMore && lastRow
			? btoa( JSON.stringify( { id: lastRow.id, captured_at: lastRow.captured_at } ) )
			: null;

		return HttpResponse.json( { rows, next_cursor: nextCursor, has_more: hasMore } );
	} )
];
