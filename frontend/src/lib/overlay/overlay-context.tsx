import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import type { OverlayItem, OverlayOptions } from '#/lib/overlay/types';
import { OverlayOutlet } from '#/lib/overlay/overlay-outlet';

interface OverlayContextValue
{
	open:     ( content: ReactNode, options?: OverlayOptions ) => string;
	close:    ( id: string ) => void;
	closeAll: ( ) => void
}

const OverlayContext = createContext< OverlayContextValue | null >( null );

export function OverlayProvider( { children }: { children: ReactNode } )
{
	const [ overlays, setOverlays ] = useState< OverlayItem[ ] >( [ ] );

	const close = useCallback( ( id: string ) =>
    {
		setOverlays( ( prev ) =>
        {
			const target = prev.find( ( o ) => o.id === id );
			target?.onClose?.( );
			return prev.filter( ( o ) => o.id !== id );
		} );
	}, [ ] );

	const open = useCallback( ( content: ReactNode, options?: OverlayOptions ) =>
    {
		const id = options?.id ?? crypto.randomUUID( );
		setOverlays( ( prev ) =>
        [
			...prev,
			{ id, content, dismissible: options?.dismissible ?? true, onClose: options?.onClose }
		] );
		return id;
	}, [ ] );

	const closeAll = useCallback( ( ) =>
    {
		setOverlays( ( prev ) =>
        {
			prev.forEach( ( o ) => o.onClose?.( ) );
			return [ ];
		} );
	}, [ ] );

	const value = useMemo( ( ) => ( { open, close, closeAll } ), [ open, close, closeAll ] );

	return (
		<OverlayContext.Provider value={ value }>
			{ children }
			<OverlayOutlet overlays={ overlays } onRequestClose={ close } />
		</OverlayContext.Provider>
	);
}

export function useOverlay( )
{
	const ctx = useContext( OverlayContext );
	if ( !ctx )
	{
		throw new Error( 'useOverlay must be used within OverlayProvider' );
	}
	return ctx;
}