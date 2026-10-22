import { readFileSync } from 'node:fs';
import { expect, it, vi } from 'vitest';
import { setSessionHint } from '#/lib/auth/session-hint';

vi.mock( '@tanstack/react-devtools', ( ) => ( { TanStackDevtools: ( ) => null } ) );

for ( const hint of [ false, true ] )
{
	for ( const route of [ '/', '/login' ] )
	{
		it( `hydrates ${ route } hint=${ hint }`, async( ) =>
		{
			vi.resetModules( );
			( window as any ).matchMedia = ( ) => ( { matches: false, addEventListener: ( ) =>
{ }, removeEventListener: ( ) =>
{ } } );
			setSessionHint( hint );
			const file = route === '/' ? 'dist/index.html' : `dist${ route }/index.html`;
			const page = new DOMParser( ).parseFromString( readFileSync( file, 'utf8' ), 'text/html' );
			document.head.innerHTML = page.head.innerHTML.replace( /<script[^>]*><\/script>/g, '' );
			document.body.innerHTML = page.body.innerHTML;
			( window as any ).__ENV__ = { API_BASE_URL: 'http://api.test', WS_BASE_URL: 'ws://api.test' };
			window.history.pushState( { }, '', route );
			const errors: string[ ] = [ ];
			const spy = vi.spyOn( console, 'error' ).mockImplementation( ( ...a ) =>
{
 errors.push( String( a[ 0 ] ) );
} );
			const seen: string[ ] = [ ];
			const snap = ( ) => seen.push( ( document.querySelector( 'header' )?.textContent ?? 'NOHEADER' ) + '|' + ( document.querySelector( 'header button[aria-label="Toggle navigation"]' ) ? 'menu' : 'nomenu' ) );
			snap( );
			await import( '../main' );
			for ( let i = 0; i < 8; i++ )
{
 await new Promise( ( r ) => setTimeout( r, 100 ) ); snap( );
}
			spy.mockRestore( );
			console.log( 'RESULT', route, hint, JSON.stringify( [ ...new Set( seen ) ] ), JSON.stringify( errors.filter( ( e ) => !e.includes( '[MSW]' ) ).map( ( e ) => e.slice( 0, 120 ) ) ) );
			expect( errors.filter( ( e ) => !e.includes( '[MSW]' ) ) ).toHaveLength( 0 );
		} );
	}
}
