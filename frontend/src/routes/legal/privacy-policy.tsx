import { PrivacyPolicyContent } from '#/components/legal/privacy-policy-content';
import { Heading } from '#/components/ui/heading';
import { PageWrapper } from '#/components/ui/page-wrapper';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute( '/legal/privacy-policy' )(
{
    component: PrivacyPolicyPage,
    head: ( ) => (
    {
        links:
		[
			{
				rel: 'canonical',
				href: 'https://www.netloganalyser.com/privacy-policy'
			}
		],
        meta:
        [
            {
                title: 'Privacy Policy | NetLogAnalyser'
            },
            {
                name: 'description',
                content: 'How NetLogAnalyser collects, uses, and protects your data.'
            },
            {
				name: 'og:title',
				content: 'NetLogAnalyser - Privacy Policy'
			},
			{
				name: 'og:description',
				content: 'How NetLogAnalyser collects, uses, and protects your data.'
			},
			{
				name: 'twitter:title',
				content: 'NetLogAnalyser - Privacy Policy'
			},
			{
				name: 'twitter:description',
				content: 'How NetLogAnalyser collects, uses, and protects your data.'
			},
			{
				name: 'og:url',
				content: 'https://www.netloganalyser.com/privacy-policy'
			},
			{
				name: 'twitter:url',
				content: 'https://www.netloganalyser.com/privacy-policy'
			}
        ]
    } )
} );

function PrivacyPolicyPage( )
{
    return (
		<PageWrapper className="lg:py-14 gap-0">
			<Heading level='h1' className='mb-6'>Privacy Policy</Heading>
			<PrivacyPolicyContent />
		</PageWrapper>
	);
}
