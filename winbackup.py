#!/usr/bin/python
from operator import itemgetter

import sys
import string
import shutil
import getopt
import os
import os.path
import errno
import logging
import tempfile
import datetime
import subprocess
from rotatebackups import RotateBackups

"""
-----------------------------------------------------------------------------
A script to backup windows files as zip through the 7z utility.
Archive files more than time windows will be deleted.

Use the -h or the --help flag to get a listing of options.

Program: Windows File Backups
Author: George Pan
Date: June 9 2016
Revision: 1.0

Revision      | Author            | Comment
-----------------------------------------------------------------------------
20160609-1.0    George Pan          Initial creation of script.
-----------------------------------------------------------------------------
"""


class WinBackup:
    def __init__(self, name="backup", keep=90, srcdir=None, store=None,
                 config_file=None):
        self.name = name
        self.keep = keep
        self.config_file = config_file
        self.store = store
        self.srcdir = srcdir

    def run_command(self, command=None, shell=False, ignore_errors=False,
                    ignore_codes=None):
        result = subprocess.call(command, shell=False)
        if result and not ignore_errors and (not ignore_codes or result in set(ignore_codes)):
            raise BaseException(str(command) + " " + str(result))

    def backup(self):

        # rotate the backups
        rotater = RotateBackups(self.keep, self.store)
        rotated_names = rotater.rotate_backups()
        arc_to = None
        if not rotated_names:
            # get the current date and timestamp and the zero backup name
            now = datetime.datetime.now()
            padding = len(str(self.keep))
            tstamp = now.strftime("%Y%m%d%H%M%S")
            zbackup_name = string.join(["".zfill(padding), tstamp, self.name], ".")

            arc_to = self.store + os.sep + zbackup_name
        else:
            arc_to = rotated_names[0]

        # create the 7z command
        arc_cmd = " ".join(["7z.exe a", arc_to, self.srcdir])
        self.run_command(command=arc_cmd, ignore_errors=True)
        print(arc_cmd)

    """
    Prints out the usage for the command line.
    """


def usage():
    usage = ["winbackup.py [-hkt]\n"]
    usage.append("  [-h | --help] prints this help and usage message\n")
    usage.append("  [-k | --keep] number of backups to keep before deleting\n")
    usage.append("  [-s | --src] directory locally to be backup\n")
    usage.append("  [-t | --store] directory locally to store the backups\n")
    message = string.join(usage)
    print(message)

    """
    Main method that starts up the backup.
    """


def main(argv):
    # set the default values
    pid_file = tempfile.gettempdir() + os.sep + "rotbackup.pid"
    keep = 90
    store = None
    padding = 5

    try:

        # process the command line options
        opts, args = getopt.getopt(argv, "hk:s:t:", ["help", "src=", "keep=", "store="])

        # if no arguments print usage
        if len(argv) == 0:
            usage()
            sys.exit()

        # loop through all of the command line options and set the appropriate
        # values, overriding defaults
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                usage()
                sys.exit()
            elif opt in ("-k", "--keep"):
                keep = int(arg)
            elif opt in ("-t", "--store"):
                store = arg
            elif opt in ("-s", "--src"):
                srcdir = arg

    except getopt.GetoptError, msg:
        # if an error happens print the usage and exit with an error
        usage()
        sys.exit(errno.EIO)

    # check options are set correctly
    if store == None:
        usage()
        sys.exit(errno.EPERM)

    # process, catch any errors, and perform cleanup
    try:
        if os.name != 'nt':
            print("This program only works on windows.")
            print("[X] Quitting...")
            sys.exit(1)

        # another rotate can't already be running
        if os.path.exists(pid_file):
            logging.warning("Win backups running, %s pid exists, exiting." % pid_file)
            sys.exit(errno.EBUSY)
        else:
            pid = str(os.getpid())
            f = open(pid_file, "w")
            f.write("%s\n" % pid)
            f.close()

        # create the backup object and call its backup method
        rotback = WinBackup(keep=keep, store=store, srcdir=srcdir)
        rotback.backup()

    except(Exception):
        logging.exception("Rotate backups failed.")
    finally:
        os.remove(pid_file)


# if we are running the script from the command line, run the main function
if __name__ == "__main__":
    main(sys.argv[1:])
