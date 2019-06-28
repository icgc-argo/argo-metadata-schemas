from glob import glob
import yaml
from jsonschema import Draft7Validator, validate, draft7_format_checker, RefResolver

def test_schema(schemas):
    for s in schemas:
        Draft7Validator.check_schema(schemas[s])


def pytest_generate_tests(metafunc):
    if 'testdoc' in metafunc.fixturenames:
        testdocs = []

        for schema_file in glob('*.yaml'):
            if schema_file == '_definitions.yaml': continue

            id = schema_file.replace('.yaml', '')
            with open(schema_file, 'r') as f:
                s = yaml.load(f, yaml.SafeLoader)

            relationDefDoc = s.get('definitions', {}).get('relationDef', {}).get('const')
            testdocs.append([id, relationDefDoc])

        metafunc.parametrize('testdoc', testdocs)


def test_relationDef(testdoc, schemas, resolvers):
    s, relationDefDoc = testdoc
    relationDefSchema = schemas['_definitions']['relationDef']

    resolver = resolvers[s]

    try:
        Draft7Validator(relationDefSchema,
                    resolver=resolver,
                    format_checker=draft7_format_checker).validate(relationDefDoc)
    except:
        assert False, 'Testing relationDef failed in "%s": "%s"' % (s, relationDefDoc)

    if 'primaryKey' not in relationDefDoc:
        assert False, 'Missing primaryKey'
    else:
        for reffrag in relationDefDoc['primaryKey']:
            try:
                resolver.resolve_fragment(schemas[s], reffrag.lstrip("#"))
            except:
                assert False, 'Testing "%s" relationDef failed on primaryKey $ref: "%s"' % (s, reffrag)

    for reffrag in relationDefDoc.get('naturalKey', []):
        try:
            resolver.resolve_fragment(schemas[s], reffrag.lstrip("#"))
        except:
            assert False, 'Testing "%s" relationDef failed on naturalKey $ref: "%s"' % (s, reffrag)

    for key in relationDefDoc.get('uniqueKey', []):
        for reffrag in key:
            try:
               resolver.resolve_fragment(schemas[s], reffrag.lstrip("#"))
            except:
                assert False, 'Testing "%s" relationDef failed on uniqueKey $ref: "%s"' % (s, reffrag)


    for relationship in relationDefDoc.get('references', []):
        # to be removed when 'read_group' became top level schema
        if relationship['targetEntity'] == 'read_group': continue

        assert relationship['targetEntity'] in schemas, \
            'No schema defined for the targetEntity "%s"' % relationship['targetEntity']

        assert len(relationship['targetKey']) == len(relationship['foreignKey']), \
            'targetKey length differs foreignKey length'

        for ref in relationship['targetKey']:
            targetEntity, reffrag = ref.split('#')
            assert targetEntity == relationship['targetEntity'], \
                'targetEntity "%s" not in $ref: %s' % (relationship['targetEntity'], ref)
            try:
                resolver.resolve_fragment(schemas[targetEntity], reffrag)
            except:
                assert False, 'Testing "%s" references failed on targetKey $ref: "%s"' % (s, reffrag)

        for reffrag in relationship['foreignKey']:
            assert reffrag.startswith('#')
            try:
                resolver.resolve_fragment(schemas[s], reffrag.lstrip("#"))
            except:
                assert False, 'Testing "%s" references failed on foreignKey $ref: "%s"' % (s, reffrag)
