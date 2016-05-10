#!/usr/bin/env python
import shutil
import os
import sys
from optparse import OptionParser
import random
from string import ascii_uppercase
import subprocess
import cups

SEED = 51
random.seed(SEED)

GENERATED = {}
FNULL = open(os.devnull, 'w')

def gen_content(fname, s):
	return '\def\SERIAL{{{0}}} \input{{{1}}}'.format(s, fname)

def generate_latex(base, serial, output):
	if not '.tex' in base:
		print "Usage: argument file must be .tex"
		exit(2)

	if not os.path.isdir(output):
		print "Output directory does not exist, creating...."
		try:
			os.mkdir(output)
		except Exception as e:
			print "Error: directory creation failed."
			exit(2)

	try:
		fname = base.split('.tex')[0]
	except:
		print "Error getting base filename. Multiple periods?"
		exit(2)

	outx = '{0}/{1}{2}.tex'.format(output, fname,serial )
	
	content = gen_content(base, serial)
	
	with open(outx, 'w') as f:
		f.write(content)

	return outx


def pdfcompile(fname, output):
	assert('.tex' in fname)
	if output:
		assert(os.path.isdir(output))

	# if not subprocess.call('pdflatex -output-directory={0} {1}'.format(output, fname)):
	print "compiling {0}".format(fname)
	subprocess.call(['pdflatex', '-output-directory={0}'.format(output), fname],
		stdout=FNULL, stderr=subprocess.STDOUT)
	return True

def generate_serial():
	return ''.join(random.choice(ascii_uppercase) for i in range(12))

def parse_options():
	parser = OptionParser()

	parser.add_option("-d", "--draft",default=False, action="store_true",
						 help='compile a draft before compiling all serialized.')

	parser.add_option("-c", "--compile", default=False, action='store_true',
						dest='compile',
						 help='compile to pdf after generating latex.')

	parser.add_option('-n', '--number', type='int', metavar='NUM',
						default=10,
						dest='num',
						help='specify number of distinct documents to create. Default is 10.')
	
	parser.add_option("-p", '--print', action='store_true',
						default=False, 
						dest='p',
							help='print after compiling to PDF.')

	parser.add_option('-o', '--output',default='./serial_output',
								dest='output',
								metavar='OUTPUT',
								help='specify a directory in which\
																 to look for pre-compiled PDFs.\
																 This allows for batching across runs.')
	return parser.parse_args()

if __name__ == '__main__':

	(opts, args) = parse_options()

	opts.output = os.path.abspath(opts.output)

	if len(args) != 1:
		print "Usage: ./generate_serials /path/to/base/tex"
		exit(1)

	if opts.draft:
		compile_as_draft(args[0])

	for i in range(opts.num):
		s = generate_serial()
		
		while s in GENERATED:
			s = generate_serial()

		GENERATED[s] = True

		outname = generate_latex(args[0], s, opts.output)

	if opts.compile:
		if not os.path.isdir(opts.output):
			print "Output directory does not exist."
			exit(1)

		if not os.path.isdir(opts.output+'/pdfs/'):
			print "PDFs directory does not exist. Creating..."

			try:
				pdfoutdir = opts.output + '/pdfs/'
				print pdfoutdir
				os.mkdir(pdfoutdir)
			except Exception as e:
				print "Error: PDF directory creation failed."
				exit(1)
		
		pdfoutdir = opts.output + '/pdfs/'
		outdircontents = os.listdir(opts.output)
		tocompile = filter(lambda x : '.tex' in x, outdircontents)
		for toc in tocompile:
			compilepath = os.path.abspath(opts.output + '/' + toc)
			pdfcompile(compilepath, pdfoutdir)

		# clean up
		pdfdirlist = map(lambda x : pdfoutdir + x, filter(lambda x : '.aux' in x 
										or '.log' in x,  os.listdir(pdfoutdir)))
		for p in pdfdirlist:
			os.remove(p)

	if opts.p:
		print "THIS OPTION PRINTS ALL PDFS IN THE PDFS DIRECTORY. Confirm?"
		while True:
			inp = raw_input("N/(y): ")
			if inp.strip().lower() == 'n':
				print "Exiting."
				exit(1)
			elif inp.strip().lower() == 'y':
				break

		try:
			conn = cups.Connection()
			printer_dict = conn.getPrinters()
		except cups.IPPError as e:
			print e
			exit(2)

		pnames = printer_dict.keys()
		print "Select a printer: "
		for i,p in enumerate(pnames):
			print "[{0}]: {1}".format(i,p)

		while True:
			pnum = raw_input("Please enter a printer number: ")
			try:
				pnum = int(pnum)
				break
			except ValueError as e:
				print e
				continue

		selection = pnames[pnum]

		while True:
			inp = raw_input("Selected: {0}. Confirm? Y/n: ".format(selection))
			if inp.strip().lower() == 'n':
				print "Exiting."
				exit(1)
			elif inp.strip().lower() == 'y':
				break

		pdfoutdir = opts.output + '/pdfs/'
		pdfs = os.listdir(pdfoutdir)
		pdfs = map(lambda x: (x,os.path.abspath(pdfoutdir + x)), pdfs)
		pdfs = filter(lambda (x,_): '.pdf' in x, pdfs)

		errored = []
		for (name, full) in pdfs:
			print "Printing {0}....".format(name)
			try:
				# print the file here
				jid = conn.printFile(selection, full, name, dict())
				while jid in conn.getJobs():
					continue
				os.remove(full)
				print "Printed"
			except Exception as e:
				print e
				errored.add(name)
				print "Print error "

		print "Errors: {0}".format(errored)
		print "Finished."
		exit(0)








