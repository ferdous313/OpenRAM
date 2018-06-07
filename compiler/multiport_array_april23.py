import debug
import design
import tech
from tech import drc, spice
from vector import vector
from globals import OPTS
from multiport import multiport



class multiport_array(design.design):
    """
    Creates a rows x cols array of memory cells. Assumes bit-lines
    and word line is connected by abutment.
    Connects the word lines and bit lines.
    """

    def __init__(self, name, cols, rows):
        design.design.__init__(self, name)
        debug.info(1, "Creating {0} {1} x {2}".format(self.name, rows, cols))


        self.column_size = cols
        self.row_size = rows
        self.read_write_ports=1
        self.read_only_ports=0
        self.add_pins()
        self.create_layout()
        self.add_labels()
        self.DRC_LVS()

    def add_pins(self):
        #self.read_write_ports
                    
        self.add_pin("BL1[0]")
        self.add_pin("BL_bar1[0]")
        self.add_pin("WL1[0]")
        self.add_pin("vdd")
        self.add_pin("gnd")

    def create_layout(self):
        self.create_cell()
        self.setup_layout_constants()
        self.add_cells()
        self.offset_all_coordinates()

    def setup_layout_constants(self):
        self.vdd_positions = []
        self.gnd_positions = []
        self.BL_positions = []
        self.BR_positions = []
        self.WL_positions = []
        self.height = self.row_size * self.cell.height
        self.width = self.column_size * self.cell.width

    def create_cell(self):
        self.cell = multiport(name="multiport", nmos_width=2 * tech.drc["minwidth_tx"])
        self.add_mod(self.cell)

    def add_cells(self):
        xoffset = 0.0
        for col in range(self.column_size):
            yoffset = 0.0
            for row in range(self.row_size):
                name = "Lima_multiport_r{0}_c{1}: ".format(row, col)

                if row % 2:
                    print(" Creating same side....Row :{0}".format(row))
                    tempy = yoffset 
                    """self.add_label(text="ROOOOWWWW_EVEN_NORMAL{0}".format(row), 
                           layer="metal2",
                           offset=vector( xoffset-5*self.cell.width,tempy))""" 
                    #tempy = yoffset + 1.5*self.cell.height
                    dir_key = "MX"
                else:
                    print(" Creating Flipped side....Row :{0} ".format( row))
                    tempy = yoffset
                    """self.add_label(text="RRRRRROOOOOOOOOOWWWWWWWWWWWWWWW_ODDD_ROTAAAAAAAATE{0}".format(row), 
                           layer="metal2",
                           offset=vector( xoffset-5*self.cell.width,tempy))""" 
                    dir_key = "R0"

                if OPTS.trim_noncritical == True:
                    if row == self.row_size - 1:
                        self.add_inst(name=name,
                                      mod=self.cell,
                                      offset=[xoffset, tempy],
                                      mirror=dir_key)
                        """self.connect_inst([ "RBL_bar1[{0}]".format(col),
                                       "RBL1[{0}]".format(col),
                                       "BL2[{0}]".format(col),
                                       "BL1[{0}]".format(col),
                                       "BL_bar1[{0}]".format(col),
                                       "BL_bar2[{0}]".format(col),
                                       "RBL2[{0}]".format(col),
                                       "RBL_bar2[{0}]".format(col),                                       
                                        "R_Row1[{0}]".format(row),
                                       "R_Row2[{0}]".format(row),
                                       
                                        "WL1[{0}]".format(row),
                                       "WL2[{0}]".format(row),
                                        "vdd",
                                        "gnd"])"""

                else:
                    self.add_inst(name=name,
                                  mod=self.cell,
                                  offset=[xoffset, tempy],
                                  mirror=dir_key)

                   
                    self.connect_inst(["BL1[{0}]".format(col),"BL_bar1[{0}]".format(col),"WL1[{0}]".format(row),"vdd", "gnd"])

                    if row%2:
                        #current is :normal
                        yoffset +=5*self.cell.height
                    else:
                        #current is :rotated
                        #yoffset += 2.3*self.cell.height
                        yoffset += 2.5*self.cell.height+drc["minwidth_metal1"]*.5
            #xoffset += 6.5*self.cell.width
            xoffset += 2.5*self.cell.width
    def add_labels(self):
        offset = vector(0.0, 0.0)
        offset_Q_Q_bar = vector(0.0, 0.0)
        offset_net = vector(0.0, 0.0)
        extra=vector(drc["minwidth_metal1"],2*drc["minwidth_metal1"])
        #extra=offset

        """for col in range(self.column_size):
           self.add_label(text="Q[{0}]".format(col),
                                       layer="metal1",
                                       offset= offset_Q_Q_bar + self.cell.Q_positions[0])
           self.add_label(text="Q_bar[{0}]".format(col),
                                       layer="metal1",
                                       offset= offset_Q_Q_bar + self.cell.Q_bar_positions[0])
           offset_Q_Q_bar.x += 6*self.cell.width"""




        for col in range(self.column_size):
            offset.y = 0.0
            for no in range(self.read_only_ports):
                self.add_label(text="RBL_bar{0}[{1}]".format(no+1,col),
                           layer="metal2",
                               offset=offset + self.cell.RBL_bar_positions[no])
                self.add_label(text="RBL{0}[{1}]".format(no+1,col),
                           layer="metal2",
                               offset=offset + self.cell.RBL_positions[no])"""

            for no in range(self.read_write_ports):
                self.add_label(text="BL{0}[{1}]".format(no+1,col),
                           layer="metal2",
                               offset=offset + self.cell.BL_positions[no])
                self.add_label(text="BL_bar{0}[{1}]".format(no+1,col),
                           layer="metal2",
                               offset=offset + self.cell.BL_bar_positions[no])

            """for no in range(self.read_only_ports): 
                                self.add_label(text="net{0}[{1}]".format(no+1,col),
                                       layer="metal1",
                                       offset= offset + self.cell.NET_positions[no])""" 

            #for row_no in range(self.read_write_ports):
            """for no in range(self.read_only_ports): 
                                self.add_label(text="net{0}[{1}]".format(no+1,col),
                                       layer="metal1",
                                       offset= offset + self.cell.NET_positions[no])"""


            

            for row in range(self.row_size):
                # only add row labels on the left most column
                if col == 0:
                    # flipped row
                    if row % 2:
                        base_offset = offset + vector(0, self.cell.height)
                        gnd_offset = base_offset -self.cell.gnd_position_extended
                        self.add_label(text="gnd",
                                   layer="metal1",
                                       offset=vector(gnd_offset.x-2.5*self.cell.height,gnd_offset.y-self.cell.height))
                        vdd_offset = base_offset -self.cell.vdd_position_extended
                        self.add_label(text="vdd",
                                   layer="metal1",
                                       offset=vector(vdd_offset.x-2.5*self.cell.height,vdd_offset.y-self.cell.height))
                        R_row1_offset =vector(gnd_offset.x-2.5*self.cell.height,gnd_offset.y-self.cell.height)
                        for no in range(self.read_only_ports):
                            R_row1_offset.y=R_row1_offset.y+2.3*drc["minwidth_metal1"]
                            self.add_label(text="R_Row{0}[{1}]".format(no+1,row),
                                       layer="metal1",
                                           offset=vector(R_row1_offset.x,R_row1_offset.y))
                            self.offset_R_row_final=vector(R_row1_offset.x,R_row1_offset.y)
                        self.WL_offset=self.offset_R_row_final.y+self.cell.pmos1.height*2-drc["metal1_to_metal1"]
                        for no in range(self.read_write_ports):  
                            self.add_label(text="WL{0}[{1}]".format(no+1,row),
                                           layer="metal1",
                                           offset=vector(self.offset_R_row_final.x,self.WL_offset)) 
                            self.WL_offset=self.WL_offset+3*drc["metal1_to_metal1"]


                       
                    # unflipped row
                    else:
                        gnd_offset = offset + self.cell.gnd_position_extended
                        # add vdd label and offset
                        self.add_label(text="gnd",
                                   layer="metal1",
                                       offset=vector(gnd_offset.x-3*self.read_only_ports*drc["metal1_to_metal1"]-.5*drc["minwidth_metal1"],gnd_offset.y))
                        self.gnd_positions.append(gnd_offset)
                        vdd_offset = offset+self.cell.vdd_position_extended
                        self.add_label(text="vdd",
                                   layer="metal1",
                                       offset=vector(vdd_offset.x,vdd_offset.y))
                        R_row1_offset =vector(gnd_offset.x-3*self.read_only_ports*drc["metal1_to_metal1"]-.5*drc["minwidth_metal1"],gnd_offset.y)
                        for no in range(self.read_only_ports):
                            gnd_offset.y=gnd_offset.y-2.3*drc["minwidth_metal1"]
                            self.add_label(text="R_Row{0}[{1}]".format(no+1,row),
                                       layer="metal1",
                                       offset=vector(R_row1_offset.x,gnd_offset.y))
                        for no in range(self.read_write_ports):  
                            self.add_label(text="WL{0}[{1}]".format(no+1,col),
                                           layer="metal1",
                                           offset=offset + self.cell.WL_positions[no])

                       

                        """for col in range(self.column_size): 
                            
                            for no in range(self.read_only_ports): 
                                self.add_label(text="net{0}[{1}]".format(no+1,row),
                                       layer="metal1",
                                       offset= offset_net + self.cell.NET_positions[no]) 
                        offset_net.x += 6*self.cell.width"""




                    # add gnd label and offset
                    """self.add_label(text="wl[{0}]".format(row),
                                   layer="metal1",
                                   offset=wl_offset)
                    self.WL_positions.append(wl_offset)"""
                    # increments to the next row heigh
                    if row%2:
                        #current is :normal
                        offset.y +=5*self.cell.height
                    else:
                        #current is :rotated
                        #yoffset += 2.3*self.cell.height
                        offset.y += 2.5*self.cell.height+drc["minwidth_metal1"]*.5
            # increments to the next column width            
            offset.x += 2.5*self.cell.width
           
    def delay(self, slope, load=0):
        from tech import drc
        wl_wire = self.gen_wl_wire()
        wl_wire.return_delay_over_wire(slope)

        wl_to_cell_delay = wl_wire.return_delay_over_wire(slope)
        # hypothetical delay from cell to bl end without sense amp
        bl_wire = self.gen_bl_wire()
        cell_load = 2 * bl_wire.return_input_cap() # we ingore the wire r
                                                   # hence just use the whole c
        bl_swing = 0.1
        cell_delay = self.cell.delay(wl_to_cell_delay.slope, cell_load, swing = bl_swing)

        #we do not consider the delay over the wire for now
        #bl_wire_delay = bl_wire.return_delay_over_wire(cell_delay.slope, swing = bl_swing)
        #return [wl_to_cell_delay, cell_delay, bl_wire_delay]
        #return self.return_delay(cell_delay.delay+wl_to_cell_delay.delay+bl_wire_delay.delay,
        #                         bl_wire_delay.slope)
        return self.return_delay(cell_delay.delay+wl_to_cell_delay.delay,
                                 wl_to_cell_delay.slope)

    def gen_wl_wire(self):
        wl_wire = self.generate_rc_net(int(self.column_size), self.width, drc["minwidth_metal1"])
        wl_wire.wire_c = 2*spice["min_tx_gate_c"] + wl_wire.wire_c # 2 access tx gate per cell
        return wl_wire

    def gen_bl_wire(self):
        bl_pos = 0
        bl_wire = self.generate_rc_net(int(self.row_size-bl_pos), self.height, drc["minwidth_metal1"])
        bl_wire.wire_c =spice["min_tx_c_para"] + bl_wire.wire_c # 1 access tx d/s per cell
        return bl_wire

    def output_load(self, bl_pos=0):
        bl_wire = self.gen_bl_wire()
        return bl_wire.wire_c # sense amp only need to charge small portion of the bl
                              # set as one segment for now

    def input_load(self):
        wl_wire = self.gen_wl_wire()
        return wl_wire.return_input_cap()
