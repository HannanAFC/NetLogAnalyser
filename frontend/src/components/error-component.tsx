import { Link, useRouter } from '@tanstack/react-router';
import { Button } from '#/components/ui/button';
import { Heading, BodyText } from '#/components/ui/heading';

interface ErrorComponentProps
{
	error: Error
}

function ErrorComponent( { error }: ErrorComponentProps )
{
	const router = useRouter( );

	if ( import.meta.env.DEV )
	{
		console.error( error );
	}

	return (
		<div className='flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center'>
			<Heading>Something went wrong</Heading>
			<BodyText className='max-w-md text-text-secondary'>
				An unexpected error occurred while loading this page. You can try
				again, or head back to the dashboard.
			</BodyText>
			<div className='flex gap-3'>
				<Button variant='secondary' onClick={ ( ) => router.invalidate( ) }>
					Try again
				</Button>
				<Link to='/dashboard'>
					<Button variant='primary'>Back to dashboard</Button>
				</Link>
			</div>
		</div>
	);
}

export { ErrorComponent };