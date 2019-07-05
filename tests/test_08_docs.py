import os
import re
import json
import pytest
import copy
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


def find_nested_entities(data, ignore_type=None, nested_entities=None):
    if nested_entities is None: nested_entities = []

    if isinstance(data, dict):
        if 'type' in data and data['type'] != ignore_type:
            nested_entities.append(copy.deepcopy(data))
            data.pop('_mocked_system_properties', None)
            data.pop('_final_doc', None)
        else:
            for key, item in data.items():
                if not isinstance(item, (dict, list, tuple)): continue
                if key == '_mocked_system_properties' or key == '_final_doc': continue

                find_nested_entities(item, ignore_type=ignore_type, nested_entities=nested_entities)
    elif isinstance(data, (list, tuple)):
        for item in data:
            find_nested_entities(item, ignore_type=ignore_type, nested_entities=nested_entities)
    else:
        pass  # do nothing


def test_docs(testdoc, schemas, resolvers):
    doc_name, schema_id, ok, json_data = testdoc

    # process nested entities first (if any), look for object with 'type' property
    nested_entities = []
    find_nested_entities(json_data, ignore_type=schema_id, nested_entities=nested_entities)
    #assert False, json.dumps(json_data, indent=2)

    for entity in nested_entities:
        s = entity['type']
        mocked_system_doc = entity.pop('_mocked_system_properties', None)
        final_doc = entity.pop('_final_doc', None)
        Draft7Validator(schemas[s],
                        resolver=resolvers[s],
                        format_checker=draft7_format_checker).validate(entity)

        if final_doc and mocked_system_doc:
            assert final_doc == {**entity, **mocked_system_doc}

    mocked_system_doc = json_data.pop('_mocked_system_properties', None)
    final_doc = json_data.pop('_final_doc', None)

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


    if final_doc and mocked_system_doc:
        assert final_doc == {**json_data, **mocked_system_doc}
