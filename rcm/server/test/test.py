import unittest
import os
import sys

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

import manager
import tempfile
import json
import filecmp


class TestManager(unittest.TestCase):
    """
    The test loads the yaml files and build the json script.
    This file is compared with the file stored in the data folder.
    """
    def test_jobscript_json_menu(self):

        # A fake slurm is needed in order to load the corresponding plugin
        fake_slurm_path = os.path.join(root_path, 'tests', 'fake_slurm')
        os.environ['PATH'] = fake_slurm_path + os.pathsep + os.environ['PATH']

        server_manager = manager.ServerManager()
        paths = [os.path.join(current_path, "test/etc/test_hierarchical/base_scheduler"),
                 os.path.join(current_path, "test/etc/test_hierarchical/base_service"),
                 os.path.join(current_path, "test/etc/test_hierarchical/slurm_gres")
                 ]

        server_manager.init(paths)
        display_dialog_ui = server_manager.root_node.get_gui_options()

        with tempfile.NamedTemporaryFile() as outfile:
            json.dump(display_dialog_ui, outfile, indent=4)
            outfile.flush()
            self.assertEqual(filecmp.cmp(os.path.join(current_path, "test/data/test_hierarchical.json"),
                              outfile.name), True)


if __name__ == '__main__':
    unittest.main(verbosity=2)