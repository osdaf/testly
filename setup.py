from setuptools import setup, find_packages

# get version
from os import path
verfile = path.join(path.dirname(__file__), 'testly', '__init__.py')
with open(verfile) as vf:
    VERSION = vf.readline().split('=')[1].strip()[1:-1]

setup (
	name             = 'testly',
	version          = VERSION,
	description      = "Python unittest with data provider and more.",
	url              = "https://github.com/pwwang/testly",
	author           = "pwwang",
	author_email     = "pwwang@pwwang.com",
	license          = "MIT License",
	packages         = find_packages(),
	install_requires = [
		'six', 'icdiff'
    ],
)
