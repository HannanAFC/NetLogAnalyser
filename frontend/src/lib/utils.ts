import type { ClassValue } from 'clsx';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useEffect, useState } from 'react';

/** Merge Tailwind classes without style conflicts. */
export function cn( ...inputs: ClassValue[ ] )
{
	return twMerge( clsx( ...inputs ) );
}

/**
 * Normalise TanStack Form field errors into a displayable string.
 *
 * TanStack Form field validators can return:
 * - a plain `string` (custom function validators), or
 * - a Zod `ZodIssue` object with a `.message` property.
 */
export function fieldError( errors: unknown[ ] ): string | undefined
{
	const first = errors[ 0 ];
	if ( !first ) return undefined;
	if ( typeof first === 'string' ) return first;
	if ( typeof first === 'object' && 'message' in first )
		return ( first as { message: string } ).message;
	return String( first );
}

export function formatApiKeyDate( iso: string | null ): string
{
	if ( !iso ) return '-';
	return new Intl.DateTimeFormat( 'en-US',
	{
		month: 'short',
		day: 'numeric',
		year: 'numeric',
		hour: 'numeric',
		minute: '2-digit'
	} ).format( new Date( iso ) );
}

export function formatRelativeTime( isoTimestamp: string ): string
{
	const deltaMs = Date.now() - new Date( isoTimestamp ).getTime( );
	const deltaSeconds = Math.round( deltaMs / 1000 );

	if ( deltaSeconds < 5 )   return 'just now';
	if ( deltaSeconds < 60 )  return `${ deltaSeconds }s ago`;
	const minutes = Math.round( deltaSeconds / 60 );
	if ( minutes < 60 )       return `${ minutes }m ago`;
	const hours = Math.round( minutes / 60 );
	return `${ hours }h ago`;
}

export function useDebounce< T >( value: T, delay = 500 ): T
{
	const [ debouncedValue, setDebouncedValue ] = useState( value );

	useEffect( ( ) =>
	{
		const handler = setTimeout( ( ) =>
		{
			setDebouncedValue( value );
		}, delay );

		return ( ) => clearTimeout( handler );
	}, [ value, delay ] );

	return debouncedValue;
}