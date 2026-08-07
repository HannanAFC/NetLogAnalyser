import { AnomalyIndicator } from '#/components/live-feed/anomaly-indicator';
import type { LogEntry } from '#/lib/logs/types';
import { useEffect, useState } from 'react';

// Minimal relative-time formatting with no new dependency. If date-fns,
// dayjs, or similar is already used elsewhere in the project, prefer that
// instead of this - this exists only so Phase C doesn't silently pull in
// a library decision that belongs to a separate conversation.
function formatRelativeTime( isoTimestamp: string ): string
{
	const deltaMs = Date.now() - new Date( isoTimestamp ).getTime();
	const deltaSeconds = Math.round( deltaMs / 1000 );

	if ( deltaSeconds < 5 )   return 'just now';
	if ( deltaSeconds < 60 )  return `${ deltaSeconds }s ago`;
	const minutes = Math.round( deltaSeconds / 60 );
	if ( minutes < 60 )       return `${ minutes }m ago`;
	const hours = Math.round( minutes / 60 );
	return `${ hours }h ago`;
}

/** Re-renders on a 30 s cadence so relative timestamps stay live. */
function useRelativeTime( isoTimestamp: string ): string
{
	const [ label, setLabel ] = useState( ( ) => formatRelativeTime( isoTimestamp ) );

	useEffect( ( ) =>
	{
		setLabel( formatRelativeTime( isoTimestamp ) );
		const id = setInterval( ( ) => setLabel( formatRelativeTime( isoTimestamp ) ), 30_000 );
		return ( ) => clearInterval( id );
	}, [ isoTimestamp ] );

	return label;
}

interface LogEntryRowProps {
	entry: LogEntry
}

export function LogEntryRow( { entry }: LogEntryRowProps )
{
	const relativeTime = useRelativeTime( entry.captured_at );

	return (
		<tr className="border-b border-border last:border-0 hover:bg-inset transition-colors duration-150">
			<td className="whitespace-nowrap px-3 py-2 text-xs text-text-secondary">
				{ relativeTime }
			</td>
			<td className="whitespace-nowrap px-3 py-2 font-mono text-sm">
				{ entry.src_ip }:{ entry.src_port }
			</td>
			<td className="whitespace-nowrap px-3 py-2 text-text-secondary">→</td>
			<td className="whitespace-nowrap px-3 py-2 font-mono text-sm">
				{ entry.dst_ip }:{ entry.dst_port }
			</td>
			<td className="whitespace-nowrap px-3 py-2 text-xs">
				{ entry.protocol }
			</td>
			<td className="whitespace-nowrap px-3 py-2 text-right text-xs text-text-secondary tabular-nums">
				{ entry.packet_size_bytes.toLocaleString() } B
			</td>
			<td className="whitespace-nowrap px-3 py-2 text-xs">
				{ entry.src_geo_status === 'resolved' ? entry.src_country_code : entry.src_geo_status.toUpperCase( ) }
			</td>
			<td className="whitespace-nowrap px-3 py-2 text-xs">
				{  entry.dst_geo_status === 'resolved' ? entry.dst_country_code : entry.dst_geo_status.toUpperCase( ) }
			</td>
			<td className="whitespace-nowrap px-3 py-2">
				<AnomalyIndicator score={ entry.anomaly_score } reasons={ entry.anomaly_reasons } />
			</td>
		</tr>
	);
}