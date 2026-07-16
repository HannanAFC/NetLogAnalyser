import { useForm } from '@tanstack/react-form';
import { createFileRoute, Link, redirect, useNavigate } from '@tanstack/react-router';
import { useRegister } from '../features/auth/hooks';
import { sessionQueryOptions } from '../features/auth/queries';
import { registerSchema } from '../features/auth/schemas';
import { apiError } from '../lib/api/errors';
import { fieldError } from '../lib/utils';

export const Route = createFileRoute( '/register' )(
{
	beforeLoad: async ( { context } ) =>
	{
		const session = await context.queryClient.ensureQueryData( sessionQueryOptions );
		if ( session ) throw redirect( { to: '/dashboard' } );
	},
	component: RegisterPage
});

function RegisterPage( )
{
	const navigate = useNavigate( );
	const register = useRegister( );

	const form = useForm(
	{
		defaultValues: { email: '', display_name: '', password: '', confirm_password: '' },
		onSubmit: async ( { value } ) =>
		{
			try
			{
				await register.mutateAsync( registerSchema.parse( value ) );
				await navigate( { to: '/dashboard', replace: true } );
			}
			catch
			{
				// already handled
			}
		},
	});

	const inputClass = "mt-1 w-full rounded-md border border-border bg-[var(--color-card)] px-3 py-2.5 text-[14px] text-text-primary placeholder:text-text-tertiary focus:border-[var(--color-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]/25 transition-[border-color,box-shadow] duration-150";

	return (
		<div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
			<div>
				<p className="eyebrow">Create your workspace</p>
				<h1 className="heading-1">Register</h1>
				<p className="body-text mt-2">Set up your account to start streaming ingest and live observability.</p>
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
						validators={{ onChange: registerSchema.shape.email, onBlur: registerSchema.shape.email }}
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

					<form.Field
						name="display_name"
						validators={{ onChange: registerSchema.shape.display_name, onBlur: registerSchema.shape.display_name }}
					>
						{ ( field ) =>
						(
							<div>
								<label htmlFor={ field.name } className="block text-[13px] font-medium text-text-primary">
									Display name
								</label>
								<input
									id={ field.name }
									type="text"
									autoComplete="username"
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
						name="password"
						validators={{ onChange: registerSchema.shape.password, onBlur: registerSchema.shape.password }}
					>
						{ ( field ) =>
						(
							<div>
								<label htmlFor={ field.name } className="block text-[13px] font-medium text-text-primary">
									Password
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
									Confirm password
								</label>
								<input
									id={ field.name }
									type="password"
									autoComplete="new-password"
									value={ field.state.value}
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

					{ register.isError && (
						<p className="text-[13px] text-critical">{ apiError( register.error ) ?? "Couldn't create that account. Try a different email." }</p>
					)}

					<form.Subscribe selector={ ( state ) => [ state.canSubmit, state.isPristine ] }>
						{ ( [ canSubmit, isPristine ] ) =>
						(
							<button
								type="submit"
								disabled={ !canSubmit || isPristine || register.isPending }
								className="inline-flex w-full items-center justify-center rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-[13px] font-semibold text-[var(--color-ink)] transition-opacity hover:opacity-90 disabled:opacity-50"
							>
								{ register.isPending ? 'Creating account…' : 'Create account' }
							</button>
						)}
					</form.Subscribe>
				</form>

				<p className="mt-5 text-[13px] text-text-secondary">
					Already have an account?{' '}
					<Link to="/login" className="font-semibold text-[var(--color-accent-strong)] hover:underline">
						Sign in
					</Link>
				</p>
			</div>
		</div>
	);
}
