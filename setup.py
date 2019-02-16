from setuptools import setup, find_packages

setup(name='zuper_utils',
      package_dir={'': 'src'},
      packages=find_packages('src'),

      zip_safe=False,
      entry_points={
            'console_scripts': [
                  'zj = zuper_ipce.zj:zj_main'
            ]
      },
      install_requires=[
            'pybase64',
            'PyContracts',
            'IPython',
            'validate_email',
            'mypy_extensions',
            'nose',
            'coverage',
            'networkx',
            'dataclasses',
        ],
      )
