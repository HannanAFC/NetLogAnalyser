import { Card } from '#/components/ui/card';
import { BodySm, BodyText, Eyebrow, Heading } from '#/components/ui/heading';
import { useResetPassword } from '#/features/auth/hooks';
import { sessionQueryOptions } from '#/features/auth/queries';
import { resetPasswordSchema } from '#/features/auth/schemas';
import { apiError } from '#/lib/api/errors';
import { fieldError } from '#/lib/utils';
import { useForm } from '@tanstack/react-form';
import { createFileRoute, Link, redirect } from '@tanstack/react-router';
import { useState } from 'react';
import { z } from 'zod';
import { Input, Label } from '../components/ui/input';

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
	component: ResetPasswordPage,
	head: ( ) => (
	{
		links:
		[
			{
				rel: 'canonical',
				href: 'https://www.netloganalyser.com/reset-password'
			}
		],
		meta:
		[
			{
				title: 'Reset Password | NetLogAnalyser'
			},
			{
				name: 'description',
				content: 'Reset you NetLogAnalyser account password to start monitoring you network traffic again.'
			},
			{
				name: 'og:title',
				content: 'NetLogAnalyser - Reset Password'
			},
			{
				name: 'og:description',
				content: 'Reset you NetLogAnalyser account password to start monitoring you network traffic again.'
			},
			{
				name: 'twitter:title',
				content: 'NetLogAnalyser - Reset Password'
			},
			{
				name: 'twitter:description',
				content: 'Reset you NetLogAnalyser account password to start monitoring you network traffic again.'
			},
			{
				name: 'og:url',
				content: 'https://www.netloganalyser.com/reset-password'
			},
			{
				name: 'twitter:url',
				content: 'https://www.netloganalyser.com/reset-password'
			}
		]
	} )
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

	if ( !token )
	{
		return (
			<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
				<Card className="text-center">
					<Heading level="h1" className="mb-2">Missing reset token</Heading>
					<BodyText>
						This page requires a reset token from your email. If you need to reset your
						password, request a new link.
					</BodyText>
					<Link
						to="/forgot-password"
						className="mt-6 inline-flex w-full items-center justify-center rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-ink transition-opacity hover:opacity-90"
					>
						Request a reset link
					</Link>
				</Card>
			</div>
		);
	}

	if ( done )
	{
		return (
			<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
				<Card className="text-center">
					<div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-accent/10">
						<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent-strong)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
							<path d="M20 6 9 17l-5-5" />
						</svg>
					</div>
					<Heading level="h1" className="mb-2">Password reset</Heading>
					<BodyText>
						Your password has been reset. All existing sessions have been signed out.
					</BodyText>
					<Link
						to="/login"
						className="mt-6 inline-flex w-full items-center justify-center rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-ink transition-opacity hover:opacity-90"
					>
						Login with new password
					</Link>
				</Card>
			</div>
		);
	}

	return (
		<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
			<div>
				<Eyebrow>Account recovery</Eyebrow>
				<Heading level="h1">Reset password</Heading>
				<BodyText className="mt-2">Choose a new password for your account.</BodyText>
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
									<Label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">New password</Label>
									<Input
										id={ field.name }
										type="password"
										autoComplete="new-password"
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
									<Label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">Confirm new password</Label>
									<Input
										id={ field.name }
										type="password"
										autoComplete="new-password"
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

					{ resetPassword.isError && (
						<BodySm className="text-critical">{ apiError( resetPassword.error ) ?? 'Could not reset your password. The link may have expired.' }</BodySm>
					)}

					<form.Subscribe selector={ ( state ) => [ state.canSubmit, state.isPristine ] }>
						{ ( [ canSubmit, isPristine ] ) =>
							(
								<button
									type="submit"
									disabled={ !canSubmit || isPristine || resetPassword.isPending }
									className="inline-flex w-full items-center justify-center rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-ink transition-opacity hover:opacity-90 disabled:opacity-50"
								>
									{ resetPassword.isPending ? 'Resetting…' : 'Reset password' }
								</button>
							)}
					</form.Subscribe>
				</form>

				<BodySm className="mt-5 text-text-secondary">
					<Link to="/login" className="font-semibold text-accent-strong hover:underline">
						Back to sign in
					</Link>
				</BodySm>
			</Card>
		</div>
	);
}
