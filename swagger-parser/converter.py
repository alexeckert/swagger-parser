import re
import json

def convert_parameters(params):
    # converts a list of dictionary of implicit parameters to a parameter object
    # to be consumed by SwaggerUI

    param_obj = []
    for param in params:
        inner_dict = {}
        inner_dict['name'] = param['name'].strip('"')
        inner_dict['in'] = param['paramType'].strip('"')

        if inner_dict['in'] == 'body':
            inner_dict['schema'] = {"$ref" : "#/definitions/" + param['dataType'].strip('"')}
        else:
            inner_dict['type'] = param['dataType'].strip('"')

        if 'value' in param:
            inner_dict['description'] = param['value'].strip('"')

        if 'required' in param:
            inner_dict['required'] = param['required']
        else:
            inner_dict['required'] = 'false'

        param_obj.append(inner_dict)

    # print(json.dumps(param_obj, indent=4 * ' '))
    return param_obj


def convert_responses(responses):
    # converts a dictionary of responses to a response object to be consumed by
    # SwaggerUI
    res_obj = {}
    for key, value in responses.items():
        inner_dict = {}
        inner_dict['description'] = value
        res_obj[key] = inner_dict

    # print(json.dumps(res_obj, indent=4 * ' '))
    return res_obj

def get_datatype_format(datatype_in):
    # dictionary of name (key) and (type, format) tuple values from the Swagger spec
    datatypes = {
        'integer': ('integer', 'int32'),
        'long':	('integer', 'int64'),
        'float':	('number', 'float'),
        'double':	('number', 'double'),
        'string':	('string', None),
        'byte':	('string', 'byte'),
        'binary':	('string', 'binary'),
        'boolean':	('boolean', None),
        'date':	('string', 'date'),
        'datetime':	('string', 'date-time'),
        'password':	('string', 'password')
    }

    datatype = datatype_in.lower()
    return datatypes[datatype]
