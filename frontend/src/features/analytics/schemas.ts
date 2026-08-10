import { z } from 'zod';

// Enums

export const timeBucketSchema = z.enum( [ 'minute', 'hour', 'day' ] );
export type TimeBucket = z.infer< typeof timeBucketSchema >;

export const directionSchema = z.enum( [ 'src', 'dst' ] );
export type Direction = z.infer< typeof directionSchema >;

export const metricSchema = z.enum( [ 'packets', 'bytes' ] );
export type Metric = z.infer< typeof metricSchema >;

export const protocolSchema = z.enum( [ 'TCP', 'UDP', 'ICMP', 'OTHER' ] );
export type Protocol = z.infer< typeof protocolSchema >;

export const geoStatusSchema = z.enum( [ 'RESOLVED', 'PRIVATE', 'UNRESOLVED', 'UNAVAILABLE' ] );
export type GeoStatus = z.infer< typeof geoStatusSchema >;


export const timeRangeParamsSchema = z.object(
{
	start: z.date( ),
	end:   z.date( )
} );
export type TimeRangeParams = z.infer< typeof timeRangeParamsSchema >;


export const summaryParamsSchema = timeRangeParamsSchema;
export type SummaryParams = z.infer< typeof summaryParamsSchema >;


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


export const protocolsParamsSchema = timeRangeParamsSchema;
export type ProtocolsParams = z.infer< typeof protocolsParamsSchema >;


export const geoParamsSchema = timeRangeParamsSchema.extend(
{
	direction: directionSchema,
	limit:     z.number ().min( 1 ).max( 50 ).default( 25 )
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
	cursor: z.string ().min( 1 ).optional( )
} );
export type AnomaliesParams = z.infer<typeof anomaliesParamsSchema>;