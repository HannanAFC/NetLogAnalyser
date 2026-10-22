import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';
import { gitConfig, titleAppName } from './shared';
import { env } from './env';
import { LayoutDashboard, Network, BookOpenText } from 'lucide-react';

export function baseOptions( ): BaseLayoutProps
{
    return {
        nav:
        {
            // JSX supported
            title: titleAppName
        },
        githubUrl: `https://github.com/${ gitConfig.user }/${ gitConfig.repo }`,
        links:
        [
            {
                text: 'Documentation',
                icon: <BookOpenText />,
                url: '/docs'
            },
            {
                text: 'Dashboard',
                icon: <LayoutDashboard />,
                url: env.frontendUrl
            },
            {
                text: 'API Page',
                icon: <Network />,
                url: env.backendUrl
            }
        ]
    };
}
