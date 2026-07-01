import { type HTMLAttributes, type ReactNode } from 'react';
import { cn } from '../../lib/utils';

type HeadingLevel = 'h1' | 'h2' | 'h3';

export interface HeadingProps extends HTMLAttributes< HTMLHeadingElement >
{
    level?:   HeadingLevel;
    children: ReactNode;
}

/**
 * Semantic heading that uses the design-system typography classes.
 *
 *   h1  – page title       (clamp 26–36px, weight 500, tight leading)
 *   h2  – section heading   (clamp 20–26px)
 *   h3  – card / subsection  (17px)
 */
export function Heading(
{
    level = 'h1',
    className,
    children,
    ...props
}: HeadingProps )
{
    const Tag = level;

    const levelClass: Record< HeadingLevel, string > =
    {
        h1: 'heading-1',
        h2: 'heading-2',
        h3: 'heading-3'
    };

    return (
        <Tag className={ cn( levelClass[ level ], className ) } { ...props }>
            { children }
        </Tag>
    );
}

/* Utility typography components */

export function Eyebrow(
{
    className,
    children,
    ...props
}: HTMLAttributes< HTMLParagraphElement > )
{
    return (
        <p className={ cn('eyebrow', className ) } { ...props }>
            { children }
        </p>
    );
}

export function SectionTitle(
{
    className,
    children,
    ...props
}: HTMLAttributes< HTMLParagraphElement > )
{
    return (
        <p className={ cn( 'section-title', className ) } { ...props }>
            { children }
        </p>
    );
}

export function BodyText(
{
    className,
    children,
    ...props
}: HTMLAttributes< HTMLParagraphElement > )
{
    return (
        <p className={ cn( 'body-text', className ) } { ...props }>
            { children }
        </p>
    );
}

export function CodeInline(
{
    className,
    children,
    ...props
}: HTMLAttributes< HTMLElement > )
{
    return (
        <code className={ cn( 'code-inline', className ) } { ...props }>
            { children }
        </code>
    );
}
