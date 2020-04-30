from setuptools import setup


setup(
    name='cldfbench_apics',
    py_modules=['cldfbench_apics'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'apics=cldfbench_apics:Dataset',
        ]
    },
    install_requires=[
        'cldfbench',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
