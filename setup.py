from setuptools import setup, find_packages
from pathlib import Path
long_description = (Path(__file__).parent / "README.md").read_text()

setup(
    name='timeline-ssg',
    version='0.0.1',
    description='Generates a life timeline out of your personal files',
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
        'gpxpy==1.5.0',
        'icalendar==5.0.10',
        'Markdown==3.5',
        'Pillow==10.0.1',
        'platformdirs==3.10.0',
        'PyMuPDF==1.21.1',
        'reverse-geocode==1.4.1',
    ],
    zip_safe=False,
)
