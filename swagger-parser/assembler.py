import json

def assemble_project(complete_paths_obj, model_list, tags, metadata):
    final_obj = {}

    # aggregate paths obj with project info
    final_obj['paths'] = complete_paths_obj
    
    # add the metadata to the final object
    final_obj['swagger'] = metadata['swagger']
    final_obj['info'] = metadata['info']
    final_obj['host'] = metadata['host']
    final_obj['basePath'] = metadata['basePath']
    final_obj['schemes'] = metadata['schemes']
    final_obj['definitions'] = {}
    
    # inject the models into the final object
    for model_file in model_list:
        try:
            with open(model_file) as mdl:
                model_obj = json.load(mdl)
                
            try:
                for model in model_obj['definitions']:
                    final_obj['definitions'][model] = model_obj['definitions'][model]
            except:
                print('WARNING: ' + model_file + ' contains an empty JSON object')
        except ValueError:
            print('WARNING: ' + model_file + ' is either empty or contains malformed JSON')
    
    # inject top-level tags
    final_obj['tags'] = []
    
    for tag in tags:
        final_obj['tags'].append({
            'name': tag[0],
            'description': tag[1]
        })

    with open('apis.json', 'w') as outfile:
        json.dump(final_obj, outfile, indent=4 * ' ')