python3 proc_setup.py build_ext --inplace
rm processimage.so
rm angryprocesses.so
mv processimage.cpython-35m-arm-linux-gnueabihf.so processimage.so
mv angryprocesses.cpython-35m-arm-linux-gnueabihf.so angryprocesses.so