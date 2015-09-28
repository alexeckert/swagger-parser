from os import listdir
from pathlib import Path

################################################
API_PATH = '../api/'
################################################

def main():
    # sequentially executes the annotation extraction and processing steps
    files = get_annotated_files()

def get_annotated_files():
    # returns a list of files that have been annotated with @Api signifying
    # that the file is a Swagger resource

    # get the list of all the files in the api directory
    # all_files = [ abspath(f) for f in listdir(API_PATH) if isfile(join(API_PATH,f)) ]
    path = Path(API_PATH)
    all_files = [ f.resolve() for f in list(path.rglob('*')) if f.is_file() ]

    # filter the files for ones containing the @Api declaration
    # eg: @Api(value = "/pet", description = "Operations about pets")
    for curr_file in all_files:
        with open(curr_file) as source_file:
            code = source_file.readlines()
            

if __name__ == '__main__':
    main()
