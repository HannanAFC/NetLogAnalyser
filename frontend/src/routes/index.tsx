import { createFileRoute, Link } from '@tanstack/react-router';
import { sessionQueryOptions } from '../features/auth/queries';
import { useSession } from '#/features/auth/hooks';

export const Route = createFileRoute( '/' )(
{
	beforeLoad: async ( { context } ) =>
	{
		await context.queryClient.ensureQueryData( sessionQueryOptions );
	},
	component: IndexPage
});

function IndexPage( )
{
	const { data: session } = useSession( );

	return (
		<div className="mx-auto mt-32 w-full max-w-lg px-4 text-center">
			<div className="mx-auto mb-6 h-[9px] w-[9px] rounded-full bg-green-500 shadow-[0_0_10px_#22c55e,0_0_24px_rgba(34,197,94,0.12)] animate-[breathe_2.8s_ease-in-out_infinite]" />

			<p className="eyebrow">NetLogAnalyser &nbsp;·&nbsp; Dashboard</p>
			<h1 className="heading-1 mb-4">
				Real-time network log<br />
				<em>ingestion and analysis</em>
			</h1>
			<p className="body-text mx-auto mb-8">
				Send network packet logs from any system, view live traffic,
				detect anomalies, and query historical data - all from one dashboard.
			</p>

			<div className="flex justify-center gap-3">
				{ session ? (
					<Link
						to="/dashboard"
						className="inline-flex items-center font-mono text-xs font-medium cursor-pointer border-none no-underline transition-[opacity,background] duration-150 tracking-[0.01em] px-4 py-[9px] gap-[7px] rounded-md bg-green-500 text-[#0a0f0a] hover:opacity-[0.88]"
					>
						Dashboard
					</Link>
				) : (
					<>
						<Link
							to="/login"
							className="inline-flex items-center font-mono text-xs font-medium cursor-pointer border-none no-underline transition-[opacity,background] duration-150 tracking-[0.01em] px-4 py-[9px] gap-[7px] rounded-md bg-green-500 text-[#0a0f0a] hover:opacity-[0.88]"
						>
							Sign in
						</Link>
						<Link
							to="/register"
							className="inline-flex items-center font-mono text-xs font-medium cursor-pointer border-none no-underline transition-[opacity,background,color,border-color] duration-150 tracking-[0.01em] px-4 py-[9px] gap-[7px] rounded-md bg-transparent text-text-secondary border border-border-hi hover:text-text-primary hover:border-[rgb(var(--color-border-hi-rgb)/0.22)]"
						>
							Create account
						</Link>
					</>
				)}

			</div>
		</div>
	)
}