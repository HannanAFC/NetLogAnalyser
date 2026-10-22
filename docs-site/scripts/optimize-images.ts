// Converts the PNG sources in assets/screenshots into responsive AVIF + WebP variants in public/screenshots.
// Run with `pnpm optimize:images` after adding or replacing a source screenshot, and commit the output.
import { mkdir, readdir, rm, writeFile } from 'node:fs/promises';
import { basename, extname, join } from 'node:path';
import sharp from 'sharp';

const sourceDir = 'assets/screenshots';
const outputDir = 'public/screenshots';
const widths    = [ 640, 1024, 1920 ];

await rm( outputDir, { recursive: true, force: true } );
await mkdir( outputDir, { recursive: true } );

const manifest: Record<string, { width: number; height: number; widths: number[] }> = { };

for ( const file of ( await readdir( sourceDir ) ).filter( ( f ) => extname( f ) === '.png' ) )
{
    const name = basename( file, '.png' );
    const input = sharp( join( sourceDir, file ) ).removeAlpha( );
    const meta = await input.metadata( );
    const { width: srcWidth, height: srcHeight } = meta;

    const sizes = [ ...new Set( [ ...widths.filter( ( w ) => w < srcWidth! ), Math.min( srcWidth!, 1920 ) ] ) ];

    for ( const w of sizes )
    {
        const resized = input.clone( ).resize( { width: w } );
        await resized.clone( ).avif( { quality: 55, effort: 6 } ).toFile( join( outputDir, `${ name }-${ w }.avif` ) );
        await resized.clone( ).webp( { quality: 80, effort: 6 } ).toFile( join( outputDir, `${ name }-${ w }.webp` ) );
    }

    // Large JPEG used for social cards and as the <img> fallback, which crawlers handle better than AVIF
    await input.clone( ).resize( { width: Math.min( srcWidth!, 1200 ) } ).jpeg( { quality: 82, mozjpeg: true } ).toFile( join( outputDir, `${ name }.jpg` ) );

    manifest[ name ] = { width: srcWidth!, height: srcHeight!, widths: sizes };
    console.log( `${ name }: ${ sizes.join( ', ' ) }` );
}

await writeFile( join( outputDir, 'manifest.json' ), JSON.stringify( manifest, null, 2 ) + '\n' );
