import { useMemo } from 'react';
import { CustomDateRangePicker } from '#/components/ui/custom-date-range-picker';
import type { DateRangeValue } from '#/components/ui/custom-date-range-picker';
import type { TimeRangePreset, TimeRangeSearch } from '#/lib/time-range/schema';

interface TimeRangePickerProps
{
	search:         TimeRangeSearch;
	setPreset:      ( preset: TimeRangePreset ) => void;
	setCustomRange: ( start: Date, end: Date ) => void;
	className?:     string;
}

export function TimeRangePicker(
{
	search,
	setPreset,
	setCustomRange,
	className
}: TimeRangePickerProps )
{
	const rangeValue = useMemo( ( ): DateRangeValue | null =>
	{
		if ( !search.start || !search.end ) return null;
		return { start: new Date( search.start ), end: new Date( search.end ) };
	}, [ search.start, search.end, search.preset ] );

	const presetValue = useMemo( ( ): TimeRangePreset | null =>
	{
		return search.preset;
	}, [ search.start, search.end, search.preset ] );

	return (
		<CustomDateRangePicker
			preset={ presetValue }
			value={ rangeValue }
			setPreset={ setPreset }
			setCustomRange={ setCustomRange }
			className={ className }
		/>
	);
}
