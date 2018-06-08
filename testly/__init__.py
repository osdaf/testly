VERSION = '0.0.0alpha'
import logging, sys, re
import unittest, types, traceback, pprint
from sys import stderr
from six import with_metaclass, StringIO
from tempfile import gettempdir
from os import remove, path
from builtins import str
from collections import namedtuple
from contextlib import contextmanager

def _createTestMethod(func, *args, **kwargs):
	return lambda self: func(self, *args, **kwargs)

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

class Data(object):
	def __init__(self, *args, **kwargs):
		self.args   = args
		self.kwargs = kwargs

	def __call__(self):
		return self.args, self.kwargs

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

class _assertLogsHandler(logging.Handler):

	LOGFMT = "%(levelname)s:%(name)s:%(message)s"

	def __init__(self):
		LoggingWatcher = namedtuple("_LoggingWatcher", ["records", "output"])
		logging.Handler.__init__(self)
		self.watcher = LoggingWatcher([], [])

	def flush(self):
		pass

	def emit(self, record):
		self.watcher.records.append(record)
		msg = self.format(record)
		self.watcher.output.append(msg)

class MetaTestCase(type):

	def __new__(meta, classname, bases, classDict):

		classDict = Box(classDict)

		testMethods	= {}
		if 'setUpMeta' in classDict:
			classDict['setUpMeta'](classDict)
			del classDict['setUpMeta']

		for key in list(classDict.keys()):
			val = classDict[key]
			if key.startswith('dataProvider_'):
				del classDict[key]
				testname = key[13:]
				testMethods[testname] = TestSet(testname)
				if testname in classDict:
					for i, data in enumerate(val(Box(classDict))):
						testMethod = '%s-%s' % (testname, i)
						testMethods[testname].addTest(testMethod)
						if isinstance(data, Data):
							args, kwargs = data()
						elif isinstance(data, (tuple, list)):
							args, kwargs = Data(*data)()
						elif isinstance(data, dict):
							args, kwargs = Data(**data)()
						else:
							raise ValueError('Expect data type tuple/list/dict/testly.Data, but got %s' % type(data))
						classDict[testMethod] = _createTestMethod(classDict[testname], *args, **kwargs)
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

	@contextmanager
	def assertLogs(self, logger=None, level=None):
		if not isinstance(logger, logging.Logger):
			logger = logging.getLogger(logger)
		level = getattr(logging, level) if level else logging.INFO
		try:
			formatter = logging.Formatter(_assertLogsHandler.LOGFMT)
			handler   = _assertLogsHandler()
			handler.setFormatter(formatter)
			old_handlers  = logger.handlers[:]
			old_level     = logger.level
			old_propagate = logger.propagate
			logger.handlers    = [handler]
			logger.setLevel(level)
			logger.propagate   = False
			yield handler.watcher
		finally:
			logger.handlers  = old_handlers
			logger.propagate = old_propagate
			logger.setLevel(old_level)

	@contextmanager
	def assertStdOE(self):
		new_out, new_err = StringIO(), StringIO()
		old_out, old_err = sys.stdout, sys.stderr
		try:
			sys.stdout, sys.stderr = new_out, new_err
			yield sys.stdout, sys.stderr
		finally:
			sys.stdout, sys.stderr = old_out, old_err

	def assertDictContains(self, first, second, msg = None):
		isin  = True
		first = first or {}
		if not isinstance(first, dict):
			self.fail(self._formatMessage(msg, 'The first argument is not a dict.'))
		if not isinstance(second, dict):
			self.fail(self._formatMessage(msg, 'The second argument is not a dict.'))

		dict1_repr = repr(first)
		if len(dict1_repr) > 30:
			dict1_repr = dict1_repr[:30] + '...'
		dict2_repr = repr(second)
		if len(dict2_repr) > 30:
			dict2_repr = dict2_repr[:30] + '...'

		for key in first.keys():
			if key not in second:
				self.fail(self._formatMessage(msg, 'Key %s from %s is not in %s' % (key, dict1_repr, dict2_repr)))
			if first[key] != second[key]:
				self.fail(self._formatMessage(msg, '%s and %s have different values on key %s' % (dict1_repr, dict2_repr, key)))
	
	def assertDictNotContains(self, first, second, msg = None):
		isin  = True
		first = first or {}
		if not isinstance(first, dict) or not isinstance(second, dict):
			isin = False
		elif not all([key in second.keys() for key in first.keys()]):
			isin = False
		elif not all([first[key] == second[key] for key in first.keys()]):
			isin = False
		if isin:
			dict1_repr = repr(first)
			dict2_repr = repr(second)
			if len(dict2_repr) > 30:
				dict2_repr = dict2_repr[:30] + '...'
			standardMsg = '%s is in %s\n' % (dict1_repr, dict2_repr)
			msg = self._formatMessage(msg, standardMsg)
			self.fail(msg)

	def assertSeqContains(self, first, second, msg = None):
		first = first or []
		if not all([f in second for f in first]):
			seq1_repr = repr(first)
			seq2_repr = repr(second)
			if len(seq2_repr) > 30:
				seq2_repr = seq2_repr[:30] + ' ...'
			standardMsg = '%s does not contain %s' % (seq2_repr, seq1_repr)
			msg = self._formatMessage(msg, standardMsg)
			self.fail(msg)
	
	def assertSeqNotContains(self, first, second, msg = None):
		first = first or []
		if all([f in second for f in first]):
			seq1_repr = repr(first)
			seq2_repr = repr(second)
			if len(seq2_repr) > 30:
				seq2_repr = seq2_repr[:30] + '...'
			standardMsg = '%s contains %s' % (seq2_repr, seq1_repr)
			msg = self._formatMessage(msg, standardMsg)
			self.fail(msg)

	def assertInAny(self, s, sequence, msg = None):
		if not any([s in seq for seq in sequence]):
			seq1_repr = repr(s)
			seq2_repr = repr(sequence)
			if len(seq2_repr) > 30:
				seq2_repr = seq2_repr[:30] + '...'
			standardMsg = '%s is not in any elements of %s\n' % (seq1_repr, seq2_repr)
			msg = self._formatMessage(msg, standardMsg)
			self.fail(msg)

	def assertNotInAny(self, s, sequence, msg = None):
		if not all([s not in seq for seq in sequence]):
			seq1_repr = repr(s)
			seq2_repr = repr(sequence)
			if len(seq2_repr) > 30:
				seq2_repr = seq2_repr[:30] + '...'
			standardMsg = '%s is in at least one element of %s\n' % (seq1_repr, seq2_repr)
			msg = self._formatMessage(msg, standardMsg)
			self.fail(msg)

	def assertRegexAny(self, s, sequence, msg = None):
		if not any([re.search(s, seq) for seq in sequence]):
			seq1_repr = repr(s)
			seq2_repr = repr(sequence)
			if len(seq2_repr) > 30:
				seq2_repr = seq2_repr[:30] + '...'
			standardMsg = '%s does not match any elements of %s\n' % (seq1_repr, seq2_repr)
			msg = self._formatMessage(msg, standardMsg)
			self.fail(msg)

	def assertNotRegexAny(self, s, sequence, msg = None):
		if not all([not re.search(s, seq) for seq in sequence]):
			seq1_repr = repr(s)
			seq2_repr = repr(sequence)
			if len(seq2_repr) > 30:
				seq2_repr = seq2_repr[:30] + '...'
			standardMsg = '%s matches at least one elements of %s\n' % (seq1_repr, seq2_repr)
			msg = self._formatMessage(msg, standardMsg)
			self.fail(msg)

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
					error_case, error_message = unittest.loader._make_failed_import_test(
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
					error_case, error_message = unittest.loader._make_failed_test(
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
