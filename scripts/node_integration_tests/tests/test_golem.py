import unittest

from .base import NodeTestBase


class GolemNodeTest(NodeTestBase, unittest.TestCase):

    def test_regular_task_run(self):
        exit_code = self._run_test('golem.regular_run.RegularRun')
        self.assertEqual(exit_code, 0)

    def test_no_concent(self):
        exit_code = self._run_test('golem.no_concent.NoConcent')
        self.assertEqual(exit_code, 0)

    def test_rpc(self):
        exit_code = self._run_test('golem.rpc_test.RPCTest')
        self.assertEqual(exit_code, 0)

    def test_rpc_mainnet(self):
        exit_code = self._run_test(
            'golem.rpc_test.MainnetRPCTest', '--mainnet')
        self.assertEqual(exit_code, 0)

    def test_task_timeout(self):
        exit_code = self._run_test('golem.task_timeout.TaskTimeoutAndRestart')
        self.assertEqual(exit_code, 0)

    def test_exr(self):
        exit_code = self._run_test('golem.exr.RegularRun')
        self.assertEqual(exit_code, 0)

    def test_jpeg(self):
        exit_code = self._run_test('golem.jpeg.RegularRun')
        self.assertEqual(exit_code, 0)

    def test_jpg(self):
        exit_code = self._run_test('golem.jpg.RegularRun')
        self.assertEqual(exit_code, 0)

