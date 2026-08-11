import type { HTMLAttributes } from 'react';
import { BodyText, Eyebrow, Heading } from '#/components/ui/heading';

export interface PageHeadingProps extends HTMLAttributes< HTMLDivElement >
{
	eyebrow?:      string;
	title:         string;
	description?:  string;
}

export function PageHeading( { eyebrow, title, description, className, ...props }: PageHeadingProps )
{
	return (
		<div className={ className } { ...props }>
			{ eyebrow && <Eyebrow>{ eyebrow }</Eyebrow> }
			<Heading level="h1">{ title }</Heading>
			{ description && <BodyText className="mt-2">{ description }</BodyText> }
		</div>
	);
}
