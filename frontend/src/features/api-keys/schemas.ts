import { z } from 'zod';

export const createApiKeySchema = z
    .object(
    {
        label: z.string( 'Please enter a valid label' ).trim( ).min( 1, 'Label must be at least 1 character long' ).max( 100, 'Label must be a maximum of 100 characters long' )
    } );
export type CreateApiKeyPayload = z.infer< typeof createApiKeySchema >;