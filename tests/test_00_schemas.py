from jsonschema import Draft7Validator, validate


def test_metaschema(metaschema):
    Draft7Validator.check_schema(metaschema)

def test_schemas(schemas, metaschema):
    for s in sorted(schemas):
        print(s)
        validate(schemas[s], metaschema)
