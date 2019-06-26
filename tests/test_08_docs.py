import os
import re
import json
import pytest
from glob import glob
from jsonschema import Draft7Validator, RefResolver, draft7_format_checker


@pytest.fixture(scope="module")
def resolvers(base_url, schemas):
    # pre-cache all schemas here with keys being full url
    schemastore = {}
    for schema_id in schemas:
        schemastore["%s/%s" % (base_url, schema_id)] = schemas[schema_id]

    resolvers = {}
    for schema_id in schemas:
        if schema_id not in resolvers:
            resolvers[schema_id] = RefResolver("%s/%s" % (base_url, schema_id),
                                        schemas[schema_id],
                                        schemastore)

    return resolvers


def pytest_generate_tests(metafunc):
    if 'testdoc' in metafunc.fixturenames:
        testdocs = []
        for d in sorted(glob(os.path.join('_example_docs', '*.json'))):
            m = re.match(r'^_example_docs\/\d+\.(\w+)\.\d+\.(ok|ko)\.\w+$', d)
            if m:
                schema_id, ok = m.groups()

                with open(d, 'r') as f:
                    json_data = json.load(f)

                if isinstance(json_data, dict):
                    testdocs.append([d, schema_id, ok, json_data])
                elif isinstance(json_data, list):
                    for i, doc in enumerate(json_data):
                        if not isinstance(doc, dict):
                            raise(Exception("Test doc is not a JSON object, file: %s, doc index in the file: [%s]" % (d, i)))
                        testdocs.append(["%s:[%s]" % (d, i), schema_id, ok, doc])

            else:
                print(d)
                raise(Exception("Testing JSON doc %s name does not match 'd+.(schema_id).d+.(ok)|(ko).json'!" % d))

        metafunc.parametrize('testdoc', testdocs)


def test_docs(testdoc, schemas, resolvers):
    doc_name, schema_id, ok, json_data = testdoc
    print(doc_name)  # useful to display when a test failed
    resolver = resolvers[schema_id]

    if ok.lower() == 'ok':
        Draft7Validator(schemas[schema_id], resolver=resolver, format_checker=draft7_format_checker).validate(json_data)

    elif ok.lower() == 'ko':
        invalid = False
        try:
            Draft7Validator(schemas[schema_id], resolver=resolver, format_checker=draft7_format_checker).validate(json_data)
        except:
            invalid = True

        if invalid:  # expect to be invalid
            assert True
        else:
            print('JSON doc %s should fail but it passed schema validation!' % testdoc)
            assert False

    else:
        print("This should never happen, current test doc: %s" % doc_name)
        assert False
