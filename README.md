# testly
Enhanced unittest with data provider and more for python

- Data provider
- Command line argument to run a test set (by the same data provider)
- 100% compatible with `unittest`
- Python2, 3 compatible

## Install
```bash
pip install git+git://github.com/pwwang/testly.git
```

## Example
```python
import sys, testly

class TestTest(testly.TestCase):

	def setUp(self):
		# setUp for test set
		if self.isFirst():
			sys.stderr.write('TestSet %s starts ... ' % self.setName())
		# setUp for regular tests
		elif not self.isOfSet():
			# regulator setUp for other tests
			sys.stderr.write('Test %s starts ...' % self._testMethodName)

	def tearDown(self):
		# tearDown for test set
		if self.isLast():
			sys.stderr.write('TestSet %s ends ... ' % self.setName())
		# tearDown for regular tests
		elif not self.isOfSet():
			# regulator setUp for other tests
			sys.stderr.write('Test %s ends ... ' % self._testMethodName)

	def dataProvider_test1(self):
		yield 1, 1
		yield 2, 2
		yield 3, 3
		yield 4, 4

	def test1(self, in_, out):
		self.assertEqual(in_, out)

	def dataProvider_test2(self):
		yield 1, 1
		yield dict(in_ = 2, out = 2)
		yield 3, 3
		yield testly.Data(4, out = 4)

	def test2(self, in_, out):
		self.assertEqual(in_, out)

	# compatible with original tests
	def test3(self):
		# python2, python3 compatible assertions
		self.assertCountEqual([1,2], [2,1])
		self.assertRaisesRegex(ZeroDivisionError, "(integer )?division (or modulo )?by zero", lambda: 1/0)
		self.assertRegex('abcd', r'\w+')

if __name__ == '__main__':
	testly.main(verbosity = 2)
```

Run all tests:
```bash
> python test.py
test1-0 (__main__.TestTest) ... TestSet test1 starts ... ok
test1-1 (__main__.TestTest) ... ok
test1-2 (__main__.TestTest) ... ok
test1-3 (__main__.TestTest) ... TestSet test1 ends ... ok
test2-0 (__main__.TestTest) ... TestSet test2 starts ... ok
test2-1 (__main__.TestTest) ... ok
test2-2 (__main__.TestTest) ... ok
test2-3 (__main__.TestTest) ... TestSet test2 ends ... ok
test3 (__main__.TestTest) ... Test test3 starts ...Test test3 ends ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.001s

OK
```

Run a specific test (`setUp`, `tearDown` for test set also work):
```bash
> python test.py TestTest.test1-2
test1-2 (__main__.TestTest) ... TestSet test1 starts ... TestSet test1 ends ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK

> python test.py TestTest.test3
test3 (__main__.TestTest) ... Test test3 starts ...Test test3 ends ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```

Run a specific test set:
```bash
> python test.py TestTest.test1
test1-0 (__main__.TestTest) ... TestSet test1 starts ... ok
test1-1 (__main__.TestTest) ... ok
test1-2 (__main__.TestTest) ... ok
test1-3 (__main__.TestTest) ... TestSet test1 ends ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.000s

OK
```
