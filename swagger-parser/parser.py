import re
from pathlib import Path

################################################
API_PATH = '../api/'
################################################

def main():
    # sequentially executes the annotation extraction and processing steps
    api_annotated_files = get_api_annotated_files()
    logger(str(api_annotated_files))

    # for each file we parse the classes and, in turn, it's methods
    for source_file in api_annotated_files:
        parse_class(source_file)

    # inside each class we parse the methods
    # parse_methods()
    #
    # parse_api_operation()
    #
    # parse_api_reponses()
    #
    # parse_http_method()
    #
    # parse_path()

def parse_class(source_file):
    # logic to extract the class data and associated annotations

    # find api declaration associated to the class
    with source_file.open() as curr_file:
        code = curr_file.read()

    matches = re.search('(/\*api(.*?)(public|private|protected|)(.*?)class(.*?){)', code, re.DOTALL)

    class_annotations = matches.group(0)
    logger(class_annotations)
    logger("-------------------------------")
    path = parse_path(class_annotations)
    logger(path)
    logger("-------------------------------")
    produces = parse_produces(class_annotations)
    logger(produces)
    logger("-------------------------------")
    api = parse_api(class_annotations)
    logger(api)

def parse_path(annotations):
    # takes a string containing a subset of the annotations and returns the
    # value of the path variable
    matches = re.search('@Path\("(.*?)"\)', annotations, re.DOTALL)
    if matches:
        return matches.group(1)
    else:
        return ''
        
def parse_produces(annotations):
    # takes a string containing a subset of the annotations and returns a list
    # containing the types it produces
    matches = re.search('@Produces\(\{(.*?)\}\)', annotations, re.DOTALL)
    inner_content = matches.group(1)

    # strip away white space and double quotation marks (")
    produces = [x.strip('" ') for x in inner_content.split(",")]

    return produces

def parse_api(annotations):
    # takes a string containing a subset of the annotations and returns a dict
    # containing the the key-value pair (value: '..', description: '..')

    api_result = []

    matches = re.search('@Api\((.*?)\)', annotations, re.DOTALL)
    inner_content = matches.group(1)

    # split by comma
    elements = [x for x in inner_content.split(",")]

    for element in elements:
        key_matches = re.search('(\w+).?=', element, re.DOTALL)
        val_matches = re.search('"(.*?)"', element, re.DOTALL)
        key = key_matches.group(1)
        val = val_matches.group(1)

        api_result.append((key, val))

    return dict(api_result)

def get_api_annotated_files():
    # returns a list of files that have been annotated with @Api signifying
    # that the file is a Swagger resource, as well as the start index of @Api(...)
    file_list = []

    # get the list of all the files in the api directory
    # all_files = [ abspath(f) for f in listdir(API_PATH) if isfile(join(API_PATH,f)) ]
    path = Path(API_PATH)
    all_files = [ f.resolve() for f in list(path.rglob('*')) if f.is_file() ]

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

    print(OKBLUE + str(msg) + ENDC)

if __name__ == '__main__':
    main()
