from __future__ import print_function
import difflib, itertools

DEFAULT_CONSOLE_WIDTH = 160
MIN_CONSOLE_WIDTH     = 80

class Colors(object):
	none      = ''
	end       = '\033[0m'
	bold      = '\033[1m'
	underline = '\033[4m'

	# regular colors
	black    = '\033[30m'
	red      = '\033[31m'
	green    = '\033[32m'
	yellow   = '\033[33m'
	blue     = '\033[34m'
	magenta  = '\033[35m'
	cyan     = '\033[36m'
	gray     = '\033[37m'
	white    = '\033[97m'
	darkgray = '\033[90m'

	# bgcolors
	bgblack   = '\033[40m'
	bgred     = '\033[41m'
	bggreen   = '\033[42m'
	bgyellow  = '\033[43m'
	bgblue    = '\033[44m'
	bgmagenta = '\033[45m'
	bgcyan    = '\033[46m'
	bgwhite   = '\033[47m'

class Theme(object):

	# themes
	DEFAULT = {
		'delete': Colors.red,
		'insert': Colors.green,
		'equal' : Colors.white,
		'change': Colors.yellow,
		'lineno': Colors.darkgray,
		'sep'   : Colors.darkgray,
	}

	BRIGHT = {
		'delete': Colors.magenta,
		'insert': Colors.cyan,
		'equal' : Colors.gray,
		'change': Colors.yellow,
		'lineno': Colors.darkgray,
		'sep'   : Colors.darkgray,
	}

	CONTRAST = {
		'delete': Colors.bgred,
		'insert': Colors.bggreen,
		'equal' : Colors.bgwhite + Colors.black,
		'change': Colors.bgyellow,
		'lineno': Colors.darkgray,
		'sep'   : Colors.darkgray,
	}

	PLAIN = {
		'delete': Colors.underline + Colors.white,
		'insert': Colors.underline + Colors.bold + Colors.white,
		'change': Colors.underline,
		'equal' : Colors.gray,
		'lineno': Colors.darkgray,
		'sep'   : Colors.darkgray,
	}

	def __init__(self, theme = 'default'):
		self.theme = theme

	def __getattr__(self, name):
		def color(s):
			return getattr(Theme, self.theme.upper())[name] + s + Colors.end
		return color

class CDiff (object):
	"""
	Colored diff
	"""

	@staticmethod
	def _consoleWidth(default = DEFAULT_CONSOLE_WIDTH):
		def ioctl_GWINSZ(fd):
			try:
				import fcntl
				import termios
				import struct
				cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
			except Exception:
				return None
			return cr
		cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
		if cr and cr[1] > 0:
			return cr[1]
		else:
			return default

	@staticmethod
	def _getLen(mdexpr):
		# '\x00', '\x01', '+' or '-' or '^'
		return len(mdexpr) - mdexpr.count('\x00') * 3

	@staticmethod
	def _getWidth(md, cwidth = None, lineno = True):
		cwidth       = cwidth or CDiff._consoleWidth(DEFAULT_CONSOLE_WIDTH)
		cwidth       = max(cwidth, MIN_CONSOLE_WIDTH)

		maxlnno_left = maxlnno_right = 0
		maxwidth     = int(MIN_CONSOLE_WIDTH / 2)
			
		for left, right, match in list(md):
			if left is None: 
				continue
			if lineno:
				maxlnno_left  = max(maxlnno_left, left[0] or 0)
				maxlnno_right = max(maxlnno_right, right[0] or 0)
			maxwidth = max(CDiff._getLen(left[1]), CDiff._getLen(right[1]), maxwidth)
		
		maxlnno_left  = len(str(maxlnno_left))
		maxlnno_right = len(str(maxlnno_right))

		if lineno:
			#                                100. ab | 100. cd
			availwidth = int((cwidth - maxlnno_left - 2 - 3 - maxlnno_right - 2) / 2)
		else:
			availwidth = int((cwidth - 3) / 2)
		return min(maxwidth, availwidth), maxlnno_left, maxlnno_right


	def __init__(self, linejunk = None, charjunk = difflib.IS_CHARACTER_JUNK, lineno = True, theme = 'default'):
		self.linejunk = linejunk
		self.charjunk = charjunk
		self.theme    = Theme(theme)
		self.lineno   = lineno

	def _replaceTag(self, s):
		return s.replace('\x00+', getattr(self.theme, self.theme.theme.upper())['insert']) \
				.replace('\x00-', getattr(self.theme, self.theme.theme.upper())['delete']) \
				.replace('\x00^', getattr(self.theme, self.theme.theme.upper())['change']) \
				.replace('\x01', Colors.end)

	@staticmethod
	def _split(s, width):
		ret = []

		opened  = False
		opentag = None
		length  = 0
		tmp     = ''
		for c in list(s):
			if c == '\x00':
				opened = True
				tmp += c
			elif opened and not opentag:
				opentag = c
				tmp += c
			elif opened and c == '\x01':
				opened = False
				# give up if tmp is empty, because it's already added at line 169
				if tmp != '\x00' + opentag: 
					tmp += c
				else:
					tmp = ''
			else:
				length += 1
				tmp += c

			if length == width:
				if not opened:
					ret.append(tmp)
					tmp    = ''
					length = 0
				else:
					ret.append(tmp + '\x01')
					tmp = '\x00' + opentag
					length = 0
					
		if tmp: ret.append(tmp + ' ' * (width - CDiff._getLen(tmp)))
		return ret

	def diff(self, a, b, context = 3, cwidth = None):
		if not isinstance(a, list):
			a = a.splitlines()
		if not isinstance(b, list):
			b = b.splitlines()

		a = [str(_) for _ in a]
		b = [str(_) for _ in b]
		
		md = difflib._mdiff(a, b, context, self.linejunk, self.charjunk)
		md, md2 = itertools.tee(md)
		width, lnno_left, lnno_right = CDiff._getWidth(md2, cwidth, self.lineno)
		output = []

		for left, right, match in md:
			linefmt         = '{lineno_left}{leftstr}{sep}{lineno_right}{rightstr}\n'
			if match is None:
				if self.lineno:
					lineno_left  = str(' ').rjust(lnno_left + 2)
					lineno_right = str(' ').rjust(lnno_right + 2)
				else:
					lineno_left = lineno_right = ''
					
				output.append(linefmt.format(
					lineno_left  = self.theme.lineno(lineno_left),
					lineno_right = self.theme.lineno(lineno_right),
					leftstr      = self.theme.sep('-' * width),
					rightstr     = self.theme.sep('-' * width),
					sep          = self.theme.sep(' | ')
				))
				continue

			lefts  = CDiff._split(left[1]  if left[1]  != '\n' else '', width)
			rights = CDiff._split(right[1] if right[1] != '\n' else '', width)

			for i in range(max(len(lefts), len(rights))):
				if i == 0:
					if self.lineno:
						lineno_left  = (str(left[0]).rjust(lnno_left) + '. ') if left[0] else str(' ').rjust(lnno_left + 2)
						lineno_right = (str(right[0]).rjust(lnno_right) + '. ') if right[0] else str(' ').rjust(lnno_right + 2)
					else:
						lineno_left  = lineno_right = ''
				else:
					if self.lineno:
						lineno_left  = str(' ').rjust(lnno_left + 2)
						lineno_right = str(' ').rjust(lnno_right + 2)
					else:
						lineno_left  = lineno_right = ''

				if i < len(lefts):
					leftstr = self._replaceTag(lefts[i])
				else:
					leftstr = ' ' * width
				
				if i < len(rights):
					rightstr = self._replaceTag(rights[i])
				else:
					rightstr = ' ' * width
				
				output.append(linefmt.format(
					lineno_left  = self.theme.lineno(lineno_left),
					lineno_right = self.theme.lineno(lineno_right),
					leftstr      = leftstr,
					rightstr     = rightstr,
					sep          = self.theme.sep(' | ')
				))


		for line in output:
			yield line
	



if __name__ == '__main__': # pragma: no cover 
	
	str1 = "lorem ipsum dolor sit amet"
	str2 = "lorem foo ipsum dolor amet"
	print ('# Inline diff without line number:')
	print (''.join(list(CDiff(lineno = False).diff(str1, str2))))
	
	print ('# Lines with line number:')
	print (''.join(list(CDiff().diff("abc\n1111121111aa234a", "def\n111111111a223aa"))))

	str1 = '''oooooooone
two
aaa
tree
1
1
1
1
1
1
fourfourfourfourfourfourfourfourfour very very very very very very very very very very very very very very very very very very very very very very very very very very long line
'''.splitlines()
	str2 = '''oooooooore
emu
three
1
1
1
1
1
1
aaa
fivefivefivefivefivefivefivefivefive
'''.splitlines()
	print ('# Multiple lines with auto console width: ')
	print (''.join(list(CDiff().diff(str1, str2))))

	print ('# Multiple lines with fixed column width: ')
	print (''.join(list(CDiff().diff(str1, str2, cwidth = 100))))

	print ('# Multiple lines with 1 context line: ')
	print (''.join(list(CDiff().diff(str1, str2, cwidth = 100, context = 1))))

	print ('# Multiple lines with bright theme: ')
	print (''.join(list(CDiff(theme = 'bright').diff(str1, str2, cwidth = 100, context = 1))))

	print ('# Multiple lines with contrast theme: ')
	print (''.join(list(CDiff(theme = 'contrast').diff(str1, str2, cwidth = 100, context = 1))))

	print ('# Multiple lines with plain theme: ')
	print (''.join(list(CDiff(theme = 'plain').diff(str1, str2, cwidth = 100, context = 1))))

	print ('# List:')
	print (''.join(list(CDiff(lineno = False).diff(['aaaaaaaaaaaaa', 'bbbbbbbbbbb', 'cccccccccccc'], ['aaaaaaaaaaaaa', 'bbbbbbdddbb', 'cccccccccccc', 'dddddddddd']))))
