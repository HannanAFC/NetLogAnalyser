import { z } from 'zod';

export const timeRangePresetSchema = z.enum( [ '15m', '1h', '6h', '12h', '24h', '7d', '15d', '30d', 'custom' ] );
export type TimeRangePreset = z.infer< typeof timeRangePresetSchema >;

export const timeRangeSearchSchema = z.object(
{
	preset: timeRangePresetSchema.default( '24h' ).catch( '24h' ),
	start:  z.iso.datetime( { offset: true } ).optional( ).catch( undefined ),
	end:    z.iso.datetime( { offset: true } ).optional( ).catch( undefined )
} );
export type TimeRangeSearch = z.infer< typeof timeRangeSearchSchema >;