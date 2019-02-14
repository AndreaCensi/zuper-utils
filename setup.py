from setuptools import setup, find_packages

setup(name='zuper_utils',
      package_dir={'': 'src'},
      packages=find_packages('src'),

      zip_safe=False,
      entry_points={
            'console_scripts': [
                  'zj = zuper_json.zj:zj_main'
            ]
      },
      )
