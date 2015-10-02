import re
import json

# "responses" : {
#   "400" : {
#     "description" : "Invalid ID supplied"
#   },
#   "404" : {
#     "description" : "Pet not found"
#   },
#   "405" : {
#     "description" : "Validation exception"
#   }
# }

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
