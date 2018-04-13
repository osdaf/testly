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
		yield 2, 2
		yield 3, 3
		yield 4, 4
		
	def test2(self, in_, out):
		self.assertEqual(in_, out)
		
	# compatible with original tests
	def test3(self):
		self.assertEqual('a', 'a')
		
if __name__ == '__main__':
	testly.main(verbosity = 2)