from distutils.core import setup, Extension

module1 = Extension('apng2gif',

					libraries = ['stdc++', 'm', 'png', 'z'],
                    sources = ['apng2gif.cpp'])

setup (name = 'APNG2gif',
       version = '1.0',
       description = 'This is a animated png convert to gif package',
       ext_modules = [module1])