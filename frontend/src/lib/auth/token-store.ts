import { setSessionHint } from './session-hint';

/**
 * This is where the JWT token is stored, token is stored in memory
 * Does not handle auth state.
 * Every set/clear also updates the session hint, so all login, refresh and
 * logout paths keep it in sync.
*/
let accessToken: string | null = null;

export const tokenStore =
{
	get: ( ) => accessToken,
	set: ( token: string | null ) =>
	{
		accessToken = token;
		setSessionHint( token !== null );
	}
};
