import sys, logging
from testly import Data, Box, TestSet, TestCase, main
from collections import OrderedDict

class TestOther(TestCase):

	def dataProvider_testData(self):
		yield (), {}
		yield (1,2,3), dict(a=1,b=2,c=3)

	def testData(self, args, kwargs):
		self.assertEqual(self.setName(), 'testData')
		self.assertEqual(self.isOfSet(), True)
		args2, kwargs2 = Data(*args, **kwargs)()
		self.assertTupleEqual(args2, args)
		self.assertDictEqual(kwargs2, kwargs)

	def dataProvider_testBox(self):
		box = Box()
		yield box, {}, '<Box: {}>'

		box1 = Box()
		box1.a = Box()
		yield box1, dict(a = {}), '<Box: {a=<Box: {}>}>'
		box2 = Box()
		box2.a = Box()
		box2.a.b = 1
		yield box2, dict(a = dict(b = 1)), '<Box: {a=<Box: {b=1}>}>'
		
		box4 = Box()
		box4.__a = 1
		yield box4, dict(_TestOther__a = 1), '<Box: {_TestOther__a=1}>'

	def testBox(self, box, out, rep):
		self.assertDictEqual(box, out)
		self.assertEqual(repr(box), rep)

	def testTestSet(self):
		self.assertEqual(self.isOfSet(), False)
		# init
		ts = TestSet('testset')
		self.assertEqual(ts.name, 'testset')
		self.assertEqual(ts.tests, [])

		# is first/last
		self.assertFalse(ts.isFirst('test1'))
		self.assertFalse(ts.isLast('test1'))

		# add test
		ts.addTest('test1')
		ts.addTest('test2')
		self.assertListEqual(ts.tests, ['test1', 'test2'])

		# is first
		self.assertFalse(ts.isFirst('test3'))
		self.assertFalse(ts.isFirst('test2'))
		self.assertTrue(ts.isFirst('test1'))

		# is last
		self.assertFalse(ts.isLast('test3'))
		self.assertFalse(ts.isLast('test1'))
		self.assertTrue(ts.isLast('test2'))

class TestTestCase(TestCase):

	def setUpMeta(self):
		self.meta = True

	def dataProvider_testLogs(self):
		yield [
			('info', 'Hello'),
			('debug', 'world!'),
		], 'INFO', [
			'INFO:root:Hello'
		]

		yield [
			('info', 'Hello'),
			('error', 'world!'),
			('debug', 'hey!'),
		], 'ERROR', [
			'ERROR:root:world!'
		]

	def testLogs(self, logs, level, outs):
		self.assertTrue(self.meta)
		with self.assertLogs(level = level) as logouts:
			for key, val in logs:
				getattr(logging, key)(val)
		self.assertCountEqual(logouts.output, outs)

	def dataProvider_testStdOE(self):
		yield '', ''
		yield 'a;lwjf', ''
		yield '', 'oerwg'
		yield 'oawjfwa\nawlf', 'awif\n8awf'

	def testStdOE(self, stdout, stderr):
		with self.assertStdOE() as (out, err):
			with self.assertStdOE() as (out2, err2):
				sys.stdout.write(stdout)
				sys.stderr.write(stderr)
			sys.stdout.write(out2.getvalue())
			sys.stderr.write(err2.getvalue())
		self.assertEqual(out.getvalue(), stdout)
		self.assertEqual(err.getvalue(), stderr)

	def dataProvider_testMethods(self):
		yield 'assertMultiLineEqual', '\n'.join(['oooooooone', 'two', 'aaa', 'tree', '1', '1', '1', '1', '1', '1', 'fourfourfourfourfourfourfourfourfour very very very very very very very very very very very very very very very very very very very very very very very very very very long line']), '\n'.join(['oooooooore', 'emu', 'three', '1', '1', '1', '1', '1', '1', 'aaa', 'fivefivefivefivefivefivefivefivefive']), [
			"'oooooooone\\ntwo\\naaa\\ntree\\n1\\n1\\n1\\n1\\n1\\n1\\nfourfourfourfourfourfourfourfourf [truncated]... != 'oooooooore\\nemu\\nthree\\n1\\n1\\n1\\n1\\n1\\n1\\naaa\\nfivefivefivefivefivefivefivefive [truncated]...",
			## colored diff
			'\x1b[90m 1. \x1b[0moooooooo\x1b[33mn\x1b[0me                                                                                                                       \x1b[90m | \x1b[0m\x1b[90m 1. \x1b[0moooooooo\x1b[33mr\x1b[0me                                                                                                                       ', 
			'\x1b[90m 2. \x1b[0m\x1b[31mtwo\x1b[0m                                                                                                                              \x1b[90m | \x1b[0m\x1b[90m 2. \x1b[0m\x1b[32memu\x1b[0m                                                                                                                              ', 
			'\x1b[90m 3. \x1b[0m\x1b[31maaa\x1b[0m                                                                                                                              \x1b[90m | \x1b[0m\x1b[90m    \x1b[0m                                                                                                                                 ', 
			'\x1b[90m 4. \x1b[0mtree                                                                                                                             \x1b[90m | \x1b[0m\x1b[90m 3. \x1b[0mt\x1b[32mh\x1b[0mree                                                                                                                            ', 
			'\x1b[90m 5. \x1b[0m1                                                                                                                                \x1b[90m | \x1b[0m\x1b[90m 4. \x1b[0m1                                                                                                                                ', 
			'\x1b[90m    \x1b[0m\x1b[90m---------------------------------------------------------------------------------------------------------------------------------\x1b[0m\x1b[90m | \x1b[0m\x1b[90m    \x1b[0m\x1b[90m---------------------------------------------------------------------------------------------------------------------------------\x1b[0m', 
			'\x1b[90m10. \x1b[0m1                                                                                                                                \x1b[90m | \x1b[0m\x1b[90m 9. \x1b[0m1                                                                                                                                ', 
			'\x1b[90m11. \x1b[0m\x1b[31mfourfourfourfourfourfourfourfourfour very very very very very very very very very very very very very very very very very very ve\x1b[0m\x1b[90m | \x1b[0m\x1b[90m10. \x1b[0m\x1b[32maaa\x1b[0m                                                                                                                              ', 
			'\x1b[90m    \x1b[0m\x1b[31mry very very very very very very very long line\x1b[0m                                                                                  \x1b[90m | \x1b[0m\x1b[90m    \x1b[0m                                                                                                                                 ', 
			'\x1b[90m    \x1b[0m                                                                                                                                 \x1b[90m | \x1b[0m\x1b[90m11. \x1b[0m\x1b[32mfivefivefivefivefivefivefivefivefive\x1b[0m                                                                                             '
		]

		# 1. OrderedDict is just to make sure the output is in order
		yield 'assertDictEqual', OrderedDict([('a', 1), ('b', 2)]), OrderedDict([('a',1), ('b',3), ('c', 8)]), [
			"OrderedDict([('a', 1), ('b', 2)]) != OrderedDict([('a', 1), ('b', 3), ('c', 8)])", 
			"\x1b[90m1. \x1b[0m('a', 1)                                \x1b[90m | \x1b[0m\x1b[90m1. \x1b[0m('a', 1)                                ", 
			"\x1b[90m2. \x1b[0m('b', \x1b[33m2\x1b[0m)                                \x1b[90m | \x1b[0m\x1b[90m2. \x1b[0m('b', \x1b[33m3\x1b[0m)                                ", 
			"\x1b[90m   \x1b[0m                                        \x1b[90m | \x1b[0m\x1b[90m3. \x1b[0m\x1b[32m('c', 8)\x1b[0m                                "
		]

		yield 'assertDictEqual', OrderedDict([('a', 1), ('b', 2)]), OrderedDict([('a',1), ('b',3), ('c', 8)]), [
			"Dict not equal"
		], 'Dict not equal', 'contrast'

		yield 'assertDictEqual', OrderedDict([('a', 1), ('b', 2)]), OrderedDict([('a',1), ('b',3), ('c', 8)]), [
			"OrderedDict([('a', 1), ('b', 2)]) != OrderedDict([('a', 1), ('b', 3), ('c', 8)])", 
			"\x1b[90m1. \x1b[0m('a', 1)                                \x1b[90m | \x1b[0m\x1b[90m1. \x1b[0m('a', 1)                                ", 
			"\x1b[90m2. \x1b[0m('b', \x1b[43m2\x1b[0m)                                \x1b[90m | \x1b[0m\x1b[90m2. \x1b[0m('b', \x1b[43m3\x1b[0m)                                ", 
			"\x1b[90m   \x1b[0m                                        \x1b[90m | \x1b[0m\x1b[90m3. \x1b[0m\x1b[42m('c', 8)\x1b[0m                                "
		], None, 'contrast'

		# 4
		yield 'assertSequenceEqual', ['oooooooone', 'two', 'aaa', 'tree', '1', '1', '1', '1', '1', '1', 'fourfourfourfourfourfourfourfourfour very very very very very very very very very very very very very very very very very very very very very very very very very very long line'], ['oooooooore', 'emu', 'three', '1', '1', '1', '1', '1', '1', 'aaa', 'fivefivefivefivefivefivefivefivefive'], ["Sequences differ: ['oooooooone', 'two', 'aaa', '... != ['oooooooore', 'emu', 'three',...", 
		'First differing element 0:', 'oooooooone', 'oooooooore', 
		'\x1b[90m 1. \x1b[0moooooooo\x1b[33mn\x1b[0me                                                                                                                       \x1b[90m | \x1b[0m\x1b[90m 1. \x1b[0moooooooo\x1b[33mr\x1b[0me                                                                                                                       ', 
		'\x1b[90m 2. \x1b[0m\x1b[31mtwo\x1b[0m                                                                                                                              \x1b[90m | \x1b[0m\x1b[90m 2. \x1b[0m\x1b[32memu\x1b[0m                                                                                                                              ', 
		'\x1b[90m 3. \x1b[0m\x1b[31maaa\x1b[0m                                                                                                                              \x1b[90m | \x1b[0m\x1b[90m    \x1b[0m                                                                                                                                 ', 
		'\x1b[90m 4. \x1b[0mtree                                                                                                                             \x1b[90m | \x1b[0m\x1b[90m 3. \x1b[0mt\x1b[32mh\x1b[0mree                                                                                                                            ', 
		'\x1b[90m 5. \x1b[0m1                                                                                                                                \x1b[90m | \x1b[0m\x1b[90m 4. \x1b[0m1                                                                                                                                ', 
		'\x1b[90m    \x1b[0m\x1b[90m---------------------------------------------------------------------------------------------------------------------------------\x1b[0m\x1b[90m | \x1b[0m\x1b[90m    \x1b[0m\x1b[90m---------------------------------------------------------------------------------------------------------------------------------\x1b[0m', 
		'\x1b[90m10. \x1b[0m1                                                                                                                                \x1b[90m | \x1b[0m\x1b[90m 9. \x1b[0m1                                                                                                                                ', 
		'\x1b[90m11. \x1b[0m\x1b[31mfourfourfourfourfourfourfourfourfour very very very very very very very very very very very very very very very very very very ve\x1b[0m\x1b[90m | \x1b[0m\x1b[90m10. \x1b[0m\x1b[32maaa\x1b[0m                                                                                                                              ', 
		'\x1b[90m    \x1b[0m\x1b[31mry very very very very very very very long line\x1b[0m                                                                                  \x1b[90m | \x1b[0m\x1b[90m    \x1b[0m                                                                                                                                 ', 
		'\x1b[90m    \x1b[0m                                                                                                                                 \x1b[90m | \x1b[0m\x1b[90m11. \x1b[0m\x1b[32mfivefivefivefivefivefivefivefivefive\x1b[0m                                                                                             ']

		# 5
		yield 'assertDictContains', 1, {}, ['The first argument is not a dict.']
		yield 'assertDictContains', {}, 1, ['The second argument is not a dict.']
		yield 'assertDictContains', {'a': 1}, {}, ['Key a from {\'a\': 1} is not in {}']
		yield 'assertDictContains', {'a': 1}, {'a': 2}, ['{\'a\': 1} and {\'a\': 2} have different values on key a']

		# 9
		yield 'assertDictNotContains', {}, {}, ['{} is in {}']
		yield 'assertDictNotContains', {'a':1}, {'b':2}, ["{'a': 1} is in {'b': 2}"]

		yield 'assertSeqContains', [1], [], ['[] does not contain [1]']
		yield 'assertSeqNotContains', [], [1], ['[1] contains []']

		# 13
		yield 'assertInAny', 'abc', ['d','e'], ["'abc' is not in any elements of ['d', 'e']"]
		yield 'assertNotInAny', 'ef', ['def','ghi'], ["'ef' is in at least one element of ['def', 'ghi']"]

		yield 'assertRegexAny', r'^$', ['a', 'b'], ["'^$' does not match any elements of ['a', 'b']"]
		yield 'assertNotRegexAny', r'^a$', ['a', 'b'], ["'^a$' matches at least one element of ['a', 'b']"]

		# 17
		yield 'assertCountEqual', [1,2,2], [2,1], ['Element counts were not equal:', 'First has 2, Second has 1:  2']
		yield 'assertRaisesRegex', ZeroDivisionError, r'aaa', ['"aaa" does not match "', 'by zero'], lambda: 1/0
		yield 'assertRegex', 'string', r'regex', ["Regex", " didn't match: "]

	def testMethods(self, method, first, second, stderrs, msg = None, diffTheme = 'default'):
		self.diffTheme = diffTheme
		self.maxDiff   = None
		with self.assertStdOE() as (out, err):
			try:
				getattr(self, method)(first, second, msg)
			except AssertionError as ex:
				sys.stderr.write(str(ex))
		for se in stderrs:
			self.assertInAny(se, err.getvalue().splitlines())


if __name__ == '__main__':
	main(verbosity = 2)
