from setuptools import setup, find_packages
from setuptools.command.install import install

class CustomInstallCommand(install):
    def run(self):
        print("\n\n🐶 Woof! Thanks for installing Pasqui. This package is dedicated to my doggo, Pasqui! 🐾")
        # Call the default install command to proceed with the installation
        install.run(self)

setup(
    name='pasqui',
    version='0.1.0',
    packages=find_packages(where="src"),
    package_dir={"": "src"}, # Finds the pasqui directory inside src
    install_requires=[
        'pdfplumber',
        'python-docx',
        'openai',
        'tiktoken',
        'pandas',
        'scipy',
        'langchain',
        'kor',
        'requests',
        'markdownify',
        'scikit-learn',
        'langchain-community',
        'langchain-openai',
    ],
    author='Natalia Cabrera-Morales',
    author_email='natalia.cabrera.m@mail.pucv.cl',
    description="""This python library is useful to perform serveral functions needed to structure unstructured text,
    including, file convertion, errors tracking, embeddings creation, summarisation and structuring. It was created
    based on my dissertation work at University of Cambridge""",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/NcabreraM/pasqui',
    license='MIT',
    cmdclass={
        'install': CustomInstallCommand,
    },
)
