import { requestWsTicket } from '#/features/live-feed/api';
import { logEntryBatchMessageSchema } from '#/features/live-feed/schemas';
import { env } from '#/lib/env';
import type { LogEntry } from '#/lib/logs/types';

export type ConnectionStatus = 'idle' | 'connecting' | 'open' | 'reconnecting' | 'error' | 'closed';

export interface LiveFeedSocketCallbacks {
	onEntries:      ( entries: LogEntry[ ] ) => void
	onStatusChange: ( status: ConnectionStatus ) => void
}

const HEARTBEAT_INTERVAL_MS = 25_000;
const BASE_RECONNECT_DELAY_MS = 1_000;
const MAX_RECONNECT_DELAY_MS = 30_000;

const CLOSE_CODE_BAD_TICKET       = 4401;
const CLOSE_CODE_ORIGIN_REJECTED  = 4403;
const CLOSE_CODE_CONNECTION_LIMIT = 4409;

/**
 * Connection manager for the live-feed websocket.
 */
export class LiveFeedSocket
{
	private socket:          WebSocket | null                        = null;
	private heartbeatTimer:  ReturnType< typeof setInterval > | null = null;
	private reconnectTimer:  ReturnType< typeof setTimeout > | null  = null;
	private reconnectAttempt                                         = 0;
	private closedByCaller                                           = false;

	constructor( private readonly callbacks: LiveFeedSocketCallbacks )
{ }

	async connect( ): Promise< void >
	{
		this.closedByCaller = false;
		await this.openConnection( );
	}

	disconnect( ): void
	{
		this.closedByCaller = true;
		this.clearTimers( );
		this.socket?.close( 1000 );
		this.socket = null;
	}

	private async openConnection( ): Promise< void >
	{
		this.setStatus( this.reconnectAttempt === 0 ? 'connecting' : 'reconnecting' );

		let ticket: string;
		try
        {
			ticket = await requestWsTicket( );
		}
        catch
        {
			this.scheduleReconnect( );
			return;
		}

		if ( this.closedByCaller ) return;

		const socket = new WebSocket( `${ env.wsBaseUrl }/live?ticket=${ encodeURIComponent( ticket ) }` );
		this.socket = socket;

		socket.onopen = ( ) =>
        {
			this.reconnectAttempt = 0;
			this.setStatus( 'open' );
			this.startHeartbeat( );
		};

		socket.onmessage = ( event ) =>
        {
			this.handleMessage( event.data as string );
		};

		socket.onclose = ( event ) =>
        {
			this.stopHeartbeat( );
			if ( this.closedByCaller )
            {
				this.setStatus( 'closed' );
				return;
			}
			this.handleUnexpectedClose( event.code );
		};

		socket.onerror = ( ) =>
        {
            // onclose fires after onerror so reconnect logic is there
			this.setStatus( 'error' );
		};
	}

	private handleMessage( raw: string ): void
	{
		let parsed: unknown;
		try
        {
			parsed = JSON.parse( raw );
		}
        catch
        {
			return;
		}

		const result = logEntryBatchMessageSchema.safeParse( parsed );
		if ( !result.success )
        {
			return;
		}

		this.callbacks.onEntries( result.data.data );
	}

	private handleUnexpectedClose( code: number ): void
	{
		switch ( code )
        {
			case CLOSE_CODE_ORIGIN_REJECTED:
				// no retry as unrecoverable
				this.setStatus( 'error' );
				return;

			case CLOSE_CODE_CONNECTION_LIMIT:
                // slower reconnect
				this.setStatus( 'error' );
				this.scheduleReconnect( MAX_RECONNECT_DELAY_MS );
				return;

			case CLOSE_CODE_BAD_TICKET:
			default:
                // ticket invalid or server drop
				this.scheduleReconnect( );
				return;
		}
	}

	private scheduleReconnect( forcedDelay?: number ): void
	{
		this.setStatus( 'reconnecting' );
		const delay = forcedDelay ?? Math.min(
			BASE_RECONNECT_DELAY_MS * 2 ** this.reconnectAttempt,
			MAX_RECONNECT_DELAY_MS
		);
		this.reconnectAttempt += 1;
		this.reconnectTimer = setTimeout( ( ) =>
        {
			if ( !this.closedByCaller ) void this.openConnection( );
		}, delay );
	}

	private startHeartbeat( ): void
	{
		this.heartbeatTimer = setInterval( ( ) =>
        {
			this.socket?.send( 'ping' );
		}, HEARTBEAT_INTERVAL_MS );
	}

	private stopHeartbeat( ): void
	{
		if ( this.heartbeatTimer ) clearInterval( this.heartbeatTimer );
		this.heartbeatTimer = null;
	}

	private clearTimers( ): void
	{
		this.stopHeartbeat( );
		if ( this.reconnectTimer ) clearTimeout( this.reconnectTimer );
		this.reconnectTimer = null;
	}

	private setStatus( status: ConnectionStatus ): void
	{
		this.callbacks.onStatusChange( status );
	}
}