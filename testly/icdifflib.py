import warnings
import difflib, icdiff
import sys

def _getIcOptions():
	origargv = [arg for arg in sys.argv]
	options = icdiff.get_options()[0]
	sys.argv = origargv
	return options

def ndiff(a, b, linejunk=None, charjunk=difflib.IS_CHARACTER_JUNK):
	options = _getIcOptions()
	cd = icdiff.ConsoleDiff(
		cols              = int(options.cols),
		show_all_spaces   = options.show_all_spaces,
		highlight         = options.highlight,
		line_numbers      = options.line_numbers,
		tabsize           = int(options.tabsize)
	)
	with warnings.catch_warnings():
		warnings.simplefilter('ignore')
		for line in cd.make_table(
				a, b, 'First', 'Second',
				context=(not options.whole_file),
				numlines=int(options.unified)):
			line = "%s\n" % line
			yield line.encode(options.output_encoding)
