#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""\
YML/YSLT 2 processor version 6.2
Copyleft (c), 2009-2020 Volker Birk  http://fdik.org/yml/

"""

import sys, os, codecs, locale
import fileinput, unicodedata
from optparse import OptionParser

try:
    from lxml import etree
except:
    sys.stderr.write("This program needs lxml, see http://codespeak.net/lxml/\n")
    sys.exit(1)

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

from yml2.yml2 import ymlCStyle, comment, oldSyntax
from yml2.pyPEG import parse, u
import yml2.backend as backend

YML_DEFAULT_PATHS = [os.path.dirname(backend.__file__)]

def printInfo(option, opt_str, value, parser):
    sys.stdout.write(__doc__)
    sys.exit(0)

class YMLAssert(Exception): pass

def w(msg):
    if isinstance(msg, BaseException):
        try:
            msg = str(msg) + "\n"
        except:
            msg = u(msg) + "\n"
    sys.stderr.write(msg)

def main():
    dirsepname = {':': 'a colon', ';': 'a semicolon'}.get(os.path.pathsep, "a '%s'" % os.path.pathsep)
    optParser = OptionParser()
    optParser.add_option("-C", "--old-syntax", action="store_true", dest="old_syntax",
            help="syntax of YML 2 version 1.x (compatibility mode)", default=False)
    optParser.add_option("-D", "--emit-linenumbers", action="store_true", dest="emitlinenumbers",
            help="emit line numbers into the resulting XML for debugging purposes", default=False)
    optParser.add_option("--debug", action="store_true", dest="trace",
            help="switch on tracing to stderr", default=False)
    optParser.add_option("-d", "--paramdict", dest="params", metavar="PARAMS",
            help="call X/YSLT script with dictionary PARAMS as parameters")
    optParser.add_option("-e", "--xpath", dest="xpath", metavar="XPATH",
            help="execute XPath expression XPATH and print result")
    optParser.add_option("-E", "--encoding", dest="encoding", metavar="ENCODING", default=locale.getdefaultlocale()[1],
            help="encoding of input files (default to locale)")
    optParser.add_option("-I", "--include", dest="includePathText", metavar="INCLUDE_PATH",
            help="precede YML_PATH by %s separated INCLUDE_PATH to search for include files" % dirsepname)
    optParser.add_option("-m", "--omit-empty-parm-tags", action="store_true", dest="omitemptyparm",
            help="does nothing (only there for compatibility reasons)", default=False)
    optParser.add_option("-M", "--empty-input-document", action="store_true", dest="emptyinput",
            help="use an empty input document", default=False)
    optParser.add_option("-n", "--normalization", dest="normalization", metavar="NORMALIZATION", default="NFC",
            help="Unicode normalization (none, NFD, NFKD, NFC, NFKC, FCD, default is NFC)")
    optParser.add_option("-o", "--output", dest="outputFile", metavar="FILE",
            help="place output in file FILE")
    optParser.add_option("-p", "--parse-only", action="store_true", dest="parseonly",
            help="parse only, then output pyAST as text to stdout", default=False)
    optParser.add_option("-P", "--pretty", action="store_true", default=False,
            help="pretty print output adding whitespace")
    optParser.add_option("-s", "--stringparamdict", dest="stringparams", metavar="STRINGPARAMS",
            help="call X/YSLT script with dictionary STRINGPARAMS as string parameters")
    optParser.add_option("-x", "--xml", action="store_true", default=False,
            help="input document is XML already")
    optParser.add_option("-X", "--xslt", dest="xslt", metavar="XSLTSCRIPT",
            help="execute XSLT script XSLTSCRIPT")
    optParser.add_option("-y", "--yslt", dest="yslt", metavar="YSLTSCRIPT",
            help="execute YSLT script YSLTSCRIPT")
    optParser.add_option("-Y", "--xml2yml", action="store_true", default=False,
            help="convert XML to normalized YML code")
    optParser.add_option("-V", "--version", action="callback", callback=printInfo, help="show version info and exit")
    (options, args) = optParser.parse_args()

    if options.old_syntax:
        oldSyntax()

    if options.trace:
        backend.enable_tracing = True

    if options.emitlinenumbers:
        backend.emitlinenumbers = True

    if options.includePathText:
        backend.includePath = options.includePathText.split(os.path.pathsep)

    backend.encoding = options.encoding

    dirs = os.environ.get('YML_PATH', '.').split(os.path.pathsep) + YML_DEFAULT_PATHS
    backend.includePath.extend(dirs)

    if options.xml2yml:
        for directory in backend.includePath:
            name = os.path.join(directory, "xml2yml.ysl2")
            if os.path.isfile(name):
                options.yslt = name
                options.xml = True
                break
        else:
            sys.stderr.write("Error: Stylesheet xml2yml.ysl2 required for --xml2yml not found\n")
            sys.stderr.write("Please check your YML_PATH\n")
            sys.exit(1)

    if  (options.xslt and options.yslt) or (options.xslt and options.xpath) or (options.yslt and options.xpath):
        sys.stderr.write("Cannot combine --xpath, --xslt and --yslt params\n")
        sys.exit(1)

    try:
        ymlC = ymlCStyle()

        rtext = ""

        if not options.emptyinput:
            files = fileinput.input(args, mode="rU", openhook=fileinput.hook_encoded(options.encoding))

            if options.xml:
                rtext = ""
                for line in files:
                    rtext += line
            else:
                result = parse(ymlC, files, True, comment)
                if options.parseonly:
                    print(result)
                    sys.exit(0)
                else:
                    rtext = backend.finish(result)

        if not rtext:
            rtext = "<empty/>"

        def ymldebug(context, text):
            if options.trace:
                sys.stderr.write("Debug: " + codecs.encode(u(text), options.encoding) + "\n")
            return ""

        def ymlassert(context, value, msg):
            if options.trace:
                if not value:
                    raise YMLAssert(msg)
            return ""

        ymlns = etree.FunctionNamespace("http://fdik.org/yml")
        ymlns.prefix = "yml"
        ymlns['debug'] = ymldebug
        ymlns['assert'] = ymlassert

        if options.xpath:
            tree = etree.fromstring(rtext)
            ltree = tree.xpath(codecs.decode(options.xpath, options.encoding))
            rtext = ""
            try:
                for rtree in ltree:
                    rtext += etree.tostring(rtree, pretty_print=options.pretty, encoding=unicode)
            except:
                rtext = ltree

        elif options.yslt or options.xslt:
            params = {}

            if options.yslt:
                backend.clearAll()
                yscript = fileinput.input(options.yslt, mode="rU", openhook=fileinput.hook_encoded(options.encoding))
                yresult = parse(ymlC, yscript, True, comment)
                ytext = backend.finish(yresult)
            else:
                yscript = fileinput.input(options.xslt, mode="rU")
                ytext = ""
                for line in yscript:
                    ytext += line

            doc = etree.fromstring(rtext)

            xsltree = etree.XML(ytext, base_url=os.path.abspath(yscript.filename()))
            transform = etree.XSLT(xsltree)
            
            if options.params:
                params = eval(options.params)
                for key, value in params.iteritems():
                    if type(value) is not str:
                        params[key] = u(value)
            if options.stringparams:
                for key, value in eval(options.stringparams).iteritems():
                    params[key] = "'" + u(value) + "'"

            rresult = transform(doc, **params)
            # lxml is somewhat buggy
            try:
                rtext = u(rresult)
            except:
                rtext = etree.tostring(rresult, encoding=unicode)
                if not rtext:
                    rtext = codecs.decode(str(rresult), "utf-8")

        if options.normalization != "none":
            rtext = unicodedata.normalize(options.normalization, rtext)

        if options.pretty:
            plaintext = etree.tostring(etree.fromstring(rtext), pretty_print=True, xml_declaration=True, encoding=options.encoding)
        else:
            if isinstance(rtext, str):
                plaintext = codecs.encode(rtext, options.encoding)
            else:
                plaintext = rtext

        try:
            if plaintext[-1] == "\n":
                plaintext = plaintext[:-1]
        except: pass

        if options.outputFile and options.outputFile != "-":
            outfile = open(options.outputFile, "wb")
            outfile.write(plaintext)
            outfile.close()
        else:
            sys.stdout.buffer.write(plaintext)
            if not options.pretty:
                print()

    except KeyboardInterrupt:
        w("\n")
        sys.exit(1)
    except YMLAssert as msg:
        w("YML Assertion failed: " + u(msg) + "\n")
        sys.exit(2)
    except KeyError as msg:
        w("not found: " + u(msg) + "\n")
        sys.exit(4)
    except LookupError as msg:
        w("not found: " + u(msg) + "\n")
        sys.exit(4)
    except etree.XMLSyntaxError as e:
        log = e.error_log.filter_from_level(etree.ErrorLevels.FATAL)
        for entry in log:
            w("XML error: " + u(entry.message) + "\n")
        sys.exit(5)
    except Exception as msg:
        w(msg)
        sys.exit(5)


if __name__ == "__main__":
    sys.exit(main())

