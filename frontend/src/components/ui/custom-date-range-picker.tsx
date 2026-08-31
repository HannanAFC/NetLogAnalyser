import { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import {
	Calendar,
	ChevronLeft,
	ChevronRight,
	ChevronDown,
	Clock
} from 'lucide-react';
import { Button } from '#/components/ui/button';
import { cn } from '#/lib/utils';
import type { TimeRangePreset } from '#/lib/time-range/schema';

const MONTH_NAMES =
[
	'January', 'February', 'March', 'April', 'May', 'June',
	'July', 'August', 'September', 'October', 'November', 'December'
] as const;

const DAY_HEADERS = [ 'Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa' ] as const;

function daysInMonth( year: number, month: number ): number
{
	return new Date( year, month + 1, 0 ).getDate( );
}

function firstDayOfMonth( year: number, month: number ): number
{
	return new Date( year, month, 1 ).getDay( );
}

function isSameDay( a: Date, b: Date ): boolean
{
	return (
		a.getFullYear( ) === b.getFullYear( ) &&
		a.getMonth( ) === b.getMonth( ) &&
		a.getDate( ) === b.getDate( )
	);
}

function toLocalDateOnly( date: Date ): Date
{
	return new Date( date.getFullYear( ), date.getMonth( ), date.getDate( ) );
}

function dateToTime( date: Date ): number
{
	return toLocalDateOnly( date ).getTime( );
}

function formatDateDisplay( date: Date ): string
{
	const y = date.getFullYear( );
	const m = String( date.getMonth( ) + 1 ).padStart( 2, '0' );
	const d = String( date.getDate( ) ).padStart( 2, '0' );
	return `${ y }-${ m }-${ d }`;
}

function formatTimeDisplay( date: Date ): string
{
	const h  = String( date.getHours( ) ).padStart( 2, '0' );
	const mi = String( date.getMinutes( ) ).padStart( 2, '0' );
	return `${ h }:${ mi }`;
}

export interface DateRangeValue
{
	start:  Date;
	end:    Date;
}

interface CustomDateRangePickerProps
{
	value:     DateRangeValue | null;
	preset:    TimeRangePreset | null;
	setPreset:      ( preset: TimeRangePreset ) => void;
	setCustomRange: ( start: Date, end: Date ) => void;
	className?: string;
}

type QuickPreset = { label: string; value: TimeRangePreset };

const QUICK_PRESETS: QuickPreset[ ] =
[
	{
		label: 'Last 15 min',
		value: '15m'
	},
	{
		label: 'Last hour',
		value: '1h'
	},
	{
		label: 'Last 6 hours',
		value: '6h'
	},
	{
		label: 'Last 12 hours',
		value: '12h'
	},
	{
		label: 'Last 24 hours',
		value: '24h'
	},
	{
		label: 'Last 7 days',
		value: '7d'
	},
	{
		label: 'Last 15 days',
		value: '15d'
	},
	{
		label: 'Last 30 days',
		value: '30d'
	}
];

type CellRole = 'range-start' | 'range-end' | 'in-range' | 'none';

interface CalendarMonthProps
{
	year:          number;
	month:         number;
	rangeStart:    Date | null;
	rangeEnd:      Date | null;
	onDateClick:   ( date: Date ) => void;
	onDateEnter:   ( date: Date ) => void;
	onDateLeave:   ( ) => void;
	onPrevMonth:   ( ) => void;
	onNextMonth:   ( ) => void;
	maxDate?:      Date;
}

function CalendarMonth(
{
	year,
	month,
	rangeStart,
	rangeEnd,
	onDateClick,
	onDateEnter,
	onDateLeave,
	onPrevMonth,
	onNextMonth,
	maxDate
}: CalendarMonthProps )
{
	const today = useMemo( ( ) => toLocalDateOnly( new Date( ) ), [ ] );
	const total = daysInMonth( year, month );
	const off   = firstDayOfMonth( year, month );

	const cells: ( Date | null )[ ] = [ ];
	for ( let i = 0; i < off; i++ ) cells.push( null );
	for ( let d = 1; d <= total; d++ ) cells.push( new Date( year, month, d ) );
	while ( cells.length < 42 ) cells.push( null );

	const lo = rangeStart && rangeEnd
		? Math.min( dateToTime( rangeStart ), dateToTime( rangeEnd ) )
		: rangeStart ? dateToTime( rangeStart ) : null;
	const hi = rangeStart && rangeEnd
		? Math.max( dateToTime( rangeStart ), dateToTime( rangeEnd ) )
		: rangeEnd ? dateToTime( rangeEnd ) : null;

	function getCellRole( date: Date ): CellRole
	{
		if ( !lo ) return 'none';
		const t = toLocalDateOnly( date ).getTime( );

		if ( lo === hi && t === lo ) return 'range-start';

		if ( t === lo ) return 'range-start';
		if ( hi !== null && t === hi ) return 'range-end';
		if ( hi !== null && t > lo && t < hi ) return 'in-range';

		return 'none';
	}

	return (
		<div className="flex flex-col gap-0.5">
			<div className="flex items-center justify-between px-1 mb-0.5">
				<Button
					type="button"
					onClick={ onPrevMonth }
					variant='ghost'
					aria-label="Previous month"
				>
					<ChevronLeft size={ 20 } />
				</Button>
				<span className="text-[13px] font-medium text-text-primary tabular-nums">
					{ MONTH_NAMES[ month ] } { year }
				</span>
				<Button
					type="button"
					onClick={ onNextMonth }
					variant='ghost'
					aria-label="Next month"
				>
					<ChevronRight size={ 20 } />
				</Button>
			</div>

			<div className="grid grid-cols-7">
				{ DAY_HEADERS.map( ( day ) => (
					<div
						key={ day }
						className="h-7 flex items-center justify-center text-[10px] font-mono font-medium text-text-tertiary tracking-wider"
					>
						{ day }
					</div>
				) ) }
			</div>

			<div className="grid grid-cols-7 gap-y-1">
				{ cells.map( ( date, idx ) =>
				{
					if ( !date )
						return <div key={ `empty-${ idx }` } className="h-8" />;

					const d        = toLocalDateOnly( date );
					const role     = getCellRole( date );
					const isToday  = isSameDay( d, today );
					const isFuture = maxDate ? d > toLocalDateOnly( maxDate ) : false;

					const isRangeEdge  = role === 'range-start' || role === 'range-end';
					const isInRange    = role === 'in-range';
					const isSingleDay  = lo !== null && lo === hi;

					return (
						<button
							type="button"
							key={ date.toISOString( ) }
							disabled={ isFuture }
							onClick={ ( ) => onDateClick( date ) }
							onMouseEnter={ ( ) => onDateEnter( date ) }
							onMouseLeave={ onDateLeave }
							className={ cn(
								'h-8 w-full flex items-center justify-center text-[13px]',
								'transition-all duration-150',
								'focus:outline-none cursor-pointer active:scale-95',

								isFuture && 'text-text-tertiary/30 cursor-default',

								!isFuture && isRangeEdge && 'bg-accent text-ink font-semibold',
								!isFuture && isSingleDay && isRangeEdge && 'rounded-md',
								!isFuture && !isSingleDay && role === 'range-start' && 'rounded-l-md',
								!isFuture && !isSingleDay && role === 'range-end' && 'rounded-r-md',

								!isFuture && isInRange && 'bg-accent/15 text-text-primary',

								!isFuture && !isRangeEdge && !isInRange && isToday && 'text-accent font-semibold',

								!isFuture && !isRangeEdge && !isInRange && !isToday && 'text-text-primary hover:bg-card-2 rounded-sm'
							) }
						>
							{ date.getDate( ) }
						</button>
					);
				} ) }
			</div>
		</div>
	);
}

export function CustomDateRangePicker(
{
	value,
	preset,
	setPreset,
	setCustomRange,
	className
}: CustomDateRangePickerProps )
{
	const [ open, setOpen ]                 = useState( false );
	const [ viewYear, setViewYear ]         = useState( new Date( ).getFullYear( ) );
	const [ viewMonth, setViewMonth ]       = useState( new Date( ).getMonth( ) );
	const [ pickingStart, setPickingStart ] = useState<Date | null>(
		value ? value.start : null
	);
	const [ pickingEnd, setPickingEnd ]     = useState<Date | null>(
		value ? value.end : null
	);
	const [ hoverDate, setHoverDate ]       = useState<Date | null>( null );
	const [ startTime, setStartTime ]       = useState(
		value ? formatTimeDisplay( value.start ) : '00:00'
	);
	const [ endTime, setEndTime ]           = useState(
		value ? formatTimeDisplay( value.end ) : '23:59'
	);

	const containerRef = useRef<HTMLDivElement>( null );

	useEffect( ( ) =>
	{
		if ( !open ) return;

		function handleClick( e: MouseEvent )
		{
			if (
				containerRef.current &&
				!containerRef.current.contains( e.target as Node )
			)
				setOpen( false );
		}

		document.addEventListener( 'mousedown', handleClick );
		return ( ) => document.removeEventListener( 'mousedown', handleClick );
	}, [ open ] );

	useEffect( ( ) =>
	{
		if ( !open ) return;
		function handleKey( e: KeyboardEvent )
		{
			if ( e.key === 'Escape' ) setOpen( false );
		}
		document.addEventListener( 'keydown', handleKey );
		return ( ) => document.removeEventListener( 'keydown', handleKey );
	}, [ open ] );

	useEffect( ( ) =>
	{
		if ( value )
		{
			setPickingStart( value.start );
			setPickingEnd( value.end );
			setStartTime( formatTimeDisplay( value.start ) );
			setEndTime( formatTimeDisplay( value.end ) );
		}
	}, [ value ] );

	const now = useMemo( ( ) => new Date( ), [ ] );

	const handleDateClick = useCallback( ( date: Date ) =>
	{
		if ( date > now ) return;
		if ( !pickingStart || pickingEnd )
		{
			setPickingStart( date );
			setPickingEnd( null );
		}
		else
		{
			if ( date < pickingStart )
			{
				setPickingStart( date );
				setPickingEnd( pickingStart );
			}
			else
			{
				setPickingEnd( date );
			}
		}
	}, [ pickingStart, pickingEnd ] );

	function handlePrevMonth( )
	{
		if ( viewMonth === 0 )
		{
			setViewYear( viewYear - 1 );
			setViewMonth( 11 );
		}
		else
		{
			setViewMonth( viewMonth - 1 );
		}
	}

	function handleNextMonth( )
	{
		if ( viewMonth === 11 )
		{
			setViewYear( viewYear + 1 );
			setViewMonth( 0 );
		}
		else
		{
			setViewMonth( viewMonth + 1 );
		}
	}

	function applyTimeToDate( date: Date, timeStr: string ): Date
	{
		const [ h, m ] = timeStr.split( ':' ).map( Number );
		const result   = new Date( date );
		result.setHours( h || 0, m || 0, 0, 0 );
		return result;
	}

	function handleApply( )
	{
		if ( !pickingStart ) return;

		const endDate = pickingEnd ?? pickingStart;

		let start = applyTimeToDate( pickingStart, startTime );
		let end   = applyTimeToDate( endDate, endTime );

		if ( start > now ) start = now;
		if ( end > now ) end = now;

		if ( start > end )
		{
			const tmp = start;
			start = end;
			end   = tmp;
		}

		setCustomRange( start, end );
		setOpen( false );
	}

	function handleCancel( )
	{
		if ( value )
		{
			setPickingStart( value.start );
			setPickingEnd( value.end );
			setStartTime( formatTimeDisplay( value.start ) );
			setEndTime( formatTimeDisplay( value.end ) );
		}
		setOpen( false );
	}

	function handleQuickPreset( value: TimeRangePreset )
	{
		setPreset( value );
		setOpen( false );
	}

	function handleTimeChange(
		timeStr: string,
		setter: ( t: string ) => void
	)
	{
		if ( /^\d{0,2}:?\d{0,2}$/.test( timeStr ) )
			setter( timeStr );
	}

	const displayText = value
		? `${ formatDateDisplay( value.start ) } ${ formatTimeDisplay( value.start ) }  —  ${ formatDateDisplay( value.end ) } ${ formatTimeDisplay( value.end ) }`
		:  ( preset ? `(${ preset }) Select date range...` : 'Select date range...' );

	const visualStart = pickingStart;
	const visualEnd   = pickingEnd ?? hoverDate;

	return (
		<div ref={ containerRef } className={ cn( 'relative inline-block', className ) }>
			<Button
				type="button"
				onClick={ ( ) => setOpen( !open ) }
				className={ cn(
					'inline-flex items-center gap-2 px-4 py-2.25 text-xs',
					'font-mono font-medium tracking-[0.01em]',
					'rounded-md border border-border-hi',
					'bg-transparent text-text-secondary',
					'hover:text-text-primary hover:border-border-hi/50',
					'transition-[color,border-color] duration-150',
					open && 'border-accent text-text-primary'
				) }
			>
				<Calendar size={ 14 } className="text-text-tertiary" />
				<span className={ cn( !value && 'text-text-tertiary' ) }>
					{ displayText }
				</span>
				<ChevronDown
					size={ 12 }
					className={ cn(
						'text-text-tertiary transition-transform duration-150',
						open && 'rotate-180'
					) }
				/>
			</Button>

			<div
				className={ cn(
					'absolute left-0 top-full mt-2 z-50 min-w-sm',
					'rounded-lg border border-border bg-card',
					'shadow-soft p-3',
					'flex flex-col gap-3',
					'max-w-full md:w-md',
					'transition-all duration-150 ease-out origin-top-left',
					open
						? 'opacity-100 scale-100'
						: 'opacity-0 scale-95 pointer-events-none'
				) }
			>
				<div className="grid grid-cols-2 gap-1">
					{ QUICK_PRESETS.map( ( preset ) => (
						<Button
							key={ preset.label }
							type="button"
							onClick={ ( ) => handleQuickPreset( preset.value ) }
							variant='ghost'
						>
							{ preset.label }
						</Button>
					) ) }
				</div>

				<div className="border-t border-border" />

				<CalendarMonth
					year={ viewYear }
					month={ viewMonth }
					rangeStart={ visualStart }
					rangeEnd={ visualEnd }
					onDateClick={ handleDateClick }
					onDateEnter={ setHoverDate }
					onDateLeave={ ( ) => setHoverDate( null ) }
					onPrevMonth={ handlePrevMonth }
					onNextMonth={ handleNextMonth }
					maxDate={ now }
				/>

				<div className="border-t border-border" />

				<div className="flex items-center gap-3">
					<div className="flex items-center gap-1.5">
						<Clock size={ 12 } className="text-text-tertiary" />
						<span className="text-[10px] font-mono text-text-tertiary tracking-wider uppercase">Start</span>
						<input
							type="text"
							value={ startTime }
							onChange={ ( e ) => handleTimeChange( e.target.value, setStartTime ) }
							placeholder="HH:MM"
							maxLength={ 5 }
							className={ cn(
								'w-14 px-1.5 py-0.5 rounded-sm text-[11px] text-center',
								'font-mono tabular-nums',
								'bg-inset border border-border text-text-primary',
								'placeholder:text-text-tertiary',
								'focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/25',
								'transition-[border-color,box-shadow] duration-150'
							) }
						/>
					</div>
					<span className="text-text-tertiary text-xs">—</span>
					<div className="flex items-center gap-1.5">
						<Clock size={ 12 } className="text-text-tertiary" />
						<span className="text-[10px] font-mono text-text-tertiary tracking-wider uppercase">End</span>
						<input
							type="text"
							value={ endTime }
							onChange={ ( e ) => handleTimeChange( e.target.value, setEndTime ) }
							placeholder="HH:MM"
							maxLength={ 5 }
							className={ cn(
								'w-14 px-1.5 py-0.5 rounded-sm text-[11px] text-center',
								'font-mono tabular-nums',
								'bg-inset border border-border text-text-primary',
								'placeholder:text-text-tertiary',
								'focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/25',
								'transition-[border-color,box-shadow] duration-150'
							) }
						/>
					</div>
				</div>

				<div className="border-t border-border" />

				<div className="flex items-center justify-between">
					<Button
						type="button"
						variant="ghost"
						size="sm"
						onClick={ handleCancel }
					>
						Cancel
					</Button>
					<Button
						type="button"
						variant="primary"
						size="sm"
						onClick={ handleApply }
						disabled={ !pickingStart }
					>
						Apply range
					</Button>
				</div>
			</div>
		</div>
	);
}
