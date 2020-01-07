from setuptools import find_packages, setup

setup(
    name='apidoc',
    version='0.1.0',
    packages=find_packages(),
    # packages=['apidoc'],
    include_package_data=True,
    python_requires='>=3.7.5',
    install_requires=[
        'apispec~=3.1.0',
        'apispec-webframeworks~=0.5.2',
        'flask~=1.1.1',
        'marshmallow~=3.3.0'
    ]
)
