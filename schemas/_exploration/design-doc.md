Note that this is the first draft of the ARGO dictionary design, it gives the starting point of the iterative process.

ARGO data dictionary inherits major features from [ICGC data dictionary](https://docs.icgc.org/dictionary/viewer/). The latest version (0.19a) of the dictionary can be downloaded from: https://submissions.dcc.icgc.org/ws/dictionaries/0.19a. The ICGC dictionary is defined in a JSON document, which includes definition of submission TSV files and relationships among them. Restrictions such as value pattern, permissible values (ie, codelist) and more flexible script based validation rules are also supported.

Leveraging open standard, ARGO data dictionary uses JSON Schema (https://json-schema.org/) to define all of its entity types, such as: donor, specimen, sample and therapy etc. With a few custom keywords, we extended JSON Schema to support additional features such as modeling relationships, context-specific enums and script based validations. Here are the custom keywords:

* `systemProperties`: properties that are managed by the system not by data submitter.
* `primaryKey`: similary to RDBMS PK. It defines surrogat key and natural (business) key.
* `uniqueKeys`: similary to RDBMS unique key constraint, it defines keys (a key consists of one or more properties) must be unique across all documents within the entity.
* `scriptValidations`: this defines a list of scripts to be called in order to perform more complex logic to ensure conformity of the submitted data. All scripts are managed in a directory named `_scripts`. The dictionary is implementation language agnostic, so scripts can be written in any language.
* `references`: similar to RDBMS' foreign key constraint, it defines the relationship between two related entity types.

To better support complex and large amount of permissible values, CV term definitions can be outsourced to a separate diretory: `_cv_terms`. They are linked back to JSON Schema via `scriptValidations`, eg, `"$cv(tumour_stage)"`. The mechanism also allows us to support context-specific CV terms, for example: `"$cv(tumour_or_normal_designation, specimen_type)"` returns CV terms for tumour stages that are only applicable to the chosen tumour staging system.

One of the modeling design goals is to stay domain and language agnostic, much like Entity-Relationship (ER) model widely adopted in the RDBMS world. Same modeling technique can be applied to different application domains, implementation can use any programming language.
