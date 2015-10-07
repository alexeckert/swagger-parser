import re
import json

    # "/pet/findByTags" : {
    #   "get" : {
    #     "tags" : [ "pet" ],
    #     "summary" : "Finds Pets by tags",
    #     "description" : "Muliple tags can be provided with comma seperated strings. Use tag1, tag2, tag3 for testing.",
    #     "operationId" : "findPetsByTags",
    #     "produces" : [ "application/xml", "application/json" ],
    #     "parameters" : [ {
    #       "name" : "tags",
    #       "in" : "query",
    #       "description" : "Tags to filter by",
    #       "required" : true,
    #       "type" : "array",
    #       "items" : {
    #         "type" : "string"
    #       },
    #       "collectionFormat" : "csv"
    #     } ],
    #     "responses" : {
    #       "200" : {
    #         "description" : "successful operation",
    #         "schema" : {
    #           "type" : "array",
    #           "items" : {
    #             "$ref" : "#/definitions/Pet"
    #           }
    #         }
    #       },
    #       "400" : {
    #         "description" : "Invalid tag value"
    #       }
    #     }
    #   }
    # }

def assemble_method(http_method, method_name, produces, consumes, path,
    class_path, api_responses, api_operations, implicit_params):
    # method level assembly of Swagger objects in eg - "get" : {....}
    method_obj = {}
    http_verb = http_method.lower()
    method_obj[http_verb] = {}

    method_obj[http_verb]['operationId'] = method_name
    method_obj[http_verb]['summary'] = api_operations['value']

    if 'notes' in api_operations:
        # if notes is not None
        method_obj[http_verb]['description'] = api_operations['notes']

    if not produces:
        method_obj[http_verb]['produces'] = produces

    if not consumes:
        method_obj[http_verb]['consumes'] = consumes

    method_obj[http_verb]['parameters'] = convert_parameters(implicit_params)
    method_obj[http_verb]['responses'] = convert_responses(api_responses, api_operations)

    print(json.dumps(method_obj, indent=4 * ' '))


def convert_parameters(params):
    # converts a list of dictionary of implicit parameters to a parameter object
    # to be consumed by SwaggerUI

    param_obj = []
    for param in params:
        inner_dict = {}
        inner_dict['name'] = param['name'].strip('"')
        inner_dict['in'] = param['paramType'].strip('"')

        data_type_val = param['dataType'].strip('"')
        datatype_format = get_datatype_format(data_type_val)
        if not datatype_format:
            # if we got None then the datatype is not a Swagger primitive
            # so we need to check if it's a single primitive or a List/Array of
            # non-primitive types

            non_prim_regex = re.compile('(\w+\[.*?\]|List<\w+>)')
            matches = non_prim_regex.match(data_type_val)
            if matches:
                # we have an array/List of non-primitives to process
                type_regex = re.compile('(\w+)\[.*?\]|List<(\w+)>')

                if 'List' in data_type_val:
                    class_type = type_regex.match(data_type_val).group(2)
                else:
                    class_type = type_regex.match(data_type_val).group(1)

                inner_dict['schema'] = {}
                inner_dict['schema']['type'] = "array"
                inner_dict['schema']['items'] = {"$ref" : "#/definitions/" + class_type}

            else:
                # create a single element schema since it's a single non-prim
                inner_dict['schema'] = {"$ref" : "#/definitions/" + data_type_val}

        else:
            # it's a Swagger primitive so handle it normally
            inner_dict['type'], inner_dict['format'] = datatype_format

        if 'value' in param:
            inner_dict['description'] = param['value'].strip('"')

        if 'required' in param:
            inner_dict['required'] = param['required']
        else:
            inner_dict['required'] = 'false'

        param_obj.append(inner_dict)

    # print(json.dumps(param_obj, indent=4 * ' '))
    return param_obj


def convert_responses(responses, operations):
    # converts a dictionary of responses to a response object to be consumed by
    # SwaggerUI
    res_obj = {}
    for key, value in responses.items():
        inner_dict = {}
        inner_dict['description'] = value
        res_obj[key] = inner_dict

    if 'response' in operations:
        # check the operations param to see if it contains any 'response' or
        # 'responseContainer' keys for a status 200
        inner_dict = {}
        inner_dict['description'] = "successful operation"
        if 'responseContainer' in operations:
            # we have a schema with types and items objects
            inner_dict['schema'] = {}
            inner_dict['schema']['type'] = "array"
            inner_dict['schema']['items'] = {"$ref" : "#/definitions/" + operations['response']}
        else:
            # we only have a schema with a single $ref obj
            inner_dict['schema'] = {"$ref" : "#/definitions/" + operations['response']}

        res_obj['200'] = inner_dict

    # print(json.dumps(res_obj, indent=4 * ' '))
    return res_obj

def get_datatype_format(datatype_in):
    # dictionary of name (key) and (type, format) tuple values from the Swagger spec
    datatypes = {
        'integer': ('integer', 'int32'),
        'long':	('integer', 'int64'),
        'float':	('number', 'float'),
        'double':	('number', 'double'),
        'string':	('string', ''),
        'byte':	('string', 'byte'),
        'binary':	('string', 'binary'),
        'boolean':	('boolean', ''),
        'date':	('string', 'date'),
        'datetime':	('string', 'date-time'),
        'password':	('string', 'password')
    }

    datatype = datatype_in.lower()
    if datatype in datatypes:
        return datatypes[datatype]
    else:
        return None
