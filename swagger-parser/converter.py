import re
import json

################################################
PROJECT_INFO = 'project-info.json'
################################################

def assemble_class(swagger_methods, api):
    # the paths object that gets passed around from one assembled
    # class to another
    paths = {}

    for method in swagger_methods:
        # go through each method and assemble it
        method_obj = assemble_method(method['http_method'], method['method_name'],
            method['api_responses'], method['api_operations'], method['implicit_params'])

        if 'tags' not in method_obj and 'tags' in api:
            # if tags obj already exists in the method then it overwrites the
            # class level declaration - so in this case we create a new one
            method_obj['tags'] = api['tags']


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
            paths[full_path][method['http_method'].lower()] = method_obj
        else:
            paths[full_path] = {}
            paths[full_path][method['http_method'].lower()] = method_obj

    # debugger(json.dumps(paths, indent=4 * ' '))
    return paths

def assemble_method(http_method, method_name, api_responses, api_operations,
    implicit_params):
    # method level assembly of Swagger objects in eg - "get" : {....}
    method_obj = {}

    method_obj['operationId'] = method_name
    method_obj['summary'] = api_operations['value']

    if 'notes' in api_operations:
        # if notes is not None
        method_obj['description'] = api_operations['notes']

    if 'produces' in api_operations:
        produces = [x.strip(' ') for x in api_operations['produces'].split(",")]
        method_obj['produces'] = produces

    if 'consumes' in api_operations:
        consumes = [x.strip(' ') for x in api_operations['consumes'].split(",")]
        method_obj['consumes'] = consumes
        
    if 'tags' in api_operations:
        method_obj['tags'] = api_operations['tags']

    method_obj['parameters'] = convert_parameters(implicit_params)
    method_obj['responses'] = convert_responses(api_responses, api_operations)

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
            
        if 'defaultValue' in param and 'type' in inner_dict:
            default_val = param['defaultValue'].strip('"')
            # check the dataType field (if if exists) to type-cast the defaultValue element
            if inner_dict['type'] == 'string':
                inner_dict['default'] = str(default_val)
            elif inner_dict['type'] == 'integer':
                inner_dict['default'] = int(default_val)
            elif inner_dict['type'] == 'number':
                inner_dict['default'] = float(default_val)
                    
        if 'allowableValues' in param:
            allow_vals = param['allowableValues']
            # if range, then minimum - maximum
            if 'range' in allow_vals:
                range_matches = re.search('range(\[|\()\s*?(\S.*?)\s*?,\s*?(\S.*?)\s*?(\]|\))', allow_vals)

                # range_matches 1: [ or (, 2: start or -infinity, 3: end or infinity, 4: ] or )
                start_bracket = range_matches.group(1)
                end_bracket = range_matches.group(4)
                                
                if isfloat(range_matches.group(2)):
                    start_range = float(range_matches.group(2))
                elif isint(range_matches.group(2)):
                    start_range = int(range_matches.group(2))
                else:
                    start_range = range_matches.group(2)
                
                if isfloat(range_matches.group(3)):
                    end_range = float(range_matches.group(3))
                elif isint(range_matches.group(3)):
                    end_range = int(range_matches.group(3))
                else:
                    end_range = range_matches.group(3)
                    
                if type(start_range) != str:
                    inner_dict['minimum'] = (start_range if start_bracket == '[' else start_range - 1)
                
                if type(end_range) != str:# and 'infinity' in end_range:
                    inner_dict['maximum'] = (end_range if end_bracket == ']' else end_range - 1)
            else:
                # if comma-separated list, then enum
                enum_matches = [x.strip('"') for x in re.split('\s?,\s?', allow_vals)]
                inner_dict['enum'] = enum_matches
            

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

def isint(str_in):
    if str_in.isdigit():
        return True
    else:
        return False

def isfloat(str_in):
    if '.' in str_in and str_in.replace('.', '').isdigit():
        return True
    else:
        return False

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
