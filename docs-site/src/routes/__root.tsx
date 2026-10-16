import { createRootRoute, HeadContent, Outlet, Scripts } from '@tanstack/react-router';
import appCss from '@/styles/app.css?url';
import { RootProvider } from 'fumadocs-ui/provider/tanstack';
import { TanStackDevtools } from '@tanstack/react-devtools';
import { TanStackRouterDevtoolsPanel } from '@tanstack/react-router-devtools';
import { env } from '@/lib/env';

export const Route = createRootRoute(
    {
        head: ( ) => (
        {
            links:
            [
                {
                    rel: 'icon',
                    type: 'image/png',
                    href: '/favicon-96x96.png',
                    sizes: '96x96'
                },
                {
                    rel: 'icon',
                    type: 'image/svg+xml',
                    href: '/favicon.svg'
                },
                {
                    rel: 'shortcut icon',
                    href: '/favicon.ico'
                },
                {
                    rel: 'apple-touch-icon',
                    sizes: '180x180',
                    href: '/apple-touch-icon.png'
                },
                {
                    rel: 'manifest',
                    href: '/manifest.json'
                },
                {
                    rel: 'canonical',
                    href: env.docsUrl
                },
                {
                    rel: 'stylesheet',
                    href: appCss
                }
            ],
            meta:
            [
                {
                    charSet: 'utf-8'
                },
                {
                    name: 'viewport',
                    content: 'width=device-width, initial-scale=1'
                },
                {
                    title: 'NetLogAnalyser Docs'
                }
            ]
        } ),
        component: RootComponent
    } );

function RootComponent( )
{
    return (
        <html suppressHydrationWarning>
            <head>
                <HeadContent />
            </head>
            <body className="flex flex-col min-h-screen">
                <RootProvider>
                    <Outlet />
                </RootProvider>
                <Scripts />
                { import.meta.env.DEV && (
                    <TanStackDevtools
                        plugins={
                        [
                            {
                                name: 'TanStack Router',
                                render: <TanStackRouterDevtoolsPanel />
                            }
                        ] }
                    />
                ) }
            </body>
        </html>
    );
}
