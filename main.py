import os
import glob
import yaml
from pprint import pprint
import string
from box import Box


import requests
import json

def chat_completion_request(messages, model: str):
    try:

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}", # place your API key here or use some sort of .env
            },
            data=json.dumps({
                "model": model, 
                "messages": messages
            })
        )

        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

class YAML_Reader:

    def __init__(self):
        self.yaml_files = glob.glob('documents/doc4.yaml')
        with open('block-types.yaml') as file:
            data = yaml.full_load(file)

        print("Reading document")
        pprint(self.yaml_files[0])

        self.block_types = {}
        for primitive in data['primitives']:
            self.block_types[primitive['name']] = primitive

        self.immutable_keys = ['name', 'template', 'children', 'generate']


    
    def read_and_pprint_yaml(self, file_path):
        with open(file_path, 'r') as file:
            data = yaml.full_load(file)
            pprint(data)

    def run(self):
        for yaml_file in self.yaml_files:

            with open(yaml_file, 'r') as file:
                data = yaml.full_load(file)

            res = self.expand_node(data['root'])
            print("Done!")
            return res

    def validate_yaml(self, yaml_object):
        # Implement validation logic to ensure required fields are present
        required_fields = ['type', 'ideas', 'context']
        for field in required_fields:
            if field not in yaml_object:
                raise ValueError(f"Missing required field: {field}")
        if 'children' in yaml_object and yaml_object['children'] is not None:
            for child in yaml_object['children']:
                self.validate_yaml(child)

    def generate_node(self, request, system_message=None, post_message=None, temperature=1.0):
        response = request

        # model = "mistralai/mixtral-8x22b-instruct"
        model = "gryphe/mythomax-l2-13b"

        messages = [{"role": "user", "content": request}]
        if system_message:
            messages.insert(0, {"role": "system", "content": system_message})
        if post_message:
            messages.append({"role": "user", "content": post_message})

        print('-' * 10)
        print(f"GENERATION REQUEST")
        print(f"Temperature {temperature}")
        pprint(messages)
        print('-' * 4)
        print(f"GENERATION RESPONSE")
        
        response = chat_completion_request(messages, model)
        if not response:
            return ''

        response = json.loads(response._content.decode('utf-8').strip())['choices'][0]['message']['content']

        print(response)
        print('-' * 10)

        return response

    def expand_node(self, yaml_object, parent_object=None, level=0):
        obj = Box(yaml_object)
       
        indent = "    " * level
        result = ''
        print(f"{indent} Expanding {obj.type}")

        # Incorporate properties from block_types
        block_type = self.block_types.get(obj.type)
        if block_type:
            for key, value in block_type.items():
                if key == 'name':
                    continue
                if not obj.get(key):
                    obj[key] = value
        # print("-" * (level * 4+10) + "Expanded object:")
        # pprint(obj.to_dict())
        # print("-" * (level * 4+10))

        # Inherit properties from parent if not present in the child
       
        if parent_object:
            for key, value in parent_object.items():
                if key in self.immutable_keys:
                    continue
                if not obj.get(key):
                    print(f"{indent} Inheriting {key} from parent")
                    obj[key] = value


        # If there are children, expand them first before assembling ourselves

        if obj.get('children'):
            print(f"{indent} Checking children for this node")
            # Process children and integrate into the template
            for child in obj.children:
                print(f"{indent} Adding properties for child: {child.type}")
                # Incorporate properties from block_types
                block_type = self.block_types.get(child.type)
                if block_type:
                    for key, value in block_type.items():
                        if key in self.immutable_keys:
                            continue
                        if not child.get(key):
                            child[key] = value

                child_output = child.get('output')
                if child_output:
                    expanded_child = self.expand_node(child, obj, level + 1)
                    obj[child_output] = expanded_child
                    print(f"{indent} Attaching {child_output} to {obj.type}")

                # Update parent object with children's keys if not present
                print(f"{indent} Updating parent with child keys")
                for key, value in child.items():
                    if not obj.get(key) and key not in self.immutable_keys:
                        print(f"{indent} Taking {key} from child")
                        obj[key] = value


        if not obj.template:
            raise ValueError(f"Missing template for {obj.type}")

        print(f"{indent} Applying template to {obj.type} with {obj.keys()}")
        template = string.Template(obj.template)
        result = template.safe_substitute(**obj)
        # double substitution - feels funny but?
        if '$' in result:
            print(f"{indent} Parameters found within template output, re-substituting (max once)")
            template = string.Template(result)
            result = template.safe_substitute(**obj)

        # replace \n's with real linebreaks
        result = result.replace(r'\n', '\n')

        # apply generation if this node is generative
        if obj.get('generate'):
            print(f"{indent} Generation request from: {obj.type}")
            system_message = obj.get('system_message')
            post_message = obj.get('post_message')
            temperature = obj.get('temperature')
            result = self.generate_node(result, system_message, post_message, temperature)
    
        print(f"{indent} Resolving {obj.type}")
        return result
    

# to run:
# reader = YAML_Reader()
# res = reader.run()
