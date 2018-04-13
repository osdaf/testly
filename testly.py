import unittest, types
from sys import stderr
from six import with_metaclass

def _createTestMethod(func, *args):
	return lambda self: func(self, *args)
	
def _isFirst(testMethods):
	def isFirst(self):
		name = self.setName()
		if name not in testMethods: 
			return False
		return testMethods[name].isFirst(self._testMethodName)
	return isFirst
	
def _isLast(testMethods):
	def isLast(self):
		name = self.setName()
		if name not in testMethods: 
			return False
		return testMethods[name].isLast(self._testMethodName)
	return isLast
	
def _setName(testMethods):
	def setName(self):
		for testset in testMethods.values():
			if self._testMethodName in testset.tests:
				return testset.name
		return self._testMethodName
	return setName
	
class Box(dict):
	"""
	Allow dot operation for dict
	"""
	def __repr__(self):
		return '<Box: {%s}>' % ', '.join(['%s=%s' % (k,v) for k,v in self.items()])

	def __getattr__(self, name):
		if not name.startswith('__'):
			return self[name]
		else:
			super(Box, self).__getattr__(name)
		
	def __setattr__(self, name, val):
		if not name.startswith('__'):
			self[name] = val
		else:
			super(Box, self).__setattr__(name, val)
		
class TestSet(object):
	def __init__(self, name):
		self.name  = name
		self.tests = []
		
	def addTest(self, testname):
		self.tests.append(testname)
		
	def isFirst(self, testname):
		if not self.tests:
			return False
		return self.tests[0] == testname
		
	def isLast(self, testname):
		if not self.tests:
			return False
		return self.tests[-1] == testname		

class MetaTestCase(type):

	def __new__(meta, classname, bases, classDict):
		
		testMethods	= {}
		for key in list(classDict.keys()):
			val = classDict[key]
			if key.startswith('dataProvider_'):
				del classDict[key]
				testname = key[13:]
				testMethods[testname] = TestSet(testname)
				if testname in classDict:
					for i, data in enumerate(val(Box(classDict))):
						testMethod = '%s__%s' % (testname, i)
						testMethods[testname].addTest(testMethod)
						classDict[testMethod] = _createTestMethod(classDict[testname], *data)
					del classDict[testname]
					classDict[testname] = testMethods[testname]
				else:
					stderr.write('WARNING: Data provider [%s] ignored: no corresponding test method [%s] found.' % (key, testname))
	
		classDict['isFirst'] = _isFirst(testMethods)
		classDict['isLast']  = _isLast(testMethods)
		classDict['setName'] = _setName(testMethods)
		classDict['isOfSet'] = lambda self: self._testMethodName != self.setName()
		return type.__new__(meta, classname, bases, classDict)

class TestCase(with_metaclass(MetaTestCase, unittest.TestCase)):
	
	assertCountEqual  = unittest.TestCase.assertCountEqual  if hasattr(unittest.TestCase, 'assertCountEqual')  else unittest.TestCase.assertItemsEqual 
	assertRaisesRegex = unittest.TestCase.assertRaisesRegex if hasattr(unittest.TestCase, 'assertRaisesRegex') else unittest.TestCase.assertRaisesRegexp 
	assertRegex       = unittest.TestCase.assertRegex       if hasattr(unittest.TestCase, 'assertRegex') else unittest.TestCase.assertRegexpMatches 
		

class TestLoader(unittest.TestLoader):

	def loadTestsFromName(self, name, module=None):
		"""Return a suite of all test cases given a string specifier.
		The name may resolve either to a module, a test case class, a
		test method within a test case class, or a callable object which
		returns a TestCase or TestSuite instance.
		The method optionally resolves the names relative to a given module.
		"""
		parts = name.split('.')
		
		error_case, error_message = None, None
		if module is None:
			parts_copy = parts[:]
			while parts_copy:
				try:
					module_name = '.'.join(parts_copy)
					module = __import__(module_name)
					break
				except ImportError:
					next_attribute = parts_copy.pop()
					# Last error so we can give it to the user if needed.
					error_case, error_message = _make_failed_import_test(
						next_attribute, self.suiteClass)
					if not parts_copy:
						# Even the top level import failed: report that error.
						self.errors.append(error_message)
						return error_case
			parts = parts[1:]
		obj = module
		
		for part in parts:
			try:
				parent, obj = obj, getattr(obj, part)
			except AttributeError as e:
				# We can't traverse some part of the name.
				if (getattr(obj, '__path__', None) is not None
					and error_case is not None):
					# This is a package (no __path__ per importlib docs), and we
					# encountered an error importing something. We cannot tell
					# the difference between package.WrongNameTestClass and
					# package.wrong_module_name so we just report the
					# ImportError - it is more informative.
					self.errors.append(error_message)
					return error_case
				else:
					# Otherwise, we signal that an AttributeError has occurred.
					error_case, error_message = _make_failed_test(
						part, e, self.suiteClass,
						'Failed to access attribute:\n%s' % (
							traceback.format_exc(),))
					self.errors.append(error_message)
					return error_case
		
		if isinstance(obj, types.ModuleType):
			return self.loadTestsFromModule(obj)
		elif isinstance(obj, type) and issubclass(obj, unittest.case.TestCase):
			return self.loadTestsFromTestCase(obj)
		elif (isinstance(obj, (types.FunctionType, types.MethodType)) and
			  isinstance(parent, type) and
			  issubclass(parent, unittest.case.TestCase)):
			
			name    = parts[-1]
			inst    = parent(name)
			if inst.isOfSet():
				getattr(inst, inst.setName()).tests = [name]
			# static methods follow a different path
			if not isinstance(getattr(inst, name), types.FunctionType):
				return self.suiteClass([inst])
		elif isinstance(obj, unittest.suite.TestSuite):
			return obj
		elif isinstance(obj, TestSet): # implies issubclass(parent, TestCase)
			return self.suiteClass([parent(name) for name in obj.tests])			
			
		if callable(obj):
			test = obj()
			if isinstance(test, unittest.suite.TestSuite):
				return test
			elif isinstance(test, case.TestCase):
				return self.suiteClass([test])
			else:
				raise TypeError("calling %s returned %s, not a test" %
								(obj, test))
		else:
			raise TypeError("don't know how to make test from: %s" % obj)
	
class TestProgram(unittest.TestProgram):

	def __init__(self, 
		module      = '__main__', 
		defaultTest = None, 
		argv        = None,
		testRunner  = None, 
		testLoader  = TestLoader(),
		exit        = True, 
		verbosity   = 1, 
		failfast    = None, 
		catchbreak  = None,
		buffer      = None):
		super(TestProgram, self).__init__(
			module      = module,
			defaultTest = defaultTest,
			argv        = argv,
			testRunner  = testRunner,
			testLoader  = testLoader,
			exit        = exit,
			verbosity   = verbosity,
			failfast    = failfast,
			catchbreak  = catchbreak,
			buffer      = buffer
		)
	
main = TestProgram
	
	
