import { Link } from '@tanstack/react-router';
import { Card } from './ui/card';
import { BodyText, Heading } from './ui/heading';

export function NotFound( )
{
	return (
		<div className="flex min-h-0 flex-1 items-center justify-center px-4 py-16 sm:px-6">
			<Card className="max-w-md text-center">
				<Heading level='h1' className="text-7xl font-mono text-accent-strong select-none">
					404
				</Heading>
				<div className="">
					<Heading level="h1" className="">Page not found</Heading>
					<BodyText className="mx-auto mt-3 max-w-sm">
						The page you're looking for doesn't exist or has been moved.
					</BodyText>
					<Link
						to="/"
						className="mt-6 inline-flex items-center justify-center rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-ink no-underline transition-opacity hover:opacity-90"
					>
						Back to home
					</Link>
				</div>
			</Card>
		</div>
	);
}
