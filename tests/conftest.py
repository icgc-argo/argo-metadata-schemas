import os
import sys
import yaml
from glob import glob
import pytest
from jsonschema import RefResolver


rootDir = os.path.dirname(os.path.abspath(__file__)) + '/../schemas/'
os.chdir(rootDir)


# get schema name and release version
with open('_definitions.yaml', 'r') as c:
    cfg = yaml.load(c, yaml.SafeLoader)

base_path = '/'.join(('http://dcc.icgc-argo.org',
                        'schemas',
                        cfg['_']['properties']['id']['const'],
                        cfg['_']['properties']['release']['const']
                    ))


@pytest.fixture(scope="session")
def base_url():
    return base_path


@pytest.fixture(scope="session")
def schemas():
    schemas = {}

    # read in all schemas.
    for s in glob('*.yaml') + glob('*/*.yaml'):
        with open(s, 'r') as f:
            schema = yaml.load(f, yaml.SafeLoader)
            schemas[schema['$id']] = schema
 
    return schemas


@pytest.fixture(scope="session")
def schemastore(base_url, schemas):
    # pre-cache all schemas here with keys being full url
    schemastore = {}
    for schema_id in schemas:
        schemastore["%s/%s" % (base_url, schema_id)] = schemas[schema_id]

    return schemastore


@pytest.fixture(scope="session")
def resolvers(base_url, schemastore, schemas):
    resolvers = {}
    for schema_id in schemas:
        if schema_id not in resolvers:
            resolvers[schema_id] = RefResolver("%s/%s" % (base_url, schema_id),
                                        schemas[schema_id],
                                        schemastore)

    return resolvers
