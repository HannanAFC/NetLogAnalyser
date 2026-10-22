// Converts the PNG sources in assets/screenshots into responsive AVIF + WebP variants in public/screenshots.
// The output is generated (and gitignored), so this runs before dev, build and type checking. Filenames carry a hash of
// the source and of this script, which lets the files be cached forever, and unchanged sources are not re-encoded.
// Pass --force to re-encode regardless.
import { createHash } from 'node:crypto';
import { mkdir, readdir, readFile, rm, writeFile } from 'node:fs/promises';
import { basename, extname, join } from 'node:path';
import sharp from 'sharp';

const sourceDir    = 'assets/screenshots';
const outputDir    = 'public/screenshots';
const manifestPath = join( outputDir, 'manifest.json' );
const widths       = [ 640, 1024, 1920 ];
const force        = process.argv.includes( '--force' );

interface ManifestEntry
{
    width:  number;
    height: number;
    widths: number[];
    hash:   string;
}

const script = await readFile( new URL( import.meta.url ) );
const files  = ( await readdir( sourceDir ) ).filter( ( f ) => extname( f ) === '.png' ).sort( );

const hashes: Record<string, string> = { };
for ( const file of files )
{
    hashes[ basename( file, '.png' ) ] = createHash( 'sha256' ).update( await readFile( join( sourceDir, file ) ) ).update( script ).digest( 'hex' ).slice( 0, 10 );
}

if ( !force )
{
    try
    {
        const existing: Record<string, ManifestEntry> = JSON.parse( await readFile( manifestPath, 'utf8' ) );
        const names = Object.keys( hashes );

        // The manifest is committed but the images are not, so a fresh checkout has one without the other
        const present = new Set( await readdir( outputDir ) );
        const complete = names.every( ( name ) => existing[ name ]?.hash === hashes[ name ]
            && present.has( `${ name }.${ hashes[ name ] }.jpg` )
            && existing[ name ].widths.every( ( w ) => present.has( `${ name }.${ hashes[ name ] }-${ w }.avif` ) && present.has( `${ name }.${ hashes[ name ] }-${ w }.webp` ) ) );

        if ( names.length === Object.keys( existing ).length && complete )
        {
            console.log( 'Screenshots are up to date' );
            process.exit( 0 );
        }
    }
    catch
    {
        // No manifest yet, or an unreadable one: generate everything
    }
}

await rm( outputDir, { recursive: true, force: true } );
await mkdir( outputDir, { recursive: true } );

const manifest: Record<string, ManifestEntry> = { };

for ( const file of files )
{
    const name  = basename( file, '.png' );
    const hash  = hashes[ name ];
    const input = sharp( join( sourceDir, file ) ).removeAlpha( );
    const { width: srcWidth, height: srcHeight } = await input.metadata( );

    const sizes = [ ...new Set( [ ...widths.filter( ( w ) => w < srcWidth! ), Math.min( srcWidth!, 1920 ) ] ) ];

    for ( const w of sizes )
    {
        const resized = input.clone( ).resize( { width: w } );
        await resized.clone( ).avif( { quality: 55, effort: 6 } ).toFile( join( outputDir, `${ name }.${ hash }-${ w }.avif` ) );
        await resized.clone( ).webp( { quality: 80, effort: 6 } ).toFile( join( outputDir, `${ name }.${ hash }-${ w }.webp` ) );
    }

    // Large JPEG used for social cards and as the <img> fallback, which crawlers handle better than AVIF
    await input.clone( ).resize( { width: Math.min( srcWidth!, 1200 ) } ).jpeg( { quality: 82, mozjpeg: true } ).toFile( join( outputDir, `${ name }.${ hash }.jpg` ) );

    manifest[ name ] = { width: srcWidth!, height: srcHeight!, widths: sizes, hash };
    console.log( `${ name }: ${ sizes.join( ', ' ) }` );
}

await writeFile( manifestPath, JSON.stringify( manifest, null, 2 ) + '\n' );
