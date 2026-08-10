// components/time-range-picker.tsx
//
// Deliberately styleless beyond what Button/Input already carry — this
// component composes your existing design-system primitives rather than
// introducing new hardcoded colors or spacing. Two ways to restyle it
// without forking the component:
//
//   1. Restyle Button/Input themselves — every preset button and the
//      custom-range inputs pick that up automatically.
//   2. Pass `classNames` to override a specific part for just this
//      instance (e.g. tighter gap on a dashboard header vs a full page).
//
// ASSUMPTIONS to verify against your actual components:
//   - Button accepts `variant: 'primary' | 'secondary' | 'ghost' | 'danger'`
//   - Input accepts standard input props + forwards a `className`
// Adjust the variant names/props below if they differ.

import { useState } from 'react';
import { Button } from '#/components/ui/button';
import { Input } from '#/components/ui/input';
import { cn } from '#/lib/utils';
import type { TimeRangePreset, TimeRangeSearch } from '#/lib/time-range/schema';

const PRESET_OPTIONS: { value: Exclude< TimeRangePreset, 'custom' >; label: string }[ ] =
[
	{ value: '1h',  label: '1h' },
	{ value: '24h', label: '24h' },
	{ value: '7d',  label: '7d' },
	{ value: '30d', label: '30d' }
];

interface TimeRangePickerClassNames
{
	root?:               string;
	presetGroup?:        string;
	presetButton?:       string;
	presetButtonActive?: string;
	customRangeGroup?:   string;
	customInput?:        string;
}

interface TimeRangePickerProps
{
	search:               TimeRangeSearch;
	onPresetChange:       ( preset: TimeRangePreset ) => void;
	onCustomRangeChange:  ( start: Date, end: Date ) => void;
	className?:           string;
	classNames?:          TimeRangePickerClassNames;
}

function toDatetimeLocal( date: Date ): string
{
	const pad = ( n: number ) => String( n ).padStart( 2, '0' );
	return `${ date.getFullYear( ) }-${ pad( date.getMonth( ) + 1 ) }-${ pad( date.getDate( ) ) }T${ pad( date.getHours( ) ) }:${ pad( date.getMinutes( ) ) }`;
}

export function TimeRangePicker(
{
	search,
	onPresetChange,
	onCustomRangeChange,
	className,
	classNames = { }
}: TimeRangePickerProps )
{
	const isCustom = search.preset === 'custom';

	const [ draftStart, setDraftStart ] = useState( search.start ?? '' );
	const [ draftEnd, setDraftEnd ]     = useState( search.end ?? '' );

	function handleApplyCustomRange( )
	{
		if ( !draftStart || !draftEnd ) return;
		onCustomRangeChange( new Date( draftStart ), new Date( draftEnd ) );
	}

	return (
		<div className={ cn( 'flex flex-wrap items-center gap-2', className, classNames.root ) }>
			<div
				role="group"
				aria-label="Time range"
				className={ cn( 'flex items-center gap-1', classNames.presetGroup ) }
			>
				{ PRESET_OPTIONS.map( ( option ) =>
				{
					const isActive = search.preset === option.value;
					return (
						<Button
							key={ option.value }
							type="button"
							variant={ isActive ? 'primary' : 'ghost' }
							aria-pressed={ isActive }
							onClick={ () => onPresetChange( option.value ) }
							className={ cn(
								classNames.presetButton,
								isActive && classNames.presetButtonActive
							) }
						>
							{ option.label }
						</Button>
					);
				} ) }
				<Button
					type="button"
					variant={ isCustom ? 'primary' : 'ghost' }
					aria-pressed={ isCustom }
					onClick={ ( ) => onPresetChange( 'custom' ) }
					className={ cn(
						classNames.presetButton,
						isCustom && classNames.presetButtonActive
					) }
				>
					Custom
				</Button>
			</div>

			{ isCustom && (
				<div className={ cn( 'flex items-center gap-2', classNames.customRangeGroup ) }>
					<Input
						type="datetime-local"
						value={ draftStart ? toDatetimeLocal( new Date( draftStart ) ) : '' }
						onChange={ ( e ) => setDraftStart( new Date( e.target.value ).toISOString( ) ) }
						className={ cn( 'm-0', classNames.customInput ) }
						aria-label="Custom range start"
					/>
					<span aria-hidden="true">|</span>
					<Input
						type="datetime-local"
						value={ draftEnd ? toDatetimeLocal( new Date( draftEnd ) ) : '' }
						onChange={ ( e ) => setDraftEnd( new Date( e.target.value ).toISOString( ) ) }
						className={ cn( 'm-0', classNames.customInput ) }
						aria-label="Custom range end"
					/>
					<Button type="button" variant="secondary" onClick={ handleApplyCustomRange }>
						Apply
					</Button>
				</div>
			) }
		</div>
	);
}