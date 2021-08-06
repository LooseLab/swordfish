from setuptools import find_packages, setup


setup(
    name="swordfish",
    version="0.0.1",
    license="MIT",
    # author="",
    # author_email="",
    description="Read Until and Run Until demonstrator",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/LooseLab/swordfish",
    project_urls={
        "Source Code": "https://github.com/LooseLab/swordfish/",
        "Issue Tracker": "https://github.com/LooseLab/swordfish/issues",
    },
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    python_requires=">=3.6",
    install_requires=["toml", "minknow-api", "requests"],
    entry_points={
        "console_scripts": [
            "swordfish = swordfish.cli:main",
        ]
    },
)
