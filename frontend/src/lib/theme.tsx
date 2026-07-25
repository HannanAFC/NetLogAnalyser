import { createContext, useCallback, useContext, useEffect, useState } from 'react';

export type ThemeMode = 'auto' | 'light' | 'dark';

interface ThemeContextValue
{
	mode: ThemeMode;
	setMode: ( mode: ThemeMode ) => void;
	resolved: 'light' | 'dark';
}

const STORAGE_KEY = 'netloganalyser-theme';

function readStored(): ThemeMode
{
	try
	{
		const raw = localStorage.getItem( STORAGE_KEY );
		if ( raw === 'light' || raw === 'dark' || raw === 'auto' ) return raw;
	}
 	catch
	{ /* storage blocked */ }
	return 'auto';
}

function resolveTheme( mode: ThemeMode ): 'light' | 'dark'
{
	if ( mode === 'light' || mode === 'dark' ) return mode;
	if ( typeof window !== 'undefined' && window.matchMedia( '(prefers-color-scheme: dark)' ).matches )
	{
		return 'dark';
	}
	return 'light';
}

function applyDataTheme( mode: ThemeMode ): void
{
	if ( mode === 'auto' )
	{
		document.documentElement.removeAttribute( 'data-theme' );
	}
 	else
	{
		document.documentElement.setAttribute( 'data-theme', mode );
	}
}

const ThemeContext = createContext<ThemeContextValue>(
{
	mode: 'auto',
	setMode: () =>
	{},
	resolved: 'light'
} );

export function ThemeProvider( { children }: { children: React.ReactNode } )
{
	const [ mode, setModeRaw ] = useState<ThemeMode>( readStored );
	const resolved = resolveTheme( mode );

	const setMode = useCallback( ( next: ThemeMode ) =>
	{
		setModeRaw( next );
		try
		{
			localStorage.setItem( STORAGE_KEY, next );
		}
 		catch
		{	 /* storage blocked */ }
	}, [] );

	useEffect( () =>
	{
		applyDataTheme( mode );
	}, [ mode ] );

	/* Listen for OS preference changes when in auto mode */
	useEffect( () =>
	{
		if ( mode !== 'auto' ) return;
		const mq = window.matchMedia( '(prefers-color-scheme: dark)' );
		const handler = () => setModeRaw( 'auto' ); /* re-render to pick up new resolved */
		mq.addEventListener( 'change', handler );
		return () => mq.removeEventListener( 'change', handler );
	}, [ mode ] );

	return (
		<ThemeContext.Provider value={{ mode, setMode, resolved }}>
			{children}
		</ThemeContext.Provider>
	);
}

export function useTheme(): ThemeContextValue
{
	return useContext( ThemeContext );
}