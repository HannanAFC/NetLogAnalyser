import { Button } from '#/components/ui/button';
import { Card } from '#/components/ui/card';
import { BodySm, BodyText, Eyebrow, Heading, SectionTitle } from '#/components/ui/heading';
import { useLogout, useSession } from '#/features/auth/hooks';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute( '/_authenticated/dashboard' )(
{
	component: DashboardPage,
	head: ( ) => (
	{
		links:
		[
			{
				rel: 'canonical',
				href: 'https://www.netloganalyser.com/dashboard'
			}
		],
		meta:
		[
			{
				title: 'Dashboard | NetLogAnalyser'
			},
			{
				name: 'description',
				content: 'Live overview of your network traffic - packets per second, protocol breakdown, top talkers, and real-time anomaly alerts.'
			},
			{
				name: 'og:title',
				content: 'NetLogAnalyser - Dashboard'
			},
			{
				name: 'og:description',
				content: 'Live overview of your network traffic - packets per second, protocol breakdown, top talkers, and real-time anomaly alerts.'
			},
			{
				name: 'twitter:title',
				content: 'NetLogAnalyser - Dashboard'
			},
			{
				name: 'twitter:description',
				content: 'Live overview of your network traffic - packets per second, protocol breakdown, top talkers, and real-time anomaly alerts.'
			},
			{
				name: 'og:url',
				content: 'https://www.netloganalyser.com/dashboard'
			},
			{
				name: 'twitter:url',
				content: 'https://www.netloganalyser.com/dashboard'
			}
		]
	} )
} );

function DashboardPage( )
{
	const { data: session } = useSession( );
	const logout = useLogout( );

	return (
		<div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
			<section className="flex flex-col gap-4">
				<Eyebrow>Operator dashboard</Eyebrow>
				<Heading level="h1" className="max-w-2xl">Welcome back, { session?.display_name }.</Heading>
				<BodyText className="max-w-xl">
					Live packet flow and anomaly context surfaced for faster triage and cleaner reporting.
				</BodyText>
			</section>

			<section className="mt-8 grid gap-3 sm:grid-cols-2">
				<Card>
					<SectionTitle>Analytics</SectionTitle>
					<Heading level="h3" className="mt-2">Traffic overview</Heading>
					<BodySm className="mt-2">Time-bucketed packet counts and protocol breakdowns with geo enrichment.</BodySm>
				</Card>
				<Card>
					<SectionTitle>Session</SectionTitle>
					<Heading level="h3" className="mt-2">Controls</Heading>
					<BodySm className="mt-2 mb-4">Logged in as { session?.email }.</BodySm>
					<Button variant="secondary" onClick={ ( ) => logout.mutate( ) } disabled={ logout.isPending }>
						{ logout.isPending ? 'Logging out…' : 'Logout' }
					</Button>
				</Card>
			</section>
		</div>
	);
}
