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
            m = re.match(r'^_example_docs\/\d+\.(\w+)\.\d+[a-z0-9-]*\.(ok|ko)\.\w+$', d)
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

        metafunc.parametrize('testdoc', testdocs, ids=[v[0] for v in testdocs])


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


def convert_nested_ref_schema_to_local_properties(data=None, schema_id=None, schemas=None, resolvers=None):
    if data is None: data = {}

    if isinstance(data, dict):
        if '$ref' in data and 'definitions' in data:
            referenced_entity_type = data['$ref']

            local_properties = data['definitions']['systemProperties']
            data.pop('$ref')
            data.update(local_properties)
            # assert False, json.dumps(data, indent=2)

            # TODO: need to validate relationDef, although this may not be the best way
            if data['definitions'].get('relationDef'):
                relationDefSchema = data['definitions']['relationDef']
                relationDefDoc = data['definitions']['relationDef']['const']
                resolver = resolvers[schema_id]

                try:
                    Draft7Validator(relationDefSchema,
                                resolver=resolver,
                                format_checker=draft7_format_checker).validate(relationDefDoc)
                except:
                    assert False, 'Testing relationDef failed in "%s": "%s"' % (schema_id, relationDefDoc)

                for relationship in relationDefDoc.get('references', []):
                    if relationship['targetEntity'] == 'data_object':
                        assert referenced_entity_type in schemas, \
                            'No schema defined for the targetEntity "%s"' % referenced_entity_type
                    else:
                        assert relationship['targetEntity'] in schemas, \
                            'No schema defined for the targetEntity "%s"' % relationship['targetEntity']

                    assert len(relationship['targetKey']) == len(relationship['foreignKey']), \
                        'targetKey length differs foreignKey length'

                    for ref in relationship['targetKey']:
                        targetEntity, reffrag = ref.split('#')

                        if relationship['targetEntity'] == 'data_object':
                            assert targetEntity == referenced_entity_type, \
                                'targetEntity "%s" not in $ref: %s' % (relationship['targetEntity'], ref)
                        else:
                            assert targetEntity == relationship['targetEntity'], \
                                'targetEntity "%s" not in $ref: %s' % (relationship['targetEntity'], ref)

                        try:
                            resolver.resolve_fragment(schemas[targetEntity], reffrag)
                        except:
                            assert False, 'Testing "%s" references failed on targetKey $ref: "%s"' % (schema_id, reffrag)

                    for reffrag in relationship['foreignKey']:
                        assert reffrag.startswith('#')
                        try:
                            _, frag = reffrag.split('#')
                            resolver.resolve_fragment(schemas[schema_id], frag)
                        except:
                            assert False, 'Testing "%s" references failed on foreignKey $ref: "%s"' % (schema_id, reffrag)

        else:
            for _, item in data.items():
                if not isinstance(item, (dict, list, tuple)): continue

                convert_nested_ref_schema_to_local_properties(item, schema_id, schemas, resolvers)
    elif isinstance(data, (list, tuple)):
        for item in data:
            convert_nested_ref_schema_to_local_properties(item, schema_id, schemas, resolvers)
    else:
        pass


def merge_system_properties(schema, schema_id, schemas, resolvers):
    original_schema = copy.deepcopy(schema)
    systemProperties = original_schema.get('definitions', {}).get('systemProperties')

    # merge 'required'
    if 'required' in original_schema and 'required' in systemProperties:
        original_schema['required'].extend(systemProperties['required'])

    # merge 'propertyNames.enum'
    if original_schema.get('propertyNames', {}).get('enum', []) and \
        systemProperties.get('propertyNames', {}).get('enum', []):
        # propertyNames should have no overlap
        if set(original_schema['propertyNames']['enum']).intersection(
                set(systemProperties['propertyNames']['enum'])
            ):
            assert False, 'System properties overlap with normal properties in schema: %s' % json.dumps(schema)

        original_schema['propertyNames']['enum'].extend(systemProperties['propertyNames']['enum'])

    if 'properties' in original_schema:
        if 'properties' in systemProperties:
            original_schema['allOf'] = [
                {'properties': original_schema.pop('properties')},
                {'properties': systemProperties['properties']}
            ]
        elif 'allOf' in systemProperties:
            original_schema['allOf'] = [{'properties': original_schema.pop('properties')}] + \
                systemProperties['allOf']
        else:
            assert False, 'Invalid systemProperties definition in: %s' % original_schema
    elif 'allOf' in original_schema:
        if 'properties' in systemProperties:
            original_schema['allOf'].extend(
                {'properties': systemProperties['properties']}
            )
        elif 'allOf' in systemProperties:
            original_schema['allOf'].extend(systemProperties['allOf'])
        else:
            assert False, 'Invalid systemProperties definition in: %s' % original_schema
    else:
        assert False, 'Invalid schema definition: %s' % original_schema

    convert_nested_ref_schema_to_local_properties(original_schema, schema_id, schemas, resolvers)
    return original_schema


def test_docs(testdoc, schemas, resolvers):
    doc_name, schema_id, ok, json_data = testdoc

    # process nested entities first (if any), look for object with 'type' property
    nested_entities = []
    find_nested_entities(json_data, ignore_type=schema_id, nested_entities=nested_entities)
    # assert False, json.dumps(json_data, indent=2)

    for entity in nested_entities:
        s = entity['type']
        mocked_system_doc = entity.pop('_mocked_system_properties', None)
        final_doc = entity.pop('_final_doc', None)
        Draft7Validator(schemas[s],
                        resolver=resolvers[s],
                        format_checker=draft7_format_checker).validate(entity)

        if final_doc and mocked_system_doc:
            assert final_doc == {**entity, **mocked_system_doc}
            final_schema = merge_system_properties(schemas[s], s, schemas, resolvers)
            # assert False, json.dumps(final_schema, indent=2)
            Draft7Validator(final_schema, resolver=resolvers[s],
                        format_checker=draft7_format_checker).validate(final_doc)

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

        final_schema = merge_system_properties(schemas[schema_id], schema_id, schemas, resolvers)
        # assert False, json.dumps(final_schema, indent=2)
        Draft7Validator(final_schema, resolver=resolvers[schema_id],
                    format_checker=draft7_format_checker).validate(final_doc)
