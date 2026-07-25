import { Card } from '#/components/ui/card';
import { BodySm, BodyText, Eyebrow, Heading } from '#/components/ui/heading';
import { useRegister } from '#/features/auth/hooks';
import { sessionQueryOptions } from '#/features/auth/queries';
import { registerSchema } from '#/features/auth/schemas';
import { apiError } from '#/lib/api/errors';
import { fieldError } from '#/lib/utils';
import { useForm } from '@tanstack/react-form';
import { createFileRoute, Link, redirect } from '@tanstack/react-router';
import { useState } from 'react';
import { Input, Label } from '../components/ui/input';

export const Route = createFileRoute( '/register' )(
	{
		beforeLoad: async( { context } ) =>
		{
			const session = await context.queryClient.ensureQueryData( sessionQueryOptions );
			if ( session ) throw redirect( { to: '/dashboard' } );
		},
		component: RegisterPage
	} );

function RegisterPage( )
{
	const register = useRegister( );
	const [ registeredEmail, setRegisteredEmail ] = useState< string | null >( null );

	const form = useForm(
		{
			defaultValues: { email: '', display_name: '', password: '', confirm_password: '' },
			onSubmit: async( { value } ) =>
			{
				try
				{
					const parsed = registerSchema.parse( value );
					await register.mutateAsync( parsed );
					setRegisteredEmail( parsed.email );
				}
				catch
				{
				// already handled
				}
			}
		} );

	if ( registeredEmail )
	{
		return (
			<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
				<Card className="p-8 text-center">
					<div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-accent/10">
						<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent-strong)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
							<rect x="2" y="4" width="20" height="16" rx="2" />
							<path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
						</svg>
					</div>
					<Heading level="h1" className="mb-2">Check your email</Heading>
					<BodyText>
						We sent a verification link to{' '}
						<span className="font-semibold text-text-primary">{ registeredEmail }</span>.
					</BodyText>
					<BodySm className="mt-3">
						Click the link in the email to verify your address. If you don&apos;t see it, check
						your spam folder or request a new one below.
					</BodySm>

					<div className="mt-6 space-y-3">
						<Link
							to="/login"
							className="inline-flex w-full items-center justify-center rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-ink transition-opacity hover:opacity-90"
						>
							Continue to sign in
						</Link>
						<Link
							to="/verify-email"
							className="block text-sm font-medium text-accent-strong hover:underline"
						>
							Resend verification email
						</Link>
					</div>
				</Card>
			</div>
		);
	}

	return (
		<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
			<div>
				<Eyebrow>Create your workspace</Eyebrow>
				<Heading level="h1">Register</Heading>
				<BodyText className="mt-2">Set up your account to start streaming ingest and live observability.</BodyText>
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
						validators={{ onChange: registerSchema.shape.email, onBlur: registerSchema.shape.email }}
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

					<form.Field
						name="display_name"
						validators={{ onChange: registerSchema.shape.display_name, onBlur: registerSchema.shape.display_name }}
					>
						{ ( field ) =>
							(
								<div>
									<Label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">Display name</Label>
									<Input
										id={ field.name }
										type="text"
										autoComplete="username"
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
						name="password"
						validators={{ onChange: registerSchema.shape.password, onBlur: registerSchema.shape.password }}
					>
						{ ( field ) =>
							(
								<div>
									<Label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">Password</Label>
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
									<Label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">Confirm password</Label>
									<Input
										id={ field.name }
										type="password"
										autoComplete="new-password"
										value={ field.state.value}
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

					{ register.isError && (
						<BodySm className="text-critical">{ apiError( register.error ) ?? "Couldn't create that account. Try a different email." }</BodySm>
					)}

					<form.Subscribe selector={ ( state ) => [ state.canSubmit, state.isPristine ] }>
						{ ( [ canSubmit, isPristine ] ) =>
							(
								<button
									type="submit"
									disabled={ !canSubmit || isPristine || register.isPending }
									className="inline-flex w-full items-center justify-center rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-ink transition-opacity hover:opacity-90 disabled:opacity-50"
								>
									{ register.isPending ? 'Creating account…' : 'Create account' }
								</button>
							)}
					</form.Subscribe>
				</form>

				<BodySm className="mt-5 text-text-secondary">
					Already have an account?{' '}
					<Link to="/login" className="font-semibold text-accent-strong hover:underline">
						Sign in
					</Link>
				</BodySm>
			</Card>
		</div>
	);
}
