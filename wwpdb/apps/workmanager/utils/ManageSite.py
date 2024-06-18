##
# File:  ManageSite.py
# Date:  20-Nov-2019
# Updates:
##
"""
Tool for managing the OneDep workflow manager user database.

This tool allows for queryng adding/removing sites, and dumping restoring users
"""
__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import argparse
import sys

from wwpdb.apps.workmanager.db_access.StatusDbApi import StatusDbApi


class UserManager(object):
    def __init__(self, siteId=None):
        self.__siteId = siteId
        self.__statusDB = StatusDbApi(siteId=self.__siteId, verbose=True)

    def listSites(self, verbose):
        sites = self.__statusDB.getSites()
        sdata = {}
        for s in sites:
            site = s['site']
            if site == 'ALL':
                continue
            if site not in sdata:
                sdata[site] = {}
            sdata[site][s['code']] = {'da_group_id': s['da_group_id'],
                                      'group_name' : s['group_name']}

        for s in sdata:
            if verbose:
                print("Site: {}".format(s))
                for code in ['LANN', 'ANN']:
                    if code in sdata[s]:
                        d = sdata[s][code]
                        print("     {:4s} group: {:2d}  name: {}".format(code, d['da_group_id'], d['group_name']))
            else:
                print(s)

    def listSiteUsers(self, site):
        users = self.__statusDB.getSiteUser(site)

        for u in users:
            print('{:4s} uname: {:6s} Name: {:30s}   initials {:6s} active: {:1d}  pass: {:s}'.format(u['code'],
                                                                                                      u['user_name'],
                                                                                                      "%s %s" % (u['first_name'], u['last_name']),
                                                                                                      u['initials'],
                                                                                                      u['active'],
                                                                                                      u['password']
                                                                                                      ))

    def addSite(self, site, lead, email, first, last):
        status = self.__statusDB. addSite(site, lead, email, first, last)
        if status != 'OK':
            print("Problem adding site - might already exist")

    def deleteSite(self, site):
        status = self.__statusDB.deleteSite(site)
        if status != 'OK':
            print(status)


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(help='sub-command help')
    sub_a = subparsers.add_parser('list-sites', help='list installed webfe packages')
    sub_a.add_argument("-v", "--verbose", action='store_true', help='Display additional info for site')
    sub_a.set_defaults(func="list")

    sub_b = subparsers.add_parser('list-users', help='list users in WFM db for site')
    sub_b.add_argument("-s", "--wfm-site", help='WFM site id to list', required=True)
    sub_b.set_defaults(func="list_users")

    sub_c = subparsers.add_parser('add-site', help='add a new site')
    sub_c.add_argument("-s", "--wfm-site", help='WFM site id to list', required=True)
    sub_c.add_argument("--lead-user", help='Lead user for assignments', required=True)
    sub_c.add_argument("--email", help='email of lead user', required=True)
    sub_c.add_argument("--first-name", help='first name of lead user', required=True)
    sub_c.add_argument("--last-name", help='last name of lead user', required=True)
    sub_c.set_defaults(func="add_site")

    sub_d = subparsers.add_parser('delete-site', help='add a new site')
    sub_d.add_argument("-s", "--wfm-site", help='WFM site id to list', required=True)
    sub_d.set_defaults(func="delete_site")

    args = parser.parse_args()

    if 'func' not in args:
        parser.print_usage()
        sys.exit(1)

    print(args)

    um = UserManager()

    if args.func == 'list':
        um.listSites(args.verbose)
    elif args.func == 'list_users':
        um.listSiteUsers(site=args.wfm_site)
    elif args.func == 'add_site':
        um.addSite(site=args.wfm_site, lead=args.lead_user, email=args.email,
                   first=args.first_name, last=args.last_name)
    elif args.func == 'delete_site':
        um.deleteSite(site=args.wfm_site)


if __name__ == '__main__':
    main()
