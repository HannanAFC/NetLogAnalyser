import { ApiKeysSection } from '#/components/settings/api-keys/api-keys-section';
import { BodyText, Eyebrow, Heading } from '#/components/ui/heading';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute( '/_authenticated/settings' )(
{
	component: SettingsPage,
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

function SettingsPage( )
{

	return (
		<div className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
			<div className="mb-8">
				<Eyebrow>Configuration</Eyebrow>
				<Heading level="h1" className="mt-1">Settings</Heading>
				<BodyText className="mt-2">Manage your account, API keys, and preferences.</BodyText>
			</div>

			<div className="mb-6 flex gap-1 border-b border-border">
				<button
					type="button"
					className="relative px-4 py-2.5 text-sm font-medium text-accent-strong after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:rounded-full after:bg-accent"
				>
					API keys
				</button>
			</div>

			<ApiKeysSection />
		</div>
	);
}