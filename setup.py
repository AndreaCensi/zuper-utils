from setuptools import setup, find_packages


def get_version(filename):
    import ast

    version = None
    with open(filename) as f:
        for line in f:
            if line.startswith("__version__"):
                version = ast.parse(line).body[0].value.s
                break
        else:
            raise ValueError("No version found in %r." % filename)
    if version is None:
        raise ValueError(filename)
    return version


shell_version = get_version(filename="src/zuper_ipce/__init__.py")

setup(
    name="zuper-utils",
    package_dir={"": "src"},
    packages=find_packages("src"),
    version=shell_version,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            # 'zj = zuper_ipce.zj:zj_main',
            "json2cbor = zuper_ipce:json2cbor_main",
            "cbor2json = zuper_ipce:cbor2json_main",
            "cbor2yaml = zuper_ipce:cbor2yaml_main",
        ]
    },
    install_requires=[
        "oyaml",
        "pybase64",
        "PyYAML",
        "validate_email",
        "mypy_extensions",
        "typing_extensions",
        "nose",
        "coverage>=1.4.33",
        "dataclasses",
        "jsonschema",
        "cbor2",
        "numpy",
        "base58",
        "zuper-commons>=3,<4",
        "frozendict",
        "pytz",
        "termcolor",
        "numpy",
    ],
)
