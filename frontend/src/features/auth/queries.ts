import { queryOptions } from '@tanstack/react-query';
import { tokenStore } from '../../lib/auth/token-store';
import { sessionQueryKey } from '../../lib/auth/session-key';
import { getMe, refreshRequest } from './api';
import type { User } from '../../lib/auth/types';

export { sessionQueryKey };

/**
 * Figure out auth state on page load / refresh
 *
 * As the access token lives only in memory, there will be no access 
 * token on page load. So an access token is fetched via the refresh, 
 * then the user is fetched. Any failure here means not logged in - return
 * null.
 */
async function fetchSession( ): Promise< User | null >
{
	try
	{
		if ( !tokenStore.get( ) )
		{
			const { access_token, user } = await refreshRequest( );
			tokenStore.set( access_token );
			return user;
		}
		return await getMe( );
	}
	catch
	{
		tokenStore.set( null );
		return null;
	}
}

export const sessionQueryOptions = queryOptions(
{
	queryKey: sessionQueryKey,
	queryFn:  fetchSession,
	// The session is invalidated on a backend request with
	// an invalid access token so no need to have a stale time 
	staleTime: Infinity,
	retry:     false
});
