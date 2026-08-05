import type { ClassValue } from 'clsx';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

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