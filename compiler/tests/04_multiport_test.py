#!/usr/bin/env python2.7
"""
Run regresion tests on a Multiported sram cell. Here Read_only_ports and Read_write_ports are the configurable ports numbers.
Running Command is:
python2.7 04_multiport_test.py -t scn3me_subm
python2.7 04_multiport_test.py
"""

import unittest
from testutils import header
import sys,os
sys.path.append(os.path.join(sys.path[0],".."))
import globals
import debug
import calibre
import sys

OPTS = globals.OPTS

#@unittest.skip("SKIPPING 04_nand_2_test")


class multiport_test(unittest.TestCase):

    def runTest(self):
        globals.init_openram("config_20_{0}".format(OPTS.tech_name))
        # we will manually run lvs/drc
        OPTS.check_lvsdrc = False

        import multiport
        import tech

        debug.info(2, "Checking multiport cell")
        tx = multiport.multiport(name="a_multiport",Read_Write_ports=4, Read_Only_ports=2,nmos_width=2 * tech.drc["minwidth_tx"])
        OPTS.check_lvsdrc = True
        self.local_check(tx)
        #globals.end_openram()
        

    def local_check(self, tx):
        tempspice = OPTS.openram_temp + "temp.sp"
        tempgds = OPTS.openram_temp + "temp.gds"

        tx.sp_write(tempspice)
        tx.gds_write(tempgds)

        self.assertFalse(calibre.run_drc(tx.name, tempgds))
        self.assertFalse(calibre.run_lvs(tx.name, tempgds, tempspice))

        #os.remove(tempspice)
        #os.remove(tempgds)


# instantiate a copy of the class to actually run the test
if __name__ == "__main__":
    (OPTS, args) = globals.parse_args()
    del sys.argv[1:]
    header(__file__, OPTS.tech_name)
    unittest.main()
