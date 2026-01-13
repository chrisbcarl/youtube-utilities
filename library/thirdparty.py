'''
Author:      Chris Carl
Date:        2023-11-12
Email:       chrisbcarl@outlook.com

Description:
    third party augmentations
'''

# third party imports
import yaml


def load_yaml(yaml_filepath):
    with open(yaml_filepath, encoding='utf-8') as r:
        return yaml.safe_load(r)
