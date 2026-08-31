import { Card } from '#/components/ui/card';
import { BodySm } from '#/components/ui/heading';
import { PageWrapper } from '#/components/ui/page-wrapper';
import { PageHeading } from '#/components/ui/page-heading';
import { useLogin } from '#/features/auth/hooks';
import { sessionQueryOptions } from '#/features/auth/queries';
import { loginSchema } from '#/features/auth/schemas';
import { apiError, isEmailNotVerifiedError } from '#/lib/api/errors';
import { useForm } from '@tanstack/react-form';
import { createFileRoute, Link, redirect, useNavigate } from '@tanstack/react-router';
import { z } from 'zod';
import { Input, Label } from '../components/ui/input';
import { useEmailVerificationEnabled } from '#/features/config/hooks';
import { Button } from '#/components/ui/button';

const loginSearchSchema = z.object(
	{
		redirect: z.string( ).optional( )
	} );

export const Route = createFileRoute( '/login' )(
{
	validateSearch: loginSearchSchema,
	beforeLoad: async( { context } ) =>
	{
		// Don't show form to logged in user
		const session = await context.queryClient.ensureQueryData( sessionQueryOptions );
		if ( session ) throw redirect( { to: '/dashboard' } );
	},
	component: LoginPage,
	head: ( ) => (
	{
		links:
		[
			{
				rel: 'canonical',
				href: 'https://www.netloganalyser.com/login'
			}
		],
		meta:
		[
			{
				title: 'Login | NetLogAnalyser'
			},
			{
				name: 'description',
				content: 'Sign in to your NetLogAnalyser account to access your real-time network monitoring dashboard.'
			},
			{
				name: 'og:title',
				content: 'NetLogAnalyser - Login'
			},
			{
				name: 'og:description',
				content: 'Sign in to your NetLogAnalyser account to access your real-time network monitoring dashboard.'
			},
			{
				name: 'twitter:title',
				content: 'NetLogAnalyser - Login'
			},
			{
				name: 'twitter:description',
				content: 'Sign in to your NetLogAnalyser account to access your real-time network monitoring dashboard.'
			},
			{
				name: 'og:url',
				content: 'https://www.netloganalyser.com/register'
			},
			{
				name: 'twitter:url',
				content: 'https://www.netloganalyser.com/register'
			}
		]
	} )
} );

function LoginPage()
{
	const { redirect: redirectTo } = Route.useSearch( );
	const navigate = useNavigate( );
	const login = useLogin( );
	const emailVerificationEnabled = useEmailVerificationEnabled( );

	const form = useForm(
		{
			defaultValues: { email: '', password: '' },
			onSubmit: async( { value } ) =>
			{
				await login.mutateAsync( loginSchema.parse( value ) );
				await navigate( { to: redirectTo ?? '/dashboard', replace: true } );
			}
		} );

	return (
		<PageWrapper maxWidth="md" className="py-16 gap-6">
			<PageHeading title="Login" description="Sign in to your NetLogAnalyser account to access your real-time network monitoring dashboard." />

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
						validators={{ onChange: loginSchema.shape.email, onBlur: loginSchema.shape.email }}
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
									<BodySm className="text-danger">
										{ field.state.meta.errors[ 0 ]?.message }
									</BodySm>
								) }
							</div>
						) }
					</form.Field>

					<form.Field
						name="password"
						validators={{ onChange: loginSchema.shape.password, onBlur: loginSchema.shape.password }}
					>
						{ ( field ) =>
						(
							<div>
								<Label htmlFor={ field.name } className="block text-sm font-medium text-text-primary">Password</Label>
								<Input
									id={ field.name }
									type="password"
									autoComplete="current-password"
									value={ field.state.value }
									onBlur={ field.handleBlur }
									onChange={ ( e ) => field.handleChange( e.target.value ) }
								/>
								{ field.state.meta.errors.length > 0 && (
									<BodySm className="text-danger">
										{ field.state.meta.errors[ 0 ]?.message }
									</BodySm>
								)}
							</div>
						)}
					</form.Field>

					{ login.isError && isEmailNotVerifiedError( login.error ) &&
					(
						<div className="rounded-md border border-accent-strong/30 bg-accent/5 px-4 py-3">
							<BodySm className="text-text-primary">
								Your email hasn't been verified yet.{' '}
								<Link to="/verify-email" className="font-semibold text-accent-strong hover:underline">
									Verify your email
								</Link>{' '}
								to sign in.
							</BodySm>
						</div>
					) }

					{ login.isError && !isEmailNotVerifiedError( login.error ) &&
					(
						<BodySm className="text-danger">
							{ apiError( login.error ) ?? 'An unexpected error occurred.' }
						</BodySm>
					) }

					{ emailVerificationEnabled === true &&
					(
						<div className="flex items-center justify-end">
							<Link to="/forgot-password" className="text-sm font-medium text-accent-strong hover:underline">
								Forgot password?
							</Link>
						</div>
					) }

					<form.Subscribe selector={ ( state ) => [ state.canSubmit, state.isPristine ] }>
						{ ( [ canSubmit, isPristine ] ) => (
							<Button
								type="submit"
								disabled={ !canSubmit || isPristine || login.isPending }
								className="w-full items-center justify-center"
							>
								{ login.isPending ? 'Logging in…' : 'Login' }
							</Button>
						)}
					</form.Subscribe>
				</form>

				<BodySm className="mt-5 text-text-secondary">
					No account?{' '}
					<Link to="/register" className="font-semibold text-accent-strong hover:underline">
						Register
					</Link>
				</BodySm>
			</Card>
		</PageWrapper>
	);
}
