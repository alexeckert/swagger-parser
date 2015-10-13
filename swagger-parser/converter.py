import re
import json

################################################
PROJECT_INFO = 'project-info.json'
################################################

def assemble_class(swagger_methods):
    # the paths object that gets passed around from one assembled
    # class to another
    paths = {}

    for method in swagger_methods:
        # go through each method and assemble it
        method_obj = assemble_method(method['http_method'], method['method_name'],
            method['api_responses'], method['api_operations'], method['implicit_params'])

        # for each method that has been assembled, add it to the paths object
        if method['path']:
            # if the path var is not None, append it to the class path
            full_path = method['class_path'] + method['path']
        else:
            # if the path var is None, use only the class_path
            full_path = method['class_path']

        # check if a path matches full_path has already been added
        if full_path in paths:
            # append the new HTTP verb to the existing path
            paths[full_path] = method_obj
        else:
            paths[full_path] = {}
            paths[full_path] = method_obj

    # debugger(json.dumps(paths, indent=4 * ' '))
    return paths

def assemble_method(http_method, method_name, api_responses, api_operations,
    implicit_params):
    # method level assembly of Swagger objects in eg - "get" : {....}
    method_obj = {}
    http_verb = http_method.lower()
    method_obj[http_verb] = {}

    method_obj[http_verb]['operationId'] = method_name
    method_obj[http_verb]['summary'] = api_operations['value']

    if 'notes' in api_operations:
        # if notes is not None
        method_obj[http_verb]['description'] = api_operations['notes']

    if 'produces' in api_operations:
        produces = [x.strip(' ') for x in api_operations['produces'].split(",")]
        method_obj[http_verb]['produces'] = produces

    if 'consumes' in api_operations:
        consumes = [x.strip(' ') for x in api_operations['consumes'].split(",")]
        method_obj[http_verb]['consumes'] = consumes
        print(consumes)

    method_obj[http_verb]['parameters'] = convert_parameters(implicit_params)
    method_obj[http_verb]['responses'] = convert_responses(api_responses, api_operations)

    # print(json.dumps(method_obj, indent=4 * ' '))

    return method_obj

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
             is_required = param['required']
             if is_required.lower() == 'true':
                 inner_dict['required'] = True
             else:
                inner_dict['required'] = False
        else:
            inner_dict['required'] = False

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

def assemble_project(complete_paths_obj):
    # get info file
    with open(PROJECT_INFO) as info_file:
        final_obj = json.load(info_file)

    # aggregate paths obj with project info
    final_obj['paths'] = complete_paths_obj

    with open('swagger.json', 'w') as outfile:
        json.dump(final_obj, outfile, indent=4 * ' ')

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


def logger(msg):
    OKBLUE = '\033[94m'
    ENDC = '\033[0m'

    print(colors.OKBLUE + str(msg) + colors.ENDC)

def debugger(msg):
    OKBLUE = '\033[94m'
    ENDC = '\033[0m'

    print(colors.WARNING + str(msg) + colors.ENDC)

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
