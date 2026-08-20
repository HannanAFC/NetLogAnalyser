import type { AnomalyReason } from '#/lib/logs/types';
import { Badge  } from '../ui/badge';
import type { BadgeVariant } from '../ui/badge';

type Severity = 'none' | 'low' | 'medium' | 'high';

function severityFor( score: number ): Severity
{
	if ( score <= 0 )   return 'none';
	if ( score < 0.3 )  return 'low';
	if ( score < 0.7 )  return 'medium';
	return 'high';
}

const SEVERITY_STYLES: Record< Severity, BadgeVariant > =
{
	none:   'default',
	low:    'low',
	medium: 'medium',
	high:   'high'
};

const SEVERITY_LABELS: Record< Severity, string > =
{
	none:   'Normal',
	low:    'Low',
	medium: 'Medium',
	high:   'High'
};

interface AnomalyIndicatorProps
{
	score:   number
	reasons: AnomalyReason[ ]
}

export function AnomalyIndicator( { score, reasons }: AnomalyIndicatorProps )
{
	const severity = severityFor( score );
	const title = reasons.length > 0
		? reasons.map( ( r ) => `${ r.name } (${ r.score.toFixed( 2 ) })${ r.detail ? `: ${ r.detail }` : '' }` ).join( '\n' )
		: undefined;

	return (
        <Badge
            variant={ SEVERITY_STYLES[ severity ] }
            className='inline-flex gap-1'
            title={ title }
        >
            { SEVERITY_LABELS[ severity ] }
			{ severity !== 'none' && (
				<span className="tabular-nums opacity-75">{ score.toFixed( 2 ) }</span>
			) }
        </Badge>
	);
}