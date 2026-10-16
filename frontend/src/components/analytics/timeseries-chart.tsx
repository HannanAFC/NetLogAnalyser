import { useMemo } from 'react';
import { scaleLinear, scaleUtc } from 'd3-scale';
import { defineChart, dot, lineY } from '@tanstack/charts';
import { tooltip } from '@tanstack/charts/tooltip';
import { Chart } from '@tanstack/react-charts';

import { useTimeseries } from '#/features/analytics/hooks';
import type { TimeBucket, TimeRangeParams } from '#/features/analytics/schemas';
import { Card, CardDescription } from '../ui/card';
import { decorative } from '@tanstack/charts/mark/decorative';
import { formatApiKeyDate } from '#/lib/utils';

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
			marks:
			[
				decorative(
					lineY(
						points,
						{
							x: 'ts',
							y: 'count'
						}
					)
				),
				dot(
					points,
					{
						id: 'timeseries',
						x: 'ts',
						y: 'count',
						states:
						[
							{
								when: { focus: 'primary' },
								style:
								{
									r: 7,
									stroke: 'Canvas',
									strokeWidth: 2
								},
								transition:
								{
									type: 'tween',
									duration: 300,
									easing: 'ease-out'
								}
							}
						]
					}
				)
			],
			scales:
			{
				x: { scale: scaleUtc, grid: true },
				y: { scale: scaleLinear, nice: true, grid: true, axis: { label: 'Packets' } }
			},
			tooltip:
			{
				anchor: 'point',
				placement: [ 'top', 'right', 'left', 'bottom' ],
				use: tooltip,
				items:
				[
					{
						channel: 'y',
						label: 'Packet count:',
						text: ( point ) => point.datum.count
					},
					{
						channel: 'x',
						label: 'Time:',
						text: ( point ) => formatApiKeyDate( point.datum.ts.toISOString( ) )
					}
				]
			}
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