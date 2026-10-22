/**
 * Tries to guess if the browser has a session.
 */
const STORAGE_KEY = 'netloganalyser-has-session';

export function hasSessionHint( ): boolean
{
	try
	{
		return localStorage.getItem( STORAGE_KEY ) === '1';
	}
	catch
	{
		// Storage blocked - fall back to always trying the refresh.
		return true;
	}
}

export function setSessionHint( value: boolean ): void
{
	try
	{
		if ( value )
		{
			localStorage.setItem( STORAGE_KEY, '1' );
		}
		else
		{
			localStorage.removeItem( STORAGE_KEY );
		}
	}
	catch
	{
        // storage blocked
    }
}
