# NetLogAnalyser Docs

This is a Fumadocs application that hosts the full documentation website for NetLogAnalyser. Opposed to the frontend, this is not a static build, a node server needs to be running in order to serve the search API, dynamic OpenGraph images and SSR.

## Testing
Testing is limited to linting, this is because code should rarely be modified, all documentation is written as `.mdx` files and is parsed by the server, so for documentation purposes, code shouldn't be touched.

## Build notes
In order to create the API reference, the application has to fetch the Open API schema from the backend before build time, it will attempt to retry this 3 times before continuing the build process. The `.mdx` files generated from this process are kept out of version control for now as they are automatically generated files and there are a lot of these files. However, the `meta.json` file is still included as it includes grouping for the pages.