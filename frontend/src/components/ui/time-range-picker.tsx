import { useMemo } from 'react';
import { CustomDateRangePicker } from '#/components/ui/custom-date-range-picker';
import type { DateRangeValue } from '#/components/ui/custom-date-range-picker';
import type { TimeRangeSearch } from '#/lib/time-range/schema';

interface TimeRangePickerProps
{
	search:    TimeRangeSearch;
	onChange:  ( start: Date, end: Date ) => void;
	className?: string;
}

export function TimeRangePicker(
{
	search,
	onChange,
	className
}: TimeRangePickerProps )
{
	const rangeValue = useMemo( ( ): DateRangeValue | null =>
	{
		if ( !search.start || !search.end ) return null;
		return { start: new Date( search.start ), end: new Date( search.end ) };
	}, [ search.start, search.end ] );

	function handleChange( range: DateRangeValue )
	{
		onChange( range.start, range.end );
	}

	return (
		<CustomDateRangePicker
			value={ rangeValue }
			onChange={ handleChange }
			className={ className }
		/>
	);
}
