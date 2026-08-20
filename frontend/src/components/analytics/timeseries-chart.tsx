import { useMemo } from 'react';
import { scaleLinear, scaleUtc } from 'd3-scale';
import { defineChart, lineY } from '@tanstack/charts';
import { tooltip } from '@tanstack/charts/tooltip';
import { Chart } from '@tanstack/react-charts';

import { useTimeseries } from '#/features/analytics/hooks';
import type { TimeBucket, TimeRangeParams } from '#/features/analytics/schemas';
import { Card, CardDescription } from '../ui/card';

interface TimeseriesChartProps
{
	range:  TimeRangeParams;
	bucket: TimeBucket;
}

export function TimeseriesChart( { range, bucket }: TimeseriesChartProps )
{
	const { data, isPending, isError } = useTimeseries( { ...range, bucket } );
	const points = ( data?.points ?? [] ).map( ( p ) => ( { ts: new Date( p.ts ), count: p.count } ) );

	const definition = useMemo( ( ) =>
    {
		return defineChart(
        {
			marks: [ lineY( points, { id: 'timeseries', x: 'ts', y: 'count', points: true } ) ],
			x: { scale: scaleUtc, grid: true },
			y: { scale: scaleLinear, nice: true, grid: true, axis: { label: 'Packets' } },
			tooltip
		} );
	}, [ data ] );

	if ( isPending ) return <div className="h-70 animate-pulse" aria-hidden="true" />;
	if ( isError )   return <p className="text-text-secondary text-sm">Couldn't load the chart for this range.</p>;

	if ( points.length > 1 )
	{
		return (
			<Card>
				<Chart definition={ definition } height={ 280 } ariaLabel="Packet count over time" />
			</Card>
		);
	}
	else
	{
		return (
			<Card variant='medium'>
				<CardDescription variant='medium'>
					Timeseries not available for the current time range.
				</CardDescription>
			</Card>
		);
	};
}