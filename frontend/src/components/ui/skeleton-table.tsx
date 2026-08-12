import { cn } from '#/lib/utils';
import type { HTMLAttributes } from 'react';

export interface SkeletonColumn
{
	skeletonWidth?:    string;
}

interface SkeletonTableRowProps extends HTMLAttributes< HTMLTableRowElement >
{
	columns: SkeletonColumn[ ];
}

export function SkeletonTableRow( { columns, className, ...props }: SkeletonTableRowProps )
{
	return (
		<tr className={ cn( 'animate-pulse border-b border-border last:border-0', className ) } { ...props }>
			{ columns.map( ( col, i ) =>
			(
				<td key={ i } className="px-3 py-2">
					<div className={ cn( 'h-8 rounded bg-card', col.skeletonWidth ?? 'w-10' ) } />
				</td>
			) ) }
		</tr>
	);
}

interface SkeletonTableRowsProps
{
	columns: SkeletonColumn[ ];
	count:   number;
}

interface EmptyTableRowsProps extends HTMLAttributes< HTMLTableRowElement >
{
	count: number;
}

export function SkeletonTableRows( { columns, count }: SkeletonTableRowsProps )
{
	return (
		<tbody>
			{ Array.from( { length: count }, ( _, i ) =>
			(
				<SkeletonTableRow key={ i } columns={ columns } />
			) ) }
		</tbody>
	);
}

export function EmptyTableRows( { count }: EmptyTableRowsProps )
{
	return (
		<tbody>
			{ Array.from( { length: count }, ( _, i ) =>
			(
				<tr key={ i } className='h-9.5 border-b border-border last:border-0'></tr>
			) ) }
		</tbody>
	);
}
