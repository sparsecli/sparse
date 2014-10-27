
import os
import re
import sys
import difflib

if len(sys.argv) < 3:
	print sys.argv[0], "LINUXSRC linux-checker.make"
	os.exit(1)

linuxdir = sys.argv[1]
makefile = sys.argv[2]
print linuxdir,makefile

cflags = {}
for f in os.popen('find %s -name ".*.o.cmd"'%linuxdir):
	cmdfile = f.strip()
	l = open(cmdfile).readline()
	cmd = l.split()[3:]
	if not cmd[-1].endswith('.c') or cmd[-1].endswith('.mod.c') or '-D__KERNEL__' not in cmd:
		continue
	cfile = cmd.pop()
	ofile = cmd.pop()
	if cmd[-1] == '-o': cmd.pop()
	if cmd[-1] == '-c': cmd.pop()
	if cmd[0].startswith('-Wp,-MD,'): cmd.pop(0)
	modname = cmd.pop()[29:-2] if cmd[-1].startswith('-D"KBUILD_MODNAME=KBUILD_STR(') else ''
	basename = cmd.pop()[30:-2] if cmd[-1].startswith('-D"KBUILD_BASENAME=KBUILD_STR(') else ''

	#print basename, modname, cmd
	options = cmd
	#print cmd[-1]
	#std = linuxdir + '/' + re.sub(r'(.*/)([^/]+).c', r'\1.\2.o.std.sparse',cmd[-1])
	#assert os.path.exists(std)
	cflags.setdefault(tuple(options), []).append((cfile, basename, modname))
	#print cfile, basename, modname
	continue
	if options not in cflags:
		print # " ".join(cmd)
		s = difflib.SequenceMatcher(None, prev,options)
		op = s.get_opcodes()
		for t,i1,i2,j1,j2 in op:
			if t == 'equal':
				continue
			elif t == 'replace':
				print '-', ' '.join(prev[i1:i2])
				print '+', ' '.join(options[j1:j2])
			elif t == 'insert':
				print '+', ' '.join(options[j1:j2])
			elif t == 'delete':
				print '-', ' '.join(prev[i1:i2])
		cflags[options] = 1

orders = [(len(files),o, files) for o,files in cflags.items()]
orders.sort()
orders.reverse()
for num, options,v in orders:
	print options
	print num, 'files'

