import re
from pathlib import Path
import converter
import json

################################################
API_PATH = '../api/'
################################################

def main():
    # sequentially executes the annotation extraction and processing steps
    api_annotated_files = get_api_annotated_files()
    # logger(str(api_annotated_files))

    swagger_classes = []

    # for each file we parse the classes and, in turn, it's methods
    for source_file in api_annotated_files:
        swagger_class = parse_class(source_file)
        swagger_classes.append(swagger_class)

    # once we have all the swagger classes we merge their paths objects and
    # construct the swagger project info from the config file
    complete_paths_obj = {}
    for paths_obj in swagger_classes:
        for key, value in paths_obj.items():
            complete_paths_obj[key] = value

    converter.assemble_project(complete_paths_obj)

    # logger(json.dumps(complete_paths_obj, indent=4 * ' '))

def parse_class(source_file):
    # logic to extract the class data and associated annotations

    # find api declaration associated to the class
    with source_file.open() as curr_file:
        code = curr_file.read()

    matches = re.search('(/\*api(.*?)(public|private|protected|)(.*?)class(.*?){)', code, re.DOTALL)

    class_annotations = matches.group(0)
    path = parse_path(class_annotations)
    produces = parse_produces(class_annotations)
    api = parse_api(class_annotations)

    swagger_methods = parse_methods(code, path)
    swagger_class = converter.assemble_class(swagger_methods)

    return swagger_class

def parse_methods(code, class_path):
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
        # @GET|POST|PUT|DELETE... tag in the annotation
        http_method = parse_http_method(annotation[0])
        if http_method:
            method_name, method_return = method_sig_analyzer(annotation[1])
            path = parse_path(annotation[0])
            api_operations = parse_api_operation(annotation[0])
            api_responses = parse_api_responses(annotation[0])
            consumes = parse_consumes(annotation[0])
            produces = parse_produces(annotation[0])
            implicit_params = parse_implicit_params(annotation[0])

            method = {}
            method['http_method'] = http_method
            method['method_name'] = method_name
            method['produces'] = produces
            method['consumes'] = consumes
            method['path'] = path
            method['class_path'] = class_path
            method['api_responses'] = api_responses
            method['api_operations'] = api_operations
            method['implicit_params'] = implicit_params

            # swagger_method = converter.assemble_method(http_method, method_name,
            #     produces, consumes, path, class_path, api_responses,
            #         api_operations, implicit_params)

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

    key_val_regex = re.compile('(\w+)\s*?=\s*?"(.*?)"', re.DOTALL)
    parts = re.split('\*\s*?@', annotations)
    for item in parts:
        if 'ApiOperation' in item:
            api_op_regex = re.compile('ApiOperation\((.*)\)', re.DOTALL)
            matches = api_op_regex.search(item)
            key_val_annotations = matches.group(1)

            key_val_list = key_val_regex.findall(key_val_annotations)

    return dict(key_val_list)

def parse_api_responses(annotations):
    # takes a set of annotations and returns a dict of attributes contained
    # in @ApiResponses tag body
    api_responses = []

    key_val_regex = re.compile('(\w+)\s*?=\s*?(".*?"|[0-9]{3})', re.DOTALL)
    inner_tag_regex = pattern = re.compile('@ApiResponses\((.*?}).*?\)', re.DOTALL)

    inner_tag = inner_tag_regex.search(annotations)
    response_annotations = inner_tag.group(1)

    single_res_regex = re.compile('ApiResponse\((.*?)\)', re.DOTALL)
    res_list = single_res_regex.findall(response_annotations)

    res_code_regex = re.compile('code\s*?=\s*?([0-9]{3})', re.DOTALL)
    res_msg_regex = re.compile('message\s*?=\s*?"(.*?)"', re.DOTALL)

    for res in res_list:
        code = res_code_regex.search(res).group(1)
        message = res_msg_regex.search(res).group(1)
        code_and_msg = (code, message)
        api_responses.append(code_and_msg)

    return dict(api_responses)

def parse_implicit_params(annotations):
    # takes a set of annotations and returns a dict of attributes contained
    # in @ApiImplicitParams tag body

    implicit_params = []

    key_val_regex = re.compile('(\w+)\s*?=\s*?(".*?"|true|false)', re.DOTALL)
    inner_tag_regex = pattern = re.compile('@ApiImplicitParams\((.*?}).*?\)', re.DOTALL)

    inner_tag = inner_tag_regex.search(annotations)

    if inner_tag:
        implicit_param_annotations = inner_tag.group(1)

        single_param_regex = re.compile('ApiImplicitParam\((.*?)\)', re.DOTALL)
        param_list = single_param_regex.findall(implicit_param_annotations)

        for param in param_list:
            key_val_list = key_val_regex.findall(param)
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
    # containing the the key-value pair (value: '..', description: '..')

    api_result = []

    matches = re.search('@Api\((.*?)\)', annotations, re.DOTALL)
    inner_content = matches.group(1)

    # split by comma ONLY if the quotation marks (") match up
    # this essentially allows commas within quotations as opposed to solely limiting
    # the use of commas as an attribute delimiter

    key_val_regex = re.compile('(\w+)\s*?=\s*?"(.*?)"', re.DOTALL)
    key_val_list = key_val_regex.findall(inner_content)

    return dict(key_val_list)

def get_api_annotated_files():
    # returns a list of files that have been annotated with @Api signifying
    # that the file is a Swagger resource, as well as the start index of @Api(...)
    file_list = []

    # get the list of all the java files in the api directory
    # all_files = [ abspath(f) for f in listdir(API_PATH) if isfile(join(API_PATH,f)) ]
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
