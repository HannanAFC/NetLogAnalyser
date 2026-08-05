import { z } from 'zod';

// Runtime-validates every message off the wire before it touches React
// state. Unlike a REST response (typed via axios generics, but never
// actually checked at runtime either), a WebSocket message is server data
// arriving completely outside the request/response type-safety net - if
// the backend's broadcast shape (websocket/pubsub.py's _BROADCAST_FIELDS)
// ever drifts from this, we want a dropped message, not a crash or silent
// garbage in the feed.

const anomalyReasonSchema = z.object(
{
	name:   z.string( ),
	score:  z.number( ),
	detail: z.string( ).nullable( )
} );

const logEntryPublicSchema = z.object(
{
	id:                z.number( ).optional( ),
	src_ip:            z.string( ),
	dst_ip:            z.string( ),
	src_port:          z.number( ),
	dst_port:          z.number( ),
	protocol:          z.enum( [ 'TCP', 'UDP', 'ICMP', 'OTHER' ] ),
	packet_size_bytes: z.number( ),
	flags:             z.string( ).nullable( ),
	country_code:      z.string( ).nullable( ),
	anomaly_score:     z.number( ),
	anomaly_reasons:   z.array( anomalyReasonSchema ),
	captured_at:       z.string( )
} );

export const logEntryBatchMessageSchema = z.object(
{
	type: z.literal( 'log_entry_batch' ),
	data: z.array( logEntryPublicSchema )
} );

export type LogEntryBatchMessage = z.infer< typeof logEntryBatchMessageSchema >;