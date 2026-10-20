import { createFileRoute, notFound } from '@tanstack/react-router';
import { DocsLayout } from 'fumadocs-ui/layouts/docs';
import { createServerFn } from '@tanstack/react-start';
import { docs, source } from '@/lib/source';
import {
    DocsBody,
    DocsDescription,
    DocsPage,
    DocsTitle,
    MarkdownCopyButton,
    ViewOptionsPopover
} from 'fumadocs-ui/layouts/docs/page';
import { baseOptions } from '@/lib/layout.shared';
import { appName, getPageImageUrl, getPageMarkdownUrl, gitConfig } from '@/lib/shared';
import { useFumadocsLoader } from 'fumadocs-core/source/client';
import { Suspense, use } from 'react';
import { useMDXComponents } from '@/components/mdx';
import { OpenAPIPage } from '@/components/api-page';
import { openapi } from '@/lib/openapi';
import { env } from '@/lib/env';
import type { OpenAPIPageProps_Preloaded } from 'fumadocs-openapi/ui';

export const Route = createFileRoute( '/docs/$' )(
    {
        component: Page,
        loader: async( { params } ) =>
        {
            const slugs = params._splat?.split( '/' ) ?? [ ];
            const data  = await serverLoader( { data: slugs } );
            await docs.getPage( data.path )?.preload( );
            return data;
        },
        head: ( { loaderData } ) => (
        {
            meta: loaderData
                ? [
                    { title: `${ loaderData.title } | ${ appName }` },
                    { name: 'description', content: loaderData.description },
                    { property: 'og:title', content: loaderData.title },
                    { property: 'og:description', content: loaderData.description },
                    { property: 'og:site_name', content: appName },
                    { property: 'og:type', content: 'article' },
                    { property: 'og:url', content: loaderData.url },
                    { property: 'og:image', content: loaderData.imageUrl },
                    { name: 'twitter:card', content: 'summary_large_image' },
                    { name: 'twitter:url', content: loaderData.url },
                    { name: 'twitter:title', content: loaderData.title },
                    { name: 'twitter:description', content: loaderData.description },
                    { name: 'twitter:image', content: loaderData.imageUrl }
                ]
                : [ ]
        } )
    } );

const serverLoader = createServerFn( { method: 'GET' } )
  .validator( ( slugs: string[ ] ) => slugs )
  .handler( async( { data: slugs } ) =>
    {
        const page = source.getPage( slugs );
        if ( !page ) throw notFound( );
        const siteUrl = env.docsUrl;

        return {
            path:        page.path,
            url:         `${ siteUrl }${ page.url }`,
            title:       page.data.title,
            description: page.data.description ?? '',
            preloaded:   ( await openapi.preloadOpenAPIPage( page ) ).preloaded,
            markdownUrl: getPageMarkdownUrl( page ).url,
            imageUrl:    `${ siteUrl }${ getPageImageUrl( page ).url }`,
            pageTree:    await source.serializePageTree( source.getPageTree( ) )
        };
    } );

function Content( { path, markdownUrl, preloaded }: { path: string; markdownUrl: string; preloaded: OpenAPIPageProps_Preloaded[ 'preloaded' ] } )
{
    const page = docs.getPage( path );
    if ( !page ) throw new Error( `unknown page: ${ path }` );

    const { toc } = use( page.load( ) );
    const MDX = page.body;

    return (
        <DocsPage toc={ toc }>
            <DocsTitle>{ page.title }</DocsTitle>
            <DocsDescription>{ page.description }</DocsDescription>
            <div className="flex flex-row gap-2 items-center border-b -mt-4 pb-6">
                <MarkdownCopyButton markdownUrl={ markdownUrl } />
                <ViewOptionsPopover
                    markdownUrl={ markdownUrl }
                    githubUrl={ `https://github.com/${ gitConfig.user }/${ gitConfig.repo }/blob/${ gitConfig.branch }/docs-site/content/docs/${ path }` }
                />
            </div>
            <DocsBody>
                <MDX
                    components={ useMDXComponents( {
                        OpenAPIPage: ( props: Omit<OpenAPIPageProps_Preloaded, 'preloaded'> ) => <OpenAPIPage { ...props } preloaded={ preloaded } />
                    } ) }
                />
            </DocsBody>
        </DocsPage>
    );
}

function Page( )
{
    const { path, pageTree, markdownUrl, preloaded } = useFumadocsLoader( Route.useLoaderData( ) );

    return (
        <DocsLayout { ...baseOptions( ) } tree={ pageTree }>
            <Suspense>
                <Content path={ path } markdownUrl={ markdownUrl } preloaded={ preloaded } />
            </Suspense>
        </DocsLayout>
    );
}
