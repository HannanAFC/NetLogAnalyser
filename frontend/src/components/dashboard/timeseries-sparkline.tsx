// components/dashboard/timeseries-sparkline.tsx
import { useMemo } from 'react';
import { isAxiosError } from 'axios';
import { scaleLinear, scaleUtc } from 'd3-scale';
import { defineChart, lineY } from '@tanstack/charts';
import { Chart } from '@tanstack/react-charts';

import { useTimeseries } from '#/features/analytics/hooks';
import { resolveBucket } from '#/lib/time-range/timeseries-bucket';
import type { TimeRangeParams } from '#/features/analytics/schemas';
import { Card, CardDescription } from '../ui/card';

interface TimeseriesSparklineProps
{
	range: TimeRangeParams;
}

export function TimeseriesSparkline( { range }: TimeseriesSparklineProps )
{
	const { bucket } = useMemo(
		( ) => resolveBucket( range.start, range.end ),
		[ range.start, range.end ]
	);

	const { data, isPending, isError, error } = useTimeseries( { ...range, bucket } );
    const points = ( data?.points ?? [ ] ).map( ( p ) => ( { ts: new Date( p.ts ), count: p.count } ) );
	const definition = useMemo( ( ) =>
    {
		return defineChart(
        {
			marks: [ lineY( points, { id: 'sparkline', x: 'ts', y: 'count' } ) ],
			x: { scale: scaleUtc },
			y: { scale: scaleLinear }
		} );
	}, [ data ] );

	if ( isPending )
	{
		return <div className="h-75 shadow-card border-border border bg-card animate-pulse rounded-lg" aria-hidden="true" />;
	}
	else if ( isError )
	{
		if ( isAxiosError( error ) && error.response?.status === 422 )
		{
			console.warn( 'Bucket validation failed: ', error.response.data );
		}

		return (
            <Card variant='critical'>
                <CardDescription variant='critical'>
                    Couldn't load the chart for this range.
                </CardDescription>
            </Card>
		);
	}
	else if ( points.length <= 1 )
    {
        return (
            <Card variant='info'>
                <CardDescription variant='info'>
                    Not enough data points to load the chart, try reducing the time range.
                </CardDescription>
            </Card>
        );
	}
	else
	{
		return (
			<Card>
				<Chart definition={ definition } height={ 300 } ariaLabel="Packet volume over the selected range" />
			</Card>
		);
	}
}