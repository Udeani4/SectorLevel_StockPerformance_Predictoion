'''
The setup.py file is an essential part of packaging and distributing Python projects. It is used by setuptools (or distutils in older Python versions) to define the configuration of your project, such as its metadata, dependencies, and more
'''

from setuptools import find_packages,setup
## find_packages will scan through all the files and anyone with __init__.py  will become a package that can be imported 
from typing import List ## This is for type castng

def get_requirements()->List[str]:
    """
    This function will return a list of requirements
    """
    requirement_list:List[str]=[] ## returns a list of string
    try:
        with open('requirements.txt','r') as file:
            ## read lines from the file
            lines=file.readlines()
            ## process the line
            for line in lines:
                requirement=line.strip()
                ## ignore the empty lines and '-e .'
                if requirement and requirement!='-e .':
                    requirement_list.append(requirement)
    except FileNotFoundError:
        print('requirements.txt file not found')
    
    return requirement_list


## Our main aim is to setup the metadata
setup(
    name='NGX_Stock_Prediction',
    version='0.0.1',
    author='Udeani Izuchukwu',
    author_email='udeaniizu04@gmail.com',
    packages=find_packages(),
    install_requires=get_requirements() ## This will find all the requirements and install them.
)

# print(get_requirements())