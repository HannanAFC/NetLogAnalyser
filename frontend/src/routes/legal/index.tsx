import { Card } from '#/components/ui/card';
import { Heading } from '#/components/ui/heading';
import { PageWrapper } from '#/components/ui/page-wrapper';
import { createFileRoute, Link } from '@tanstack/react-router';

export const Route = createFileRoute( '/legal/' )(
{
    component: LegalPage,
    head: ( ) => (
    {
        links:
		[
			{
				rel: 'canonical',
				href: 'https://www.netloganalyser.com/legal'
			}
		],
        meta:
        [
            {
                title: 'Legal | NetLogAnalyser'
            },
            {
                name: 'description',
                content: 'Legal information regarding NetLogAnalyser.'
            },
            {
				name: 'og:title',
				content: 'NetLogAnalyser - Legal'
			},
			{
				name: 'og:description',
				content: 'Legal information regarding NetLogAnalyser.'
			},
			{
				name: 'twitter:title',
				content: 'NetLogAnalyser - Legal'
			},
			{
				name: 'twitter:description',
				content: 'Legal information regarding NetLogAnalyser.'
			},
			{
				name: 'og:url',
				content: 'https://www.netloganalyser.com/legal'
			},
			{
				name: 'twitter:url',
				content: 'https://www.netloganalyser.com/legal'
			}
        ]
    } )
} );

function LegalPage( )
{
    return (
        <PageWrapper maxWidth='4xl'>
            <Heading level="h1" className="max-w-2xl">Legal Information</Heading>
            <section className='grid grid-cols-2 gap-4'>
                <Link to='/legal/privacy-policy'>
                    <Card glow={ true } className='h-full'>
                        <Heading level='h2'>Privacy Policy</Heading>
                    </Card>
                </Link>
                <Link to='/legal/terms'>
                    <Card glow={ true } className='h-full'>
                        <Heading level='h2'>Terms & Conditions</Heading>
                    </Card>
                </Link>
            </section>
        </PageWrapper>
    );
}
