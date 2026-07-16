import { useForm } from '@tanstack/react-form';
import { createFileRoute, Link, redirect, useNavigate } from '@tanstack/react-router';
import { z } from 'zod';
import { useLogin } from '../features/auth/hooks';
import { sessionQueryOptions } from '../features/auth/queries';
import { loginSchema } from '../features/auth/schemas';

const loginSearchSchema = z.object(
{
    redirect: z.string( ).optional( ),
});

export const Route = createFileRoute( '/login' )(
{
    validateSearch: loginSearchSchema,
    beforeLoad: async ( { context } ) =>
    {
        // Don't show form to logged in user
        const session = await context.queryClient.ensureQueryData( sessionQueryOptions );
        if ( session ) throw redirect( { to: '/dashboard' } );
    },
    component: LoginPage
});

function LoginPage() {
    const { redirect: redirectTo } = Route.useSearch( );
    const navigate = useNavigate( );
    const login = useLogin( );

    const form = useForm(
    {
        defaultValues: { email: '', password: '' },
        onSubmit: async ( { value } ) =>
        {
            await login.mutateAsync( loginSchema.parse( value ) );
            await navigate( { to: redirectTo ?? '/dashboard', replace: true } );
        }
    });

    return (
        <div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 sm:px-6">
            <div>
                <p className="eyebrow">Secure access</p>
                <h1 className="heading-1">Sign in</h1>
                <p className="body-text mt-2">Enter your credentials to access the live operations view.</p>
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
                        validators={{ onChange: loginSchema.shape.email, onBlur: loginSchema.shape.email }}
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
                                    className="mt-1 w-full rounded-md border border-border bg-[var(--color-card)] px-3 py-2.5 text-[14px] text-text-primary placeholder:text-text-tertiary focus:border-[var(--color-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]/25 transition-[border-color,box-shadow] duration-150"
                                />
                                { field.state.meta.errors.length > 0 && (
                                    <p className="mt-1 text-[12px] text-critical">
                                        { field.state.meta.errors[ 0 ]?.message }
                                    </p>
                                )}
                            </div>
                        )}
                    </form.Field>

                    <form.Field
                        name="password"
                        validators={{ onChange: loginSchema.shape.password, onBlur: loginSchema.shape.password }}
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
                                autoComplete="current-password"
                                value={ field.state.value }
                                onBlur={ field.handleBlur }
                                onChange={ ( e ) => field.handleChange( e.target.value ) }
                                className="mt-1 w-full rounded-md border border-border bg-[var(--color-card)] px-3 py-2.5 text-[14px] text-text-primary placeholder:text-text-tertiary focus:border-[var(--color-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]/25 transition-[border-color,box-shadow] duration-150"
                            />
                            { field.state.meta.errors.length > 0 && (
                                <p className="mt-1 text-[12px] text-critical">
                                    { field.state.meta.errors[ 0 ]?.message }
                                </p>
                            )}
                        </div>
                    )}
                    </form.Field>

                    { login.isError && (
                    <p className="text-[13px] text-critical">Incorrect email or password.</p>
                    )}

                    <form.Subscribe selector={ ( state ) => [ state.canSubmit, state.isPristine ] }>
                    { ( [ canSubmit, isPristine ] ) => (
                        <button
                            type="submit"
                            disabled={ !canSubmit || isPristine || login.isPending }
                            className="inline-flex w-full items-center justify-center rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-[13px] font-semibold text-[var(--color-ink)] transition-opacity hover:opacity-90 disabled:opacity-50"
                        >
                        { login.isPending ? 'Signing in…' : 'Sign in' }
                        </button>
                    )}
                    </form.Subscribe>
                </form>

                <p className="mt-5 text-[13px] text-text-secondary">
                    No account?{' '}
                    <Link to="/register" className="font-semibold text-[var(--color-accent-strong)] hover:underline">
                        Register
                    </Link>
                </p>
            </div>
        </div>
    );
}
