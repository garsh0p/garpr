import os
import unittest
import time
from garprLogging.log import Log
from time import strftime, localtime

LOG_FLAG = False
TEST_DIR1 = os.path.join(os.path.dirname(__file__), '../config')
TEST_DIR2 = os.path.dirname(__file__)
TEST_DIR3 = None
TEST_NAME = 'testlog.log'
TEST_STRING = 'This is a test. Hello World. Unplug your controller dawg, unplug your controller'
DEFAULT_PATH = '../garprLogging/garpr.log'

class TestLog(unittest.TestCase):

    def setUp(self):
        self.LOG_FLAG = False
        self.log1 = Log(TEST_DIR1, TEST_NAME)
        self.log2 = Log(TEST_DIR2, TEST_NAME)
        self.log3 = Log(TEST_DIR3, TEST_NAME)
        print 'setup complete'

    def tearDown(self):
        print 'teardown'
        if(os.path.exists(os.path.join(TEST_DIR1, TEST_NAME))):
            os.remove(os.path.join(TEST_DIR1, TEST_NAME))
        if (os.path.exists(os.path.join(TEST_DIR2, TEST_NAME))):
            os.remove(os.path.join(TEST_DIR2, TEST_NAME))

        # THIS IS SUPPOSED TO DELETE THE LAST LINES IN THE DEFAULT LOG FILE (MADE BY THE TESTS)
        # TODO Doesn't work but really should. Doesn't hurt for now
        print self.LOG_FLAG
        if self.LOG_FLAG is True:
            if os.path.exists(os.path.join(os.path.dirname(__file__), '../garprLogging/garpr.log')):
                line = None
                lines = None
                # REBUILD DEFAULT LOG FILE
                with open(os.path.join(os.path.dirname(__file__), '../garprLogging/garpr.log'), 'r') as f:
                    lines = f.readlines()
                    f.close()
                with open(os.path.join(os.path.dirname(__file__), '../garprLogging/garpr.log'), 'r+') as f:
                    f.writelines([item for item in lines[:len(lines)-1]])
                    f.close()
        print 'teardown complete'

    def test_write_file1(self):
        self.log1.write(TEST_STRING)
        logtime = str(time.strftime("%Y-%m-%d %H:%M", localtime()))
        l = None
        with open(os.path.join(TEST_DIR1, TEST_NAME), 'r') as f:
            for line in f:
                l = line
                break
            f.close()

        self.assertEqual(logtime in str(l) and TEST_STRING in str(l), True)

    def test_write_file2(self):
        self.log2.write(TEST_STRING)
        logtime = str(time.strftime("%Y-%m-%d %H:%M", localtime()))
        l = None
        with open(TEST_NAME, 'r') as f:
            for line in f:
                l = line
                break
            f.close()

        self.assertEqual(logtime in str(l) and TEST_STRING in str(l), True)

    def test_write_default1(self):
        Log.log('TEST', 'THIS IS A TEST')
        logtime = str(time.strftime("%Y-%m-%d %H:%M", localtime()))
        l = None
        with open(os.path.join(os.path.dirname(__file__), DEFAULT_PATH), 'r') as f:
            for line in f:
                l = line
            f.close()
        self.assertEqual(logtime in str(l) and '[TEST]' in str(l) and 'THIS IS A TEST' in str(l), True)
        self.LOG_FLAG = True

    def test_write_default2(self):
        Log.log(None, 'THIS IS A TEST')
        logtime = str(time.strftime("%Y-%m-%d %H:%M", localtime()))
        l = None
        with open(os.path.join(os.path.dirname(__file__), DEFAULT_PATH), 'r') as f:
            for line in f:
                l = line
            f.close()
        self.assertEqual(logtime in str(l) and 'THIS IS A TEST' in str(l), True)
        self.LOG_FLAG = True

