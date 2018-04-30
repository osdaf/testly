VERSION = '0.0.0alpha'
import icdifflib, logging
import unittest, types, traceback, pprint
from sys import stderr
from six import with_metaclass, StringIO
from tempfile import gettempdir
from os import remove, path
from builtins import str
from collections import namedtuple

difflib   = icdifflib
safe_repr = unittest.util.safe_repr
unittest.case.difflib = difflib

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

class _AssertLogsHelper(object):
	"""A context manager used to implement TestCase.assertLogs()."""

	LOGFMT = "%(levelname)s:%(name)s:%(message)s"

	def __init__(self, testcase, logname, level):
		self.testcase = testcase
		self.logname  = logname
		self.level    = getattr(logging, level) if level else logging.INFO
		self.msg      = None

	def __enter__(self):
		logger    = self.logger = self.logname if isinstance(self.logname, logging.Logger) else logging.getLogger(self.logname)
		formatter = logging.Formatter(self.LOGFMT)
		handler   = _assertLogsHandler()

		handler.setFormatter(formatter)
		self.watcher       = handler.watcher
		self.old_handlers  = logger.handlers[:]
		self.old_level     = logger.level
		self.old_propagate = logger.propagate
		logger.handlers    = [handler]
		logger.setLevel(self.level)
		logger.propagate   = False
		return handler.watcher

	def __exit__(self, exc_type, exc_value, tb):
		self.logger.handlers  = self.old_handlers
		self.logger.propagate = self.old_propagate
		self.logger.setLevel(self.old_level)
		if exc_type is not None:
			# let unexpected exceptions pass through
			return False
		if len(self.watcher.records) == 0:
			msg = self.testcase._formatMessage(self.msg, 'No logs of level {} or higher triggered on {}'.format(
				logging.getLevelName(self.level), self.logger.name
			))

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

	def assertSequenceEqual(self, seq1, seq2, msg=None, seq_type=None):
		"""An equality assertion for ordered sequences (like lists and tuples).

		For the purposes of this function, a valid ordered sequence type is one
		which can be indexed, has a length, and has an equality operator.

		Args:
			seq1: The first sequence to compare.
			seq2: The second sequence to compare.
			seq_type: The expected datatype of the sequences, or None if no
					datatype should be enforced.
			msg: Optional message to use on failure instead of a list of
					differences.
		"""
		if seq_type is not None:
			seq_type_name = seq_type.__name__
			if not isinstance(seq1, seq_type):
				raise self.failureException('First sequence is not a %s: %s'
										% (seq_type_name, safe_repr(seq1)))
			if not isinstance(seq2, seq_type):
				raise self.failureException('Second sequence is not a %s: %s'
										% (seq_type_name, safe_repr(seq2)))
		else:
			seq_type_name = "sequence"

		differing = None
		try:
			len1 = len(seq1)
		except (TypeError, NotImplementedError):
			differing = 'First %s has no length.    Non-sequence?' % (
					seq_type_name)

		if differing is None:
			try:
				len2 = len(seq2)
			except (TypeError, NotImplementedError):
				differing = 'Second %s has no length.    Non-sequence?' % (
						seq_type_name)

		if differing is None:
			if seq1 == seq2:
				return

			seq1_repr = safe_repr(seq1)
			seq2_repr = safe_repr(seq2)
			if len(seq1_repr) > 30:
				seq1_repr = seq1_repr[:30] + '...'
			if len(seq2_repr) > 30:
				seq2_repr = seq2_repr[:30] + '...'
			elements = (seq_type_name.capitalize(), seq1_repr, seq2_repr)
			differing = '%ss differ: %s != %s\n' % elements

		standardMsg = differing
		diffMsg = '\n' + str('\n'.join([line.decode() for line in \
			difflib.ndiff(pprint.pformat(seq1).splitlines(),
						  pprint.pformat(seq2).splitlines())]))
		standardMsg = self._truncateMessage(standardMsg, diffMsg)
		msg = self._formatMessage(msg, standardMsg)
		self.fail(msg)

	def assertLogs(self, logger=None, level=None):
		return _AssertLogsHelper(self, logger, level)

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
