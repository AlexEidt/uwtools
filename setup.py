from setuptools import setup

setup(name='uwtools',
      version='0.1',
      description='Easy data collection/manipulation for courses at the University of Washington',
      url='https://github.com/AlexEidt/uwtools',
      author='AlexEidt',
      author_email='alex.eidt@outlook.com',
      license='MIT',
      packages=['uwtools'],
      install_requires=[
          'tqdm',
          'pandas',
          'beautifulsoup4',
          'requests'
      ],
      zip_safe=False)