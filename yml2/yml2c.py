#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""\
YML 2 compiler version 6.2
Copyleft (c), 2009-2020, Volker Birk  http://fdik.org/yml/

"""

import sys, os, codecs, locale
import fileinput, unicodedata
from optparse import OptionParser

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

from yml2.pyPEG import parse, u
from yml2.yml2 import ymlCStyle, comment, oldSyntax
import yml2.backend as backend

YML_DEFAULT_PATHS = [os.path.dirname(backend.__file__)]

def printInfo(option, opt_str, value, parser):
    sys.stdout.write(__doc__)
    sys.exit(0)

def w(msg):
    if isinstance(msg, BaseException):
        msg = str(msg) + "\n"
    if type(msg) is bytes:
        msg = codecs.encode(msg, sys.stderr.encoding)
    sys.stderr.write(msg)

def main():
    dirsepname = {':': 'a colon', ';': 'a semicolon'}.get(os.path.pathsep, "a '%s'" % os.path.pathsep)
    optParser = OptionParser()
    optParser.add_option("-C", "--old-syntax", action="store_true", dest="old_syntax",
            help="syntax of YML 2 version 1.x (compatibility mode)", default=False)
    optParser.add_option("-D", "--emit-linenumbers", action="store_true", dest="emitlinenumbers",
            help="emit line numbers into the resulting XML for debugging purposes", default=False)
    optParser.add_option("-E", "--encoding", dest="encoding", metavar="ENCODING", default=locale.getdefaultlocale()[1],
            help="encoding of input files (default to locale)")
    optParser.add_option("-I", "--include", dest="includePathText", metavar="INCLUDE_PATH",
            help="precede YML_PATH by %s separated INCLUDE_PATH to search for include files" % dirsepname)
    optParser.add_option("-m", "--omit-empty-parm-tags", action="store_true", dest="omitemptyparm",
            help="does nothing (only there for compatibility reasons)", default=False)
    optParser.add_option("-n", "--normalization", dest="normalization", metavar="NORMALIZATION", default="NFC",
            help="Unicode normalization (none, NFD, NFKD, NFC, NFKC, FCD, default is NFC)")
    optParser.add_option("-o", "--output", dest="outputFile", metavar="FILE",
            help="place output in file FILE")
    optParser.add_option("-p", "--parse-only", action="store_true", dest="parseonly",
            help="parse only, then output pyAST as text to stdout", default=False)
    optParser.add_option("-V", "--version", action="callback", callback=printInfo, help="show version info")
    (options, args) = optParser.parse_args()

    if options.old_syntax:
        oldSyntax()

    if options.emitlinenumbers:
        backend.emitlinenumbers = True

    backend.encoding = options.encoding

    try:
        if options.includePathText:
            backend.includePath = options.includePathText.split(os.path.pathsep)

        dirs = os.environ.get('YML_PATH', '.').split(os.path.pathsep) + YML_DEFAULT_PATHS
        backend.includePath.extend(dirs)

        files = fileinput.input(args, mode="rU", openhook=fileinput.hook_encoded(options.encoding))

        ymlC = ymlCStyle()
        result = parse(ymlC, files, True, comment, packrat=True)

        if options.parseonly:
            print(result)
        else:
            result = backend.finish(result)
            if options.normalization != "none":
                result = unicodedata.normalize(options.normalization, result)

            if options.outputFile and options.outputFile != "-":
                outfile = open(options.outputFile, "wb")
                outfile.write(codecs.encode(result, options.encoding))
                outfile.close()
            else:
                sys.stdout.buffer.write(codecs.encode(result, options.encoding))
                print()

    except KeyboardInterrupt:
        w("\n")
        sys.exit(1)
    except KeyError as msg:
        w("not found: " + u(msg) + "\n")
        sys.exit(4)
    except LookupError as msg:
        w("not found: " + u(msg) + "\n")
        sys.exit(4)
    except Exception as msg:
        w(msg)
        sys.exit(5)


if __name__ == "__main__":
    sys.exit(main())

