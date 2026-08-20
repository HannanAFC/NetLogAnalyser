import type { TimeBucket } from '#/features/analytics/schemas';

export const MAX_POINTS = 1000;

const HOUR_MS = 60 * 60 * 1000;
const DAY_MS  = 24 * HOUR_MS;

const BUCKET_SECONDS: Record< TimeBucket, number > =
{
	minute: 60,
	hour:   3600,
	day:    86400
};

export function autoBucket( spanMs: number ): TimeBucket
{
	if ( spanMs <= 2 * HOUR_MS ) return 'minute';
	if ( spanMs <= 7 * DAY_MS ) return 'hour';
	return 'day';
}

export function pointCount( spanMs: number, bucket: TimeBucket ): number
{
	return spanMs / 1000 / BUCKET_SECONDS[ bucket ];
}

export function isBucketValid( spanMs: number, bucket: TimeBucket ): boolean
{
	return pointCount( spanMs, bucket ) <= MAX_POINTS;
}

export function maxSpanForBucket( bucket: TimeBucket ): number
{
	return MAX_POINTS * BUCKET_SECONDS[ bucket ] * 1000;
}

export interface ResolvedBucket
{
	bucket:     TimeBucket;
	requested:  TimeBucket | undefined;
	wasClamped: boolean;
}

export function resolveBucket( start: Date, end: Date, requested?: TimeBucket ): ResolvedBucket
{
	const spanMs = end.getTime( ) - start.getTime( );

	if ( requested && isBucketValid( spanMs, requested ) )
	{
		return { bucket: requested, requested, wasClamped: false };
	}

	return { bucket: autoBucket( spanMs ), requested, wasClamped: Boolean( requested ) };
}