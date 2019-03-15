from setuptools import setup, find_packages

setup(name='zuper_utils',
      package_dir={'': 'src'},
      packages=find_packages('src'),

      zip_safe=False,
      entry_points={
          'console_scripts': [
              'zj = zuper_ipce.zj:zj_main',
              'json2cbor = zuper_json:json2cbor_main',
              'cbor2json = zuper_json:cbor2json_main',
          ]
      },
      install_requires=[
          'pybase64',
          'PyContracts',
          'IPython',
          'validate_email',
          'mypy_extensions',
          'nose',
          'coverage>=1.4.33',
          'networkx',
          'dataclasses',
          'jsonschema',
          'pydot',
          'multihash',
          'py-cid',
          'cbor2',
          'numpy',
          'base58',
      ],
      )
