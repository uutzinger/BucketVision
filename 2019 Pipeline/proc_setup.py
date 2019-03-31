# python3 ./proc_setup.py build_ext --inplace
# rm processimage.so
# rm angryprocesses.so
# mv processimage.cpython-35m-arm-linux-gnueabihf.so processimage.so
# mv angryprocesses.cpython-35m-arm-linux-gnueabihf.so angryprocesses.so

from distutils.core import setup
from Cython.Build import cythonize


setup(ext_modules=cythonize("processimage.py"))
setup(ext_modules=cythonize("angryprocesses.py"))

