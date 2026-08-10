import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Mock } from 'vitest';

import type { ConnectionStatus, LiveFeedSocketCallbacks } from '#/features/live-feed/connection';
import type { LogEntry } from '#/lib/logs/types';

// ═══════════════════════════════════════════════════════════════════
// vi.mock is hoisted — use vi.hoisted so the factory can reference
// the mock function before the const declaration is evaluated.
// ═══════════════════════════════════════════════════════════════════

const { mockRequestWsTicket } = vi.hoisted( ( ) => ( {
	mockRequestWsTicket: vi.fn( ).mockResolvedValue( 'fake-ws-ticket' )
} ) );

vi.mock( '#/features/live-feed/api', ( ) => ( {
	requestWsTicket: mockRequestWsTicket
} ) );

// eslint-disable-next-line import/first
import { LiveFeedSocket } from '#/features/live-feed/connection';

// ═══════════════════════════════════════════════════════════════════
// Mock WebSocket
// ═══════════════════════════════════════════════════════════════════

type WebSocketEventHandler = ( event: unknown ) => void;

const mockSocketInstances: MockWebSocket[ ] = [ ];

class MockWebSocket
{
	static CONNECTING = 0;
	static OPEN       = 1;
	static CLOSING    = 2;
	static CLOSED     = 3;

	url:       string;
	readyState = MockWebSocket.CONNECTING;

	onopen:    WebSocketEventHandler | null = null;
	onmessage: WebSocketEventHandler | null = null;
	onclose:   WebSocketEventHandler | null = null;
	onerror:   WebSocketEventHandler | null = null;

	sentMessages: string[ ] = [ ];

	constructor( url: string )
	{
		this.url = url;
		mockSocketInstances.push( this );

		// Fire onopen after the caller has attached its handler.
		// setTimeout(0) is controlled by vi.useFakeTimers().
		setTimeout( ( ) =>
		{
			this.readyState = MockWebSocket.OPEN;
			this.onopen?.( { } );
		}, 0 );
	}

	send( data: string ): void
	{
		this.sentMessages.push( data );
	}

	close( code?: number ): void
	{
		this.readyState = MockWebSocket.CLOSED;
		this.onclose?.(
			{ code: code ?? 1000 }
		);
	}
}

// ═══════════════════════════════════════════════════════════════════
// Helpers
// ═══════════════════════════════════════════════════════════════════

const SAMPLE_ENTRY: LogEntry = {
	src_ip:            '10.0.0.1',
	dst_ip:            '10.0.0.2',
	src_port:          443,
	dst_port:          8080,
	protocol:          'TCP',
	packet_size_bytes: 1500,
	flags:             'SYN',
	dst_country_code:  'US',
	src_country_code:  null,
	dst_geo_status:    'resolved',
	src_geo_status:    'private',
	anomaly_score:     0.05,
	anomaly_reasons:   [ ],
	captured_at:       '2025-08-01T12:00:00Z'
};

const VALID_MESSAGE_DATA = JSON.stringify(
{
	type: 'log_entry_batch',
	data: [ SAMPLE_ENTRY ]
} );

function makeCallbacks( ): {
	onEntries:      Mock< ( entries: LogEntry[ ] ) => void >
	onStatusChange: Mock< ( status: ConnectionStatus ) => void >
}
{
	return {
		onEntries:      vi.fn( ),
		onStatusChange: vi.fn( )
	};
}

// ═══════════════════════════════════════════════════════════════════
// Setup / teardown
// ═══════════════════════════════════════════════════════════════════

beforeEach( ( ) =>
{
	mockSocketInstances.length = 0;
	mockRequestWsTicket.mockReset( ).mockResolvedValue( 'fake-ws-ticket' );

	vi.stubGlobal( 'WebSocket', MockWebSocket );
	vi.useFakeTimers( );
} );

afterEach( ( ) =>
{
	vi.restoreAllMocks( );
	vi.useRealTimers( );
} );

async function createSocket( callbacks?: LiveFeedSocketCallbacks ): Promise< LiveFeedSocket >
{
	const cb = callbacks ?? makeCallbacks( );
	const socket = new LiveFeedSocket( cb );
	const connectPromise = socket.connect( );

	// Advance past setTimeout(0) that fires onopen — must NOT use
	// runAllTimersAsync (infinite heartbeat setInterval would abort).
	await vi.advanceTimersByTimeAsync( 0 );

	await connectPromise;

	return socket;
}

function latestMockSocket( ): MockWebSocket
{
	return mockSocketInstances[ mockSocketInstances.length - 1 ];
}

// ═══════════════════════════════════════════════════════════════════
// Tests — connection lifecycle
// ═══════════════════════════════════════════════════════════════════

describe( 'LiveFeedSocket — connection', ( ) =>
{
	it( 'transitions status: idle → connecting → open on successful connect', async( ) =>
	{
		const { onStatusChange } = makeCallbacks( );

		const socket = new LiveFeedSocket( { onEntries: vi.fn( ), onStatusChange } );
		const promise = socket.connect( );
		await vi.advanceTimersByTimeAsync( 0 );
		await promise;

		expect( onStatusChange ).toHaveBeenCalledWith( 'connecting' );
		expect( onStatusChange ).toHaveBeenCalledWith( 'open' );
	} );

	it( 'calls requestWsTicket and opens WebSocket with ticket in URL', async( ) =>
	{
		await createSocket( );

		expect( mockRequestWsTicket ).toHaveBeenCalledOnce( );
		expect( latestMockSocket( ).url ).toContain( '?ticket=fake-ws-ticket' );
	} );

	it( 'transitions status to closed on disconnect', async( ) =>
	{
		const { onStatusChange } = makeCallbacks( );
		const socket = await createSocket( { onEntries: vi.fn( ), onStatusChange } );
		onStatusChange.mockClear( );

		socket.disconnect( );

		expect( onStatusChange ).toHaveBeenCalledWith( 'closed' );
	} );

	it( 'closes the underlying WebSocket on disconnect', async( ) =>
	{
		const socket = await createSocket( );
		const ws = latestMockSocket( );

		socket.disconnect( );

		expect( ws.readyState ).toBe( MockWebSocket.CLOSED );
	} );
} );

// ═══════════════════════════════════════════════════════════════════
// Tests — message handling
// ═══════════════════════════════════════════════════════════════════

describe( 'LiveFeedSocket — messages', ( ) =>
{
	it( 'calls onEntries with parsed entries for a valid batch', async( ) =>
	{
		const { onEntries } = makeCallbacks( );
		await createSocket( { onEntries, onStatusChange: vi.fn( ) } );

		const ws = latestMockSocket( );
		ws.onmessage?.( { data: VALID_MESSAGE_DATA } );

		expect( onEntries ).toHaveBeenCalledOnce( );
		expect( onEntries ).toHaveBeenCalledWith( [ SAMPLE_ENTRY ] );
	} );

	it( 'ignores invalid JSON (no onEntries call)', async( ) =>
	{
		const { onEntries } = makeCallbacks( );
		await createSocket( { onEntries, onStatusChange: vi.fn( ) } );

		const ws = latestMockSocket( );
		ws.onmessage?.( { data: 'not-valid-json' } );

		expect( onEntries ).not.toHaveBeenCalled( );
	} );

	it( 'ignores JSON that does not match the log_entry_batch schema', async( ) =>
	{
		const { onEntries } = makeCallbacks( );
		await createSocket( { onEntries, onStatusChange: vi.fn( ) } );

		const ws = latestMockSocket( );
		ws.onmessage?.(
			{ data: JSON.stringify( { type: 'other_type', data: [ ] } ) }
		);

		expect( onEntries ).not.toHaveBeenCalled( );
	} );

	it( 'ignores JSON that has valid type but invalid entries', async( ) =>
	{
		const { onEntries } = makeCallbacks( );
		await createSocket( { onEntries, onStatusChange: vi.fn( ) } );

		const ws = latestMockSocket( );
		ws.onmessage?.(
		{
			data: JSON.stringify(
			{
				type: 'log_entry_batch',
				data: [ { invalid: 'entry' } ]
			} )
		} );

		expect( onEntries ).not.toHaveBeenCalled( );
	} );
} );

// ═══════════════════════════════════════════════════════════════════
// Tests — unexpected close handling
// ═══════════════════════════════════════════════════════════════════

describe( 'LiveFeedSocket — unexpected close', ( ) =>
{
	it( 'sets status to error on 4403 (origin rejected) and does not reconnect', async( ) =>
	{
		const { onStatusChange } = makeCallbacks( );
		await createSocket( { onEntries: vi.fn( ), onStatusChange } );
		onStatusChange.mockClear( );

		const ws = latestMockSocket( );
		ws.onclose?.( { code: 4403 } );

		expect( onStatusChange ).toHaveBeenCalledWith( 'error' );

		// Advance past any reconnect delay — should NOT attempt reconnect
		await vi.advanceTimersByTimeAsync( 60_000 );
		expect( mockRequestWsTicket ).toHaveBeenCalledOnce( );
	} );

	it( 'sets status to error on 4409 (connection limit) and schedules reconnect', async( ) =>
	{
		const { onStatusChange } = makeCallbacks( );
		await createSocket( { onEntries: vi.fn( ), onStatusChange } );
		onStatusChange.mockClear( );

		const ws = latestMockSocket( );
		ws.onclose?.( { code: 4409 } );

		expect( onStatusChange ).toHaveBeenCalledWith( 'error' );
	} );

	it( 'schedules reconnect on 4401 (bad ticket)', async( ) =>
	{
		const { onStatusChange } = makeCallbacks( );
		await createSocket( { onEntries: vi.fn( ), onStatusChange } );
		onStatusChange.mockClear( );

		const ws = latestMockSocket( );
		ws.onclose?.( { code: 4401 } );

		expect( onStatusChange ).toHaveBeenCalledWith( 'reconnecting' );

		await vi.advanceTimersByTimeAsync( 1_100 );
		expect( mockRequestWsTicket ).toHaveBeenCalledTimes( 2 );
	} );

	it( 'does not reconnect after caller-invoked disconnect', async( ) =>
	{
		const { onStatusChange } = makeCallbacks( );
		const socket = await createSocket( { onEntries: vi.fn( ), onStatusChange } );
		onStatusChange.mockClear( );

		socket.disconnect( );

		expect( onStatusChange ).toHaveBeenCalledWith( 'closed' );

		await vi.advanceTimersByTimeAsync( 10_000 );
		expect( mockRequestWsTicket ).toHaveBeenCalledOnce( );
	} );
} );

// ═══════════════════════════════════════════════════════════════════
// Tests — error handling
// ═══════════════════════════════════════════════════════════════════

describe( 'LiveFeedSocket — errors', ( ) =>
{
	it( 'sets status to error on WebSocket error event', async( ) =>
	{
		const { onStatusChange } = makeCallbacks( );
		await createSocket( { onEntries: vi.fn( ), onStatusChange } );
		onStatusChange.mockClear( );

		const ws = latestMockSocket( );
		ws.onerror?.( { } );

		expect( onStatusChange ).toHaveBeenCalledWith( 'error' );
	} );

	it( 'schedules reconnect when requestWsTicket fails', async( ) =>
	{
		const { onEntries, onStatusChange } = makeCallbacks( );
		mockRequestWsTicket.mockRejectedValueOnce( new Error( 'Network error' ) );

		const socket = new LiveFeedSocket( { onEntries, onStatusChange } );
		const promise = socket.connect( );
		await vi.advanceTimersByTimeAsync( 0 );
		await promise;

		// Should have scheduled a reconnect
		expect( onStatusChange ).toHaveBeenCalledWith( 'connecting' );

		await vi.advanceTimersByTimeAsync( 1_100 );
		expect( mockRequestWsTicket ).toHaveBeenCalledTimes( 2 );
	} );
} );

// ═══════════════════════════════════════════════════════════════════
// Tests — heartbeat
// ═══════════════════════════════════════════════════════════════════

describe( 'LiveFeedSocket — heartbeat', ( ) =>
{
	it( 'sends ping on the heartbeat interval', async( ) =>
	{
		await createSocket( );

		const ws = latestMockSocket( );

		await vi.advanceTimersByTimeAsync( 26_000 );

		expect( ws.sentMessages ).toContain( 'ping' );
	} );

	it( 'stops heartbeat after disconnect', async( ) =>
	{
		const socket = await createSocket( );
		const ws = latestMockSocket( );

		socket.disconnect( );

		const beforeDisconnect = ws.sentMessages.length;

		await vi.advanceTimersByTimeAsync( 50_000 );

		expect( ws.sentMessages.length ).toBe( beforeDisconnect );
	} );
} );
