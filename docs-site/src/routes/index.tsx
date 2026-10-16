import { createFileRoute, Link } from '@tanstack/react-router';
import { HomeLayout } from 'fumadocs-ui/layouts/home';
import { ArrowRight, BookOpenText, Code, Rocket, Server, ShieldCheck } from 'lucide-react';
import type { ReactNode } from 'react';
import { baseOptions } from '@/lib/layout.shared';
import { env } from '@/lib/env';

const title       = 'NetLogAnalyser Docs';
const description = 'Real-time network log analysis. Send packet data to a REST API, watch it stream live, and spot anomalies as they happen. Open source and self-hostable.';

export const Route = createFileRoute( '/' )(
    {
        component: Home,
        head: ( ) => (
        {
            meta:
            [
                { title },
                { name: 'description', content: description },
                { property: 'og:title', content: title },
                { property: 'og:description', content: description },
                { property: 'og:type', content: 'website' },
                { property: 'og:url', content: env.docsUrl },
                { property: 'og:image', content: `${ env.docsUrl }/dashboard-hero.png` },
                { name: 'twitter:url', content: env.docsUrl },
                { name: 'twitter:card', content: 'summary_large_image' },
                { name: 'twitter:title', content: title },
                { name: 'twitter:description', content: description },
                { name: 'twitter:image', content: `${ env.docsUrl }/dashboard-hero.png` }
            ]
        } )
    } );

function DocLink( { slug, className, children }: { slug: string; className?: string; children: ReactNode } )
{
    return (
        <Link to="/docs/$" params={ { _splat: slug } } className={ className }>
            { children }
        </Link>
    );
}

const buttonBase = 'inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors';
const primaryButton   = `${ buttonBase } bg-fd-primary text-fd-primary-foreground hover:opacity-90`;
const secondaryButton = `${ buttonBase } border border-fd-border bg-fd-card text-fd-foreground hover:bg-fd-accent`;

function Screenshot( { src, alt, width, height, className = '' }: { src: string; alt: string; width: number; height: number; className?: string } )
{
    return (
        <div className={ `overflow-hidden rounded-xl border border-fd-border bg-fd-card shadow-lg ${ className }` }>
            <img src={ src } alt={ alt } width={ width } height={ height } loading="lazy" className="block h-auto w-full" />
        </div>
    );
}

interface FeatureProps
{
    eyebrow:  string;
    heading:  string;
    body:     string;
    href:     string;
    linkText: string;
    image:    { src: string; alt: string; width: number; height: number };
    flip?:    boolean;
}

function Feature( { eyebrow, heading, body, href, linkText, image, flip }: FeatureProps )
{
    return (
        <section className="grid items-center gap-8 lg:grid-cols-2 lg:gap-14">
            <div className={ flip ? 'lg:order-2' : '' }>
                <p className="mb-2 text-sm font-medium text-fd-primary">{ eyebrow }</p>
                <h2 className="mb-4 text-2xl font-semibold tracking-tight sm:text-3xl">{ heading }</h2>
                <p className="mb-5 leading-relaxed text-fd-muted-foreground">{ body }</p>
                <DocLink slug={ href } className="inline-flex items-center gap-1.5 text-sm font-medium text-fd-primary hover:underline">
                    { linkText } <ArrowRight className="size-4" />
                </DocLink>
            </div>
            <Screenshot { ...image } className={ flip ? 'lg:order-1' : '' } />
        </section>
    );
}

const pathways =
[
    {
        icon: Rocket,
        title: 'Getting started',
        text: 'Create an account and API key, and send your first log in a few minutes.',
        slug: 'getting-started'
    },
    {
        icon: Code,
        title: 'Sending logs',
        text: 'The ingest API: fields, batching, limits and error handling.',
        slug: 'sending-logs'
    },
    {
        icon: ShieldCheck,
        title: 'Anomaly detection',
        text: 'How scores and reasons are calculated, and how to tune them.',
        slug: 'anomaly-detection'
    },
    {
        icon: Server,
        title: 'Self-hosting',
        text: 'Run the whole stack yourself with one command.',
        slug: 'selfhost-install'
    }
];

function Home( )
{
    return (
        <HomeLayout { ...baseOptions( ) }>
            <main className="mx-auto flex w-full max-w-6xl flex-col gap-20 px-4 pb-24 pt-14 sm:gap-28 sm:pt-20">

                {/* Hero */}
                <section className="flex flex-col items-center text-center">
                    <p className="mb-4 rounded-full border border-fd-border bg-fd-card px-3 py-1 text-xs font-medium text-fd-muted-foreground">
                        Open source &middot; Self-hostable
                    </p>
                    <h1 className="max-w-3xl text-4xl font-semibold tracking-tight sm:text-6xl">
                        Network logs, analysed in real time.
                    </h1>
                    <p className="mt-5 max-w-2xl text-base leading-relaxed text-fd-muted-foreground sm:text-lg">
                        Send packet data to a simple REST API. NetLogAnalyser enriches it with geo information and anomaly scores,
                        and streams it to a live dashboard.
                    </p>
                    <div className="mt-8 flex flex-wrap justify-center gap-3">
                        <DocLink slug="getting-started" className={ primaryButton }>
                            Get started <ArrowRight className="size-4" />
                        </DocLink>
                        <DocLink slug="selfhost-install" className={ secondaryButton }>
                            <Server className="size-4" /> Self-host it
                        </DocLink>
                        <DocLink slug="API" className={ secondaryButton }>
                            <BookOpenText className="size-4" /> API reference
                        </DocLink>
                    </div>

                    <div className="relative mt-14 w-full max-w-5xl">
                        <div className="max-h-128 overflow-hidden rounded-xl border border-fd-border bg-fd-card shadow-xl sm:max-h-160">
                            <img
                                src="/dashboard-hero.png"
                                alt="The NetLogAnalyser dashboard showing summary statistics and a packet volume chart"
                                width={ 1920 }
                                height={ 1080 }
                                className="block h-auto w-full"
                            />
                        </div>
                        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-32 rounded-b-xl bg-linear-to-t from-fd-background to-transparent" />
                    </div>
                </section>

                {/* Features */}
                <Feature
                    eyebrow="Live feed"
                    heading="Watch traffic as it arrives"
                    body="Entries stream to your browser the moment they are ingested, each with its source and destination, protocol, packet size, country and anomaly score."
                    href="dashboard"
                    linkText="Tour the dashboard"
                    image={ { src: '/live-feed.png', alt: 'The live feed table showing new log entries with anomaly scores', width: 1045, height: 362 } }
                />

                <Feature
                    flip
                    eyebrow="Anomaly detection"
                    heading="Know why something looks wrong"
                    body="Every entry gets a score from 0 to 1 and a list of reasons: XMAS scans, invalid flag combinations, port scans, unusual packet sizes and protocol mismatches. Filter by minimum score and expand any row to see the details."
                    href="anomaly-detection"
                    linkText="How scoring works"
                    image={ { src: '/anomalies.png', alt: 'The anomalies table with expanded rows listing the reasons for each score', width: 1039, height: 390 } }
                />

                <Feature
                    eyebrow="Geo map"
                    heading="See where traffic comes from"
                    body="Source and destination IPs are resolved to countries with MaxMind GeoLite2 and shown on a world map, alongside a ranked breakdown by location."
                    href="dashboard"
                    linkText="Explore the analytics"
                    image={ { src: '/geomap.png', alt: 'A world map shaded by packet count with a table of the top countries', width: 2246, height: 1049 } }
                />

                <Feature
                    flip
                    eyebrow="API keys"
                    heading="Send logs from anywhere"
                    body="Create a key per sender, label it, and revoke it at any time. Keys are stored only as hashes, and each one authenticates a single header on one ingest endpoint."
                    href="sending-logs"
                    linkText="Read the ingest guide"
                    image={ { src: '/api-keys.png', alt: 'The API keys settings page listing active keys with revoke buttons', width: 832, height: 423 } }
                />

                {/* Self-hosting */}
                <section className="rounded-2xl border border-fd-border bg-fd-card p-6 sm:p-10">
                    <div className="mx-auto max-w-3xl text-center">
                        <h2 className="mb-3 text-2xl font-semibold tracking-tight sm:text-3xl">Run it yourself in one command</h2>
                        <p className="mb-6 text-fd-muted-foreground">
                            The installer pulls prebuilt images and generates your secrets. You get the API, dashboard, database,
                            Redis and background worker, with your data staying on your own machine.
                        </p>
                        <pre className="overflow-x-auto rounded-lg border border-fd-border bg-fd-muted p-4 text-left font-mono text-xs sm:text-sm">
                            <code>curl -fsSL https://raw.githubusercontent.com/HannanAFC/NetLogAnalyser/main/selfhost/install.sh | bash</code>
                        </pre>
                        <div className="mt-6 flex flex-wrap justify-center gap-3">
                            <DocLink slug="selfhost-install" className={ primaryButton }>
                                Self-hosting guide <ArrowRight className="size-4" />
                            </DocLink>
                            <DocLink slug="selfhost-configuration" className={ secondaryButton }>
                                Configuration reference
                            </DocLink>
                        </div>
                    </div>
                </section>

                {/* Pathways */}
                <section>
                    <h2 className="mb-8 text-center text-2xl font-semibold tracking-tight sm:text-3xl">Where to next</h2>
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                        { pathways.map( ( { icon: Icon, title: cardTitle, text, slug } ) => (
                            <DocLink
                                key={ slug }
                                slug={ slug }
                                className="group flex flex-col gap-2 rounded-xl border border-fd-border bg-fd-card p-5 transition-colors hover:bg-fd-accent"
                            >
                                <Icon className="size-5 text-fd-primary" />
                                <span className="font-medium">{ cardTitle }</span>
                                <span className="text-sm text-fd-muted-foreground">{ text }</span>
                            </DocLink>
                        ) ) }
                    </div>
                </section>
            </main>
        </HomeLayout>
    );
}
