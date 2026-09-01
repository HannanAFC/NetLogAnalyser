import { useSummary } from '#/features/analytics/hooks';
import { Card, CardDescription } from '#/components/ui/card';
import { BodySm, StatNumber } from '#/components/ui/heading';
import type { TimeRangeParams } from '#/features/analytics/schemas';
import { formatLargeNumber } from '#/lib/utils';

interface SummaryStatCardsProps
{
	range: TimeRangeParams;
}

export function SummaryStatCards( { range }: SummaryStatCardsProps )
{
	const { data, isPending, isError } = useSummary( range );

	if ( isError )
	{
		return (
			<Card variant='critical'>
				<CardDescription variant='critical'>
					Couldn't load summary for this range.
				</CardDescription>
			</Card>
		);
	}
	else if ( isPending )
	{
		return (
			<div className="grid grid-cols-2 gap-4 md:grid-cols-3">
				{ Array.from( { length: 6 } ).map( ( _, i ) =>
				(
					<Card key={ i } className="h-28 animate-pulse" >
						<></>
					</Card>
				) ) }
			</div>
		);
	}

	const stats = [
		{ label: 'Total packets',        displayValue: formatLargeNumber( data.total_packets ), value: data.total_packets.toLocaleString( ) },
		{ label: 'Unique sources',       displayValue: data.unique_src_ips.toLocaleString( ), value: data.unique_src_ips.toLocaleString( ) },
		{ label: 'Unique destinations',  displayValue: data.unique_dst_ips.toLocaleString( ), value: data.unique_dst_ips.toLocaleString( ) },
		{ label: 'Avg anomaly score',    displayValue: data.avg_anomaly_score.toFixed( 2 ), value: data.avg_anomaly_score.toFixed( 2 ) },
		{ label: 'Total bytes',          displayValue: formatLargeNumber( data.total_bytes ), value: data.total_bytes.toLocaleString( ) },
		{ label: 'High level anomalies', displayValue: formatLargeNumber( data.high_anomaly_count ), value: data.high_anomaly_count.toLocaleString( ) }
	];

	return (
		<div className="grid grid-cols-2 gap-4 md:grid-cols-3">
			{ stats.map( ( stat ) =>
			(
				<Card key={ stat.label }>
					<StatNumber title={ stat.value }>{ stat.displayValue }</StatNumber>
					<BodySm>{ stat.label }</BodySm>
				</Card>
			) ) }
		</div>
	);
}