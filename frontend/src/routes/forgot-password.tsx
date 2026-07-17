import { useForm } from '@tanstack/react-form';
import { createFileRoute, Link, redirect } from '@tanstack/react-router';
import { useState } from 'react';
import { useForgotPassword } from '../features/auth/hooks';
import { sessionQueryOptions } from '../features/auth/queries';
import { forgotPasswordSchema } from '../features/auth/schemas';
import { apiError } from '../lib/api/errors';
import { fieldError } from '../lib/utils';

export const Route = createFileRoute( '/forgot-password' )(
{
	beforeLoad: async ( { context } ) =>
	{
		const session = await context.queryClient.ensureQueryData( sessionQueryOptions );
		if ( session ) throw redirect( { to: '/dashboard' } );
	},
	component: ForgotPasswordPage
});

function ForgotPasswordPage( )
{
	const forgotPassword = useForgotPassword( );
	const [ sent, setSent ] = useState( false );

	const form = useForm(
	{
		defaultValues: { email: '' },
		onSubmit: async ( { value } ) =>
		{
			try
			{
				await forgotPassword.mutateAsync( forgotPasswordSchema.parse( value ) );
				setSent( true );
			}
			catch
			{
				// already handled
			}
		},
	});

	const inputClass = "mt-1 w-full rounded-md border border-border bg-[var(--color-card)] px-3 py-2.5 text-[14px] text-text-primary placeholder:text-text-tertiary focus:border-[var(--color-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]/25 transition-[border-color,box-shadow] duration-150";

	if ( sent )
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
						If an account with that email exists, we&apos;ve sent a password reset link.
					</p>
					<p className="body-sm mt-3">
						The link expires in 5 minutes. If you don&apos;t see it, check your spam folder.
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
				<p className="eyebrow">Account recovery</p>
				<h1 className="heading-1">Forgot password</h1>
				<p className="body-text mt-2">Enter your email and we&apos;ll send you a link to reset your password.</p>
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
						validators={{ onChange: forgotPasswordSchema.shape.email, onBlur: forgotPasswordSchema.shape.email }}
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

					{ forgotPassword.isError && (
						<p className="text-[13px] text-critical">{ apiError( forgotPassword.error ) ?? 'Something went wrong. Try again.' }</p>
					)}

					<form.Subscribe selector={ ( state ) => [ state.canSubmit, state.isPristine ] }>
						{ ( [ canSubmit, isPristine ] ) =>
						(
							<button
								type="submit"
								disabled={ !canSubmit || isPristine || forgotPassword.isPending }
								className="inline-flex w-full items-center justify-center rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-[13px] font-semibold text-[var(--color-ink)] transition-opacity hover:opacity-90 disabled:opacity-50"
							>
								{ forgotPassword.isPending ? 'Sending…' : 'Send reset link' }
							</button>
						)}
					</form.Subscribe>
				</form>

				<p className="mt-5 text-[13px] text-text-secondary">
					Remember your password?{' '}
					<Link to="/login" className="font-semibold text-[var(--color-accent-strong)] hover:underline">
						Sign in
					</Link>
				</p>
			</div>
		</div>
	);
}
