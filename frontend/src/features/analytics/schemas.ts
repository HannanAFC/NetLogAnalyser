import { z } from 'zod';
import {
	DIRECTION_VALUES,
	METRIC_VALUES,
	TIME_BUCKET_VALUES
} from '#/lib/analytics/types';

export const timeBucketSchema = z.enum( TIME_BUCKET_VALUES );
export const directionSchema  = z.enum( DIRECTION_VALUES );
export const metricSchema     = z.enum( METRIC_VALUES );

export const timeRangeParamsSchema = z.object(
{
	start: z.date( ),
	end:   z.date( )
} );

export const timeseriesParamsSchema = timeRangeParamsSchema.extend(
{
	bucket: timeBucketSchema.optional( )
} );
export type TimeseriesParams = z.infer< typeof timeseriesParamsSchema >;

export const topTalkersParamsSchema = timeRangeParamsSchema.extend(
{
	direction: directionSchema,
	metric:    metricSchema,
	limit:     z.number( ).min( 1 ).max( 100 ).default( 10 )
} );
export type TopTalkersParams = z.infer< typeof topTalkersParamsSchema >;

export const geoParamsSchema = timeRangeParamsSchema.extend(
{
	direction: directionSchema,
	limit:     z.number( ).min( 1 ).max( 50 ).default( 25 )
} );
export type GeoParams = z.infer< typeof geoParamsSchema >;

export const anomaliesFilterParamsSchema = timeRangeParamsSchema.extend(
{
	min_score: z.number( ).min( 0 ).max( 1 ).default( 0.5 ),
	limit:     z.number( ).min( 1 ).max( 100 ).default( 25 )
} );
export type AnomaliesFilterParams = z.infer< typeof anomaliesFilterParamsSchema >;

export const anomaliesParamsSchema = anomaliesFilterParamsSchema.extend(
{
	cursor: z.string( ).min( 1 ).optional( )
} );
export type AnomaliesParams = z.infer< typeof anomaliesParamsSchema >;

// re-exports for convenience and consistency

export type {
	TimeRangeParams,
	Direction,
	TimeBucket,
	Metric
} from '#/lib/analytics/types';