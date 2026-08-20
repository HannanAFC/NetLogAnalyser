import { TermsContent } from '#/components/legal/terms-content';
import { Heading } from '#/components/ui/heading';
import { PageWrapper } from '#/components/ui/page-wrapper';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute( '/legal/terms' )(
{
    component: TermsPage,
    head: ( ) => (
    {
        links:
		[
			{
				rel: 'canonical',
				href: 'https://www.netloganalyser.com/terms'
			}
		],
		meta:
        [
			{
                title: 'Terms & Conditions | NetLogAnalyser'
            },
			{
                name: 'description',
                content: 'The terms that govern your use of NetLogAnalyser.'
            },
            {
				name: 'og:title',
				content: 'NetLogAnalyser - Terms & Conditions'
			},
			{
				name: 'og:description',
				content: 'The terms that govern your use of NetLogAnalyser.'
			},
			{
				name: 'twitter:title',
				content: 'NetLogAnalyser - Terms & Conditions'
			},
			{
				name: 'twitter:description',
				content: 'The terms that govern your use of NetLogAnalyser.'
			},
			{
				name: 'og:url',
				content: 'https://www.netloganalyser.com/terms'
			},
			{
				name: 'twitter:url',
				content: 'https://www.netloganalyser.com/terms'
			}
		]
	} )
} );

function TermsPage( )
{
    return (
        <PageWrapper className="lg:py-14 gap-0">
            <Heading level='h1' className='mb-6'>Terms & Conditions</Heading>
            <TermsContent />
        </PageWrapper>
    );
}