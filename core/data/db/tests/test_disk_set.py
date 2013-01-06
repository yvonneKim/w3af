# -*- coding: UTF-8 -*-
'''
Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''
import unittest
import threading

from nose.plugins.attrib import attr

from core.controllers.misc.temp_dir import create_temp_dir
from core.data.db.disk_set import DiskSet

from core.data.parsers.url import URL
from core.data.request.HTTPQsRequest import HTTPQSRequest
from core.data.request.HTTPPostDataRequest import HTTPPostDataRequest
from core.data.dc.headers import Headers
from core.data.db.dbms import get_default_db_instance


class test_DiskSet(unittest.TestCase):

    def setUp(self):
        create_temp_dir()

    @attr('smoke')
    def test_add(self):
        ds = DiskSet()
        ds.add(1)
        ds.add(2)
        ds.add(3)
        ds.add(1)

        self.assertEqual(list(ds), [1, 2, 3])
        self.assertEqual(len(ds), 3)

    def test_add_urlobject(self):
        ds = DiskSet()

        ds.add(URL('http://w3af.org/?id=2'))
        ds.add(URL('http://w3af.org/?id=3'))
        ds.add(URL('http://w3af.org/?id=3'))

        self.assertEqual(ds[0], URL('http://w3af.org/?id=2'))
        self.assertEqual(ds[1], URL('http://w3af.org/?id=3'))
        self.assertEqual(len(ds), 2)
        self.assertFalse(URL('http://w3af.org/?id=4') in ds)
        self.assertTrue(URL('http://w3af.org/?id=2') in ds)

    def test_add_HTTPQSRequest(self):
        ds = DiskSet()

        uri = URL('http://w3af.org/?id=2')
        hdr = Headers([('Referer', 'http://w3af.org/')])

        qsr1 = HTTPQSRequest(uri, method='GET', headers=hdr)

        uri = URL('http://w3af.org/?id=3')
        qsr2 = HTTPQSRequest(uri, method='GET', headers=hdr)

        uri = URL('http://w3af.org/?id=7')
        qsr3 = HTTPQSRequest(uri, method='FOO', headers=hdr)

        ds.add(qsr1)
        ds.add(qsr2)
        ds.add(qsr2)
        ds.add(qsr1)

        self.assertEqual(ds[0], qsr1)
        self.assertEqual(ds[1], qsr2)
        self.assertFalse(qsr3 in ds)
        self.assertTrue(qsr2 in ds)
        self.assertEqual(len(ds), 2)

        # This forces an internal change in the URL object
        qsr2.get_url().url_string
        self.assertTrue(qsr2 in ds)

    @attr('smoke')
    def test_add_HTTPPostDataRequest(self):
        ds = DiskSet()

        uri = URL('http://w3af.org/?id=2')
        hdr = Headers([('Referer', 'http://w3af.org/')])

        pdr1 = HTTPPostDataRequest(uri, method='GET', headers=hdr)

        uri = URL('http://w3af.org/?id=3')
        pdr2 = HTTPPostDataRequest(uri, method='GET', headers=hdr)

        uri = URL('http://w3af.org/?id=7')
        pdr3 = HTTPPostDataRequest(uri, method='FOO', headers=hdr)

        ds.add(pdr1)
        ds.add(pdr2)
        ds.add(pdr2)
        ds.add(pdr1)

        self.assertEqual(ds[0], pdr1)
        self.assertEqual(ds[1], pdr2)
        self.assertFalse(pdr3 in ds)
        self.assertTrue(pdr2 in ds)
        self.assertEqual(len(ds), 2)

        # This forces an internal change in the URL object
        pdr2.get_url().url_string
        self.assertTrue(pdr2 in ds)

    def test_update(self):
        ds = DiskSet()
        ds.add(1)
        ds.update([2, 3, 1])

        self.assertEqual(list(ds), [1, 2, 3])

    def test_thread_safe(self):
        ds = DiskSet()

        def worker(range_inst):
            for i in range_inst:
                ds.add(i)

        threads = []
        _min = 0
        add_dups = False
        for _max in xrange(0, 1100, 100):

            th = threading.Thread(target=worker, args=(xrange(_min, _max),))
            threads.append(th)

            # For testing the uniqueness of DiskSets
            add_dups = not add_dups
            if add_dups:
                th = threading.Thread(
                    target=worker, args=(xrange(_min, _max),))
                threads.append(th)

            _min = _max

        for th in threads:
            th.start()

        for th in threads:
            th.join()

        for i in xrange(0, 1000):
            self.assertTrue(i in ds, i)

        ds_as_list = list(ds)
        self.assertEqual(len(ds_as_list), len(set(ds_as_list)))

        ds_as_list.sort()
        self.assertEqual(ds_as_list, range(1000))
    
    def test_remove_table(self):
        disk_set = DiskSet()
        table_name = disk_set.table_name
        db = get_default_db_instance()
        
        self.assertTrue(db.table_exists(table_name))
        
        del disk_set
        
        self.assertFalse(db.table_exists(table_name))