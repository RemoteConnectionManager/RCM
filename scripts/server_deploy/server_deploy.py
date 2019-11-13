import os
import errno
import glob
import logging

#lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib')
#if not lib_path in sys.path:
#    sys.path.append(lib_path)

import utils
import cascade_yaml_config


logging.debug("imported __file__:" + os.path.realpath(__file__))



class RcmServerDeploy(cascade_yaml_config.ArgparseSubcommandManager):

    def __init__(self, **kwargs):
        super(RcmServerDeploy, self).__init__(**kwargs)
        for par in kwargs:
            self.logger.debug("init par "+ par+" --> "+str(kwargs[par]))

    def _force_symlink(self, file1, file2):
        try:
            os.symlink(file1, file2)
        except OSError as e:
            if e.errno == errno.EEXIST:
                self.logger.warning("removing file-->" + file2 + " linking to -->" + file1)
                os.remove(file2)
                os.symlink(file1, file2)

    def fromsource(self,
                   source_dir='src',
                   module_base_dir='deploy/modules',
                   module_name='rcm',
                   install_dir='deploy/install',
                   module_version='fromsource',
                   module_setup='',
                   config_dir='config'):



        out_module_dir = cascade_yaml_config.abs_deploy_path(os.path.join(module_base_dir, module_name))
        if not os.path.exists(out_module_dir):
            self.logger.info("creating modules_dir-->" + out_module_dir + "<--")
            os.makedirs(out_module_dir)
        out_install_dir = cascade_yaml_config.abs_deploy_path(install_dir)
        if not os.path.exists(out_install_dir):
            self.logger.info("creating install_dir-->" + out_install_dir + "<--")
            os.makedirs(out_install_dir)

        self.logger.info("install and module dirs: " + out_install_dir + out_module_dir)

        self._force_symlink(source_dir, os.path.join(out_install_dir, 'src'))
        old_client_server_dir = os.path.join(out_install_dir, 'bin', 'server')
        if not os.path.exists(old_client_server_dir):
            os.makedirs(old_client_server_dir)
        self._force_symlink(os.path.join(source_dir, 'rcm', 'server', 'bin', 'server'),
                   os.path.join(out_install_dir, 'bin', 'server', 'rcm_new_server.py'))
        self._force_symlink(config_dir, os.path.join(out_install_dir, 'bin', 'config'))

        module_template = self.top_config['defaults', 'rcm', 'module_template']
        #print("@@@@@ module template:", module_template)
        module_out=utils.stringtemplate(module_template).safe_substitute({
             'INSTALL_DIR' : install_dir,
             'CONFIG_DIR' : config_dir,
             'MODULE_SETUP' : module_setup})

        modulefile = os.path.join(out_module_dir, module_version)
        with open(modulefile, 'w') as f:
            f.write(module_out)

        self.logger.info("writing module module file:" + modulefile)
