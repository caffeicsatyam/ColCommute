import sys, os, pkgutil, traceback

print('CWD:', os.getcwd())
print('sys.path[0]:', sys.path[0])
print('LIST:', os.listdir('.'))
print('MODS:', [m.name for m in pkgutil.iter_modules(['.'])])
try:
    import colcommute
    print('IMPORTED OK')
except Exception:
    traceback.print_exc()
