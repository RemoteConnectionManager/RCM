# -*- coding: utf-8 -*-
import re
import string
import os


class StringTemplate(string.Template):
    def __init__(self, s=''):
        string.Template.__init__(self, s)
        rr = """
         \@(?:
          (?P<escaped>\@) |   # Escape sequence of two delimiters
          (?P<named>[_a-z][_a-z0-9]*)      |   # delimiter and a Python identifier
          \{(?P<braced>[_\.\-a-z][_\.\-a-z0-9]*)\}   |   # delimiter and a braced identifier
          (?P<invalid>\@)              # Other ill-formed delimiter exprs
         )
        """
        self.pattern = re.compile(rr, re.VERBOSE | re.IGNORECASE)
        self.delimiter = '@'

    def templ_match(self, s=''):
        m = self.pattern.search(s)
        return m


class filetemplate(StringTemplate):
    def __init__(self, file=''):
        if os.path.exists(file):
            s = file.read()
            StringTemplate.__init__(self, s)
        else:
            print("file", file, "not found")
            return None


if __name__ == '__main__':

    d = dict()
    d["general"] = "BAD_SUBSTITUTE"
    d['PKG_WORK_DIR'] = "${BA_PKG_WORK_DIR}"
    d["general.download"] = "http://www.my.url/pippo.tar.gz"
    d["DOWNLOAD_URL"] = "$DOWNLOAD_URL"
    d["PKG_SOURCE_DIR"] = "${BA_PKG_SOURCE_DIR}"
    d["uu.pp"] = "BAD_SUBSTITUTE"
    d["uu"] = "OK_SUBSTITUTE"
    d["dddd"] = "OK_SUBSTITUTE"
    download = """
     -- @@--{pp.qq} -- aa@uu.pp @dddd@
     cd @{PKG_WORK_DIR}
     file=`python -c "import os; import sys;  print os.path.basename(sys.argv[1])" @DOWNLOAD_URL`
     if ! test -f ${file} ; then
       wget @{general.download}
     fi
     mkdir @{PKG_SOURCE_DIR}
     tar -xvzf  ${file} --strip-components=1 -C @{PKG_SOURCE_DIR}


    """
    print("---original--")
    print(download)
    print("-----------subst-----------")
    out = StringTemplate(download).safe_substitute(d)
    print(out)
    m = StringTemplate().templ_match(out)
    if m:
        print("----unmatched----")
        print(m.group())
    else:
        print("----------------------")

    bad = filetemplate("non_existing_file")
    print("----", bad)

    exit()
    r = StringTemplate().pattern
    print(r.pattern)
    dd = dict()
    for i in d:
        dd[i] = d[i]
        mi = r.search(download)
        if mi:
            print("matched input at pos ", mi.start())
            t = StringTemplate(download)
            out = t.safe_substitute(dd)
            print(out)
            mo = r.search(out)
            if mo:
                print("matched output at pos ", mo.start())
                print(mo.groupdict())
