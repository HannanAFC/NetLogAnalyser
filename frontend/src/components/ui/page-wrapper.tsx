import type { HTMLAttributes, ReactNode } from 'react';
import { cn } from '#/lib/utils';

type PageWidth = 'md' | '4xl' | '6xl';

const widthClasses: Record< PageWidth, string > =
{
	md:  'max-w-md',
	'4xl': 'max-w-4xl',
	'6xl': 'max-w-6xl'
};

export interface PageWrapperProps extends HTMLAttributes< HTMLDivElement >
{
	children:  ReactNode;
	maxWidth?: PageWidth;
}

export function PageWrapper( { children, maxWidth = '6xl', className, ...props }: PageWrapperProps )
{
	return (
		<div
			className={ cn(
				'mx-auto w-full px-4 py-8 sm:px-6 lg:px-8 flex flex-col gap-8',
				widthClasses[ maxWidth ],
				className
			) }
			{ ...props }
		>
			{ children }
		</div>
	);
}
