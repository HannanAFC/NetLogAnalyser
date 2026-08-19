import { AccountSection } from '#/components/settings/account/account-section';
import { ApiKeysSection } from '#/components/settings/api-keys/api-keys-section';
import { ExportsSection } from '#/components/settings/exports/exports-section';
import { BodyText, Eyebrow, Heading } from '#/components/ui/heading';
import { PageWrapper } from '#/components/ui/page-wrapper';
import { cn } from '#/lib/utils';
import { createFileRoute, Link } from '@tanstack/react-router';
import type { HTMLAttributes } from 'react';
import z from 'zod';

const settingsPageSearchSchema = z
	.object(
	{
		tab: z.enum( [ 'api-keys', 'exports', 'account' ] ).default( 'api-keys' ).catch( 'api-keys' )
	} );

export const Route = createFileRoute( '/_authenticated/settings' )(
{
	component:      SettingsPage,
	validateSearch: settingsPageSearchSchema,
	head: ( ) => (
	{
		links:
		[
			{
				rel: 'canonical',
				href: 'https://www.netloganalyser.com/settings'
			}
		],
		meta:
		[
			{
				title: 'Settings | NetLogAnalyser'
			},
			{
				name: 'description',
				content: 'Manage your NetLogAnalyser account - create, view and revoke API keys and edit account settings.'
			},
			{
				name: 'og:title',
				content: 'NetLogAnalyser - Settings'
			},
			{
				name: 'og:description',
				content: 'Manage your NetLogAnalyser account - create, view and revoke API keys and edit account settings.'
			},
			{
				name: 'twitter:title',
				content: 'NetLogAnalyser - Settings'
			},
			{
				name: 'twitter:description',
				content: 'Manage your NetLogAnalyser account - create, view and revoke API keys and edit account settings.'
			},
			{
				name: 'og:url',
				content: 'https://www.netloganalyser.com/settings'
			},
			{
				name: 'twitter:url',
				content: 'https://www.netloganalyser.com/settings'
			}
		]
	} )
} );

export interface SettingsSectionProps extends HTMLAttributes< HTMLDivElement > { };

function SettingsPage( )
{
	const { tab } = Route.useSearch( );
	const baseButtonClass = 'relative px-4 py-2.5 text-sm font-medium transition-colors after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:rounded-full after:bg-accent';
	const inActiveButtonClass = baseButtonClass + ' text-primary after:opacity-0';
	const activeButtonClass   = baseButtonClass + ' text-accent-strong after:opacity-100';

	return (
		<PageWrapper maxWidth="4xl">
			<div>
				<Eyebrow>Configuration</Eyebrow>
				<Heading level="h1" className="mt-1">Settings</Heading>
				<BodyText className="mt-2">Manage your account, API keys, and preferences.</BodyText>
			</div>

			<div className="mb-6 flex gap-1 border-b border-border w-full overflow-x-auto">
				<Link
					className={ tab === 'api-keys' ? activeButtonClass : inActiveButtonClass }
					from={ Route.fullPath }
					search={ { tab: 'api-keys' } }
				>
					API keys
				</Link>
				<Link
					className={ tab === 'exports' ? activeButtonClass : inActiveButtonClass }
					from={ Route.fullPath }
					search={ { tab: 'exports' } }
				>
					Exports
				</Link>
				<Link
					className={ tab === 'account' ? activeButtonClass : inActiveButtonClass }
					from={ Route.fullPath }
					search={ { tab: 'account' } }
				>
					Account
				</Link>
			</div>
			<div className="relative overflow-hidden">
				<div
					className={ cn( 'transition-all duration-300 ease-out', tab === 'api-keys' ? 'relative translate-x-0 opacity-100' : 'pointer-events-none absolute inset-x-0 top-0 -translate-x-8 opacity-0' ) }
					aria-hidden={ tab !== 'api-keys' }
					inert={ tab !== 'api-keys' }
				>
					<ApiKeysSection />
				</div>
				<div
					className={ cn( 'transition-all duration-300 ease-out', tab === 'exports' ? 'relative translate-x-0 opacity-100' : 'pointer-events-none absolute inset-x-0 top-0 translate-x-8 opacity-0' ) }
					aria-hidden={ tab !== 'exports' }
					inert={ tab !== 'exports' }
				>
					<ExportsSection />
				</div>
				<div
					className={ cn( 'transition-all duration-300 ease-out', tab === 'account' ? 'relative translate-x-0 opacity-100' : 'pointer-events-none absolute inset-x-0 top-0 translate-x-8 opacity-0' ) }
					aria-hidden={ tab !== 'account' }
					inert={ tab !== 'account' }
				>
					<AccountSection />
				</div>
			</div>
		</PageWrapper>
	);
}