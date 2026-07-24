import { useForm } from '@tanstack/react-form';
import { createFileRoute, Link, redirect } from '@tanstack/react-router';
import { useState } from 'react';
import { z } from 'zod';
import { useResetPassword } from '../features/auth/hooks';
import { sessionQueryOptions } from '../features/auth/queries';
import { resetPasswordSchema } from '../features/auth/schemas';
import { apiError } from '../lib/api/errors';
import { fieldError } from '../lib/utils';

const resetSearchSchema = z.object(
	{
		token: z.string( ).optional( )
	} );

export const Route = createFileRoute( '/reset-password' )(
	{
		validateSearch: resetSearchSchema,
		beforeLoad: async( { context } ) =>
		{
			const session = await context.queryClient.ensureQueryData( sessionQueryOptions );
			if ( session ) throw redirect( { to: '/dashboard' } );
		},
		component: ResetPasswordPage
	} );

function ResetPasswordPage( )
{
	const { token } = Route.useSearch( );
	const resetPassword = useResetPassword( );
	const [ done, setDone ] = useState( false );

	const form = useForm(
		{
			defaultValues: { token: token ?? '', password: '', confirm_password: '' },
			onSubmit: async( { value } ) =>
			{
				try
				{
					const parsed = resetPasswordSchema.parse( value );
					await resetPassword.mutateAsync( parsed );
					setDone( true );
				}
				catch
				{
				// already handled
				}
			}
		} );

	const inputClass = 'mt-1 w-full rounded-md border border-border bg-[var(--color-card)] px-3 py-2.5 text-[14px] text-text-primary placeholder:text-text-tertiary focus:border-[var(--color-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]/25 transition-[border-color,box-shadow] duration-150';

	if ( !token )
	{
		return (
			<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
				<div className="panel p-8 text-center">
					<h1 className="heading-1 mb-2">Missing reset token</h1>
					<p className="body-text">
						This page requires a reset token from your email. If you need to reset your
						password, request a new link.
					</p>
					<Link
						to="/forgot-password"
						className="mt-6 inline-flex w-full items-center justify-center rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-[13px] font-semibold text-[var(--color-ink)] transition-opacity hover:opacity-90"
					>
						Request a reset link
					</Link>
				</div>
			</div>
		);
	}

	if ( done )
	{
		return (
			<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
				<div className="panel p-8 text-center">
					<div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-accent)]/10">
						<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent-strong)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
							<path d="M20 6 9 17l-5-5" />
						</svg>
					</div>
					<h1 className="heading-1 mb-2">Password reset</h1>
					<p className="body-text">
						Your password has been reset. All existing sessions have been signed out.
					</p>
					<Link
						to="/login"
						className="mt-6 inline-flex w-full items-center justify-center rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-[13px] font-semibold text-[var(--color-ink)] transition-opacity hover:opacity-90"
					>
						Sign in with new password
					</Link>
				</div>
			</div>
		);
	}

	return (
		<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
			<div>
				<p className="eyebrow">Account recovery</p>
				<h1 className="heading-1">Reset password</h1>
				<p className="body-text mt-2">Choose a new password for your account.</p>
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
					{/* Hidden field to carry the token through form state */}
					<form.Field name="token">
						{ ( field ) => <input type="hidden" value={ field.state.value } /> }
					</form.Field>

					<form.Field
						name="password"
						validators={{ onChange: resetPasswordSchema.shape.password, onBlur: resetPasswordSchema.shape.password }}
					>
						{ ( field ) =>
							(
								<div>
									<label htmlFor={ field.name } className="block text-[13px] font-medium text-text-primary">
										New password
									</label>
									<input
										id={ field.name }
										type="password"
										autoComplete="new-password"
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

					<form.Field
						name="confirm_password"
						validators={
							{
								onChange: ( { value, fieldApi } ) =>
								{
									if ( !value ) return 'Please confirm your password';
									if ( value !== fieldApi.form.getFieldValue( 'password' ) ) return "Passwords don't match";
									return undefined;
								}
							}}
					>
						{ ( field ) =>
							(
								<div>
									<label htmlFor={ field.name } className="block text-[13px] font-medium text-text-primary">
										Confirm new password
									</label>
									<input
										id={ field.name }
										type="password"
										autoComplete="new-password"
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

					{ resetPassword.isError && (
						<p className="text-[13px] text-critical">{ apiError( resetPassword.error ) ?? 'Could not reset your password. The link may have expired.' }</p>
					)}

					<form.Subscribe selector={ ( state ) => [ state.canSubmit, state.isPristine ] }>
						{ ( [ canSubmit, isPristine ] ) =>
							(
								<button
									type="submit"
									disabled={ !canSubmit || isPristine || resetPassword.isPending }
									className="inline-flex w-full items-center justify-center rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-[13px] font-semibold text-[var(--color-ink)] transition-opacity hover:opacity-90 disabled:opacity-50"
								>
									{ resetPassword.isPending ? 'Resetting…' : 'Reset password' }
								</button>
							)}
					</form.Subscribe>
				</form>

				<p className="mt-5 text-[13px] text-text-secondary">
					<Link to="/login" className="font-semibold text-[var(--color-accent-strong)] hover:underline">
						Back to sign in
					</Link>
				</p>
			</div>
		</div>
	);
}
