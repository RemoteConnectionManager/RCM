import sys
import os

# set prefix.
current_file = os.path.realpath(os.path.expanduser(__file__))
current_path = os.path.dirname(os.path.dirname(current_file))
rcm_root_path = os.path.dirname(current_path)
root_path = os.path.dirname(os.path.dirname(current_path))

# Add lib folder in current prefix to default  import path
current_lib_path = os.path.join(current_path, "lib")
current_etc_path = os.path.join(current_path, "etc")
current_utils_path = os.path.join(rcm_root_path, "utils")

sys.path.insert(0, current_path)
sys.path.insert(0, current_lib_path)
sys.path.insert(0, current_utils_path)


import external
import yaml
import hiyapyco

print("etc_path:",current_etc_path)

# with open(os.path.join(current_path,'test','etc', 'test', 'test_regex.yaml'), 'r') as f:
#     yaml_string = f.read()
# print(yaml_string)
# yaml_dict = yaml.load(yaml_string)
#
# for name,test_sessions in yaml_dict['tests'].items():
#     for name,sample in test_sessions.items():
#         print(name + ' -->' + sample + '<--')

yaml_dict = hiyapyco.load(
    [os.path.join(current_path,'test','etc', 'test', 'test_regex.yaml')],
    interpolate=True,
    method=hiyapyco.METHOD_MERGE,
    failonmissingfiles=False
)

for name,test_sessions in yaml_dict['tests'].items():
    for name,sample in test_sessions.items():
        print(name + ' -->' + sample + '<--')
