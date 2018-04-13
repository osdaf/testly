import unittest
from sys import stderr
from six import with_metaclass

def _createTestMethod(func, *args):
	return lambda self: func(self, *args)
	
def _isFirstOf(testMethods):
	def isFirstOf(self, name):
		if name not in testMethods: 
			return False
		if self._testMethodName not in testMethods[name]:
			return False
		return testMethods[name].index(self._testMethodName) == 0
	return isFirstOf
	
def _isLastOf(testMethods):
	def isLastOf(self, name):
		if name not in testMethods: 
			return False
		if self._testMethodName not in testMethods[name]:
			return False
		return testMethods[name].index(self._testMethodName) == len(testMethods[name]) - 1
	return isLastOf
	
class Box(dict):
	"""
	Allow dot operation for dict
	"""
	def __repr__(self):
		return '<Box: {%s}>' % ', '.join(['%s=%s' % (k,v) for k,v in self.items()])

	def __getattr__(self, name):
		super(Box, self).__getattr__(name)
		
	def __setattr__(self, name, val):
		super(Box, self).__setattr__(name, val)

class MetaTestCase(type):

	def __new__(meta, classname, bases, classDict):
		
		testMethods    = {}
		for key, val in classDict.items():
			if key.startswith('dataProvider_'):
				del classDict[key]
				testname = key[13:]
				testMethods[testname] = []
				if testname in classDict:
					for i, data in enumerate(val(Box(classDict))):
						testMethod = '%s_%s' % (testname, i)
						testMethods[testname].append(testMethod)
						classDict[testMethod] = _createTestMethod(classDict[testname], *data)
					del classDict[testname]
				else:
					stderr.write('WARNING: Data provider [%s] ignored: no corresponding test method [%s] found.' % (key, testname))
			elif ('dataProvider_%s' % key) not in classDict:
				testMethods[key] = [key]
	
		classDict['isFirstOf'] = _isFirstOf(testMethods)
		classDict['isLastOf']  = _isLastOf(testMethods)
		return type.__new__(meta, classname, bases, classDict)
