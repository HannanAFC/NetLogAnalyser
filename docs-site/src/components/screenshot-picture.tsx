import manifest from '../../public/screenshots/manifest.json';

type Theme = 'dark' | 'light';

// Manifest keys are `<name>-<theme>`; the component takes the bare name and renders both themes
export type ScreenshotName = keyof typeof manifest extends infer Key ? Key extends `${ infer Name }-${ Theme }` ? Name : never : never;

interface ScreenshotPictureProps
{
    name:       ScreenshotName;
    alt:        string;
    sizes:      string;
    className?: string;
    priority?:  boolean;
}

const themeClass: Record<Theme, string> = { light: 'dark:hidden', dark: 'hidden dark:block' };

const variants = ( key: keyof typeof manifest, format: 'avif' | 'webp' ): string =>
    manifest[ key ].widths.map( ( w ) => `/screenshots/${ key }-${ w }.${ format } ${ w }w` ).join( ', ' );

// Both themes are rendered and the inactive one is hidden with CSS, so the site's theme toggle switches instantly.
// Lazy images that are display:none are never fetched, so below the fold only the visible theme downloads. The priority
// (hero) image is eager, which means a visitor also downloads the other theme's hero, but at this size that is a few KB.
export function ScreenshotPicture( { name, alt, sizes, className = '', priority = false }: ScreenshotPictureProps )
{
    return (
        <>
            { ( [ 'light', 'dark' ] as const ).map( ( theme ) =>
            {
                const key = `${ name }-${ theme }` as keyof typeof manifest;
                const { width, height } = manifest[ key ];

                return (
                    <picture key={ theme }>
                        <source type="image/avif" srcSet={ variants( key, 'avif' ) } sizes={ sizes } />
                        <source type="image/webp" srcSet={ variants( key, 'webp' ) } sizes={ sizes } />
                        <img
                            src={ `/screenshots/${ key }.jpg` }
                            alt={ alt }
                            width={ width }
                            height={ height }
                            className={ `${ className } ${ themeClass[ theme ] }` }
                            loading={ priority ? 'eager' : 'lazy' }
                            fetchPriority={ priority ? 'high' : 'auto' }
                            decoding={ priority ? 'sync' : 'async' }
                        />
                    </picture>
                );
            } ) }
        </>
    );
}
