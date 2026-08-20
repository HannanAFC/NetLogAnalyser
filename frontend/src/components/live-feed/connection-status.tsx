import type { ConnectionStatus } from '#/features/live-feed/connection';

const STATUS_STYLES: Record< ConnectionStatus, string > =
{
	idle:         'bg-inset text-text-tertiary',
	connecting:   'bg-warning/10 text-warning',
	open:         'bg-success/10 text-success',
	reconnecting: 'bg-warning/10 text-warning',
	error:        'bg-danger/10 text-danger',
	closed:       'bg-surface-card text-text-secondary'
};

const STATUS_LABELS: Record< ConnectionStatus, string > =
{
	idle:         'Idle',
	connecting:   'Connecting…',
	open:         'Live',
	reconnecting: 'Reconnecting…',
	error:        'Connection error',
	closed:       'Disconnected'
};

// A pulsing dot only reads as "actively live" when the connection really
// is open - everything else (including mid-reconnect) should look calmer,
// not falsely urgent.
const PULSE_STATUSES: ConnectionStatus[ ] = [ 'open' ];

interface ConnectionStatusIndicatorProps
{
	status: ConnectionStatus
}

export function ConnectionStatusIndicator( { status }: ConnectionStatusIndicatorProps )
{
	const isPulsing = PULSE_STATUSES.includes( status );

	return (
		<span
			className={ `inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${ STATUS_STYLES[ status ] }` }
		>
			<span
				className={ `h-1.5 w-1.5 rounded-full bg-current ${ isPulsing ? 'animate-breathe' : '' }` }
				aria-hidden="true"
			/>
			{ STATUS_LABELS[ status ] }
		</span>
	);
}