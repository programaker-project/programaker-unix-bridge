from setuptools import setup

setup(name='plaza-unix-service',
      version='0.0.1',
      description='Unix-like abstraction to create plaza bridges.',
      author='kenkeiras',
      author_email='kenkeiras@codigoparallevar.com',
      license='Apache License 2.0',
      packages=['plaza_unix_service'],
      scripts=['bin/plaza-unix-service'],
      include_package_data=True,
      install_requires = [
          'plaza_service',
          'xdg',
      ],
      zip_safe=False)
