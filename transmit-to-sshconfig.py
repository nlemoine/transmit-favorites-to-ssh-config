#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import sys
import xml.etree.ElementTree as ET
import unicodedata,re

def slugify(str):
    slug = unicodedata.normalize("NFKD",unicode(str)).encode("ascii", "ignore")
    slug = re.sub("\(", "[", slug)
    slug = re.sub("\)", "]", slug)
    slug = re.sub(r"/[^\w]+", " ", slug)
    slug = "-".join(slug.lower().strip().split())
    return slug

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

#following from Python cookbook, #475186
def has_colours(stream):
	if not hasattr(stream, "isatty"):
		return False
	if not stream.isatty():
		return False # auto color only on TTYs
	try:
		import curses
		curses.setupterm()
		return curses.tigetnum("colors") > 2
	except:
		# guess false in case of error
		return False
has_colours = has_colours(sys.stdout)


def printout(text, colour=WHITE):
	if has_colours:
		seq = "\x1b[1;%dm" % (30+colour) + text + "\x1b[0m"
		sys.stdout.write(seq)
	else:
		sys.stdout.write(text)


user_dir       = os.path.expanduser('~')
favorites_file = ET.parse(user_dir + '/Library/Application Support/Transmit/Favorites/Favorites.xml')
favorites      = favorites_file.findall('./object[@type="FAVORITE"]')
sshconfig_file = user_dir + '/.ssh/config';


if query_yes_no("This script will add all your Transmit SFTP favorites to your SSH config file and erase the current file located in %s, do you want to continue?" % sshconfig_file) is False:
	printout("[info]	", GREEN)
	print "Script aborted"
	sys.exit(0)

sshconfig      = open(sshconfig_file, 'w')

for favorite in favorites:

	attributes = favorite.findall('./attribute[@name="protocol"]')
	has_sftp = False
	for attribute in attributes:
		if attribute.text == 'SFTP':
			has_sftp = True
			continue

	if has_sftp is False:
		continue

	collection_id   = favorite.find('./relationship[@name="collection"]').get('idrefs')
	collection_name = favorites_file.find("./object[@id='%s']/attribute[@name='name']" % collection_id).text

	host            = slugify(collection_name.lower() + '/' + favorite.find('./attribute[@name="nickname"]').text)
	hostname        = favorite.find('./attribute[@name="server"]').text
	port            = int(favorite.find('./attribute[@name="port"]').text)
	user            = favorite.find('./attribute[@name="username"]').text

	printout("[info]	", GREEN)
	print "Adding %s" % host

	item = [
		"Host %s" % host,
		"\tHostName %s" % hostname,
		"\tPort %s" % port,
		"\tUser %s" % user,
		"\n"
	]

	# Remove port if not set
	if( port <= 0 ):
		item.pop(2)

	sshconfig.write('\n'.join(item).encode('utf8'))

sshconfig.close()

printout("[info]	", GREEN)
print "All SFTP favorites from Transmit have been added to %s" % sshconfig_file
