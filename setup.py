from setuptools import setup

setup(
    name="programaker-unix-bridge",
    version="0.0.1.post8",
    description="Unix-like abstraction to create Programaker bridges.",
    author="kenkeiras",
    author_email="kenkeiras@codigoparallevar.com",
    license="Apache License 2.0",
    packages=["plaza_unix_service"],
    scripts=["bin/programaker-unix-bridge"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
    ],
    include_package_data=True,
    install_requires=[
        "plaza_service",
        "xdg",
    ],
    zip_safe=False,
)
