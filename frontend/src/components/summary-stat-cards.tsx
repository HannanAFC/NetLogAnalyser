import { useSummary } from '#/features/analytics/hooks';
import { Card } from '#/components/ui/card';
import { BodySm, StatNumber } from '#/components/ui/heading';
import type { TimeRangeParams } from '#/features/analytics/schemas';

interface SummaryStatCardsProps
{
	range: TimeRangeParams;
}

export function SummaryStatCards( { range }: SummaryStatCardsProps )
{
	const { data, isPending, isError } = useSummary( range );

	if ( isPending )
	{
		return (
			<div className="grid grid-cols-2 gap-4 md:grid-cols-5">
				{ Array.from( { length: 5 } ).map( ( _, i ) => (
					<Card key={ i } className="h-20 animate-pulse" >
                        <></>
                    </Card>
				) ) }
			</div>
		);
	}

	if ( isError )
	{
		return <p className="text-text-secondary text-sm">Couldn't load summary for this range.</p>;
	}

	const stats = [
		{ label: 'Total packets',       value: data.total_packets.toLocaleString() },
		{ label: 'Unique sources',      value: data.unique_src_ips.toLocaleString() },
		{ label: 'Unique destinations', value: data.unique_dst_ips.toLocaleString() },
		{ label: 'Avg anomaly score',   value: data.avg_anomaly_score.toFixed( 2 ) },
		{ label: 'Total bytes',         value: data.total_bytes.toLocaleString() }
	];

	return (
		<div className="grid grid-cols-2 gap-4 md:grid-cols-5">
			{ stats.map( ( stat ) => (
				<Card key={ stat.label }>
					<StatNumber>{ stat.value }</StatNumber>
					<BodySm>{ stat.label }</BodySm>
				</Card>
			) ) }
		</div>
	);
}