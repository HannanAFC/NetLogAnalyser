import type { LogEntry } from '#/lib/logs/types';

export function getLogEntryKey( entry: LogEntry ): string
{
	if ( entry.id !== undefined ) return `id:${ entry.id }`;

	return [
		entry.captured_at,
		entry.src_ip,
		entry.src_port,
		entry.dst_ip,
		entry.dst_port,
		entry.protocol
	].join( '|' );
}