# -*- coding: utf-8 -*-
import os
import datetime as dt
import tempfile
import unittest

import numpy as np
import pandas as pd

from QuantStudio.FactorDataBase.ZarrDB import ZarrDB

class TestZarrDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TestZarrDB.TempDir = tempfile.TemporaryDirectory()
        TestZarrDB.TargetTable = "TestTable"
        TestZarrDB.FactorNames = ["Factor0", "Factor1"]
        TestZarrDB.IDs = [("00000%d.SZ" % (i,)) for i in range(3)]
        TestZarrDB.DTs = [dt.datetime(2018,1,1)+dt.timedelta(i) for i in range(4)]
        TestZarrDB.Data = pd.Panel(np.zeros((len(TestZarrDB.FactorNames), len(TestZarrDB.DTs), len(TestZarrDB.IDs))), items=TestZarrDB.FactorNames, major_axis=TestZarrDB.DTs, minor_axis=TestZarrDB.IDs)
        TestZarrDB.FDB = ZarrDB(sys_args={"主目录":TestZarrDB.TempDir.name})
    # 测试连接功能
    def test_1_connect(self):
        self.FDB.connect()
    # 测试写入功能
    def test_2_writeData(self):
        # 创建因子表并写入数据
        self.FDB.writeData(self.Data.iloc[:, 0:2, 0:1], self.TargetTable)
        # 以 update 方式写入数据
        self.Data.iloc[0, 1:3, 0:2] = 1.0
        self.FDB.writeData(self.Data.iloc[:, 1:3, 0:2], self.TargetTable, if_exists="update")
        # 以 append 方式写入数据
        self.Data.iloc[0, 2:4, 2] = 2.0
        self.FDB.writeData(self.Data.iloc[:, 2:4, 0:3], self.TargetTable, if_exists="append")
    # 测试读取功能
    def test_3_readData(self):
        self.assertEqual(self.FDB.TableNames, [self.TargetTable])
        FT = self.FDB.getTable(self.TargetTable)
        self.assertEqual(FT.Name, self.TargetTable)
        FactorNames = FT.FactorNames
        self.assertEqual(FactorNames, self.FactorNames)
        IDs = FT.getID()
        self.assertEqual(IDs, self.IDs)
        DTs = FT.getDateTime()
        self.assertEqual(DTs, self.DTs)
        Data = FT.readData(factor_names=FactorNames, ids=IDs, dts=DTs)
        Data.iloc[0, 0:2, 2] = 0
        Err = (Data.iloc[0] - self.Data.iloc[0]).abs()
        self.assertEqual(Err.max().max(), 0)
        self.assertEqual(Data.iloc[1].abs().sum().sum(), 0)
    # 测试因子表的操作
    def test_4_alterData(self):
        # 重命名因子
        OldFactorName, self.FactorNames[1] = self.FactorNames[1], "New"+self.FactorNames[1]
        self.FDB.renameFactor(self.TargetTable, OldFactorName, self.FactorNames[1])
        self.assertSetEqual(set(self.FDB.getTable(self.TargetTable).FactorNames), set(self.FactorNames))
        # 删除因子
        self.FDB.deleteFactor(self.TargetTable, [self.FactorNames[1]])
        self.assertSetEqual(set(self.FDB.getTable(self.TargetTable).FactorNames), {self.FactorNames[0]})
        # 重命名表
        OldTargetTable, self.TargetTable = self.TargetTable, "New"+self.TargetTable
        self.FDB.renameTable(OldTargetTable, self.TargetTable)
        self.assertTrue(OldTargetTable not in self.FDB.TableNames)
        self.assertTrue(self.TargetTable in self.FDB.TableNames)
        # 删除表
        self.FDB.deleteTable(table_name=self.TargetTable)
        self.assertListEqual(self.FDB.TableNames, [])

if __name__=="__main__":
    unittest.main()