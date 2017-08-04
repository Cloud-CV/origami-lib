from distutils.core import setup
setup(
  name = 'origami­-lib',
  packages = ['origami­-lib'],
  version = '0.1',
  description = 'Library to set up your project to run on Origami',
  author = 'CloudCV Team',
  author_email = 'team@cloudcv.org',
  url = 'https://github.com/Cloud-CV/origami-lib', 
  download_url = 'https://github.com/Cloud-CV/origami-lib/archive/0.1.tar.gz', 
  install_requires = [
    'flask',
    'flask-cors',
    'requests',
    'python-magic',
    'tornado'
  ]
)
