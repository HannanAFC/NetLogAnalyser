import { Card } from '#/components/ui/card';
import { BodySm, BodyText, Eyebrow, Heading } from '#/components/ui/heading';
import { useResendVerification, useVerifyEmail } from '#/features/auth/hooks';
import { sessionQueryOptions } from '#/features/auth/queries';
import { resendVerificationSchema } from '#/features/auth/schemas';
import { apiError } from '#/lib/api/errors';
import { fieldError } from '#/lib/utils';
import { useForm } from '@tanstack/react-form';
import { createFileRoute, Link, redirect } from '@tanstack/react-router';
import { useEffect, useState } from 'react';
import { z } from 'zod';
import { Input, Label } from '../components/ui/input';

const verifySearchSchema = z.object(
	{
		token: z.string( ).optional( )
	} );

export const Route = createFileRoute( '/verify-email' )(
{
	validateSearch: verifySearchSchema,
	beforeLoad: async( { context } ) =>
	{
		const session = await context.queryClient.ensureQueryData( sessionQueryOptions );
		if ( session ) throw redirect( { to: '/dashboard' } );
	},
	component: VerifyEmailPage,
	head: ( ) =>(
	{
		links:
		[
			{
				rel: 'canonical',
				href: 'https://www.netloganalyser.com/verify-email'
			}
		],
		meta:
		[
			{
				title: "Verify Email | NetLogAnalyser"
			},
			{
				name: 'description',
				content: 'Verify you NetLogAnalyser account to start monitoring your network traffic.'
			},
			{
				name: 'og:title',
				content: 'NetLogAnalyser - Verify Email'
			},
			{
				name: 'og:description',
				content: 'Verify you NetLogAnalyser account to start monitoring your network traffic.'
			},
			{
				name: 'twitter:title',
				content: 'NetLogAnalyser - Verify Email'
			},
			{
				name: 'twitter:description',
				content: 'Verify you NetLogAnalyser account to start monitoring your network traffic.'
			},
			{
				name: 'og:url',
				content: 'https://www.netloganalyser.com/verify-email'
			},
			{
				name: 'twitter:url',
				content: 'https://www.netloganalyser.com/verify-email'
			}
		]
	} )
} );

function VerifyEmailPage( )
{
	const { token } = Route.useSearch( );
	const verifyEmail = useVerifyEmail( );
	const resendVerification = useResendVerification( );
	const [ verified, setVerified ] = useState( false );
	const [ error, setError ] = useState< string | null >( null );
	const [ resent, setResent ] = useState( false );

	// Auto-verify when token is present in the URL
	useEffect( ( ) =>
	{
		if ( !token ) return;

		verifyEmail.mutateAsync( token )
			.then( ( ) => setVerified( true ) )
			.catch( ( err: unknown ) => setError( apiError( err ) ?? 'This verification link is invalid or has expired.' ) );
	}, [ token ] );

	const form = useForm(
		{
			defaultValues: { email: '' },
			onSubmit: async( { value } ) =>
			{
				try
				{
					await resendVerification.mutateAsync( resendVerificationSchema.parse( value ) );
					setResent( true );
				}
				catch
				{
				// already handled
				}
			}
		} );

	if ( token && !verified && !error )
	{
		return (
			<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
				<Card className="text-center">
					<div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center">
						<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent-strong)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="animate-spin">
							<path d="M21 12a9 9 0 1 1-6.219-8.56" />
						</svg>
					</div>
					<Heading level="h1" className="mb-2">Verifying your email</Heading>
					<BodyText>Please wait a moment…</BodyText>
				</Card>
			</div>
		);
	}

	if ( token && verified )
	{
		return (
			<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
				<Card className="text-center">
					<div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-accent/10">
						<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent-strong)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
							<path d="M20 6 9 17l-5-5" />
						</svg>
					</div>
					<Heading level="h1" className="mb-2">Email verified</Heading>
					<BodyText>Your email has been confirmed. You can now sign in.</BodyText>
					<Link
						to="/login"
						className="mt-6 inline-flex w-full items-center justify-center rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-ink transition-opacity hover:opacity-90"
					>
						Continue to sign in
					</Link>
				</Card>
			</div>
		);
	}

	if ( token && error )
	{
		return (
			<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
				<Card className="text-center">
					<div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-accent/10">
						<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent-strong)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
							<circle cx="12" cy="12" r="10" />
							<path d="m15 9-6 6" />
							<path d="m9 9 6 6" />
						</svg>
					</div>
					<Heading level="h1" className="mb-2">Verification failed</Heading>
					<BodyText>{ error }</BodyText>
					<BodySm className="mt-3">
						You can request a new verification link below.
					</BodySm>
					<Link
						to="/verify-email"
						className="mt-6 inline-flex w-full items-center justify-center rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-ink transition-opacity hover:opacity-90"
					>
						Request a new link
					</Link>
				</Card>
			</div>
		);
	}

	if ( resent )
	{
		return (
			<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
				<Card className="text-center">
					<div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-accent/10">
						<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent-strong)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
							<rect x="2" y="4" width="20" height="16" rx="2" />
							<path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
						</svg>
					</div>
					<Heading level="h1" className="mb-2">Check your email</Heading>
					<BodyText>
						If an unverified account with that email exists, we&apos;ve sent a new
						verification link.
					</BodyText>
					<BodySm className="mt-3">
						The link expires in 60 minutes. Check your spam folder if you don&apos;t see it.
					</BodySm>
					<Link
						to="/login"
						className="mt-6 inline-flex w-full items-center justify-center rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-ink transition-opacity hover:opacity-90"
					>
						Back to sign in
					</Link>
				</Card>
			</div>
		);
	}

	return (
		<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
			<div>
				<Eyebrow>Account setup</Eyebrow>
				<Heading level="h1">Verify your email</Heading>
				<BodyText className="mt-2">Enter the email you registered with to receive a new verification link.</BodyText>
			</div>

			<Card>
				<form
					onSubmit={ ( event ) =>
					{
						event.preventDefault( );
						event.stopPropagation( );
						form.handleSubmit( );
					}}
					className="space-y-4"
				>
					<form.Field
						name="email"
						validators={{ onChange: resendVerificationSchema.shape.email, onBlur: resendVerificationSchema.shape.email }}
					>
						{ ( field ) =>
							(
								<div>
									<Label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">Email</Label>
									<Input
										id={ field.name }
										type="email"
										autoComplete="email"
										value={ field.state.value }
										onBlur={ field.handleBlur }
										onChange={ ( e ) => field.handleChange( e.target.value ) }
									/>
									{ field.state.meta.errors.length > 0 && (
										<BodySm className="text-critical">
											{ fieldError( field.state.meta.errors ) }
										</BodySm>
									)}
								</div>
							)}
					</form.Field>

					{ resendVerification.isError && (
						<BodySm className="text-critical">{ apiError( resendVerification.error ) ?? 'Something went wrong. Try again.' }</BodySm>
					)}

					<form.Subscribe selector={ ( state ) => [ state.canSubmit, state.isPristine ] }>
						{ ( [ canSubmit, isPristine ] ) =>
							(
								<button
									type="submit"
									disabled={ !canSubmit || isPristine || resendVerification.isPending }
									className="inline-flex w-full items-center justify-center rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-ink transition-opacity hover:opacity-90 disabled:opacity-50"
								>
									{ resendVerification.isPending ? 'Sending…' : 'Send verification link' }
								</button>
							)}
					</form.Subscribe>
				</form>

				<BodySm className="mt-5 text-text-secondary">
					Already verified?{' '}
					<Link to="/login" className="font-semibold text-accent-strong hover:underline">
						Login
					</Link>
				</BodySm>
			</Card>
		</div>
	);
}
