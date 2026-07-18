import { useForm } from '@tanstack/react-form';
import { createFileRoute, Link, redirect } from '@tanstack/react-router';
import { useEffect, useState } from 'react';
import { z } from 'zod';
import { useResendVerification, useVerifyEmail } from '../features/auth/hooks';
import { sessionQueryOptions } from '../features/auth/queries';
import { resendVerificationSchema } from '../features/auth/schemas';
import { apiError } from '../lib/api/errors';
import { fieldError } from '../lib/utils';

const verifySearchSchema = z.object(
{
	token: z.string( ).optional( ),
});

export const Route = createFileRoute( '/verify-email' )(
{
	validateSearch: verifySearchSchema,
	beforeLoad: async ( { context } ) =>
	{
		const session = await context.queryClient.ensureQueryData( sessionQueryOptions );
		if ( session ) throw redirect( { to: '/dashboard' } );
	},
	component: VerifyEmailPage
});

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
		onSubmit: async ( { value } ) =>
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
		},
	});

	const inputClass = "mt-1 w-full rounded-md border border-border bg-[var(--color-card)] px-3 py-2.5 text-[14px] text-text-primary placeholder:text-text-tertiary focus:border-[var(--color-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]/25 transition-[border-color,box-shadow] duration-150";

	if ( token && !verified && !error )
	{
		return (
			<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
				<div className="panel p-8 text-center">
					<div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center">
						<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent-strong)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="animate-spin">
							<path d="M21 12a9 9 0 1 1-6.219-8.56" />
						</svg>
					</div>
					<h1 className="heading-1 mb-2">Verifying your email</h1>
					<p className="body-text">Please wait a moment…</p>
				</div>
			</div>
		);
	}

	if ( token && verified )
	{
		return (
			<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
				<div className="panel p-8 text-center">
					<div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-accent)]/10">
						<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent-strong)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
							<path d="M20 6 9 17l-5-5" />
						</svg>
					</div>
					<h1 className="heading-1 mb-2">Email verified</h1>
					<p className="body-text">Your email has been confirmed. You can now sign in.</p>
					<Link
						to="/login"
						className="mt-6 inline-flex w-full items-center justify-center rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-[13px] font-semibold text-[var(--color-ink)] transition-opacity hover:opacity-90"
					>
						Continue to sign in
					</Link>
				</div>
			</div>
		);
	}

	if ( token && error )
	{
		return (
			<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
				<div className="panel p-8 text-center">
					<div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-accent)]/10">
						<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent-strong)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
							<circle cx="12" cy="12" r="10" />
							<path d="m15 9-6 6" />
							<path d="m9 9 6 6" />
						</svg>
					</div>
					<h1 className="heading-1 mb-2">Verification failed</h1>
					<p className="body-text">{ error }</p>
					<p className="body-sm mt-3">
						You can request a new verification link below.
					</p>
					<Link
						to="/verify-email"
						className="mt-6 inline-flex w-full items-center justify-center rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-[13px] font-semibold text-[var(--color-ink)] transition-opacity hover:opacity-90"
					>
						Request a new link
					</Link>
				</div>
			</div>
		);
	}

	if ( resent )
	{
		return (
			<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
				<div className="panel p-8 text-center">
					<div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-accent)]/10">
						<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent-strong)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
							<rect x="2" y="4" width="20" height="16" rx="2" />
							<path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
						</svg>
					</div>
					<h1 className="heading-1 mb-2">Check your email</h1>
					<p className="body-text">
						If an unverified account with that email exists, we&apos;ve sent a new
						verification link.
					</p>
					<p className="body-sm mt-3">
						The link expires in 60 minutes. Check your spam folder if you don&apos;t see it.
					</p>
					<Link
						to="/login"
						className="mt-6 inline-flex w-full items-center justify-center rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-[13px] font-semibold text-[var(--color-ink)] transition-opacity hover:opacity-90"
					>
						Back to sign in
					</Link>
				</div>
			</div>
		);
	}

	return (
		<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
			<div>
				<p className="eyebrow">Account setup</p>
				<h1 className="heading-1">Verify your email</h1>
				<p className="body-text mt-2">Enter the email you registered with to receive a new verification link.</p>
			</div>

			<div className="panel p-6">
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
								<label htmlFor={ field.name } className="block text-[13px] font-medium text-text-primary">
									Email
								</label>
								<input
									id={ field.name }
									type="email"
									autoComplete="email"
									value={ field.state.value }
									onBlur={ field.handleBlur }
									onChange={ ( e ) => field.handleChange( e.target.value ) }
									className={ inputClass }
								/>
								{ field.state.meta.errors.length > 0 && (
									<p className="mt-1 text-[12px] text-critical">
										{ fieldError( field.state.meta.errors ) }
									</p>
								)}
							</div>
						)}
					</form.Field>

					{ resendVerification.isError && (
						<p className="text-[13px] text-critical">{ apiError( resendVerification.error ) ?? 'Something went wrong. Try again.' }</p>
					)}

					<form.Subscribe selector={ ( state ) => [ state.canSubmit, state.isPristine ] }>
						{ ( [ canSubmit, isPristine ] ) =>
						(
							<button
								type="submit"
								disabled={ !canSubmit || isPristine || resendVerification.isPending }
								className="inline-flex w-full items-center justify-center rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-[13px] font-semibold text-[var(--color-ink)] transition-opacity hover:opacity-90 disabled:opacity-50"
							>
								{ resendVerification.isPending ? 'Sending…' : 'Send verification link' }
							</button>
						)}
					</form.Subscribe>
				</form>

				<p className="mt-5 text-[13px] text-text-secondary">
					Already verified?{' '}
					<Link to="/login" className="font-semibold text-[var(--color-accent-strong)] hover:underline">
						Sign in
					</Link>
				</p>
			</div>
		</div>
	);
}
