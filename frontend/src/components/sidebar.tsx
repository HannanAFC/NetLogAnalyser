import { Button } from '#/components/ui/button';
import { BodySm } from '#/components/ui/heading';
import { cn } from '#/lib/utils';
import { Link, useLocation } from '@tanstack/react-router';
import { Activity, BarChart3, Globe, History, LayoutDashboard, Settings, ShieldAlert, X } from 'lucide-react';
import type { ReactNode } from 'react';
import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';

interface SidebarContextValue
{
	open:   boolean;
	toggle: ( ) => void;
	close:  ( ) => void;
}

const SidebarContext = createContext< SidebarContextValue >(
{
	open:   false,
	toggle: ( ) =>
    {},
	close:  ( ) =>
    {}
} );

export function useSidebar( )
{
	return useContext( SidebarContext );
}

export function SidebarProvider( { children }: { children: ReactNode } )
{
	const [ open, setOpen ] = useState( false );
	const toggle = useCallback( () => setOpen( ( prev ) => !prev ), [] );
	const close = useCallback( () => setOpen( false ), [] );

	return (
		<SidebarContext.Provider value={ { open, toggle, close } }>
			{ children }
		</SidebarContext.Provider>
	);
}

type NavSection =
{
	label: string;
	items: NavItem[ ];
};

type NavItem =
{
	label: string;
	to:    string;
	icon:  typeof LayoutDashboard;
};

const sections: NavSection[ ] =
[
	{
		label: 'Monitoring',
		items:
		[
			{ label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
			{ label: 'Live feed', to: '/live-feed', icon: Activity },
			{ label: 'Log history', to: '/log-history', icon: History },
			{ label: 'Anomalies', to: '/anomalies', icon: ShieldAlert }
		]
	},
	{
		label: 'Analyse',
		items:
		[
			{ label: 'Geo map', to: '/geo-map', icon: Globe },
			{ label: 'Analytics', to: '/analytics', icon: BarChart3 }
		]
	}
];

interface SidebarProps
{
	open:    boolean;
	onClose: ( ) => void;
}

export function Sidebar( { open, onClose }: SidebarProps )
{
	const location = useLocation() ;
	const sidebarRef = useRef< HTMLElement >( null );

	// Close on Escape
	useEffect( ( ) =>
	{
		function handleKeyDown( e: KeyboardEvent )
		{
			if ( e.key === 'Escape' && open ) onClose();
		}
		document.addEventListener( 'keydown', handleKeyDown );
		return () => document.removeEventListener( 'keydown', handleKeyDown );
	}, [ open, onClose ] );

	// Close on route change
	useEffect( ( ) =>
	{
		onClose( );
	}, [ location.pathname, onClose ] );

	// Trap focus when open on mobile
	useEffect( ( ) =>
	{
		if ( open ) sidebarRef.current?.focus( );
	}, [ open ] );

	function handleLinkClick( )
	{
		onClose( );
	}

	return (
		<>
			{/* Backdrop */}
            <div
                className={ cn( 'fixed inset-0 z-30 bg-black/30 transition-opacity duration-300',
                    !open ? 'pointer-events-none opacity-0' : ''
                ) }
                onClick={ onClose }
                aria-hidden="true"
            />

			<aside
				ref={ sidebarRef }
				tabIndex={ -1 }
				className={ cn(
					'fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-border bg-card shadow-soft transition-transform duration-300 ease-out',
					open ? 'translate-x-0' : '-translate-x-full'
				) }
			>
				<div className="flex items-center justify-between px-3 py-3">
					<span className="text-md font-semibold text-text-primary">Navigation</span>
					<Button
						type="button"
						onClick={ onClose }
						variant='ghost'
						aria-label="Close navigation"
					>
						<X className="h-4 w-4" />
					</Button>
				</div>

				<nav className="flex flex-1 flex-col gap-6 overflow-y-auto px-3 py-2">
					{ sections.map( ( section ) =>
					(
						<div key={ section.label }>
							<BodySm className="mb-1.5 px-2 font-semibold uppercase tracking-[0.10em] text-text-tertiary">
								{ section.label }
							</BodySm>
							<ul className="flex flex-col gap-0.5">
								{ section.items.map( ( item ) =>
								{
									const Icon = item.icon;
									const isActive = location.pathname === item.to;

									return (
										<li key={ item.to }>
											<Link
												to={ item.to }
												onClick={ handleLinkClick }
												className={ cn(
													'flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm font-medium no-underline transition-colors duration-150',
													isActive
														? 'bg-accent/10 text-accent-strong'
														: 'text-text-secondary hover:bg-inset hover:text-text-primary'
												) }
											>
												<Icon className="h-4 w-4 shrink-0" />
												{ item.label }
											</Link>
										</li>
									);
								} ) }
							</ul>
						</div>
					) ) }
				</nav>

				<div className="border-t border-border px-3 py-3">
					<Link
						to="/settings"
						onClick={ handleLinkClick }
						className={ cn(
							'flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm font-medium no-underline transition-colors duration-150',
							location.pathname.startsWith( '/settings' )
								? 'bg-accent/10 text-accent-strong'
								: 'text-text-secondary hover:bg-inset hover:text-text-primary'
						) }
					>
						<Settings className="h-4 w-4 shrink-0" />
						Settings
					</Link>
				</div>
			</aside>
		</>
	);
}
