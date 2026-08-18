// components/ui/table-frame.tsx
import type { HTMLAttributes, ReactNode, RefObject } from 'react';
import { cn } from '#/lib/utils';

export type TableHeightVariant = 'sm' | 'md' | 'lg';

export const TableHeightClasses: Record< TableHeightVariant, string > =
{
	sm: 'max-h-100',
	md: 'max-h-200',
	lg: 'max-h-300'
};

export const TableHeightPx: Record< TableHeightVariant, number > =
{
	sm: 400,
	md: 800,
	lg: 1200
};

interface TableFrameProps extends HTMLAttributes< HTMLDivElement >
{
	scrollRef?:     RefObject< HTMLDivElement | null >;
	isEmpty:        boolean;
	isError?:       boolean;
	errorMessage?:  ReactNode;
	emptyMessage?:  ReactNode;
	maxHeight?:     TableHeightVariant;
	children:       ReactNode;
}

export function TableFrame(
{
	className,
	scrollRef,
	isEmpty,
	isError = false,
	errorMessage,
	emptyMessage,
	maxHeight = 'md',
	children,
	...props
}: TableFrameProps )
{
	const showOverlay = isError || isEmpty;
	const overlayContent = isError ? errorMessage ?? null : emptyMessage ?? null;

	return (
		<div className={ cn( 'shadow-card rounded-lg border border-border overflow-hidden', className ) } { ...props }>
			<div
				ref={ scrollRef }
				className={ cn(
					'overflow-y-auto relative h-full',
					TableHeightClasses[ maxHeight ],
					showOverlay && 'overflow-hidden'
				) }
			>
				{ children }

				<div
					className={ cn(
						'pointer-events-none absolute inset-x-0 bottom-0 top-0',
						'backdrop-blur-[3px] bg-linear-to-b from-transparent from-0% to-paper to-35%',
						'transition-opacity duration-150',
						showOverlay ? 'opacity-100' : 'opacity-0'
					) }
				/>
				<div
					className={ cn(
						'absolute inset-x-0 top-[50%] left-[50%] -translate-1/2 w-max max-w-4/5',
						showOverlay ? 'opacity-100' : 'opacity-0 pointer-events-none'
					) }
				>
					{ overlayContent }
				</div>
			</div>
		</div>
	);
}