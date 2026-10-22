// Captures the screenshots used on the docs landing page from a running dev stack, then optimises them.
//
//   docker compose --profile dev up        # backend :8000 and frontend :3000
//   pnpm generate:screenshots
//
// A demo account, API keys and synthetic traffic are created through the backend API (see screenshots/seed.ts),
// each page is captured in both themes, and the PNGs land in assets/screenshots as `<name>-<theme>.png` for `optimize:images`.
//
// This creates an account and thousands of log entries, so it refuses to run against anything but a local stack
// unless SCREENSHOT_ALLOW_REMOTE=1 is set.
import { mkdir } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { chromium, type Locator, type Page } from 'playwright';
import { demo, freshTraffic, ingest, seed } from './screenshots/seed.ts';

const frontend  = process.env.SCREENSHOT_FRONTEND_URL ?? 'http://localhost:3000';
const backend   = process.env.SCREENSHOT_BACKEND_URL  ?? 'http://localhost:8000';
const outputDir = 'assets/screenshots';
const themes    = [ 'dark', 'light' ] as const;
type Theme = typeof themes[ number ];

const localHosts = new Set( [ 'localhost', '127.0.0.1', '[::1]', 'host.docker.internal', 'backend', 'frontend' ] );

function assertLocal( label: string, url: string )
{
    const { hostname } = new URL( url );
    if ( localHosts.has( hostname ) || hostname.endsWith( '.localhost' ) || process.env.SCREENSHOT_ALLOW_REMOTE === '1' )
    {
        return;
    }
    throw new Error(
        `Refusing to run against ${ label } "${ url }": the generator registers a demo account and ingests fake traffic, so it only targets a local dev stack. `
        + 'Set SCREENSHOT_ALLOW_REMOTE=1 if you really mean it.' );
}

assertLocal( 'the frontend', frontend );
assertLocal( 'the backend', backend );
const viewport  = { width: 1440, height: 900 };
// The hero is shown at 16:9 on the landing page, so it gets a larger viewport. At 1.5x every source is crisp for 2x
// screens at the sizes the landing page displays them, without bloating the committed PNGs.
const heroViewport = { width: 1920, height: 1080 };
const scale        = 1.5;
const rateLimitWindowSeconds = 20;

// Dev-only UI that should never end up in a screenshot (TanStack devtools trigger)
const hideChrome = '#tanstack_devtools, body > button[class^="go"], [class^="go"][aria-label*="devtools" i] { display: none !important; }';

async function login( page: Page )
{
    await page.goto( `${ frontend }/login` );
    await page.getByLabel( 'Email' ).fill( demo.email );
    await page.getByLabel( 'Password' ).fill( demo.password );
    await page.getByRole( 'button', { name: /sign in|log in|login/i } ).click( );
    await page.waitForURL( /\/dashboard/ );
}

async function open( page: Page, path: string )
{
    await page.goto( `${ frontend }${ path }` );
    await page.addStyleTag( { content: hideChrome } );
}

// Screenshot a region of the page, with a little breathing room around it
async function shoot( page: Page, name: string, theme: Theme, target: Locator, options: { maxHeight?: number } = { } )
{
    const { maxHeight = Infinity } = options;
    const box = await target.boundingBox( );
    if ( !box ) throw new Error( `${ name }: nothing to capture` );

    await page.screenshot(
        {
            path:       `${ outputDir }/${ name }-${ theme }.png`,
            animations: 'disabled',
            fullPage:   true, // a clip below the fold is otherwise cut off at the viewport
            clip:       { x: box.x, y: box.y, width: box.width, height: Math.min( box.height, maxHeight ) }
        } );
    console.log( `  ${ name }-${ theme }` );
}

async function shootViewport( page: Page, name: string, theme: Theme )
{
    await page.screenshot( { path: `${ outputDir }/${ name }-${ theme }.png`, animations: 'disabled' } );
    console.log( `  ${ name }-${ theme }` );
}

const tableFrame = ( page: Page ) => page.locator( 'table' ).first( ).locator( 'xpath=ancestor::div[contains(@class,"shadow-card")][1]' );

console.log( 'Seeding demo data' );
console.log( backend );
const keys = await seed( backend );

await mkdir( outputDir, { recursive: true } );

const browser = await chromium.launch( );

async function session( theme: Theme )
{
    const context = await browser.newContext( { viewport: heroViewport, deviceScaleFactor: scale, colorScheme: theme, reducedMotion: 'reduce' } );
    await context.addInitScript( ( mode ) => localStorage.setItem( 'netloganalyser-theme', mode ), theme );
    const page = await context.newPage( );
    await login( page );
    return page;
}

try
{
    console.log( 'Capturing' );

    for ( const [ index, theme ] of themes.entries( ) )
    {
        if ( index > 0 )
        {
            // Each theme makes enough API calls to hit the general rate limit (RATELIMIT_GENERAL_*) if run back to back
            console.log( `Waiting ${ rateLimitWindowSeconds }s for the API rate limit window to reset` );
            await new Promise( ( resolve ) => setTimeout( resolve, rateLimitWindowSeconds * 1000 ) );
        }

        console.log( `${ theme } theme` );
        const page = await session( theme );

        await page.setViewportSize( heroViewport );
        await open( page, '/dashboard?preset=1h' );
        await page.getByText( 'Live', { exact: true } ).waitFor( );
        await page.locator( 'svg path' ).nth( 10 ).waitFor( { state: 'attached' } );
        await page.waitForTimeout( 800 );
        await shootViewport( page, 'dashboard-hero', theme );

        await page.setViewportSize( viewport );

        // The newest rows should be seconds old, so send a fresh burst just before the live feed capture
        await open( page, '/live-feed' );
        await page.getByText( 'Live', { exact: true } ).waitFor( );
        await ingest( backend, keys, freshTraffic( 12 ) );
        await page.waitForTimeout( 1500 );
        await shoot( page, 'live-feed', theme, tableFrame( page ), { maxHeight: 380 } );

        await open( page, '/anomalies?min_score=0.5' );
        await page.getByRole( 'button', { name: 'Expand row' } ).first( ).waitFor( );
        for ( let i = 0; i < 2; i++ )
        {
            await page.getByRole( 'button', { name: 'Expand row' } ).first( ).click( );
        }
        await page.waitForTimeout( 500 );
        await shoot( page, 'anomalies', theme, tableFrame( page ), { maxHeight: 400 } );

        await open( page, '/geomap' );
        await page.locator( 'table' ).first( ).waitFor( );
        await page.locator( 'svg path' ).nth( 50 ).waitFor( { state: 'attached' } );
        await page.waitForTimeout( 1000 );
        await shoot( page, 'geomap', theme, page.locator( 'div.grid' ).filter( { has: page.locator( 'table' ) } ).first( ) );

        await open( page, '/settings?tab=api-keys' );
        await page.getByRole( 'heading', { name: /Active keys/ } ).waitFor( );
        await shoot( page, 'api-keys', theme, page.locator( 'div[class*="rounded"]' ).filter( { has: page.getByRole( 'heading', { name: /Active keys/ } ) } ).last( ) );

        await page.context( ).close( );
    }
}
finally
{
    await browser.close( );
}

console.log( 'Optimising' );
const optimised = spawnSync( 'pnpm', [ 'run', 'optimize:images' ], { stdio: 'inherit' } );
process.exit( optimised.status ?? 1 );
