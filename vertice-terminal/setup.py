from setuptools import setup, find_packages

setup(
    name='vcli',  # Nome do pacote corrigido para consistência
    version='1.0.0',
    description='Vértice CLI - Cyber Security Command Center',
    author='JuanCS-Dev',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'typer>=0.12.3',
        'rich>=13.0.0',
        'httpx>=0.25.0',
        'pyyaml>=6.0',
        'python-dotenv>=1.0.0',
        'questionary>=2.0.0',
        'diskcache>=5.6.0',
        'typing-extensions>=4.0.0',
        'prompt-toolkit>=3.0.0',
    ],
    entry_points={
        'console_scripts': [
            'vcli=vertice.cli:app',  # Standard CLI with subcommands
            'vertice=vertice.interactive_shell:main',  # Direct to interactive shell
        ],
    },
    python_requires='>=3.8',
)
