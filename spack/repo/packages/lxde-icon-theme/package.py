# Copyright 2013-2019 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *


class LxdeIconTheme(AutotoolsPackage):
    """The LXDE Icon Theme package contains nuoveXT 2.2 Icon Theme for LXDE."""

    homepage = "http://www.linuxfromscratch.org/blfs/view/svn/x/lxde-icon-theme.html"
    url      = "https://downloads.sourceforge.net/lxde/lxde-icon-theme-0.5.1.tar.xz"

    version('0.5.1', sha256='e3d0b7399f28a360a3755171c9a08147d68f853f518be5485f5064675037916c')

    def install(self, spec, prefix):
        make()
        make('install')

    def setup_environment(self, spack_env, run_env):
        spack_env.prepend_path("XDG_DATA_DIRS",
                               self.prefix.share)
        run_env.prepend_path("XDG_DATA_DIRS",
                             self.prefix.share)

