import os
import json
import re
import sublime_plugin
from os import path

NODEDIR = path.dirname(__file__) + "/nodelib"


class Nodejs():
	def __init__(self):
		self.data = []
		self.loaded = False

	def parseNode(self):
		"""
		parse every json as dict
		"""
		files = os.listdir(NODEDIR)
		for f in files:
			with open(NODEDIR + "/" + f, 'r') as fi:
				j = json.load(fi)
				self.dealDict(j, [])
		self.loaded = True
		print("nodejs completions loaded")

	def dealDict(self, obj, parent):
		if 'type' in obj and 'name' in obj and 'textRaw' in obj:
			if obj['type'] == 'modules':
				self.__dealModule(obj, parent)
			if obj['type'] == 'methods':
				self.__dealMethod(obj, parent)
			if obj['type'] == 'properties':
				self.__dealProperteis(obj, parent)
			if obj['type'] == 'events':
				self.__dealEvent(obj, parent)
			parent.append({'name': obj['name'], 'type': obj['type'], 'textRaw': obj['textRaw']})

		for k, v in obj.items():
			if isinstance(v, dict):
				self.dealDict(v, parent)
			elif isinstance(v, list):
				self.__dealList(v, parent, k)
			elif isinstance(v, str):
				# print "%s.%s=%s" % (parent, k, v)
				pass

		if 'type' in obj and 'name' in obj and 'textRaw' in obj:
			parent.pop()

	def __dealList(self, list, parent, type):
		for v in list:
			v['type'] = type
			if isinstance(v, dict):
				self.dealDict(v, parent)
			elif isinstance(v, list):
				self.__dealList(v, parent)
			elif isinstance(v, str):
				# print "%s=%s" % parent, v
				pass

	def __dealModule(self, md, parent):
		# print("var %s = require(\"%s\");" % (md['name'], md['name']))
		snippets = {
			"content": "var {0} = requre('{1}');".format(md['name'], md['name']),
			"doc": md['desc'],
			"trigger": "requre{0}".format(md['name'])
		}
		self.data.append(snippets)

	def __dealMethod(self, md, parent):
		m = md['textRaw']
		match = re.match(r'([a-zA-Z_0-9.]+)(.*)', m)
		if match and len(match.groups()) == 2:
			mname = match.group(1)
			pname = match.group(2)
			pnames = re.findall(r'([a-zA-Z_0-9.]+)', pname)
			snippets = {
				"content": "{0}({1}) {{\n\t${{1:content}}\n}}".format(mname, ', '.join(pnames)),
				"doc": md['desc'],
				"trigger": mname
			}
			self.data.append(snippets)

	def __dealProperteis(self, md, parent):
		snippets = {
			"content": "{0}.{1}".format(parent[-1]['name'], md['name']),
			"doc": md['desc'],
			"trigger": "{0}.{1}".format(parent[-1]['name'], md['name'])
		}
		self.data.append(snippets)

	def __dealEvent(self, md, parent):
		eFunc = re.match('<p><code>(.*)</code>', md['desc'])
		eFunc = eFunc and eFunc.group(1) or 'function() {{}}'
		snippets = {
			"content": '{0}.on("{1}", {2});'.format(parent[-1]['name'], md['name'], eFunc),
			"doc": md['desc'],
			"trigger": '{0}.on{1}'.format(parent[-1]['name'], md['name'])
		}
		self.data.append(snippets)

nodejs = Nodejs()


class NodejsCompleteListener(sublime_plugin.EventListener):
	def __isNodeJsView(self, view):
		return view.settings().get('syntax')

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
			return [(snippets['trigger'], snippets['content']) for snippets in nodejs.data]

# match = re.match(r'([a-zA-Z_0-9.]+)(.*)', 'request.write(chunk[, encoding][, callback])')
# print(match.groups())
# pm = re.findall(r'([a-zA-Z_0-9.]+\]?)', match.group(2))
# print(pm)

