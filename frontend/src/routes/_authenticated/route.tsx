import { createFileRoute, redirect, isRedirect, Outlet, useNavigate } from '@tanstack/react-router';
import { useEffect } from 'react';
import { sessionQueryOptions } from '../../features/auth/queries';
import { useSession } from '../../features/auth/hooks';

export const Route = createFileRoute( '/_authenticated' )(
	{
		beforeLoad: async( { context, location } ) =>
		{
			try
			{
				const session = await context.queryClient.ensureQueryData( sessionQueryOptions );
				if ( !session )
				{
					throw redirect( { to: '/login', search: { redirect: location.href } } );
				}
			}
			catch( error )
			{
				if ( isRedirect( error ) ) throw error;
				// Network error, etc. - fail closed.
				throw redirect( { to: '/login', search: { redirect: location.href } } );
			}
		},
		component: AuthenticatedLayout
	} );

function AuthenticatedLayout( )
{
	// beforeLoad only runs on navigation. This watches the *same* cached
	// session for the case where it goes null mid-visit - e.g. the axios
	// interceptor cleared it after a refresh-token failure - and bounces
	// the user out without waiting for the next navigation to notice.
	const { data: session } = useSession( );
	const navigate = useNavigate( );

	useEffect( ( ) =>
	{
		if ( session === null )
		{
			navigate( { to: '/login', replace: true } );
		}
	}, [ session, navigate ] );

	return <Outlet />;
}
