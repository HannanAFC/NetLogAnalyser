import { z } from 'zod';

// Used by the log-history route's validateSearch (Phase D) so pagination
// state is bookmarkable/shareable via the URL, e.g. /logs?cursor=abc123.
// `limit` is deliberately not part of this - page size is an internal
// hook default, not user-controlled URL state, unless a page-size
// selector gets built later.
export const logsSearchSchema = z.object(
{
	cursor: z.string( ).min( 1 ).optional( )
} );

export type LogsSearch = z.infer< typeof logsSearchSchema >;