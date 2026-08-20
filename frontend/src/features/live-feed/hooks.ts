import { useEffect, useRef, useState } from 'react';

import { LiveFeedSocket  } from '#/features/live-feed/connection';
import type { ConnectionStatus } from '#/features/live-feed/connection';
import { useInitialLogs } from '#/features/logs/hooks';
import type { LogEntry } from '#/lib/logs/types';

// Bounds memory/render cost for a long-running live feed - old live
// entries just fall off the end rather than growing this list forever.
const MAX_LIVE_ENTRIES = 200;

export function useLiveFeed( )
{
	const initial = useInitialLogs( );
	const [ liveEntries, setLiveEntries ] = useState< LogEntry[ ] >( [ ] );
	const [ connectionStatus, setConnectionStatus ] = useState< ConnectionStatus >( 'idle' );
	const socketRef = useRef< LiveFeedSocket | null >( null );

	useEffect( ( ) =>
	{
		const socket = new LiveFeedSocket(
		{
			onEntries: ( entries ) =>
			{
				setLiveEntries( ( prev ) => [ ...entries, ...prev ].slice( 0, MAX_LIVE_ENTRIES ) );
			},
			onStatusChange: setConnectionStatus
		} );
		socketRef.current = socket;
		void socket.connect( );

		return ( ) =>
		{
			socket.disconnect( );
			socketRef.current = null;
		};
	}, [ ] );

	const entries = [ ...liveEntries, ...initial.entries ].slice( 0, MAX_LIVE_ENTRIES );

	return {
		entries,
		connectionStatus,
		isLoadingInitial: initial.isLoading,
		isInitialError:   initial.isError
	};
}