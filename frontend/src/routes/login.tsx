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
        <div className="mx-auto mt-24 w-full max-w-sm px-4">
            <h1 className="heading-1 mb-2">Sign in</h1>
            <p className="body-sm mb-8">Enter your credentials to access the dashboard.</p>

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
                                className="mt-1 w-full rounded-md border bg-surface-card px-3 py-2 font-sans text-sm text-text-primary placeholder:text-text-tertiary border-border focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500/40 transition-[border-color,box-shadow] duration-150"
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
                    validators={{ onChange: loginSchema.shape.password, onBlur: loginSchema.shape.password }}
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
                            autoComplete="current-password"
                            value={ field.state.value }
                            onBlur={ field.handleBlur }
                            onChange={ ( e ) => field.handleChange( e.target.value ) }
                            className="mt-1 w-full rounded-md border bg-surface-card px-3 py-2 font-sans text-sm text-text-primary placeholder:text-text-tertiary border-border focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500/40 transition-[border-color,box-shadow] duration-150"
                        />
                        { field.state.meta.errors.length > 0 && (
                            <p className="mt-1 text-xs text-critical">
                                { field.state.meta.errors[ 0 ]?.message }
                            </p>
                        )}
                    </div>
                )}
                </form.Field>

                { login.isError && (
                <p className="text-sm text-critical">Incorrect email or password.</p>
                )}

                <form.Subscribe selector={ ( state ) => [ state.canSubmit, state.isPristine ] }>
                { ( [ canSubmit, isPristine ] ) => (
                    <button
                        type="submit"
                        disabled={ !canSubmit || isPristine || login.isPending }
                        className="inline-flex w-full items-center justify-center font-mono text-xs font-medium cursor-pointer border-none no-underline transition-[opacity,background] duration-150 tracking-[0.01em] px-4 py-[9px] gap-[7px] rounded-md bg-green-500 text-[#0a0f0a] hover:opacity-[0.88] disabled:opacity-50"
                    >
                    { login.isPending ? 'Signing in…' : 'Sign in' }
                    </button>
                )}
                </form.Subscribe>
            </form>

            <p className="mt-4 body-sm">
                No account?{' '}
                <Link to="/register" className="font-medium text-green-500 hover:underline">
                    Register
                </Link>
            </p>
        </div>
    );
}
