# !/usr/bin/env python
# -*- coding:utf-8 -*-

from setuptools import setup, find_packages    
    
setup(    
    name = "setupdemo",
    version = "0.3",    
    packages = find_packages(),    
    
    description = "egg test demo",    
    long_description = "egg test demo",    
    author = "luhouxiang",    
    author_email = "luhouxiang@hotmail.com",    
    
    license = "GPL",    
    keywords = ("setupdemo", "egg"),    
    platforms = "Independant",    
    url = "http://blog.csdn.net/hong201/",  
    entry_points = {  
        'console_scripts': [  
            'setupdemo = setupdemo.hello:main'
        ]  
    }  
)  