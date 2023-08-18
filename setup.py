from setuptools import setup, find_packages
from pathlib import Path
long_description = (Path(__file__).parent / "README.md").read_text()

setup(
    name='timeline',
    version='0.0.1',
    description='Timeline generator',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='http://github.com/nicbou/timeline',
    author='Nicolas Bouliane',
    author_email='contact@nicolasbouliane.com',
    license='MIT',
    packages=find_packages(),
    scripts=['timeline/bin/timeline'],
    package_data={
        'timeline.templates': ['*', ],
    },
    python_requires='>=3.11',
    install_requires=[
        'Markdown==3.4.3',
    ],
    zip_safe=False,
)
