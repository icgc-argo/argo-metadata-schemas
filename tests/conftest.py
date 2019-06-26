import os
import sys
import yaml
from glob import glob
import pytest

rootDir = os.path.dirname(os.path.abspath(__file__)) + '/../dictionary/'
os.chdir(rootDir)

# get config
with open('_settings.conf', 'r') as c:
    cfg = yaml.load(c, yaml.SafeLoader)

base_path = '/'.join(('http://dcc.icgc-argo.org', 'schemas', cfg['id'], cfg['version']))


@pytest.fixture(scope="session")
def base_url():
    return base_path


@pytest.fixture(scope="session")
def schemas():
    schemas = {}

    # read in all schemas
    for s in glob('*.yaml'):
        id = s.replace('.yaml', '')
        with open(s, 'r') as f:
            schemas[id] = yaml.load(f, yaml.SafeLoader)
 
    return schemas


@pytest.fixture(scope="session")
def metaschema():

    with open('_meta-schemas/draft-00.yaml', 'r') as m:
        metaschema = yaml.load(m, yaml.SafeLoader)

    del metaschema['$schema']
    return metaschema
