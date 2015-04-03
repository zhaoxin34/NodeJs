import os
import json
import re
import sublime
import sublime_plugin
from os import path
from collections import deque
import pprint
import html

NODEDIR = path.dirname(__file__) + "/nodelib"
NAME_ALIES_FILE = NODEDIR + "/name_alies.txt"
DEBUG = True
pp = pprint.PrettyPrinter(indent=4)


class Nodejs():
    def __init__(self):
        self.data = deque()
        self.nameAlies = None
        self.loaded = False
        self.__loadNameAlies()

    def parseNode(self):
        """
        load file from a folder
        parse to json
        replace alies names
        generate completions
        """
        files = os.listdir(NODEDIR)
        for f in files:
            if not f.endswith('.json'):
                continue
            with open(NODEDIR + "/" + f, encoding='UTF-8') as fi:
                j = json.load(fi)
                self.__dealDict(j)

        self.__dealAliesName(self.data)
        # modify trigger as trigger\t{parent}.{type}
        self.loaded = True
        if self.data:
            for dic in self.data:
                dic['trigger'] = "{0}\t{1}.{2}".format(dic['trigger'], dic['parent'], dic['type'])
        print("nodejs completions loaded")

    def __loadNameAlies(self):
        with open(NAME_ALIES_FILE) as fi:
            nameAlies = [line.split(',') for line in fi.readlines()]
            nameAlies = [(x.strip(), y.strip()) for x, y in nameAlies]
            self.nameAlies = nameAlies
            # print(self.nameAlies)

    def __dealDict(self, obj, parent=None):
        if (isinstance(obj, dict) and (
                'modules' in obj or 'classes' in obj or 'methods'in obj
                or 'properties' in obj or 'events' in obj)):
            for k, v in obj.items():
                if isinstance(v, dict):
                    self.__dealDict(v, obj)
                elif isinstance(v, list):
                    self.__dealList(v, obj, k)
                elif isinstance(v, str):
                    # print "%s.%s=%s" % (parent, k, v)
                    pass

        if 'type' in obj and 'name' in obj and 'textRaw' in obj:
            if obj['type'] == 'module':
                self.__dealModule(obj, parent)
            if obj['type'] == 'classe':
                self.__dealClass(obj, parent)
            if obj['type'] == 'method':
                self.__dealMethod(obj, parent)
            if obj['type'] == 'propertie':
                self.__dealProperties(obj, parent)
            if obj['type'] == 'event':
                self.__dealEvent(obj, parent)

    def __dealList(self, list, parent, type):
        for v in list:
            if isinstance(v, dict):
                self.__dealDict(v, parent)
            elif isinstance(v, list):
                self.__dealList(v, parent)
            elif isinstance(v, str):
                # print "%s=%s" % parent, v
                pass

    def __dealModule(self, md, parent):
        # print("var %s = require(\"%s\");" % (md['name'], md['name']))
        parentName = 'nodejs'
        if parent and 'name' in parent:
            parentName = parent['name']
        snippets = {
            "content": "var {0} = require('{1}');".format(md['name'], md['name']),
            "doc": md['desc'],
            "trigger": "require{0}".format(md['name']),
            "type": 'module',
            "parent": parentName
        }
        self.data.append(snippets)

    def __dealMethod(self, md, parent):
        m = md['textRaw']
        match = re.match(r'([a-zA-Z_0-9.]+)(.*)', m)
        if match and len(match.groups()) == 2:
            mname = match.group(1)
            pname = match.group(2)
            pnames = re.findall(r'([a-zA-Z_0-9.]+)', pname)
            pnames2 = ["${{{0}:{1}}}".format(i+1, v) for i, v in enumerate(pnames)]
            snippets = {
                "content": "{0}({1})".format(mname, ', '.join(pnames2)),
                "doc": md['desc'],
                "trigger": mname,
                "type": 'method',
                "parent": parent['name']
            }
            self.data.append(snippets)

    def __dealProperties(self, md, parent):
        snippets = {
            "content": "{0}.{1}".format(parent['name'], md['name']),
            "doc": md['desc'],
            "trigger": "{0}.{1}".format(parent['name'], md['name']),
            "type": 'properties',
            "parent": parent['name']
        }
        self.data.append(snippets)

    def __dealEvent(self, md, parent):
        eFunc = re.match('<p><code>(.*)</code>', md['desc'])
        eFunc = eFunc and eFunc.group(1) or 'function() {{}}'
        snippets = {
            "content": '{0}.on("{1}", {2});'.format(parent['name'], md['name'], eFunc),
            "doc": md['desc'],
            "trigger": '{0}.on{1}'.format(parent['name'], md['name']),
            "type": 'event',
            "parent": parent['name']
        }
        self.data.append(snippets)

    def __dealClass(self, md, parent):
        snippets = {
            "content": "{0}".format(md['name']),
            "doc": md['desc'],
            "trigger": "{0}".format(md['name']),
            "type": 'class',
            "parent": parent['name']
        }
        self.data.append(snippets)

    def __dealAliesName(self, snippets):
        for snippet in snippets:
            trigger = snippet['trigger']
            content = snippet['content']
            for x, y in self.nameAlies:
                trigger = trigger.replace(x, y)
                content = content.replace(x, y)
            snippet['trigger'] = trigger
            snippet['content'] = content
        
nodejs = Nodejs()
if DEBUG:
    print("=======" * 20)
    nodejs.parseNode()
    for snippets in nodejs.data:
        pp.pprint(snippets['trigger'])
        pp.pprint(snippets['content'])


class NodejsCompleteListener(sublime_plugin.EventListener):
    def __isNodeJsView(self, view):
        return 'nodejs' in view.scope_name(0)

    def on_post_save(self, view):
        pass

    def on_load(self, view):
        if self.__isNodeJsView(view) and not nodejs.loaded:
            nodejs.parseNode()

    def on_activated(self, view):
        if self.__isNodeJsView(view) and not nodejs.loaded:
            nodejs.parseNode()

    def on_query_completions(self, view, prefix, locations):
        """
        add completions to the editer
        """
        if self.__isNodeJsView(view):
            # view.show_popup(
            #   decodeHtmlentities(nodejs.data[0]['doc']),
            #   flags=sublime.COOPERATE_WITH_AUTO_COMPLETE)
            return [(snippets['trigger'], snippets['content']) for snippets in nodejs.data]


def decodeHtmlentities(string):
    entity_re = re.compile("&(#?)(\d{1,5}|\w{1,8});")

    def substitute_entity(match):
        from html.entities import name2codepoint as n2cp
        ent = match.group(2)
        if match.group(1) == "#":
            return chr(int(ent))
        else:
            cp = n2cp.get(ent)

            if cp:
                return chr(cp)
            else:
                return match.group()

    return entity_re.subn(substitute_entity, string)[0]
# match = re.match(r'([a-zA-Z_0-9.]+)(.*)', 'request.write(chunk[, encoding][, callback])')
# print(match.groups())
# pm = re.findall(r'([a-zA-Z_0-9.]+\]?)', match.group(2))
# print(pm)
