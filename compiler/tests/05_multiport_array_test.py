#!/usr/bin/env python2.7
"""
Run a regresion test on a basic array
"""

import unittest
from testutils import header
import sys,os
sys.path.append(os.path.join(sys.path[0],".."))
import globals
import debug
import calibre

OPTS = globals.OPTS

#@unittest.skip("SKIPPING 05_array_test")


class array_test(unittest.TestCase):

    def runTest(self):
        globals.init_openram("config_20_{0}".format(OPTS.tech_name))
        # we will manually run lvs/drc
        OPTS.check_lvsdrc = False
        import multiport
        import tech

        """debug.info(2, "Checking multiport cell")
        tx = multiport.multiport(name="a_multiport",Read_Write_ports=4, Read_Only_ports=2, nmos_width=2 * tech.drc["minwidth_tx"])
        OPTS.check_lvsdrc = True
        self.local_check(tx)"""



        import multiport_array

        debug.info(2, "Testing 3x3 array for multiport cell")
        a = multiport_array.multiport_array(name="multiport_array", Read_Write_ports=1, Read_Only_ports=0,cols=1, rows=1)

        OPTS.check_lvsdrc = True

        self.local_check(a)
        #globals.end_openram()

    def local_check(self, a):
        tempspice = OPTS.openram_temp + "temp.sp"
        tempgds = OPTS.openram_temp + "temp.gds"
        temppdf = OPTS.openram_temp + "temp.pdf"

        a.sp_write(tempspice)
        a.gds_write(tempgds)

        self.assertFalse(calibre.run_drc(a.name, tempgds))
        self.assertFalse(calibre.run_lvs(a.name, tempgds, tempspice))

        #os.remove(tempspice)
        #os.remove(tempgds)


# instantiate a copy of the class to actually run the test
if __name__ == "__main__":
    (OPTS, args) = globals.parse_args()
    del sys.argv[1:]
    header(__file__, OPTS.tech_name)
    unittest.main()
