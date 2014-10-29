
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
allcfiles = {}
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
	b = re.sub(r'-','_',os.path.basename(cfile)[:-2])
	if modname == b:
		modname = '@'
	assert basename == b
	options = tuple(cmd)
	hashed = cflags.setdefault(options, ([], options))
	hashed[0].append(cfile)
	allcfiles.setdefault(os.path.dirname(cfile), []).append((os.path.basename(cfile), hashed[1], basename, modname))
	#print cfile, basename, modname

orders = [(len(files[0]),o, files) for o,files in cflags.items()]
orders.sort()
orders.reverse()
base = []
expr = {}
for num, options,v in orders:
	#print options
	#print num, 'files'
	for i, x in enumerate(base):
		b, user = x
		op = difflib.SequenceMatcher(None, b,options).get_opcodes()
		op = [ o for o in op if o[0] != 'equal']
		opmap = {}
		first = op[0]
		if first[0] == 'replace' or len([ 1 for o in op if o[0] == first[0]]) < len(op):
			continue
		delta = []
		if first[0] == 'delete':
			for o, i1,i2,j1,j2 in op:
				delta += b[i1:i2]
			base[i] = (options, user)
			expr[b] = (options, delta)
			expr[options] = (options, '')
			#print 'replace base', i, delta
			#print user
			for u in user:
				#print "merge", expr[u][1], delta
				expr[u] = (options, expr[u][1] + delta)
				
			user.append(b)
			#print 'replace base', i, delta
		else:
			for o, i1,i2,j1,j2 in op:
				delta += options[j1:j2]
			expr[options] = (b, delta)
			user.append(options)
		#print first[0], i, delta
		break
	else:
		#print 'add to base'
		base.append((options, []))
		expr[options] = (options, '')
alldir = allcfiles.items()
alldir.sort()

emit = {}
for d,v in alldir:
	#print '# dir ', d
	print
	opthash = {}
	for c, o, basename, mod in v:
		opthash.setdefault((o,mod), []).append(c)
	for key, clist in opthash.items():
		o,mod = key
		optbase, delta = expr[o]
		if optbase not in emit:
			emit[optbase] = 'basecflags%d'%len(emit)
			print '%s = %s'%(emit[optbase], ' '.join(optbase))
			print
		olist = [ c[:-2] + '.sp' for c in clist]
		if len(olist)==1:
			print "%s : %%.sp : %%.c"%(os.path.join(d, olist[0]))
		else:
			print "$(addprefix %s/, %s) : %%.sp : %%.c"%(d, ' '.join(olist))
		if mod == '@':
			print '\t$(call checkfile, %s, %s)'%(emit[optbase], ' '.join(delta))
		elif mod:
			print '\t$(call checkfile-mod, %s, %s, %s)'%(emit[optbase], mod, ' '.join(delta))
		else:
			print '\t$(call checkfile-nomod, %s, %s)'%(emit[optbase], ' '.join(delta))
		#print c, expr[o][1], basename, mod
