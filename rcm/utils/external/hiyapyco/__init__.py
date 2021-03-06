#! /usr/bin/env python -tt
# vim: set fileencoding=utf-8
from __future__ import unicode_literals
"""
Hierarchical Yaml Python Config
===============================

A simple python lib allowing hierarchical config files in YAML syntax.

License
-------

(c) 2014 - 2017 Klaus Zerwes zero-sys.net
This package is free software.
This software is licensed under the terms of the
GNU GENERAL PUBLIC LICENSE version 3 or later,
as published by the Free Software Foundation.
See https://www.gnu.org/licenses/gpl.html
"""


import sys
import os
import yaml
import logging
from distutils.util import strtobool
import re
from jinja2 import Environment, Undefined, DebugUndefined, StrictUndefined, TemplateError

from . import odyldo

__all__ = [
    'load',
    'dump',
    'HiYaPyCo',
    'HiYaPyCoInvocationException',
    'HiYaPyCoImplementationException',
    ]

from . import version
__version__ = version.VERSION

logger = logging.getLogger(__name__)

_usedefaultyamlloader = False

class HiYaPyCoInvocationException(Exception):
    """dummy Exception raised on wrong invocation"""
    pass

class HiYaPyCoImplementationException(Exception):
    """dummy Exception raised if we are unable to merge some YAML stuff"""
    pass

try:
    primitiveTypes = (int, str, bool, float, unicode)
    strTypes = (str, unicode)
except NameError:
    primitiveTypes = (int, str, bool, float)
    strTypes = (str)
listTypes = (list, tuple)

# you may set this to something suitable for you
jinja2env = Environment(undefined=Undefined)

METHODS = { 'METHOD_SIMPLE':0x0001, 'METHOD_MERGE':0x0002 }
METHOD_SIMPLE = METHODS['METHOD_SIMPLE']
METHOD_MERGE = METHODS['METHOD_MERGE']

class HiYaPyCo():
    """Main class"""
    def __init__(self, *args, **kwargs):
        """
        args: YAMLfile(s)
        kwargs:
          * method: one of hiyapyco.METHOD_SIMPLE | hiyapyco.METHOD_MERGE
          * interpolate: boolean (default: False)
          * castinterpolated: boolean (default: False) try to cast values after interpolating
          * usedefaultyamlloader: boolean (default: False)
          * loglevel: one of  the valid levels from the logging module
          * failonmissingfiles: boolean (default: True)
          * loglevelmissingfiles

        Returns a representation of the merged and (if requested) interpolated config.
        Will mostly be a OrderedDict (dict if usedefaultyamlloader), but can be of any other type, depending on the yaml files.
        """
        self._data = None
        self._files = []

        self.method = None
        if 'method' in kwargs:
            logging.debug('parse kwarg method: %s ...' % kwargs['method'])
            if kwargs['method'] not in METHODS.values():
                raise HiYaPyCoInvocationException(
                        'undefined method used, must be one of: %s' %
                        ' '.join(METHODS.keys())
                    )
            self.method = kwargs['method']
            del kwargs['method']
        if self.method == None:
            self.method = METHOD_SIMPLE

        self.interpolate = False
        self.castinterpolated = False
        if 'interpolate' in kwargs:
            if not isinstance(kwargs['interpolate'], bool):
                raise HiYaPyCoInvocationException(
                        'value of "interpolate" must be boolean (got: "%s" as %s)' %
                        (kwargs['interpolate'], type(kwargs['interpolate']),)
                        )
            self.interpolate = kwargs['interpolate']
            del kwargs['interpolate']
            if 'castinterpolated' in kwargs:
                if not isinstance(kwargs['castinterpolated'], bool):
                    raise HiYaPyCoInvocationException(
                            'value of "castinterpolated" must be boolean (got: "%s" as %s)' %
                            (kwargs['castinterpolated'], type(kwargs['castinterpolated']),)
                        )
                self.castinterpolated = kwargs['castinterpolated']
                del kwargs['castinterpolated']

        if 'usedefaultyamlloader' in kwargs:
            if not isinstance(kwargs['usedefaultyamlloader'], bool):
                raise HiYaPyCoInvocationException(
                        'value of "usedefaultyamlloader" must be boolean (got: "%s" as %s)' %
                        (kwargs['usedefaultyamlloader'], type(kwargs['usedefaultyamlloader']),)
                        )
            global _usedefaultyamlloader
            _usedefaultyamlloader = kwargs['usedefaultyamlloader']
            del kwargs['usedefaultyamlloader']

        self.failonmissingfiles = True
        if 'failonmissingfiles' in kwargs:
            if not isinstance(kwargs['failonmissingfiles'], bool):
                raise HiYaPyCoInvocationException(
                        'value of "failonmissingfiles" must be boolean (got: "%s" as %s)' %
                        (kwargs['failonmissingfiles'], type(kwargs['failonmissingfiles']),)
                        )
            self.failonmissingfiles = bool(kwargs['failonmissingfiles'])
            del kwargs['failonmissingfiles']

        if 'loglevelmissingfiles' in kwargs:
            logging.getLogger('testlevellogger').setLevel(kwargs['loglevelmissingfiles'])
            self.loglevelonmissingfiles = logging.getLogger('testlevellogger').getEffectiveLevel()
            del kwargs['loglevelmissingfiles']
        else:
            self.loglevelonmissingfiles = logging.ERROR
            if not self.failonmissingfiles:
                self.loglevelonmissingfiles = logging.WARN

        if 'loglevel' in kwargs:
            logger.setLevel(kwargs['loglevel'])
            del kwargs['loglevel']

        if kwargs:
            raise HiYaPyCoInvocationException('undefined keywords: %s' % ' '.join(kwargs.keys()))

        if not args:
            raise HiYaPyCoInvocationException('no yaml files defined')

        for arg in args:
            self._updatefiles(arg)

        for yamlfile in self._files[:]:
            logger.debug('yamlfile: %s ...' % yamlfile)
            if '\n' in yamlfile:
                logger.debug('loading yaml doc from str ...')
                f = yamlfile
            else:
                fn = yamlfile
                if not os.path.isabs(yamlfile):
                    fn = os.path.join(os.getcwd(), yamlfile)
                    logger.debug('path extended for yamlfile: %s' % fn)
                try:
                    f = open(fn, 'r')
                    logger.debug('open4reading: file %s' % f)
                except IOError as e:
                    logger.log(self.loglevelonmissingfiles, e)
                    if not fn == yamlfile:
                        logger.log(self.loglevelonmissingfiles,
                                'file not found: %s (%s)' % (yamlfile, fn,))
                    else:
                        logger.log(self.loglevelonmissingfiles,
                                'file not found: %s' % yamlfile)
                    if self.failonmissingfiles:
                        raise HiYaPyCoInvocationException(
                                'yaml file not found: \'%s\'' % yamlfile
                            )
                    self._files.remove(yamlfile)
                    continue
            if _usedefaultyamlloader:
                ydata = yaml.safe_load(f)
            else:
                ydata = odyldo.safe_load(f)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug('yaml data: %s' % ydata)
            if self._data is None:
                self._data = ydata
            else:
                if self.method == METHOD_SIMPLE:
                    self._data = self._simplemerge(self._data, ydata)
                else:
                    self._data = self._deepmerge(self._data, ydata)
                logger.debug('merged data: %s' % self._data)

        if self.interpolate:
            self._data = self._interpolate(self._data)

    def _updatefiles(self, arg):
        if isinstance(arg, strTypes):
            if arg in self._files:
                logger.warn('ignoring duplicated file %s' % arg)
                return
            self._files.append(arg)
        elif isinstance(arg, listTypes):
            for larg in arg:
                self._updatefiles(larg)
        else:
            raise HiYaPyCoInvocationException('unable to handle arg %s of type %s' % (arg, type(arg),))

    def _interpolate(self, d):
        logger.debug('interpolate "%s" of type %s ...' % (d, type(d),))
        if d is None:
            return None
        if isinstance(d, strTypes):
            return self._interpolatestr(d)
        if isinstance(d, primitiveTypes):
            return d
        if isinstance(d, listTypes):
            for k, v in enumerate(d):
                d[k] = self._interpolate(v)
            return d
        if isinstance(d, dict):
            for k in d.keys():
                d[k] = self._interpolate(d[k])
            return d
        raise HiYaPyCoImplementationException('can not interpolate "%s" of type %s' % (d, type(d),))

    def _interpolatestr(self, s):
        try:
            si = jinja2env.from_string(s).render(self._data)
        except TemplateError as e:
            # FIXME: this seems to be broken for unicode str?
            raise HiYaPyCoImplementationException('error interpolating string "%s" : %s' % (s, e,))
        if not s == si:
            if self.castinterpolated:
                if not re.match( r'^\d+\.*\d*$', si):
                    try:
                        si = bool(strtobool(si))
                    except ValueError:
                        pass
                else:
                    try:
                        if '.' in si:
                            si = float(si)
                        else:
                            si = int(si)
                    except ValueError:
                        pass
            logger.debug('interpolated "%s" to "%s" (type: %s)' % (s, si, type(si),))
        return si

    def _simplemerge(self, a, b):
        logger.debug('simplemerge %s (%s) and %s (%s)' % (a, type(a), b, type(b),))
        # FIXME: make None usage configurable
        if b is None:
            logger.debug('pass as b is None')
            pass
        elif isinstance(b, primitiveTypes):
            logger.debug('simplemerge: primitiveTypes replace a "%s"  w/ b "%s"' % (a, b,))
            a = b
        elif isinstance(b, listTypes):
            logger.debug('simplemerge: listTypes a "%s"  w/ b "%s"' % (a, b,))
            if isinstance(a, listTypes):
                for k, v in enumerate(b):
                    try:
                        a[k] = self._simplemerge(a[k], b[k])
                    except IndexError:
                        a[k] = b[k]
            else:
                logger.debug('simplemerge: replace %s w/ list %s' % (a, b,))
                a = b
        elif isinstance(b, dict):
            if isinstance(a, dict):
                logger.debug('simplemerge: update %s:"%s" by %s:"%s"' % (type(a), a, type(b), b,))
                a.update(b)
            else:
                logger.debug('simplemerge: replace %s w/ dict %s' % (a, b,))
                a = b
        else:
            raise HiYaPyCoImplementationException(
                    'can not (simple)merge %s to %s (@ "%s" try to merge "%s")' %
                    (type(b), type(a), a, b,)
                    )
        return a

    def _deepmerge(self, a, b):
        logger.debug('>'*30)
        logger.debug('deepmerge %s and %s' % (a, b,))
        # FIXME: make None usage configurable
        if b is None:
            logger.debug('pass as b is None')
            pass
        if a is None or isinstance(b, primitiveTypes):
            logger.debug('deepmerge: replace a "%s"  w/ b "%s"' % (a, b,))
            a = b
        elif isinstance(a, listTypes):
            if isinstance(b, listTypes):
                logger.debug('deepmerge: lists extend %s:"%s" by %s:"%s"' % (type(a), a, type(b), b,))
                a.extend(be for be in b if be not in a and
                            (isinstance(be, primitiveTypes) or isinstance(be, listTypes))
                        )
                srcdicts = {}
                for k, bd in enumerate(b):
                    if isinstance(bd, dict):
                        srcdicts.update({k:bd})
                logger.debug('srcdicts: %s' % srcdicts)
                for k, ad in enumerate(a):
                    logger.debug('deepmerge ad "%s" w/ k "%s" of type %s' % (ad, k, type(ad)))
                    if isinstance(ad, dict):
                        if k in srcdicts.keys():
                            # we merge only if at least one key in dict is matching
                            merge = False
                            for ak in ad.keys():
                                if ak in srcdicts[k].keys():
                                    merge = True
                                    break
                            if merge:
                                logger.debug(
                                        'deepmerge ad: deep merge list dict elem w/ key:%s: "%s" and "%s"'
                                        % (ak, ad, srcdicts[k],)
                                    )
                                a[k] = self._deepmerge(ad, srcdicts[k])
                                del srcdicts[k]
                logger.debug('deepmerge list: remaining srcdicts elems: %s' % srcdicts)
                for k in srcdicts.keys():
                    logger.debug('deepmerge list: new dict append %s:%s' % (k, srcdicts[k]))
                    a.append(srcdicts[k])
            else:
                raise HiYaPyCoImplementationException(
                        'can not merge %s to %s (@ "%s"  try to merge "%s")' %
                        (type(b), type(a), a, b,)
                        )
        elif isinstance(a, dict):
            if isinstance(b, dict):
                logger.debug('deepmerge: dict ... "%s" and "%s"' % (a, b,))
                for k in b:
                    if k in a:
                        logger.debug('deepmerge dict: loop for key "%s": "%s" and "%s"' % (k, a[k], b[k],))
                        a[k] = self._deepmerge(a[k], b[k])
                    else:
                        logger.debug('deepmerge dict: set key %s' % k)
                        a[k] = b[k]
            elif isinstance(b, listTypes):
                logger.debug('deepmerge: dict <- list ... "%s" <- "%s"' % (a, b,))
                for bd in b:
                    if isinstance(bd, dict):
                        a = self._deepmerge(a, bd)
                    else:
                        raise HiYaPyCoImplementationException(
                                'can not merge element from list of type %s to dict (@ "%s" try to merge "%s")' %
                                (type(b), a, b,)
                                )
            else:
                raise HiYaPyCoImplementationException(
                        'can not merge %s to %s (@ "%s" try to merge "%s")' %
                        (type(b), type(a), a, b,)
                        )
        logger.debug('end deepmerge part: return: "%s"' % a)
        logger.debug('<'*30)
        return a

    def yamlfiles(self):
        return self._files

    def __str__(self):
        """String representation of the class"""
        return '%s [%s]' % (__name__, os.pathsep.join(self._files))

    def data(self):
        """return the data, merged and interpolated if required"""
        return self._data

    def dump(self, **kwds):
        """dump the data as YAML"""
        return dump(self._data, **kwds)

def dump(data, **kwds):
    """dump the data as YAML"""
    if _usedefaultyamlloader:
        return yaml.safe_dump(data, **kwds)
    else:
        return odyldo.safe_dump(data, **kwds)

def load(*args, **kwargs):
    """
    Load a Hierarchical Yaml Python Config
    --------------------------------------

    args: YAMLfile(s)
    kwargs:
      * method: one of hiyapyco.METHOD_SIMPLE | hiyapyco.METHOD_MERGE
      * interpolate: boolean (default: False)
      * castinterpolated: boolean (default: False) try to cast values after interpolating
      * usedefaultyamlloader: boolean (default: False)
      * loglevel: one of  the valid levels from the logging module
      * failonmissingfiles: boolean (default: True)
      * loglevelmissingfiles

    Returns a representation of the merged and (if requested) interpolated config.
    Will mostly be a OrderedDict (dict if usedefaultyamlloader), but can be of any other type, depending on the yaml files.
    """
    hiyapyco = HiYaPyCo(*args, **kwargs)
    return hiyapyco.data()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent nu

