import type { AnyFieldApi } from '@tanstack/react-form';

export function FieldInfo( { field }: { field: AnyFieldApi } )
{
	if ( !field.state.meta.isTouched || field.state.meta.errors.length === 0 )
	{
		return null;
	}
	return (
		<p className="mt-1 text-xs text-red-600">
			{ field.state.meta.errors.map( ( error ) => error.message ).join( ', ' ) }
		</p>
	);
}