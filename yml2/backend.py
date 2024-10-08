# 2.7.4 backend

# written by VB.

import re, codecs
import fileinput
import sys, traceback, os
from xml.sax.saxutils import escape, quoteattr
from copy import copy, deepcopy
from glob import glob
from .pyPEG import code, parse, parseLine, u, Symbol
from .grammar import ymlCStyle, comment, _inner

ymlFunc, pointers, pythonFunc = {}, {}, {}
in_ns = ""
operator = []
included = ""
includePath = []
emitlinenumbers = False
encoding = "utf-8"

first = True
enable_tracing = False

ymlFunc["decl"] = "#error"
ymlFunc["define"] = "#error"
ymlFunc["operator"] = "#error"

def clearAll():
    global ymlFunc, pointers, pythonFunc, in_ns, operator, included
    ymlFunc, pointers, pythonFunc = {}, {}, {}
    in_ns = ""
    operator = []
    included = ""

lq = re.compile(r"\|(\>*)(.*)")
sq = re.compile(r"(\d*)\>(.*)")
ts = re.compile(r'(\|\|(?P<inds>\>*)\s*\n(?P<text1>.*?)\n(?P<base>\s*)\|\|)|("""(?P<text2>.*?)""")|(\>\>(?P<text3>.*?)\>\>)', re.S)
tq = re.compile(r"(\]|\<)\s*(.*)")
bq = re.compile(r"\`(.*?)\`", re.S)
bqq = re.compile(r"\s*\`\`(.*)")
all = re.compile(r".*", re.S)

line = 1

def pointer(name):
    try:
        return u(pointers[name[1:]])
    except:
        if name == "*_trace_info":
            return '""'
        if included:
            raise LookupError("in " + included + ":" + u(line) + ": pointer " + name)
        else:
            raise LookupError("in " + u(line) + ": pointer " + name)

def evalPython(expr):
    try:
        result = eval(u(expr), pythonFunc)
        if type(result) is bytes:
            return codecs.decode(result, encoding)
        else:
            return result
    except:
        name, parm, tb = sys.exc_info()
        msg = "in python expression: " + u(parm)
        if name is SyntaxError:
            tbl = traceback.format_exception(name, parm, tb)
            msg += "\n" + tbl[-3] + tbl[-2]
        else:
            msg += ": " + expr + "\n"
        if included:
            raise name("in " + included + ":" + u(line) + ": " + msg)
        else:
            raise name("in " + u(line) + ": " + msg)
    
def execPython(script):
    try:
        if type(script) is str:
            exec(script, pythonFunc)
        else:
            exec(codecs.decode(script, encoding), pythonFunc)
    except:
        name, parm, tb = sys.exc_info()
        msg = "in python script: " + u(parm)
        if name is SyntaxError:
            tbl = traceback.format_exception(name, parm, tb)
            msg += "\n" + tbl[-3] + tbl[-2]
        else:
            msg += ": " + expr + "\n"
        if included:
            raise name("in " + included + ":" + u(line) + ": " + msg)
        else:
            raise name("in " + u(line) + ": " + msg)

def textOut(text):
    if not text:
        return ""
    if type(text) is not str:
        text = codecs.decode(text, encoding)
    text = text.replace(r'\"', r'\\"')
    text = '"""' + text.replace('"', r'\"') + '"""'
    try:
        textFunc = ymlFunc["text"]
        parms = ['text', ('parm', [text])]
        c, result = textFunc(parms)
        if c:
            if type(textFunc.alias) is str:
                result += "</" + textFunc.alias + ">"
            else:
                result += "</" + codecs.decode(textFunc.alias, encoding) + ">"
        return result
    except:
        return escape(eval(text))

def strRepl(text):
    if not text:
        return ""
    if type(text) is not str:
        text = codecs.decode(text, encoding)
    text = text.replace(r'\"', r'\\"')
    text = '"""' + text.replace('"', r'\"') + '"""'
    if type(text) is str:
        return escape(eval(text))

def applyMacros(macros, text):
    result = text
    for key, value in macros.items():
        result = result.replace(key, value)
    return result

class YF:
    def __init__(self, name):
        self.name = name
        self.parms = []
        self.descends = []
        self.values = {}
        self.content = None
        self.pointers = {}
        self.macros = {}
        if in_ns:
            self.alias = in_ns + ":" + name.replace("_", "-")
        else:
            self.alias = name.replace("_", "-")
        pythonFunc["yml_" + name] = self
        if emitlinenumbers:
            self.values["yml:declared"] = u(line)

    def copy(self, newName):
        yf = YF(newName)
        yf.parms.extend(self.parms)
        yf.descends.extend(self.descends)
        yf.values = self.values.copy()
        yf.content = self.content
        yf.pointers = self.pointers.copy()
        yf.macros = self.macros.copy()
        yf.alias = self.alias
        return yf

    def patch(self, second):
        self.parms.extend(second.parms)
        self.descends.extend(second.descends)
        self.values.update(second.values)
        if second.content:
            self.content = second.content
        self.pointers.update(second.pointers)
        self.macros.update(second.macros)

    def __call__(self, called_with, hasContent = False, avoidTag = False):
        global pointers
        parms = []
        vals = {}
        if self.pointers:
            pointers.update(self.pointers)
   
        for data in called_with:
            if type(data) is tuple or type(data) is Symbol:
                if data[0] == "parm":
                    l = data[1]
                    parm = l[0]
                    if parm[0] == "*":
                        parm = pointer(parm)
                    if len(l) == 1:
                        if type(parm) is tuple or type(parm) is Symbol:
                            if parm[0] == "pyExp":
                                val = evalPython(parm[1][0])
                                parms.append(val)
                        else:
                            parms.append(evalPython((parm)))
                    else:
                        if type(parm) is tuple or type(parm) is Symbol:
                            if parm[0] == "pyExp":
                                parm = evalPython(parm[1][0])
                        val = l[1]
                        if type(val) is tuple or type(val) is Symbol:
                            if val[0] == "pyExp":
                                val = evalPython(val[1][0])
                        if val[0] == "*":
                            val = pointer(val)
                        if u(val)[0] == '"' or u(val)[0] == "'":
                            vals[parm] = evalPython(u(val))
                        else:
                            vals[parm] = u(val)
                elif data[0] == "content":
                    hasContent = True

        if enable_tracing:
            text = u(parms) + ", " + u(vals)
            pointers["_trace_info"] = '"' + u(line) + ": " + u(self.name) + " " + text.replace('"', '#') + '"'

        if emitlinenumbers:
            global first
            if first:
                vals["xmlns:yml"] = "http://fdik.org/yml"
                first = False
            vals["yml:called"] = u(line)
        return self.xml(parms, vals, hasContent, avoidTag)

    def addParm(self, parm):
        if parm[0] == "%":
            for i in range(len(self.parms)):
                if self.parms[i][0] != "%":
                    self.parms.insert(i, parm)
                    return
        self.parms.append(parm)

    def addDescend(self, desc):
        if desc[0] == "+" or desc[0] == "@":
            self.descends.append(desc[1:])
        else:
            self.descends.append(desc)

    def addValue(self, parm, value):
        if type(value) is str or type(value) is str:
            if value[0] != "'" and value[0] != '"':
                self.values[parm] = u(value)
            else:
                self.values[parm] = u(evalPython(value))
        else:
            self.values[parm] = u(evalPython(u(value)))

    def xml(self, callParms, callValues, hasContent, avoidTag = False):
        global pointers
        extraContent = ""
        if self.content:
            hasContent = True
        resultParms = self.values.copy()
        macros = self.macros.copy()
        toDelete = [ key for key in resultParms.keys() ]
        toPointers = {}
        for key in toDelete:
            if key[0] == "*":
                toPointers[key] = resultParms.pop(key)
        for key, value in callValues.items():
            if key[0] == "%":
                macros[key] = value
            else:
                resultParms[key] = value
        i = 0
        for cp in callParms:
            if i < len(self.parms):
                if self.parms[i][0] == "*":
                    toPointers[self.parms[i]] = cp
                elif self.parms[i][0] == "%":
                    macros[self.parms[i]] = u(cp)
                else:
                    resultParms[self.parms[i]] = cp
            else:
                extraContent += u(cp)
                hasContent = True
            i += 1
        for k,v in toPointers.items():
            v = applyMacros(macros, u(v))
            q = '"' if "'" in v else "'"
            pointers[k[1:]] = q + v + q
        result = ""
        for p, v in resultParms.items():
            if p[0] == "'" or p[0] == '"':
                p = eval(p)
            result += " "+ p + "=" + quoteattr(applyMacros(macros, u(v)))
        if hasContent:
            if avoidTag:
                return True, strRepl(extraContent)
            else:
                return True, "<" + self.alias + result + ">" + strRepl(extraContent)
        else:
            if avoidTag:
                return False, ""
            else:
                return False, "<" + self.alias + result + "/>"

def replaceContent(tree, subtree):
    n = 0
    while n < len(tree):
        obj = tree[n]
        if obj[0] == "func":
            l = obj[1]
            if l[0] == "content":
                d = 1
                if subtree:
                    for el in subtree:
                        tree.insert(n+d, el)
                        d += 1
                del tree[n]
                n += d
            else:
                try:
                    if l[-1][0] == "content":
                        replaceContent(l[-1][1], subtree)
                except: pass
        elif obj[0] == "funclist":
            replaceContent(obj[1], subtree)
        n += 1
    return tree

def executeCmd(text):
    if type(text) is not str:
        text = codecs.decode(text, encoding)
    for (regex, pattern) in operator:
        match = re.search(regex, text)
        while match:
            cmd = pattern
            opt = match.groups()
            for i in range(len(opt)):
                cmd = cmd.replace("%" + u(i+1), opt[i])
            text = text[:match.start()] + "`" + cmd + "`"+ text[match.end():]
            match = re.search(regex, text)

    result = ""
    m = re.search(bq, text)
    while text and m:
        cmd  = m.group(1)
        head = textOut(text[:m.start()])
        text = text[m.end():]
        try:
            r, rest = parseLine(cmd, _inner, [], True, comment)
            if rest: raise SyntaxError(cmd)
        except SyntaxError:
            if included:
                raise SyntaxError("in " + included + ":" + u(line) + ": syntax error in executing command: " + cmd.strip())
            else:
                raise SyntaxError("in " + u(line) + ": syntax error in executing command: " + cmd.strip())
        inner = _finish(r)
        result += head + inner
        m = re.search(bq, text)
    result += textOut(text)

    return result

def codegen(obj):
    global in_ns, pointers, line, included
    ctype = obj[0]

    if type(obj) is code:
        return obj

    try:
        if ctype.line: line = ctype.line
    except: pass

    if ctype == "empty":
        return code("")

    if ctype == "in_ns":
        in_ns = obj[1][0]
        subtree = obj[1]
        for sel in subtree:
            codegen(sel)
        in_ns = ""
        return code("")

    elif ctype == "decl":
        name = ""
        for data in obj[1]:
            if type(data) is str:
                name = data
                try:
                    yf = ymlFunc[name]
                    yf.alias
                except:
                    ymlFunc[name] = YF(name)
                    yf = ymlFunc[name]
                    if in_ns:
                        yf.alias = in_ns + ":" + name
                        if not enable_tracing:
                            if in_ns == "xsl" and (name == "debug" or name=="assert" or name[:7]=="_trace_"):
                                yf.alias = "-"
                                yf.addParm("skip1")
                                yf.addParm("skip2")
                                break
            elif type(data) is tuple or type(data) is Symbol:
                if data[0] == "base":
                    base = data[1][0]
                    try:
                        yf = ymlFunc[name] = ymlFunc[base].copy(name)
                    except KeyError:
                        if included:
                            raise KeyError("in " + included + ":" + u(line) + ": " + base + " as base for " + name)
                        else:
                            raise KeyError("in " + u(line) + ": " + base + " as base for " + name)
                elif data[0] == "shape":
                    shape = ymlFunc[data[1]]
                    try:
                        yf = ymlFunc[name]
                        yf.patch(shape)
                    except KeyError:
                        if included:
                            raise KeyError("in " + included + ":" + u(line) + ": " + base + " as shape for " + name)
                        else:
                            raise KeyError("in " + u(line) + ": " + base + " as shape for " + name)
                elif data[0] == "descend":
                    yf.addDescend(data[1])
                elif data[0] == "declParm":
                    l = data[1]
                    parmName = l[0]
                    if len(l)==1:
                        yf.addParm(parmName)
                    else:
                        value = l[1]
                        if parmName[0] != "%":
                            yf.addValue(parmName, value)
                        if parmName[0] == "*":
                            yf.pointers[parmName[1:]] = value
                            yf.addParm(parmName)
                        elif parmName[0] == "%":
                            if type(value) is str:
                                yf.macros[parmName] = u(evalPython(value))
                            else:
                                yf.macros[parmName] = u(evalPython(u(value)))
                            yf.addParm(parmName)
                elif data[0] == "alias":
                    if in_ns:
                        yf.alias = in_ns + ":" + data[1][0]
                    else:
                        yf.alias = data[1][0]
                elif data[0] == "content":
                    yf.content = data[1]

        return code("")

    elif ctype == "funclist":
        result = ""
        for f in obj[1]:
            result += codegen(f)
        return code(result)

    elif ctype == "parentheses":
        if len(obj[1]):
            return codegen(('func', ['_parentheses', ('content', [obj[1][0]])]))
        else:
            return ""

    elif ctype == "fparm":
        if len(obj[1]):
            return codegen(('func', ['_parm', ('content', [obj[1][0]])]))
        else:
            return ""

    elif ctype == "generic":
        return codegen(('func', ['_generic', ('content', [obj[1][0]])]))

    elif ctype == "xbase":
        return codegen(('func', ['_base', ('content', [obj[1][0]])]))

    elif ctype == "func":
        avoidTag = False
        name = obj[1][0]

        if name == "decl":
            if ymlFunc[name] == "#error":
                if included:
                    raise SyntaxError("in " + included + ":" + u(line) + ": syntax error in decl statement")
                else:
                    raise SyntaxError("in " + u(line) + ": syntax error in decl statement")
        if name == "define" or name == "operator":
            if ymlFunc[name] == "#error":
                if included:
                    raise SyntaxError("in " + included + ":" + u(line) + ": syntax error in define statement")
                else:
                    raise SyntaxError("in " + u(line) + ": syntax error in define statement")

        if name[0] == "&":
            avoidTag = True
            name = name[1:]
        hasContent = False

        if len(name) > 2:
            if name[0:2] == "**":
                return code(eval(''+pointer(name[1:])))

        if name[0] == "*":
            name = eval(pointer(name))
            if name[0] == "&":
                avoidTag = True
                name = name[1:]

        try:
            ymlFunc[name]
        except KeyError:
            try:
                if ymlFunc["_"].alias != "-":
                    return codegen(('func', ['_', ('content', [('funclist', [obj])])]))
                else:
                    ymlFunc[name] = copy(ymlFunc["_"])
                    ymlFunc[name].alias = name.replace("_", "-")
                    return codegen(obj)
            except KeyError:
                ymlFunc[name] = YF(name)
        
        if ymlFunc[name].alias == "-": avoidTag = True

        to_add = []
        if len(ymlFunc[name].descends):
            if obj[1][-1][0] != 'content':
                if included:
                    raise KeyError("in " + included + ":" + u(line) + ": " + name + " has descending attributes, but no descendants are following")
                else:
                    raise KeyError("in " + u(line) + ": " + name + " has descending attributes, but no descendants are following")

            def first_func(obj):
                if type(obj) is tuple or type(obj) is Symbol:
                    if obj[0] == 'func':
                        return obj
                    elif obj[0] == 'funclist':
                        return first_func(obj[1])
                    elif obj[0] == 'content':
                        return first_func(obj[1])
                    else:
                        return None
                elif type(obj) == list:
                    for e in obj:
                        f = first_func(e)
                        if f: return f
                    return None

            def copy_without_first_func(o, found = False):
                c = []
                for obj in o:
                    if found:
                        c.append(obj)
                    else:
                        if obj[0] == 'func':
                            if obj[1][-1][0] == 'content':
                                c.extend( obj[1][-1][1] )
                            found = True
                        else:
                            c.append( ( obj[0], copy_without_first_func(obj[1], False ) ) )
                return c

            def get_parms(obj):
                result = []
                for e in obj[1]:
                    if type(e) is tuple or type(e) is Symbol:
                        if e[0] == "parm":
                            result.append( e )
                return result

            try:
                add_params = get_parms(obj)
                for e in obj[1][-1][1]:
                    c = e[1]
                    for dname in ymlFunc[name].descends:
                        f, c = first_func(c), copy_without_first_func(c)
                        if dname[0] == "*":
                            pointers[dname[1:]] = "'" + f[1][0] + "'"
                        else:
                            add_params.append( ('parm', [dname, "'" + f[1][0] + "'"]) )
                        try:
                            add_params.extend( get_parms(f) )
                        except: pass

                    new_things = [ e[1][0] ]
                    new_things.extend( add_params )
                    new_things.append( ('content', c) )
                    
                    to_add.append( ('func', new_things ) )
            except:
                if included:
                    raise KeyError("in " + included + ":" + u(line) + ": " + name + " has descending attributes, and too less descendants are following")
                else:
                    raise KeyError("in " + u(line) + ": " + name + " has descending attributes, and too less descendants are following")

        if not to_add:
            to_add = ( obj, )

        complete = ""

        for obj in to_add:
            subtree = None
            try:
                if obj[1][-1][0] == "content":
                    subtree = obj[1][-1][1]
            except: pass
     
            if ymlFunc[name].content:
                hasContent = True
                treetemplate = deepcopy(ymlFunc[name].content)
                subtree = replaceContent(treetemplate, subtree)

            if subtree:
                hasContent = True

            hasContent, result = ymlFunc[name](obj[1], hasContent, avoidTag)

            if subtree:
                for sel in subtree:
                    result += codegen(sel)

            if hasContent and not(avoidTag):
                result += "</" + ymlFunc[name].alias + ">"

            complete += result

        return code(complete)

    elif ctype == "textsection":
        result = ''
        ll = obj[1].splitlines()
        space = len(ll[-1]) - 2
        for l in ll[1:-1]:
            m = re.match(bqq, l)
            if m:
                cmd = m.group(1)
                try:
                    r, x = parseLine(cmd, _inner, [], True, comment)
                    if x: raise SyntaxError(cmd)
                    result += _finish(r)
                except SyntaxError:
                    if included:
                        raise SyntaxError("in " + included + ":" + u(line) + ": syntax error in executing command: " + cmd.strip())
                    else:
                        raise SyntaxError("in " + u(line) + ": syntax error in executing command: " + cmd.strip())
            else:
                result += codegen(Symbol('lineQuote', '| ' + l[space:]))
        return code(result)

    elif ctype == "textsectionu":
        result = ''
        ll = obj[1].splitlines()
        space = len(ll[-1]) - 2
        for l in ll[1:-1]:
            m = re.match(bqq, l)
            if m:
                cmd = m.group(1)
                try:
                    r, x = parseLine(cmd, _inner, [], True, comment)
                    if x: raise SyntaxError(cmd)
                    result += _finish(r)
                except SyntaxError:
                    if included:
                        raise SyntaxError("in " + included + ":" + u(line) + ": syntax error in executing command: " + cmd.strip())
                    else:
                        raise SyntaxError("in " + u(line) + ": syntax error in executing command: " + cmd.strip())
            else:
                if result != '': result += ' '
                result += codegen(Symbol('quote', ['> ' + l[space:]]))
        return code(result)

    elif ctype == "lineQuote" or ctype == "quote":
        m, text, base, inds = None, "", 0, 0

        if ctype == "lineQuote":
            text = obj[1]
            m = lq.match(text)
            if m:
                inds = len(m.group(1))
                text = m.group(2)[1:]
            else: inds = 0
        elif ctype == "quote":
            inds = -1
            text = obj[1][0]
            m = sq.match(text)
            if m:
                if m.group(1):
                    inds = int(m.group(1))
                text = m.group(2)[1:]
            else:
                if type(text) is str:
                    text = u(evalPython(text))

        ind = ""
        if inds > -1:
            try:
                cmd = evalPython("indent(" + u(inds) + ")")
                result, rest = parseLine(u(cmd), _inner, [], True, comment)
                if rest:
                    raise SyntaxError()
                ind = _finish(result)
            except: pass
        
        if ctype == "lineQuote": text += "\n"

        hasTextFunc = False
        try:
            ymlFunc["text"]
            hasTextFunc = True
        except: pass

        text = executeCmd(text)
        return code(ind + text) 

    elif ctype == "tagQuote":
        m = tq.match(obj[1])
        if m.group(1) == "<":
            return code("<" + m.group(2))
        else:
            return code(m.group(2))

    elif ctype == "operator":
        operator.append((re.compile(evalPython(obj[1][0])), obj[1][1]))
        return code("")

    elif ctype == "constant":
        name = obj[1][0]
        if name[0] == "*":
            name = name[1:]
        value = obj[1][1]
        pointers[name] = value
        return code("")

    elif ctype == "include":
        reverse = False
        ktext, kxml, kpointer = False, False, False
        for arg in obj[1]:
            if type(arg) is tuple or type(arg) is Symbol:
                if arg[0] == "reverse":
                    reverse = True
                elif arg[0] == "ktext":
                    ktext = True
                elif arg[0] == "kxml":
                    kxml = True
                elif arg[0] == "kpointer":
                    kpointer = True
            elif type(arg) is str:
                filemask = arg

        if kpointer:
            filemask = eval(pointer(filemask))

        if filemask[0] == '/' or filemask[0] == '.':
            files = sorted(glob(filemask))
        else:
            files = []
            for directory in includePath:
                path = os.path.join(directory, filemask)
                files.extend(sorted(glob(path)))

        if files and reverse:
            files = files[-1::-1]

        if not(files):
            if included:
                raise IOError("in " + included + ":" + u(line) + ": include file(s) '" + filemask + "' not found")
            else:
                raise IOError("in " + u(line) + ": include file(s) '" + filemask + "' not found")

        includeFile = fileinput.input(files, mode="r", openhook=fileinput.hook_encoded(encoding))
        _included = included
        if ktext or kxml:
            text = ""
            for line in includeFile:
                included = includeFile.filename()
                if kxml:
                    if (not line[:6] == '<?xml ') and (not line[:6] == '<?XML '):
                        text += line
                else:
                    text += executeCmd(line)
            included = _included
            return code(text)
        else:
            result = parse(ymlCStyle(), includeFile, True, comment)
            included = u(filemask)
            x = _finish(result)
            included = _included
            return code(x)

    elif ctype == "pyExp":
        exp = obj[1][0]
        cmd = evalPython(exp)
        result, rest = parseLine(u(cmd), _inner, [], True, comment)
        if rest:
            raise SyntaxError(cmd)
        return code(_finish(result))

    elif ctype == "pythonCall":
        parms = []
        data = obj[1]
        for p in data:
            if type(p) is str:
                name = p
            elif type(p) is tuple or type(p) is Symbol:
                ptype = p[0]
                if ptype == "parm":
                    if p[1][0][0] == "*":
                        parms.append(pointer(p[1][0]))
                    else:
                        parms.append(p[1][0])
        if len(parms) == 0:
            exp = name + "()"
        elif len(parms) == 1:
            exp = name + "(" + u(parms[0]) + ")"
        else:
            exp = name + u(tuple(parms))
        cmd = evalPython(exp)
        result, rest = parseLine(u(cmd), _inner, [], True, comment)
        if rest:
            raise SyntaxError()
        return code(_finish(result))

    else:
        return code("")

def _finish(tree):
    result = ""
    python = ""

    for el in tree:
        if el[0] == "python":
            if el[1][0][:2] == "!!":
                python += el[1][0][2:-2]
            else:
                python += el[1][0][1:] + "\n"
            continue
        else:
            if python:
                execPython(python)
                python = ""

        try:
            result += codegen(el)
        except RuntimeError:
            if included:
                raise RuntimeError("in " + included + ":" + u(line))
            else:
                raise RuntimeError("in " + u(line))

    if python:
        execPython(python)

    return result

def finish(tree):
    global first
    first = True
    return _finish(tree)

ymlFunc["_parentheses"] = YF("parms")
ymlFunc["_parm"] = YF("parm")
ymlFunc["_generic"] = YF("generic")
ymlFunc["_base"] = YF("base")
