import type { ThemeMode } from '../../lib/theme';
import { useTheme } from '../../lib/theme';
import { Button } from './button';

const nextMode: Record< ThemeMode, ThemeMode > =
{
	auto:  'light',
	light: 'dark',
	dark:  'auto'
};

const label: Record< ThemeMode, string > =
{
	auto:  'Auto',
	light: 'Light',
	dark:  'Dark'
};

export function ThemeToggle( )
{
	const { mode, setMode } = useTheme( );

	return (
		<Button
			type="button"
			onClick={ ( ) => setMode( nextMode[ mode ] ) }
			title={ `Theme: ${ label[ mode ] }` }
			aria-label={ `Theme: ${ label[ mode ] }. Click to switch.` }
			variant='secondary'
		>
			{ mode === 'auto' ?
			(
				<svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
					<circle cx="8" cy="8" r="3" stroke="currentColor" strokeWidth="1.5" />
					<path d="M8 1.5v2M8 12.5v2M1.5 8h2M12.5 8h2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
					<path d="M3.4 3.4l1.4 1.4M11.2 11.2l1.4 1.4M12.6 3.4l-1.4 1.4M4.8 11.2l-1.4 1.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
				</svg>
			) : mode === 'light' ?
			(
				<svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
					<circle cx="8" cy="8" r="3.5" stroke="currentColor" strokeWidth="1.5" />
					<path d="M8 1v2M8 13v2M1 8h2M13 8h2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
					<path d="M3.05 3.05l1.41 1.41M11.54 11.54l1.41 1.41M12.95 3.05l-1.41 1.41M4.46 11.54l-1.41 1.41" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
				</svg>
			) :
			(
				<svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
					<path d="M13.5 10.5A6 6 0 0 1 5.5 2.5a6 6 0 1 0 8 8Z" fill="currentColor" />
				</svg>
			) }
			<span className="hidden sm:inline">{ label[ mode ] }</span>
		</Button>
	);
}
