## Example JSON Documents

This folder contains example JSON documents used for testing.

### JSON file naming convention

The file follows this naming pattern: `^(ok)|(ko)\.\d+\.(schema_id)\.\d+\.json$`. JSON starts
with `ok` are to pass while starting with `ko` will fail schema validation.

Assigning files with different numbers allow us to control the order how the files are
processed. This will make it possible to support dependency (relationship) check across
different JSONs in the future.
