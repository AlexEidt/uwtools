import setuptools

with open('README.md', mode='r') as fh:
    long_description = fh.read()

setuptools.setup(name='uwtools',
      version='1.6.0',
      description='Easy data parsing for courses at the University of Washington',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://upload.pypi.org/legacy/',
      author='AlexEidt',
      author_email='alex.eidt@outlook.com',
      license='MIT',
      packages=setuptools.find_packages(),
      install_requires=[
          'tqdm',
          'pandas',
          'beautifulsoup4',
          'requests'
      ],
      package_data = {
          'uwtools': ['*']
      },
      zip_safe=False,
      python_requires='>=3.6')