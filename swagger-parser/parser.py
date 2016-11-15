import re
from pathlib import Path
import converter
import assembler
import json
import argparse
import os
import codecs

################################################
PROJECT_INFO = '../api/SwaggerConfig.json'
################################################

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-p", "--production", help="generate a production version of the swagger.json",
                    action="store_true")
    args = arg_parser.parse_args()


    # get info file
    with open(PROJECT_INFO) as info_file:
        info_obj = json.load(info_file)

    # sequentially executes the annotation extraction and processing steps
    resource_list, model_list = get_resource_model_lists(info_obj['include'], args.production)
    tag_list = get_top_level_tags(info_obj['include'], args.production)

    swagger_classes = []

    # for each file we parse the classes and, in turn, it's methods
    for source_file in resource_list:
        swagger_class = parse_class(source_file, args.production)
        swagger_classes.append(swagger_class)

    # once we have all the swagger classes we merge their paths objects and
    # construct the swagger project info from the config file
    complete_paths_obj = {}
    for paths_obj in swagger_classes:
        for key, value in paths_obj.items():
            complete_paths_obj[key] = value

    metadata = {}
    metadata['swagger'] = info_obj['swagger']
    metadata['info'] = info_obj['info']
    metadata['host'] = info_obj['host']
    metadata['basePath'] = info_obj['basePath']
    metadata['schemes'] = info_obj['schemes']
    assembler.assemble_project(complete_paths_obj, model_list, tag_list, metadata)

    # logger(json.dumps(complete_paths_obj, indent=4 * ' '))

def parse_class(source_file, production):
    # logic to extract the class data and associated annotations

    # find api declaration associated to the class
    curr_file = codecs.open(source_file, "r", "utf-8")
    code = curr_file.read()
    curr_file.close()
    matches = re.search('(/\*api(.*?)(public|private|protected|)(.*?)class(.*?){)', code, re.DOTALL)

    class_annotations = matches.group(0)
    path = parse_path(class_annotations)
    api = parse_api(class_annotations)

    swagger_methods = parse_methods(code, path, production)
    swagger_class = converter.assemble_class(swagger_methods, api)

    return swagger_class

def parse_methods(code, class_path, production):
    # takes in a source file and extracts all the method annotations
    swagger_methods = []
    # regex for matching all /*api ... */ INCLUDING the method signature
    pattern = re.compile('/\*api(.*?)\*/(.*?){', re.DOTALL)
    # matches is a list containing 2-tuple
    #   - first is everything between /*api ... */
    #   - seconds is the method signature and potentially any other non-API
    #     tags such as @Override or @Deprecated
    annotation_matches = pattern.findall(code)

    for annotation in annotation_matches:
        # make sure we only parse methods and not classes by detecting the
        # @ApiOperation tag in the annotation
        if '@ApiOperation' in annotation[0]:
            method_name, method_return = method_sig_analyzer(annotation[1])
            path = parse_path(annotation[0])
            api_operations = parse_api_operation(annotation[0])
            api_responses = parse_api_responses(annotation[0])
            implicit_params = parse_implicit_params(annotation[0])

            method = {}
            method['http_method'] = api_operations['httpMethod']
            method['method_name'] = api_operations['nickname'] if 'nickname' in api_operations else method_name
            method['path'] = path
            method['class_path'] = class_path
            method['api_responses'] = api_responses
            method['api_operations'] = api_operations
            method['implicit_params'] = implicit_params

            if '@Internal' in annotation[0] and production:
                continue
            else:
                swagger_methods.append(method)

    return swagger_methods

def method_sig_analyzer(signature_param):
    # this method analyzes a method signature and returns its constituents

    # selection of the approprite regex is based on whether a static modifier
    # exists in the method signature or not
    method_sig_regex = re.compile('(public|private|protected)\s([^\s]+)\s(\w+)', re.DOTALL)

    if 'static' in signature_param:
        signature = signature_param.replace(' static', '')
    else:
        signature = signature_param

    method_sig_raw = signature.replace('\n', ' ')
    method_sig_matches = method_sig_regex.search(method_sig_raw)

    method_name = method_sig_matches.group(3)
    method_return = method_sig_matches.group(2)

    return method_name, method_return

def parse_api_operation(annotations):
    # takes a set of annotations and returns a dict of attributes contained
    # in @ApiOperation tag body
    greedy_key_val_rgx = re.compile('(\w+)\s*?=\s*?(".*"|true|false|\{".*"\})', re.DOTALL)
    parts = re.split('\*\s*?@', annotations)

    key_val_list = []

    for item in parts:
        if 'ApiOperation' in item:
            api_op_regex = re.compile('ApiOperation\((.*)\)', re.DOTALL)
            matches = api_op_regex.search(item)
            key_val_annotations = matches.group(1)

            attrb_list = ['value', 'authorizations', 'code',
                'consumes', 'extensions', 'hidden', 'httpMethod',
                'nickname', 'notes', 'produces', 'protocols', 'response',
                'responseContainer', 'responseHeaders', 'responseReference', 'tags']

            for attrb in attrb_list:
                attrb_regex = re.compile(attrb + '\s*?=\s*?', re.DOTALL)
                attrb_match = attrb_regex.search(key_val_annotations)

                curr_attrb_index = attrb_list.index(attrb)

                if attrb_match:
                    index = attrb_match.start()

                    # get the index of the adjacent attribute
                    next_attrb_list = [
                            re.search(i + '\s*?=\s*?', key_val_annotations, re.DOTALL).start()
                            # all the attributes except the current one being analyzed
                            for i in attrb_list[:curr_attrb_index] + attrb_list[(curr_attrb_index + 1):]

                            if  re.search(i + '\s*?=\s*?', key_val_annotations, re.DOTALL) and
                                re.search(i + '\s*?=\s*?', key_val_annotations, re.DOTALL).start() > index
                    ]

                    next_attrb_index = min(next_attrb_list) if next_attrb_list else len(key_val_annotations)

                    raw_attrb = key_val_annotations[index:next_attrb_index]
                    key_val = greedy_key_val_rgx.search(raw_attrb)

                    attrb_key = key_val.group(1)
                    attrb_val = key_val.group(2)
                    key_val_list.append((attrb_key, attrb_val))

            key_val_list.extend(parse_tags(key_val_annotations))

    return dict(key_val_list)

def parse_tags(tags_annotation):
    # takes a tag annotation and returns a list containing a single tuple
    # as the key-value pair: ('tags', ["pet", "animal"])

    tags_regex = re.compile('(tags)\s*?=\s*?\{(.*?)\}', re.DOTALL)
    tags_list = tags_regex.findall(tags_annotation)

    if tags_list:
        tags_obj = [x.strip('"') for x in re.split('\s?,\s?', tags_list[0][1])]
        return [('tags', tags_obj)]
    else:
        return []

def parse_api_responses(annotations):
    # takes a set of annotations and returns a dict of attributes contained
    # in @ApiResponses tag body
    api_responses = []

    key_val_regex = re.compile('(\w+)\s*?=\s*?(".*?"|[0-9]{3})', re.DOTALL)
    inner_tag_regex = re.compile('@ApiResponses\((.*?}).*?\)', re.DOTALL)

    inner_tag = inner_tag_regex.search(annotations)

    if inner_tag:
        response_annotations = inner_tag.group(1)

        single_response_regex = re.compile('ApiResponse\((.*?)\)', re.DOTALL)
        response_list = single_response_regex.findall(response_annotations)

        for response in response_list:
            key_val_list = key_val_regex.findall(response)
            api_responses.append(dict(key_val_list))
        return api_responses

    else:
        return None

def parse_implicit_params(annotations):
    # takes a set of annotations and returns a dict of attributes contained
    # in @ApiImplicitParams tag body

    implicit_params = []

    greedy_key_val_rgx = re.compile('(\w+)\s*?=\s*?(".*"|true|false)', re.DOTALL)
    inner_tag_regex = re.compile('@ApiImplicitParams\((.*?}).*?\)', re.DOTALL)

    inner_tag = inner_tag_regex.search(annotations)

    if inner_tag:
        implicit_param_annotations = inner_tag.group(1)

        param_list = implicit_param_annotations.split('@ApiImplicitParam(')

        for param in param_list[1:]:
            key_val_list = []

            attrb_list = ['access', 'allowableValues', 'allowMultiple',
                'dataType', 'defaultValue', 'example', 'examples',
                'name', 'paramType', 'required', 'value']

            for attrb in attrb_list:
                attrb_regex = re.compile(attrb + '\s*?=\s*?', re.DOTALL)
                attrb_match = attrb_regex.search(param)

                curr_attrb_index = attrb_list.index(attrb)

                if attrb_match:
                    index = attrb_match.start()

                    # get the index of the adjacent attribute
                    next_attrb_list = [
                            re.search(i + '\s*?=\s*?', param, re.DOTALL).start()
                            # all the attributes except the current one being analyzed
                            for i in attrb_list[:curr_attrb_index] + attrb_list[(curr_attrb_index + 1):]

                            if  re.search(i + '\s*?=\s*?', param, re.DOTALL) and
                                re.search(i + '\s*?=\s*?', param, re.DOTALL).start() > index
                    ]

                    next_attrb_index = min(next_attrb_list) if next_attrb_list else len(param)

                    raw_attrb = param[index:next_attrb_index]
                    key_val = greedy_key_val_rgx.search(raw_attrb)

                    attrb_key = key_val.group(1)
                    attrb_val = key_val.group(2)
                    key_val_list.append((attrb_key, attrb_val))

            implicit_params.append(dict(key_val_list))

        return implicit_params

    else:
        return None

def parse_http_method(annotations):
    # takes an annotations string and returns the extracted HTTP method
    # GET/POST/PUT/DELETE/...

    matches = re.search('@(GET|POST|PUT|DELETE|OPTIONS|HEAD|PATCH)', annotations, re.DOTALL)
    if matches:
        return matches.group(1)
    else:
        return None

def parse_path(annotations):
    # takes a string containing a subset of the annotations and returns the
    # value of the path variable
    matches = re.search('@Path\("(.*?)"\)', annotations, re.DOTALL)
    if matches:
        return matches.group(1)
    else:
        return None

def parse_produces(annotations):
    # takes a string containing a subset of the annotations and returns a list
    # containing the types it produces
    matches = re.search('@Produces\(\{(.*?)\}\)', annotations, re.DOTALL)
    if matches:
        inner_content = matches.group(1)
    else:
        return None

    # strip away white space and double quotation marks (")
    produces = [x.strip('" ') for x in inner_content.split(",")]
    return produces

def parse_consumes(annotations):
    # takes a string containing a subset of the annotations and returns a list
    # containing the types it consumes
    matches = re.search('@Consumes\(\{(.*?)\}\)', annotations, re.DOTALL)
    if matches:
        inner_content = matches.group(1)
    else:
        return None

    # strip away white space and double quotation marks (")
    consumes = [x.strip('" ') for x in inner_content.split(",")]

    return consumes

def parse_api(annotations):
    # takes a string containing a subset of the annotations and returns a dict
    # containing the the key-value pair (description: '..')

    api_result = []

    matches = re.search('@Api\((.*?)\)', annotations, re.DOTALL)
    inner_content = matches.group(1)

    # split by comma ONLY if the quotation marks (") match up
    # this essentially allows commas within quotations as opposed to solely limiting
    # the use of commas as an attribute delimiter
    key_val_regex = re.compile('(\w+)\s*?=\s*?"(.*?)"', re.DOTALL)
    key_val_list = key_val_regex.findall(inner_content)
    key_val_list.extend(parse_tags(inner_content))

    return dict(key_val_list)

def get_api_annotated_files_old():
    # returns a list of files that have been annotated with @Api signifying
    # that the file is a Swagger resource, as well as the start index of @Api(...)
    file_list = []

    # get the list of all the java files in the api directory
    path = Path(API_PATH)
    all_files = [ f.resolve() for f in list(path.rglob('*.java')) if f.is_file() ]

    # filter the files for ones containing the @Api declaration
    # eg: @Api(value = "/pet", description = "Operations about pets")
    for curr_file in all_files:
        with curr_file.open() as source_file:
            code = source_file.read()
            annotation_exists = code.find("@Api(")

        if (annotation_exists != -1):
            file_list.append(curr_file)

    return file_list

def get_resource_model_lists(include_list, production):
    # returns a list of files that have been annotated with @Api signifying
    # that the file is a Swagger resource, as well as the start index of @Api(...)
    resource_list = []
    model_list = []

    # read the include list and only add the production=true files
    if production:
        for file_obj in include_list:
            if file_obj['production'] and file_obj['resource']:
                file_path = '../api/' + file_obj['resource']
                if os.path.isfile(file_path):
                    resource_list.append(file_path)
                else:
                    print('WARNING: ' + file_path + ' does not exist')

            if file_obj['production'] and file_obj['model']:
                file_path = '../api/' + file_obj['model']
                if os.path.isfile(file_path):
                    model_list.append(file_path)
                else:
                    print('WARNING: ' + file_path + ' does not exist')
    else:
        for file_obj in include_list:
            if file_obj['resource']:
                file_path = '../api/' + file_obj['resource']
                if os.path.isfile(file_path):
                    resource_list.append(file_path)
                else:
                    print('WARNING: ' + file_path + ' does not exist')

            if file_obj['model']:
                file_path = '../api/' + file_obj['model']
                if os.path.isfile(file_path):
                    model_list.append(file_path)
                else:
                    print('WARNING: ' + file_path + ' does not exist')

    return resource_list, model_list

def get_top_level_tags(include_list, production):
    # returns a list of all the tags plus their descriptions
    tag_list = []

    if production:
        for file_obj in include_list:
            if file_obj['production'] and file_obj['name']:
                tag_list.append((file_obj['name'], file_obj['description']))
    else:
        for file_obj in include_list:
            if file_obj['name']:
                tag_list.append((file_obj['name'], file_obj['description']))

    return tag_list

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

if __name__ == '__main__':
    main()
