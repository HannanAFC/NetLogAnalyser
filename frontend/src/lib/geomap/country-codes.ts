import countries from 'i18n-iso-countries';
import enLocale from 'i18n-iso-countries/langs/en.json';

countries.registerLocale( enLocale );

export function numericToAlpha2( numericId: string ): string | undefined
{
	return countries.numericToAlpha2( numericId ) ?? undefined;
}

export function numericToName( numericId: string ): string | undefined
{
	return countries.getName( numericId, 'en' ) ?? undefined;
}