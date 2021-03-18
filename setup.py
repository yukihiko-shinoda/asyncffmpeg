#!/usr/bin/env python
"""The setup script."""

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as readme_file:
    readme = readme_file.read()

setup(
    author="Yukihiko Shinoda",
    author_email="yuk.hik.future@gmail.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Telecommunications Industry",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Topic :: Multimedia",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Multimedia :: Graphics :: Capture",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Capture/Recording",
        "Topic :: Multimedia :: Sound/Audio :: Conversion",
        "Topic :: Multimedia :: Video",
        "Topic :: Multimedia :: Video :: Capture",
        "Topic :: Multimedia :: Video :: Conversion",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System",
        "Topic :: System :: Archiving",
        "Topic :: System :: Archiving :: Compression",
        "Topic :: System :: Archiving :: Packaging",
        "Typing :: Typed",
    ],
    dependency_links=[],
    description="Supports async / await pattern for FFmpeg operations.",  # noqa: E501 pylint: disable=line-too-long
    exclude_package_data={"": ["__pycache__", "*.py[co]", ".pytest_cache"]},
    include_package_data=True,
    install_requires=["ffmpeg-python", "pywin32; sys_platform == 'win32'"],
    keywords="asyncffmpeg",
    long_description=readme,
    long_description_content_type="text/markdown",
    name="asyncffmpeg",
    packages=find_packages(include=["asyncffmpeg", "asyncffmpeg.*"]),  # noqa: E501 pylint: disable=line-too-long
    package_data={"asyncffmpeg": ["py.typed"]},
    python_requires=">=3.9",
    test_suite="tests",
    tests_require=["pytest>=3"],
    url="https://github.com/yukihiko-shinoda/asyncffmpeg",
    version="1.0.1",
    zip_safe=False,
)
