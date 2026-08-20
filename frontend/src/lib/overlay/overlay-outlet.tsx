import { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '#/lib/utils';
import type { OverlayItem } from '#/lib/overlay/types';

interface OverlayOutletProps
{
	overlays:       OverlayItem[ ];
	onRequestClose: ( id: string ) => void
}

export function OverlayOutlet( { overlays, onRequestClose }: OverlayOutletProps )
{
	const top = overlays[ overlays.length - 1 ];

	useEffect( ( ) =>
    {
		if ( !top || !top.dismissible )
		{
			return;
		}

		function handleKeyDown( e: KeyboardEvent )
		{
			if ( e.key === 'Escape' && top )
			{
				onRequestClose( top.id );
			}
		}
		window.addEventListener( 'keydown', handleKeyDown );
		return ( ) => window.removeEventListener( 'keydown', handleKeyDown );
	}, [ top, onRequestClose ] );

	if ( overlays.length === 0 )
	{
		document.documentElement.classList.remove( 'overflow-y-hidden' );
		return null;
	}
	else
	{
		document.documentElement.classList.add( 'overflow-y-hidden' );
	}

	return createPortal(
		<>
			{ overlays.map( ( overlay, index ) =>
            (
				<div
					key={ overlay.id }
					className={ cn(
						'fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm transition-opacity opacity-100',
						index !== overlays.length - 1 && 'pointer-events-none opacity-0'
					) }
					onClick={ ( e ) =>
                    {
						if ( overlay.dismissible && e.target === e.currentTarget )
						{
							onRequestClose( overlay.id );
						}
					}}
				>
					<div onClick={ ( e ) => e.stopPropagation( ) }>
						{ overlay.content }
					</div>
				</div>
			) ) }
		</>,
		document.body
	);
}