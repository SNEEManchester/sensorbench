class Node:

	def appendChild(self, child):
		self.children.append(child)

	def getChildren(self):
		return self.children

	def getid(self):
		return self.nodeid

	def __init__(self, i):
		self.nodeid= i
		self.children = []
