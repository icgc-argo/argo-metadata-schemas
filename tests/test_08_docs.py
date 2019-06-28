import os
import re
import json
import pytest
from glob import glob
from jsonschema import Draft7Validator, RefResolver, draft7_format_checker


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
                raise(Exception("Testing JSON doc %s name does not match 'd+.(schema_id).d+.(ok)|(ko).json'!" % d))

        metafunc.parametrize('testdoc', testdocs)


def test_docs(testdoc, schemas, resolvers):
    doc_name, schema_id, ok, json_data = testdoc
    mocked_system_doc = json_data.pop('_mocked_system_properties', None)

    resolver = resolvers[schema_id]

    if ok.lower() == 'ok':
        try:
            Draft7Validator(schemas[schema_id],
                            resolver=resolver,
                            format_checker=draft7_format_checker).validate(json_data)
        except:
            assert False, 'Test on %s failed validation!' % testdoc

    elif ok.lower() == 'ko':
        invalid = False
        try:
            Draft7Validator(schemas[schema_id],
                            resolver=resolver,
                            format_checker=draft7_format_checker).validate(json_data)
        except:
            invalid = True

        if invalid:  # expect to be invalid
            assert True
        else:
            assert False, 'Test %s should fail but it passed validation!' % testdoc

    else:
        assert False, 'This should never happen, current test doc: "%s"' % doc_name

    if mocked_system_doc:
        json_data_final = {**json_data, **mocked_system_doc}
        assert len(json_data_final) == len(json_data) + len(mocked_system_doc), \
            'System properties: "%s" overlap with submitted properties: "%s"' % \
            (", ".join(list(mocked_system_doc.keys())), ", ".join(list(json_data.keys())))

        # TODO: add validation test to cover json_data_final
