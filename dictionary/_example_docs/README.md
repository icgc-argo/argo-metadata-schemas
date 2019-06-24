## Example JSON Documents

This folder contains example JSON documents used for testing. Note that TSV files may be used as well if data is more appropriate to be represented in tabular format.

### JSON file naming convention

The file follows this naming pattern: `^\d+\.(schema_id)\.\d+\.(ok)|(ko)\.json$`. JSON file
with `ok` are to pass while with `ko` will fail schema validation.

Assigning files with different numbers allow us to control the order how the files are
processed. This will make it possible to support dependency (relationship) check across
different JSONs.
