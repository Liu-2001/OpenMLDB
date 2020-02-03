# -*- coding: utf-8 -*-
from testcasebase import TestCaseBase
import time
import os
import libs.conf as conf
from libs.test_loader import load
import libs.utils as utils
from libs.logger import infoLogger
from libs.deco import multi_dimension
import libs.ddt as ddt

@ddt.ddt
class TestOfflineEndpoint(TestCaseBase):
    @ddt.data(
        ['kSSD'],
        ['kHDD'],
    )
    @ddt.unpack
    def test_offlineendpoint_master_killed(self,storage_mode):
        """
        offlineendpoint功能正常，主节点挂掉后，可以手工故障切换，切换后可put及同步数据
        :return:
        """
        self.start_client(self.leader)
        metadata_path = '{}/metadata.txt'.format(self.testpath)
        name = 'tname{}'.format(time.time())
        # m = utils.gen_table_metadata(
        #     '"{}"'.format(name), None, 144000, 2,
        #     ('table_partition', '"{}"'.format(self.leader), '"0-3"', 'true'),
        #     ('table_partition', '"{}"'.format(self.slave1), '"1-2"', 'false'),
        #     ('table_partition', '"{}"'.format(self.slave2), '"2-3"', 'false'),
        #     ('column_desc', '"k1"', '"string"', 'true'),
        #     ('column_desc', '"k2"', '"string"', 'false'),
        #     ('column_desc', '"k3"', '"string"', 'false')
        # )
        # utils.gen_table_metadata_file(m, metadata_path)

        table_meta = {
            "name": name,
            "ttl": 144000,
            "storage_mode": storage_mode,
            "table_partition": [
                {"endpoint": self.leader,"pid_group": "0-3","is_leader": "true"},
                {"endpoint": self.slave1,"pid_group": "1-2","is_leader": "false"},
                {"endpoint": self.slave2,"pid_group": "2-3","is_leader": "false"},
            ],
            "column_desc":[
                {"name": "k1", "type": "string", "add_ts_idx": "true"},
                {"name": "k2", "type": "string", "add_ts_idx": "false"},
                {"name": "k3", "type": "string", "add_ts_idx": "false"},
            ],
        }
        utils.gen_table_meta_file(table_meta, metadata_path)
        rs0 = self.ns_create(self.ns_leader, metadata_path)
        self.assertIn('Create table ok', rs0)

        rs1 = self.showtable(self.ns_leader, name)
        tid = rs1.keys()[0][1]

        self.stop_client(self.leader)
        time.sleep(5)

        self.offlineendpoint(self.ns_leader, self.leader)
        time.sleep(10)

        rs2 = self.showtable(self.ns_leader, name)
        self.start_client(self.leader)
        time.sleep(1)

        # showtable ok
        self.assertEqual(rs2[(name, tid, '1', self.leader)], ['leader', '144000min', 'no', 'kNoCompress'])
        self.assertEqual(rs2[(name, tid, '2', self.leader)], ['leader', '144000min', 'no', 'kNoCompress'])
        self.assertEqual(rs2[(name, tid, '3', self.leader)], ['leader', '144000min', 'no', 'kNoCompress'])
        self.assertEqual(rs2[(name, tid, '1', self.slave1)], ['leader', '144000min', 'yes', 'kNoCompress'])
        act1 = rs2[(name, tid, '2', self.slave1)]
        act2 = rs2[(name, tid, '2', self.slave2)]
        roles = [x[0] for x in [act1, act2]]
        self.assertEqual(roles.count('leader'), 1)
        self.assertEqual(roles.count('follower'), 1)
        self.assertEqual(rs2[(name, tid, '3', self.slave2)], ['leader', '144000min', 'yes', 'kNoCompress'])

        # put and sync ok
        leader_new = self.slave1 if 'leader' in act1 else self.slave2
        follower = self.slave1 if 'follower' in act1 else self.slave2
        rs2 = self.put(self.slave1, tid, 1, '', self.now(), 'pk1' ,'v2', 'v3')
        self.assertIn('Put ok', rs2)
        rs3 = self.put(self.slave2, tid, 3, '', self.now(), 'pk1' ,'v2', 'v3')
        self.assertIn('Put ok', rs3)
        rs4 = self.put(leader_new, tid, 2, '', self.now(), 'pk1' ,'v2', 'v3')
        self.assertIn('Put ok', rs4)
        time.sleep(1)
        self.assertIn('v2', self.scan(follower, tid, 2, {'k1': 'pk1'}, self.now(), 1))
        self.ns_drop(self.ns_leader, name)

    @ddt.data(
        ['kSSD'],
        ['kHDD'],
    )
    @ddt.unpack
    def test_offlineendpoint_slave_killed(self,storage_mode):
        """
        offlineendpoint功能正常，从节点挂掉后，副本可以被删掉
        :return:
        """
        metadata_path = '{}/metadata.txt'.format(self.testpath)
        name = 'tname{}'.format(time.time())
        infoLogger.info(name)

        table_meta = {
            "name": name,
            "ttl": 144000,
            "storage_mode": storage_mode,
            "table_partition": [
                {"endpoint": self.leader,"pid_group": "0-3","is_leader": "true"},
                {"endpoint": self.slave1,"pid_group": "1-2","is_leader": "false"},
                {"endpoint": self.slave2,"pid_group": "2-3","is_leader": "false"},
            ]
        }
        utils.gen_table_meta_file(table_meta, metadata_path)
        rs0 = self.ns_create(self.ns_leader, metadata_path)
        self.assertIn('Create table ok', rs0)

        rs1 = self.showtable(self.ns_leader, name)
        tid = rs1.keys()[0][1]

        self.stop_client(self.slave1)
        time.sleep(5)

        self.offlineendpoint(self.ns_leader, self.slave1)
        time.sleep(10)

        rs2 = self.showtable(self.ns_leader, name)
        # showtable ok
        self.assertEqual(rs2[(name, tid, '1', self.leader)], ['leader', '144000min', 'yes', 'kNoCompress'])
        self.assertEqual(rs2[(name, tid, '2', self.leader)], ['leader', '144000min', 'yes', 'kNoCompress'])
        self.assertEqual(rs2[(name, tid, '3', self.leader)], ['leader', '144000min', 'yes', 'kNoCompress'])
        self.assertEqual(rs2[(name, tid, '1', self.slave1)], ['follower', '144000min', 'no', 'kNoCompress'])
        self.assertEqual(rs2[(name, tid, '2', self.slave1)], ['follower', '144000min', 'no', 'kNoCompress'])
        self.assertEqual(rs2[(name, tid, '2', self.slave2)], ['follower', '144000min', 'yes', 'kNoCompress'])
        self.assertEqual(rs2[(name, tid, '3', self.slave2)], ['follower', '144000min', 'yes', 'kNoCompress'])
        self.ns_drop(self.ns_leader, name)


    @ddt.data(
        ['kSSD'],
        ['kHDD'],
    )
    @ddt.unpack
    def test_offlineendpoint_alive(self,storage_mode):
        """
        offlineendpoint传入alive状态节点, 执行成功
        :return:
        """
        metadata_path = '{}/metadata.txt'.format(self.testpath)
        name = 'tname{}'.format(time.time())
        table_meta = {
            "name": name,
            "ttl": 144000,
            "storage_mode": storage_mode,
            "table_partition": [
                {"endpoint": self.leader,"pid_group": "0-3","is_leader": "true"},
                {"endpoint": self.slave1,"pid_group": "1-2","is_leader": "false"},
                {"endpoint": self.slave2,"pid_group": "2-3","is_leader": "false"},
                {"endpoint": self.leader,"pid_group": "4-6","is_leader": "false"},
                {"endpoint": self.slave1,"pid_group": "4-6","is_leader": "true"},
            ],
            "column_desc":[
                {"name": "k1", "type": "string", "add_ts_idx": "true"},
                {"name": "k2", "type": "string", "add_ts_idx": "false"},
                {"name": "k3", "type": "string", "add_ts_idx": "false"},
            ],
        }
        utils.gen_table_meta_file(table_meta, metadata_path)
        rs1 = self.ns_create(self.ns_leader, metadata_path)
        self.assertIn('Create table ok', rs1)
        rs = self.showtable(self.ns_leader, name)
        tid = rs.keys()[0][1]

        rs = self.put(self.leader, tid, 1, '', self.now(), 'pk1' ,'v2', 'v3')
        self.assertIn('Put ok', rs)
        rs = self.put(self.leader, tid, 2, '', self.now(), 'pk2' ,'v5', 'v6')
        self.assertIn('Put ok', rs)
        time.sleep(1)

        rs2 = self.offlineendpoint(self.ns_leader, self.leader)
        self.assertIn("offline endpoint ok", rs2)
        time.sleep(10)

        rs3 = self.showtable(self.ns_leader, name)
        self.assertEqual(rs3[(name, tid, '0', self.leader)], ['leader', '144000min', 'no', 'kNoCompress'])
        self.assertEqual(rs3[(name, tid, '1', self.leader)], ['leader', '144000min', 'no', 'kNoCompress'])
        self.assertEqual(rs3[(name, tid, '2', self.leader)], ['leader', '144000min', 'no', 'kNoCompress'])
        self.assertEqual(rs3[(name, tid, '3', self.leader)], ['leader', '144000min', 'no', 'kNoCompress'])
        self.assertEqual(rs3[(name, tid, '1', self.slave1)], ['leader', '144000min', 'yes', 'kNoCompress'])
        self.assertEqual(rs3[(name, tid, '3', self.slave2)], ['leader', '144000min', 'yes', 'kNoCompress'])
        self.assertEqual(rs3[(name, tid, '4', self.leader)], ['follower', '144000min', 'no', 'kNoCompress'])
        self.assertIn('v2', self.scan(self.slave1, tid, 1, {'k1': 'pk1'}, self.now(), 1))
        self.assertIn('v5', self.scan(self.slave1, tid, 2, {'k1': 'pk2'}, self.now(), 1))
        self.ns_drop(self.ns_leader, name)


if __name__ == "__main__":
    load(TestOfflineEndpoint)