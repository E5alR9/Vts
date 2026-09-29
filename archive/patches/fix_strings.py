with open('vts_7L_test.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('\n")', '\\n")')
c = c.replace('\n\')', '\\n\')')
c = c.replace('\n"]', '\\n"]')
c = c.replace('\n\']', '\\n\']')
c = c.replace('\n"}', '\\n"}')
c = c.replace('\n\'}', '\\n\'}')

with open('vts_7L_test_fix.py', 'w', encoding='utf-8') as f:
    f.write(c)

import py_compile
try:
    py_compile.compile('vts_7L_test_fix.py', doraise=True)
    print('Fixed!')
except Exception as e:
    print('Still broken:', e)
