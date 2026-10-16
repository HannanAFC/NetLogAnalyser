import { createOpenAPI } from 'fumadocs-openapi/server';
import { env } from './env.ts';

export const openapi = createOpenAPI(
    {
        input:
        {
            my_schema: async( ) =>
                {
                    const res = await fetch( env.openapiUrl );
                    return res.json( );
                }
        }
    } );