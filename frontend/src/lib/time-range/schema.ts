import { z } from 'zod';

export const timeRangePresetSchema = z.enum( [ '1h', '24h', '7d', '30d', 'custom' ] );
export type TimeRangePreset = z.infer< typeof timeRangePresetSchema >;

export const timeRangeSearchSchema = z.object(
{
	preset: timeRangePresetSchema.default( '24h' ).catch( '24h' ),
	start:  z.iso.datetime( { offset: true } ).optional( ).catch( undefined ),
	end:    z.iso.datetime( { offset: true } ).optional( ).catch( undefined )
} );
export type TimeRangeSearch = z.infer< typeof timeRangeSearchSchema >;