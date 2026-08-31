import { Card } from '#/components/ui/card';
import { BodySm, BodyText, Eyebrow, Heading } from '#/components/ui/heading';
import { useForgotPassword } from '#/features/auth/hooks';
import { sessionQueryOptions } from '#/features/auth/queries';
import { forgotPasswordSchema } from '#/features/auth/schemas';
import { apiError } from '#/lib/api/errors';
import { fieldError } from '#/lib/utils';
import { useForm } from '@tanstack/react-form';
import { createFileRoute, Link, redirect } from '@tanstack/react-router';
import { useState } from 'react';
import { Input, Label } from '../components/ui/input';
import { configQueryOptions } from '#/features/config/queries';
import { Button } from '#/components/ui/button';

export const Route = createFileRoute( '/forgot-password' )(
{
	beforeLoad: async( { context } ) =>
	{
		const session = await context.queryClient.ensureQueryData( sessionQueryOptions );
		const config  = await context.queryClient.ensureQueryData( configQueryOptions );
		if ( session ) throw redirect( { to: '/dashboard' } );
		if ( config?.email_verification_enabled === false ) throw redirect( { to: '/' } );
	},
	component: ForgotPasswordPage,
	head: ( ) => (
	{
		meta:
		[
			{
				title: 'Forgot Password | NetLogAnalyser'
			},
			{
				name:    'robots',
				content: 'noindex, nofollow'
			}
		]
	} )
} );

function ForgotPasswordPage( )
{
	const forgotPassword = useForgotPassword( );
	const [ sent, setSent ] = useState( false );

	const form = useForm(
		{
			defaultValues: { email: '' },
			onSubmit: async( { value } ) =>
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
			}
		} );

	if ( sent )
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
						If an account with that email exists, we&apos;ve sent a password reset link.
					</BodyText>
					<BodySm className="mt-3">
						The link expires in 5 minutes. If you don&apos;t see it, check your spam folder.
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
				<Heading level="h1">Forgot password</Heading>
				<BodyText className="mt-2">Enter your email and we&apos;ll send you a link to reset your password.</BodyText>
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
						validators={{ onChange: forgotPasswordSchema.shape.email, onBlur: forgotPasswordSchema.shape.email }}
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

					{ forgotPassword.isError && (
						<BodySm className="text-critical">{ apiError( forgotPassword.error ) ?? 'Something went wrong. Try again.' }</BodySm>
					)}

					<form.Subscribe selector={ ( state ) => [ state.canSubmit, state.isPristine ] }>
						{ ( [ canSubmit, isPristine ] ) =>
							(
								<Button
									type="submit"
									disabled={ !canSubmit || isPristine || forgotPassword.isPending }
									className='w-full items-center justify-center'
								>
									{ forgotPassword.isPending ? 'Sending…' : 'Send reset link' }
								</Button>
							)}
					</form.Subscribe>
				</form>

				<BodySm className="mt-5 text-text-secondary">
					Remember your password?{' '}
					<Link to="/login" className="font-semibold text-accent-strong hover:underline">
						Login
					</Link>
				</BodySm>
			</Card>
		</div>
	);
}
