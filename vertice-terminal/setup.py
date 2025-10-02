from setuptools import setup, find_packages

setup(
    name='vcli',  # Nome do pacote corrigido para consistência
    version='1.0.0',
    description='Vértice CLI - Cyber Security Command Center',
    author='JuanCS-Dev',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click>=8.1.0',
        'rich>=13.0.0',
        'httpx>=0.25.0',
        'pyyaml>=6.0',
        'python-dotenv>=1.0.0',
        'questionary>=2.0.0',
        'tabulate>=0.9.0',
        'typer>=0.12.3',
    ],
    entry_points={
        'console_scripts': [
            'vcli=vertice.cli:app',  # <-- CORREÇÃO CRÍTICA: 'vcli' agora chama o objeto 'app'
        ],
    },
    python_requires='>=3.8',
)
