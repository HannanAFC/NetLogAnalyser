import {
	anomaliesFilterParamsSchema,
	anomaliesParamsSchema,
	directionSchema,
	geoParamsSchema,
	metricSchema,
	timeBucketSchema,
	timeRangeParamsSchema,
	timeseriesParamsSchema,
	topTalkersParamsSchema
} from '#/features/analytics/schemas';
import { describe, expect, it } from 'vitest';

const START = new Date( '2024-01-01T00:00:00Z' );
const END   = new Date( '2024-01-02T00:00:00Z' );

describe( 'timeBucketSchema', ( ) =>
{
	it( 'accepts minute', ( ) =>
	{
		expect( timeBucketSchema.safeParse( 'minute' ).success ).toBe( true );
	} );

	it( 'accepts hour', ( ) =>
	{
		expect( timeBucketSchema.safeParse( 'hour' ).success ).toBe( true );
	} );

	it( 'accepts day', ( ) =>
	{
		expect( timeBucketSchema.safeParse( 'day' ).success ).toBe( true );
	} );

	it( 'rejects an invalid bucket', ( ) =>
	{
		expect( timeBucketSchema.safeParse( 'week' ).success ).toBe( false );
	} );
} );

describe( 'directionSchema', ( ) =>
{
	it( 'accepts src', ( ) =>
	{
		expect( directionSchema.safeParse( 'src' ).success ).toBe( true );
	} );

	it( 'accepts dst', ( ) =>
	{
		expect( directionSchema.safeParse( 'dst' ).success ).toBe( true );
	} );

	it( 'rejects an invalid direction', ( ) =>
	{
		expect( directionSchema.safeParse( 'both' ).success ).toBe( false );
	} );
} );

describe( 'metricSchema', ( ) =>
{
	it( 'accepts packets', ( ) =>
	{
		expect( metricSchema.safeParse( 'packets' ).success ).toBe( true );
	} );

	it( 'accepts bytes', ( ) =>
	{
		expect( metricSchema.safeParse( 'bytes' ).success ).toBe( true );
	} );

	it( 'rejects an invalid metric', ( ) =>
	{
		expect( metricSchema.safeParse( 'connections' ).success ).toBe( false );
	} );
} );

describe( 'timeRangeParamsSchema', ( ) =>
{
	it( 'accepts a valid start and end date', ( ) =>
	{
		const result = timeRangeParamsSchema.safeParse( { start: START, end: END } );

		expect( result.success ).toBe( true );
		if ( result.success )
		{
			expect( result.data.start ).toEqual( START );
			expect( result.data.end ).toEqual( END );
		}
	} );

	it( 'rejects when start is missing', ( ) =>
	{
		expect( timeRangeParamsSchema.safeParse( { end: END } ).success ).toBe( false );
	} );

	it( 'rejects when end is missing', ( ) =>
	{
		expect( timeRangeParamsSchema.safeParse( { start: START } ).success ).toBe( false );
	} );

	it( 'rejects when start is not a Date', ( ) =>
	{
		expect( timeRangeParamsSchema.safeParse( { start: '2024-01-01T00:00:00Z', end: END } ).success ).toBe( false );
	} );
} );

describe( 'timeseriesParamsSchema', ( ) =>
{
	it( 'accepts a range without a bucket', ( ) =>
	{
		expect( timeseriesParamsSchema.safeParse( { start: START, end: END } ).success ).toBe( true );
	} );

	it( 'accepts a valid bucket', ( ) =>
	{
		expect( timeseriesParamsSchema.safeParse( { start: START, end: END, bucket: 'hour' } ).success ).toBe( true );
	} );

	it( 'rejects an invalid bucket', ( ) =>
	{
		expect( timeseriesParamsSchema.safeParse( { start: START, end: END, bucket: 'week' } ).success ).toBe( false );
	} );
} );

describe( 'topTalkersParamsSchema', ( ) =>
{
	it( 'accepts valid params and defaults limit to 10', ( ) =>
	{
		const result = topTalkersParamsSchema.safeParse( { start: START, end: END, direction: 'src', metric: 'packets' } );

		expect( result.success ).toBe( true );
		if ( result.success )
		{
			expect( result.data.limit ).toBe( 10 );
		}
	} );

	it( 'accepts an explicit limit', ( ) =>
	{
		const result = topTalkersParamsSchema.safeParse( { start: START, end: END, direction: 'src', metric: 'packets', limit: 5 } );

		expect( result.success ).toBe( true );
		if ( result.success )
		{
			expect( result.data.limit ).toBe( 5 );
		}
	} );

	it( 'rejects when direction is missing', ( ) =>
	{
		expect( topTalkersParamsSchema.safeParse( { start: START, end: END, metric: 'packets' } ).success ).toBe( false );
	} );

	it( 'rejects when metric is missing', ( ) =>
	{
		expect( topTalkersParamsSchema.safeParse( { start: START, end: END, direction: 'src' } ).success ).toBe( false );
	} );

	it( 'rejects an invalid direction', ( ) =>
	{
		expect( topTalkersParamsSchema.safeParse( { start: START, end: END, direction: 'both', metric: 'packets' } ).success ).toBe( false );
	} );

	it( 'rejects a limit below 1', ( ) =>
	{
		expect( topTalkersParamsSchema.safeParse( { start: START, end: END, direction: 'src', metric: 'packets', limit: 0 } ).success ).toBe( false );
	} );

	it( 'rejects a limit above 100', ( ) =>
	{
		expect( topTalkersParamsSchema.safeParse( { start: START, end: END, direction: 'src', metric: 'packets', limit: 101 } ).success ).toBe( false );
	} );
} );

describe( 'geoParamsSchema', ( ) =>
{
	it( 'accepts valid params and defaults limit to 25', ( ) =>
	{
		const result = geoParamsSchema.safeParse( { start: START, end: END, direction: 'src' } );

		expect( result.success ).toBe( true );
		if ( result.success )
		{
			expect( result.data.limit ).toBe( 25 );
		}
	} );

	it( 'rejects an invalid direction', ( ) =>
	{
		expect( geoParamsSchema.safeParse( { start: START, end: END, direction: 'both' } ).success ).toBe( false );
	} );

	it( 'rejects a limit above 50', ( ) =>
	{
		expect( geoParamsSchema.safeParse( { start: START, end: END, direction: 'src', limit: 51 } ).success ).toBe( false );
	} );
} );

describe( 'anomaliesFilterParamsSchema', ( ) =>
{
	it( 'defaults min_score to 0.5 and limit to 25', ( ) =>
	{
		const result = anomaliesFilterParamsSchema.safeParse( { start: START, end: END } );

		expect( result.success ).toBe( true );
		if ( result.success )
		{
			expect( result.data.min_score ).toBe( 0.5 );
			expect( result.data.limit ).toBe( 25 );
		}
	} );

	it( 'accepts explicit min_score and limit', ( ) =>
	{
		const result = anomaliesFilterParamsSchema.safeParse( { start: START, end: END, min_score: 0.8, limit: 50 } );

		expect( result.success ).toBe( true );
		if ( result.success )
		{
			expect( result.data.min_score ).toBe( 0.8 );
			expect( result.data.limit ).toBe( 50 );
		}
	} );

	it( 'rejects a min_score below 0', ( ) =>
	{
		expect( anomaliesFilterParamsSchema.safeParse( { start: START, end: END, min_score: -0.1 } ).success ).toBe( false );
	} );

	it( 'rejects a min_score above 1', ( ) =>
	{
		expect( anomaliesFilterParamsSchema.safeParse( { start: START, end: END, min_score: 1.1 } ).success ).toBe( false );
	} );

	it( 'rejects a limit below 1', ( ) =>
	{
		expect( anomaliesFilterParamsSchema.safeParse( { start: START, end: END, limit: 0 } ).success ).toBe( false );
	} );
} );

describe( 'anomaliesParamsSchema', ( ) =>
{
	it( 'accepts params without a cursor', ( ) =>
	{
		const result = anomaliesParamsSchema.safeParse( { start: START, end: END } );

		expect( result.success ).toBe( true );
		if ( result.success )
		{
			expect( result.data.cursor ).toBeUndefined( );
		}
	} );

	it( 'accepts a valid cursor', ( ) =>
	{
		const result = anomaliesParamsSchema.safeParse( { start: START, end: END, cursor: 'abc123' } );

		expect( result.success ).toBe( true );
		if ( result.success )
		{
			expect( result.data.cursor ).toBe( 'abc123' );
		}
	} );

	it( 'rejects an empty cursor string', ( ) =>
	{
		expect( anomaliesParamsSchema.safeParse( { start: START, end: END, cursor: '' } ).success ).toBe( false );
	} );
} );
