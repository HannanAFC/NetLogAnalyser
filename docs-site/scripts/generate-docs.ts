import { generateFiles } from 'fumadocs-openapi';
import { openapi } from '../src/lib/openapi.ts';

void generateFiles(
    {
        input:              openapi,
        output:             './content/docs/API',
        includeDescription: true
    } );