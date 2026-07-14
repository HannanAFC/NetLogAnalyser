import { useForm } from '@tanstack/react-form';
import { createFileRoute, Link, redirect, useNavigate } from '@tanstack/react-router';
import { useRegister } from '../features/auth/hooks';
import { sessionQueryOptions } from '../features/auth/queries';
import { registerSchema } from '../features/auth/schemas';

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
			await register.mutateAsync( registerSchema.parse( value ) );
			await navigate( { to: '/dashboard', replace: true } );
		},
	});

	const inputClass = "mt-1 w-full rounded-md border bg-surface-card px-3 py-2 font-sans text-sm text-text-primary placeholder:text-text-tertiary border-border focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500/40 transition-[border-color,box-shadow] duration-150";

	return (
		<div className="mx-auto mt-24 w-full max-w-sm px-4">
			<h1 className="heading-1 mb-2">Create an account</h1>
			<p className="body-sm mb-8">Set up your NetLogAnalyser dashboard account.</p>
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
							<label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">
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
                                <p className="mt-1 text-xs text-critical">
                                    { field.state.meta.errors[ 0 ]?.message }
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
							<label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">
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
								<p className="mt-1 text-xs text-critical">
									{ field.state.meta.errors[ 0 ]?.message }
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
							<label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">
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
                                <p className="mt-1 text-xs text-critical">
                                    { field.state.meta.errors[ 0 ]?.message }
                                </p>
                            )}
						</div>
					)}
				</form.Field>

				<form.Field
					name="confirm_password"
					validators={{ onChange: registerSchema.shape.confirm_password, onBlur: registerSchema.shape.confirm_password }}
				>
					{ ( field ) =>
					(
						<div>
							<label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">
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
                                <p className="mt-1 text-xs text-critical">
                                    { field.state.meta.errors[ 0 ]?.message }
                                </p>
                            )}
						</div>
					)}
				</form.Field>

				{ register.isError && (
					<p className="text-sm text-critical">Couldn't create that account. Try a different email.</p>
				)}

				<form.Subscribe selector={ ( state ) => [ state.canSubmit, state.isPristine ] }>
					{ ( [ canSubmit, isPristine ] ) =>
					(
						<button
							type="submit"
							disabled={ !canSubmit || isPristine || register.isPending }
							className="inline-flex w-full items-center justify-center font-mono text-xs font-medium cursor-pointer border-none no-underline transition-[opacity,background] duration-150 tracking-[0.01em] px-4 py-2.25 gap-1.75 rounded-md bg-green-500 text-[#0a0f0a] hover:opacity-[0.88] disabled:opacity-50"
						>
							{ register.isPending ? 'Creating account…' : 'Create account' }
						</button>
					)}
				</form.Subscribe>
			</form>

			<p className="mt-4 body-sm">
				Already have an account?{' '}
				<Link to="/login" className="font-medium text-green-500 hover:underline">
					Sign in
				</Link>
			</p>
		</div>
	);
}
