import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { forwardRef } from 'react';
import { cn } from '../../lib/utils';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md';

const variantClasses: Record<ButtonVariant, string> =
	{
		primary:
        'bg-accent text-ink hover:opacity-90 ',
		secondary:
        'bg-transparent text-text-secondary border border-border-hi ' +
        'hover:text-text-primary hover:border-border-hi/50',
		ghost:
        'bg-transparent text-text-secondary hover:text-text-primary hover:bg-card',
		danger:
        'bg-danger text-ink border-border ' +
        'hover:opacity-80'
	};

const sizeClasses: Record< ButtonSize, string > =
	{
		sm: 'px-3 py-1.5 text-[11px] gap-1.5 rounded-sm',
		md: 'px-4 py-[9px] text-xs gap-[7px] rounded-md'
	};

export interface ButtonProps extends ButtonHTMLAttributes< HTMLButtonElement >
{
	variant?: ButtonVariant;
	size?:    ButtonSize;
	children: ReactNode
}

export const Button = forwardRef< HTMLButtonElement, ButtonProps >(
	(
		{ variant = 'primary', size = 'md', className, children, ...props },
		ref
	) =>
	{
		return (
			<button
				ref={ ref }
				className={ cn(
					'inline-flex items-center font-mono font-medium',
					'cursor-pointer no-underline',
					'transition-[opacity,background,color,border-color] duration-150',
					'tracking-[0.01em] disabled:opacity-50',
					variantClasses[ variant ],
					sizeClasses[ size ],
					className
				) }
				{ ...props }
			>
				{ children }
			</button>
		);
	}
);

Button.displayName = 'Button';
