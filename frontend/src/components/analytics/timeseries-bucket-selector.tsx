import { Button } from '#/components/ui/button';
import { isBucketValid, maxSpanForBucket } from '#/lib/time-range/timeseries-bucket';
import type { TimeBucket } from '#/features/analytics/schemas';

const BUCKET_OPTIONS: { value: TimeBucket; label: string }[ ] =
[
	{ value: 'minute', label: 'Minute' },
	{ value: 'hour',   label: 'Hour' },
	{ value: 'day',    label: 'Day' }
];

function formatDuration( ms: number ): string
{
	const hours = ms / ( 60 * 60 * 1000 );
	if ( hours < 24 ) return `${ Math.floor( hours ) }h`;
	return `${ Math.floor( hours / 24 ) }d`;
}

interface TimeseriesBucketSelectorProps
{
	start:          Date;
	end:            Date;
	bucket:         TimeBucket | undefined;   // undefined = "Auto"
	resolvedBucket: TimeBucket;               // what Auto actually resolved to, for the label
	onChange:       ( bucket: TimeBucket | undefined ) => void;
}

export function TimeseriesBucketSelector(
{
	start,
	end,
	bucket,
	resolvedBucket,
	onChange
}: TimeseriesBucketSelectorProps )
{
	const spanMs = end.getTime( ) - start.getTime( );

	return (
		<div role="group" aria-label="Bucket size" className="flex items-center gap-1">
			<Button
				type="button"
				variant={ bucket === undefined ? 'primary' : 'ghost' }
				onClick={ () => onChange( undefined ) }
			>
				Auto ({ resolvedBucket })
			</Button>

			{ BUCKET_OPTIONS.map( ( option ) =>
            {
				const valid    = isBucketValid( spanMs, option.value );
				const isActive = bucket === option.value;

				return (
					<Button
						key={ option.value }
						type="button"
						variant={ isActive ? 'primary' : 'ghost' }
						disabled={ !valid }
						title={ valid
							? undefined
							: `${ option.label } needs a range under ${ formatDuration( maxSpanForBucket( option.value ) ) } for this many points — this range is too long`
						}
						onClick={ ( ) => onChange( option.value ) }
					>
						{ option.label }
					</Button>
				);
			} ) }
		</div>
	);
}