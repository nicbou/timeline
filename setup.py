from setuptools import setup, find_packages
from pathlib import Path

long_description = (Path(__file__).parent / "README.md").read_text()

setup(
    name="timeline-ssg",
    version="0.0.1",
    description="Generates a life timeline out of your personal files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://github.com/nicbou/timeline",
    author="Nicolas Bouliane",
    author_email="contact@nicolasbouliane.com",
    license="MIT",
    packages=find_packages(),
    scripts=["timeline/bin/timeline"],
    package_data={
        "timeline.templates": [
            "*",
        ],
    },
    python_requires=">=3.11",
    install_requires=[
        "gpxpy==1.6.2",
        "icalendar==7.1.0",
        "Markdown==3.10.2",
        "Pillow==12.2.0",
        "pillow-heif==1.3.0",
        "platformdirs==4.9.6",
        "PyMuPDF==1.27.2.3",
        "pytz",
        "reverse-geocode==1.6.6",
        "timezonefinder>=8.2.4",
    ],
    zip_safe=False,
)
