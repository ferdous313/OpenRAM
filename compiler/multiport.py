import contact
import design
import debug
from tech import drc, parameter, spice
from ptx import ptx
from vector import vector
from globals import OPTS

class multiport(design.design):
    """
    This module generates gds of a dynamically configured multiported sram cell.
    
    """

    c = reload(__import__(OPTS.config.bitcell))
   
    bitcell = getattr(c, OPTS.config.bitcell)
   
    chars=["BL","WL"]
    def __init__(self, name,Read_Write_ports,Read_Only_ports, nmos_width=1,height=bitcell.chars["height"]):
   
        """ Constructor """
        design.design.__init__(self, name)
        debug.info(2, "create multiport strcuture {0} with size of {1}".format(
            name, nmos_width))

        self.nmos_width = nmos_width
        self.height = height
        
        #range(1-20): Read Write number of transisters/ports
        self.down_ptx_no=Read_Write_ports
        #range (0-15)/ Read Only Ports
        self.no_read_only_port=Read_Only_ports
        self.read_only_ports=self.no_read_only_port
        self.add_pins()
        self.create_layout()
        self.DRC_LVS()

    def add_pins(self):
        """ Add pins """
        self.add_pin_list(["vdd", "gnd"])
        i=1
        while (i<=self.down_ptx_no):
            self.add_pin_list(["BL{0}".format(i),"BL_bar{0}".format(i)])
            self.add_pin_list(["WL{0}".format(i)])
            i=i+1
 
        j=1
        while(j<=self.no_read_only_port):
            #self.add_pin_list(["net{0}".format(j)])
            self.add_pin_list(["R_Row{0}".format(j)])
            self.add_pin_list(["RBL{0}".format(j)])
            self.add_pin_list(["RBL_bar{0}".format(j)])
            j=j+1



    def create_layout(self):
        """ Layout """
        self.determine_sizes()
        self.create_ptx()
        self.setup_layout_constants()
        self.add_rails()
        self.add_ptx()
        self.constant_for_lenght()
        self.add_and_create_down_ptx()
       
        self.add_well_contacts()

        # This isn't instantiated, but we use it to get the dimensions
        self.poly_contact = contact.contact(("poly", "contact", "metal1"))

        #self.connect_well_contacts_lima()
        self.connect_rails()
        self.connect_well_contacts()
        self.connect_tx()
        self.route_pins()
       
        self.Side_PTX_add_and_create_side_ptx()
        self.extend_wells()
        self.extend_active()
       
        self.extend_rails()
       
        self.extend_Q_and_Q_bar()
    # Determine transistor size
    def determine_sizes(self):
        """ Determine the size of the transistors """
        self.nmos_size = self.nmos_width
        self.pmos_size = self.nmos_width
        self.tx_mults = 1

    # transistors are created here but not yet placed or added as a module
    def create_ptx(self):
        """ Add required modules """
        self.nmos1 = ptx(width=self.nmos_size,
                         mults=self.tx_mults,
                         tx_type="nmos")
        self.add_mod(self.nmos1)
        self.nmos2 = ptx(width=self.nmos_size,
                         mults=self.tx_mults,
                         tx_type="nmos")
        self.add_mod(self.nmos2)

        self.pmos1 = ptx(width=self.pmos_size,
                         mults=self.tx_mults,
                         tx_type="pmos")
        self.add_mod(self.pmos1)
        self.pmos2 = ptx(width=self.pmos_size,
                         mults=self.tx_mults,
                         tx_type="pmos")
        self.add_mod(self.pmos2)

    def setup_layout_constants(self):
        """ Calculate the layout constraints """
        self.well_width = self.pmos1.active_position.x \
            + 2 * self.pmos1.active_width \
            + drc["active_to_body_active"] + \
            drc["well_enclosure_active"]+drc["well_enclosure_active"]

        self.width = self.well_width

    def add_rails(self):
        """ add power rails """
        rail_width = self.width
        rail_height = drc["minwidth_metal1"]
        self.rail_height = rail_height
        # Relocate the origin
        self.gnd_position = vector(0, - 19*drc["metal1_to_metal1"])
        

        self.vdd_position = vector(0, self.height*1.3 )
        

   

    def add_well_contacts(self):
        """  Create and add well copntacts """
        # create well contacts
        layer_stack = ("active", "contact", "metal1")

        xoffset = (self.nmos_position2.x + self.pmos1.active_position.x 
                   + self.pmos1.active_width + drc["active_to_body_active"])
        yoffset = (self.pmos_position1.y +
                  self.pmos1.active_contact_positions[0].y)
        offset = self.nwell_contact_position = vector(xoffset, yoffset)
        self.pwell_contact=self.add_contact(layer_stack,offset,(1,self.nmos1.num_of_tacts))

        xoffset = (self.nmos_position2.x + self.nmos1.active_position.x
                   + self.nmos1.active_width + drc["active_to_body_active"])
        yoffset = (self.nmos_position1.y + self.nmos1.height
                   - self.nmos1.active_contact_positions[0].y
                   - self.nmos1.active_contact.height)
        offset = self.pwell_contact_position = vector(xoffset, yoffset)
        self.nwell_contact=self.add_contact(layer_stack,offset,(1,self.pmos1.num_of_tacts))

    

   

    def connect_tx(self):
        """ Connect tx poly znd drains """
        self.connect_poly()
        self.connect_drains_working()

    def connect_poly(self):
        """ poly connection """
        yoffset_nmos1 = (self.nmos_position1.y 
                            + self.nmos1.poly_positions[0].y 
                            + self.nmos1.poly_height)
        poly_length = (self.pmos_position1.y + self.pmos1.poly_positions[0].y 
                          - yoffset_nmos1 + drc["minwidth_poly"])
        for position in self.pmos1.poly_positions:
            offset = vector(position.x,
                            yoffset_nmos1 - 0.5 * drc["minwidth_poly"])
            self.add_rect(layer="poly",
                          offset=offset, width=drc["minwidth_poly"],
                          height=poly_length)
            self.add_rect(layer="poly",
                          offset=[offset.x + self.pmos1.active_contact.width + 2.7 * drc["minwidth_poly"],
                                  offset.y-2*drc["minwidth_metal1"]],
                          width=drc["minwidth_poly"],
                          height=poly_length+4*drc["minwidth_metal1"])

    def connect_drains(self):
        """  Connect pmos and nmos drains. The output will be routed to this connection point. """
        yoffset = self.nmos_position1.y + self.nmos1.active_contact_positions[0].y
        drain_length = (self.height + self.pmos1.active_contact_positions[0].y 
                        - yoffset - self.pmos1.height + 0.5 * drc["minwidth_metal2"])

        for position in self.pmos1.active_contact_positions[1:][::2]:
            start = self.drain_position = vector(position.x + 0.5 * drc["minwidth_metal1"] 
                                                + self.pmos_position2.x 
                                                + self.pmos2.active_contact.first_layer_position.x 
                                                + self.pmos2.active_contact.width / 2, 
                                           yoffset)
            mid1 = vector(start.x,
                    self.height - drc["minwidth_metal2"] - drc["metal2_to_metal2"] -
                    self.pmos_size - drc["metal1_to_metal1"] - 0.5 * drc["minwidth_metal1"])
            end = vector(position.x + 0.5 * drc["minwidth_metal1"]
                       + self.pmos2.active_contact.second_layer_position.x,
                   self.pmos_position1.y + self.pmos1.active_contact_positions[0].y)
            mid2 = vector(end.x, mid1.y)

            self.add_path("metal1",[start, mid1, mid2, end])

    def route_pins(self):
        """ Routing """
        self.route_input_gate()
       

    def route_input_gate(self):
        """ Gate routing """
        self.route_input_gate_A_Q()
        self.route_input_gate_B_Q_bar()


   

    def extend_active(self):
        """ Extension of active region """
        self.active_width = (self.pmos1.active_width
                                + drc["active_to_body_active"] 
                                + self.pmos1.active_contact.width)
        offset = (self.pmos1.active_position
                     + self.pmos_position2.scale(1,0)
                     + self.pmos_position1.scale(0,1))
        self.add_rect(layer="active",
                      offset=offset,
                      width=self.active_width,
                      height=self.pmos1.active_height)

        offset = offset + vector(self.pmos1.active_width, 0)
        width = self.active_width - self.pmos1.active_width
        self.add_rect(layer="nimplant",
                      offset=offset,
                      width=width,
                      height=self.pmos1.active_height)

        offset = vector(self.nmos_position2.x + self.nmos1.active_position.x,
                        self.nmos_position1.y - self.nmos1.active_height
                            - self.nmos1.active_position.y + self.nmos1.height)
        self.add_rect(layer="active",
                      offset=offset,
                      width=self.active_width,
                      height=self.nmos1.active_height)

        offset = offset + vector(self.nmos1.active_width,0)
        width = self.active_width - self.nmos1.active_width
        self.add_rect(layer="pimplant",
                      offset=offset,
                      width=width,
                      height=self.nmos1.active_height)

    def setup_layout_offsets(self):
        """ Defining the position of i/o pins """
        #self.A_position = self.A_position = self.input_position1
        #self.B_position = self.B_position = self.input_position2
        #self.Z_position = self.Z_position = self.output_position
        self.vdd_position = self.vdd_position
        self.gnd_position = self.gnd_position

    def input_load(self):
        from tech import spice
        return ((self.nmos_size+self.pmos_size)/parameter["min_tx_size"])*spice["min_tx_gate_c"]

    def delay(self, slope, load=0.0):
        r = spice["min_tx_r"]/(self.nmos_size/parameter["min_tx_size"])
        c_para = spice["min_tx_c_para"]*(self.nmos_size/parameter["min_tx_size"])#ff
        return self.cal_delay_with_rc(r = r, c =  c_para+load, slope =slope)

    def connect_drains_working(self):
       
        
        """pmos1 and nmos1 drain connected"""
        yoffset = self.pmos_position1.y
        start = self.nmos1_drain_position=vector( self.nmos1.active_contact_positions[0].x+.3*drc["minwidth_metal1"],self.nmos1.active_contact_positions[0].y-1*drc["minwidth_metal1"])
        end= self.pmos1_drain_position=vector(self.pmos1.active_contact_positions[0].x+.3*drc["minwidth_metal1"] ,self.pmos_position1.y+self.pmos1.active_contact_positions[0].y+1.7*drc["minwidth_metal1"])
        self.drain1_position_x= self.nmos1.active_contact_positions[0].x+.7*drc["minwidth_metal1"]
        self.add_path("metal1",[start, end])


        yoffset_drain = self.pmos1_drain_position.y
        via_offset=vector(self.pmos1.active_contact_positions[0].x  
                                                + self.pmos_position1.x 
                                                + self.pmos1.active_contact.first_layer_position.x 
                                                + self.pmos1.active_contact.width / 2
                                                - .5 * drc["minwidth_metal1"],
                                                 yoffset_drain-2*drc["minwidth_metal1"])



       
       


        """pmos2 and nmos2 drain connected"""
        yoffset = self.pmos_position1.y
        start = self.nmos2_drain_position= vector( self.nmos2.active_contact_positions[1].x+drc["minwidth_metal1"]*1.1+self.nmos_position2.x,self.nmos1.active_contact_positions[0].y-1*drc["minwidth_metal1"])
        end= self.pmos2_drain_position= vector(self.pmos2.active_contact_positions[1].x+drc["minwidth_metal1"]*1.1+self.pmos_position2.x,self.pmos_position1.y+self.pmos1.active_contact_positions[0].y+1.7*drc["minwidth_metal1"])
       
        self.add_path("metal1",[start, end])

        #yoffset_drain = self.pmos2_drain_position.y
        via_offset=vector(self.pmos2.active_contact_positions[1].x  
                                                + self.pmos_position2.x 
                                                + self.pmos2.active_contact.first_layer_position.x 
                                                + self.pmos2.active_contact.width / 2
                                                - .5 * drc["minwidth_metal1"],
                                                 yoffset_drain-2*drc["minwidth_metal1"])



    def connect_rails(self):
        """  Connect transistor pmos drains to vdd and nmos drains to gnd rail """
        correct = vector(self.pmos1.active_contact.width ,
                         0).scale(.5,0)
        poffset = self.pmos_position1 + self.pmos1.active_contact_positions[1] + correct
        temp_height = self.height - poffset.y
       

        poffset = vector(2 * self.pmos_position2.x + correct.x
                         + self.pmos2.active_contact_positions[1].x , poffset.y-3*drc["minwidth_metal1"])
       
        pos1=vector(poffset.x,self.vdd_position.y)
        

        poffset = self.gnd_height_origin=self.nmos_position1 + self.nmos1.active_contact_positions[1] 
        temp_height=self.gnd_height=self.gnd_position.y - self.nmos1.active_contact_positions[1].y-self.nmos_position1.y-drc["minwidth_metal1"]
        self.add_rect(layer="metal1",
                      offset=vector(poffset.x,poffset.y+drc["metal1_to_metal1"]),
                      width=drc["minwidth_metal1"],
                      height=temp_height)

       

    def route_input_gate_A_Q(self):
        """ routing for input A """
        correct=drc["metal1_to_metal1"]+drc["minwidth_metal1"]
        xoffset=self.drain1_position_x+correct
        yoffset = (self.height 
                       - (drc["minwidth_metal1"] 
                              + drc["metal1_to_metal1"] 
                              + self.pmos2.active_height 
                              + drc["metal1_to_metal1"] 
                              + self.pmos2.active_contact.second_layer_width
                              + .2*drc["metal1_to_metal1"]))

        if (self.nmos_width == drc["minwidth_tx"]):
            yoffset = (self.pmos_position1.y 
                        + self.pmos1.poly_positions[0].y
                        + drc["poly_extend_active"] 
                        - (self.pmos1.active_contact.height 
                               - self.pmos1.active_height) / 2 
                        - drc["metal1_to_metal1"]  
                        - self.poly_contact.width)
        #lima
        offset =[xoffset, yoffset]
       

       
        self.contact_Q_position=vector(xoffset-.7*drc["minwidth_metal1"], yoffset-drc["minwidth_metal1"]+drc["metal3_to_metal3"]*3)     
        
        self.add_contact(layers=("poly", "contact", "metal1"),
                         offset=vector(self.contact_Q_position.x,self.contact_Q_position.y+drc["minwidth_metal1"]),
                         size=(1,1),
                         rotate=270)
        

        via_offset =vector(self.contact_Q_position.x,self.contact_Q_position.y+drc["minwidth_metal1"])
        layer_stack_via1 = ["metal1", "via1", "metal2"]   
        self.add_via(layer_stack_via1,via_offset,rotate=270)
        layer_stack_via2 = ["metal2", "via2", "metal3"] 
        self.add_via(layer_stack_via2,via_offset,rotate=270)
    
        yoffset = yoffset - 1.3*drc["metal1_to_metal1"]
        offset = [xoffset+2*drc["minwidth_metal1"], yoffset]
        offset = offset - self.poly_contact.first_layer_position.rotate_scale(-1,0)
        input_length = (self.pmos1.poly_positions[0].x+drc["minwidth_metal1"]) 
        yoffset += self.poly_contact.via_layer_position.x
        offset = self.input_position_Q = vector(xoffset, yoffset-drc["minwidth_metal1"])
        

        self.Q_bar_positions=[]
        self.Q_positions=[]
        
        self.add_rect(layer="metal1",
                      offset=self.contact_Q_position,
                      width=input_length+2*drc["minwidth_metal1"],
                      height=drc["minwidth_metal1"])
        self.position_Q_array=self.contact_Q_position
       
        self.Q_positions.append( self.position_Q_array)
    def route_input_gate_B_Q_bar(self):
        """ routing for input B """
        xoffset = (self.pmos2.poly_positions[0].x
                       + self.pmos_position2.x + .8*drc["minwidth_poly"])
        yoffset = (drc["minwidth_metal1"] 
                       + drc["metal1_to_metal1"]
                       + self.nmos2.active_height
                       + 5.5*drc["minwidth_metal1"])
        if (self.nmos_width == drc["minwidth_tx"]):
            yoffset = (self.nmos_position1.y 
                        + self.nmos1.poly_positions[0].y 
                        + self.nmos1.poly_height 
                        + drc["metal1_to_metal1"])
        offset = [xoffset, yoffset]
        offset=vector(xoffset, yoffset-drc["minwidth_metal1"])
        offset_Q_bar=self.contact_Q_bar_position=vector(xoffset, yoffset)
       


        self.Q_bar_contact_position=vector(xoffset, yoffset)       
        input_length = self.pmos_position2.x- self.pmos_position1.x +self.pmos1.active_contact_positions[0].x
        xoffset= self.pmos1.active_contact_positions[0].x
        self.input_position2 = vector(xoffset+5*drc["minwidth_metal1"],
                                      # + 3*self.poly_contact.width, 
                                      yoffset + self.poly_contact.via_layer_position.x-2*drc["minwidth_metal3"])
        self.input_position_Q_bar=offset_Q_bar
        
       
        self.add_rect(layer="metal1",
                      offset=self.input_position2.scale(.2,1),
                      width=input_length,
                      height=drc["minwidth_metal1"])
        self.position_Q_bar_array=self.input_position2.scale(.5,1)   
       

        self.Q_bar_positions.append( self.position_Q_bar_array)
        self.input_Q_bar=vector(self.input_position2.x+drc["minwidth_metal1"]*.5,self.input_position2.y)
        self.add_contact(layers=("poly", "contact", "metal1"),
                         offset=self.input_Q_bar,
                         size=(1,1),
                         rotate=90)
         
        via_offset = self.input_Q_bar
        self.add_rect(layer="poly",
                      offset=vector(self.input_Q_bar.x-1.5*drc["minwidth_metal1"],self.input_Q_bar.y),
                      width=2*drc["minwidth_poly"],
                      height=2*drc["minwidth_poly"])
        layer_stack_via1 = ["metal1", "via1", "metal2"]   
        self.add_via(layer_stack_via1,via_offset,rotate=90)
        layer_stack_via2 = ["metal2", "via2", "metal3"] 
        self.add_via(layer_stack_via2,via_offset,rotate=90)








    def add_ptx(self):
        """  transistors are added and placed inside the layout         """

        # determines the spacing between the edge and nmos (rail to active
        # metal or poly_to_poly spacing)
        edge_to_nmos = max(drc["metal1_to_metal1"]
                            - self.nmos1.active_contact_positions[0].y,
                           0.5 * (drc["poly_to_poly"] - drc["minwidth_metal1"])
                             - self.nmos1.poly_positions[0].y)

        # determine the position of the first transistor from the left
        self.nmos_position1 = vector(0, 0.5 * drc["minwidth_metal1"] + edge_to_nmos)
        offset = self.nmos_position1+ vector(0,self.nmos1.height)
        self.add_inst(name="nmos1",
                      mod=self.nmos1,
                      offset=offset,
                      mirror="MX")
        #self.connect_inst(["Q_bar", "Q", "gnd", "gnd"])
        self.connect_inst(["gnd", "Q", "Q_bar", "gnd"])
        self.nmos_position2 = vector(self.nmos2.active_width - self.nmos2.active_contact.width+.5*drc["minwidth_metal1"], 
                                     self.nmos_position1.y)
        offset = self.nmos_position2 + vector(0,self.nmos2.height)
        self.add_inst(name="nmos2",
                      mod=self.nmos2,
                      offset=offset,
                      mirror="MX")
        self.connect_inst(["gnd", "Q_bar", "Q", "gnd"])

        # determines the spacing between the edge and pmos
        edge_to_pmos = max(drc["metal1_to_metal1"] \
                               - self.pmos1.active_contact_positions[0].y,
                           0.5 * drc["poly_to_poly"] - 0.5 * drc["minwidth_metal1"] \
                               - self.pmos1.poly_positions[0].y)

        self.pmos_position1 = vector(0, self.height - 0.5 * drc["minwidth_metal1"] 
                                         - edge_to_pmos-self.pmos1.height*.5 )
        #-self.pmos1.height
        self.add_inst(name="pmos1",
                      mod=self.pmos1,
                      offset=self.pmos_position1)
       
        self.connect_inst(["vdd", "Q", "Q_bar", "vdd"])
       
        self.pmos_position2 = vector(self.nmos_position2.x, self.pmos_position1.y)
        self.add_inst(name="pmos2",
                      mod=self.pmos2,
                      offset=self.pmos_position2)
        self.connect_inst(["vdd","Q_bar", "Q","vdd"])
    
    
    def connect_well_contacts(self):
        """  Connect well contacts to vdd and gnd rail """
        well_tap_length = (self.vdd_position.y - self.nwell_contact_position.y)
        offset = vector(self.nwell_contact_position.x 
                        + self.nwell_contact.second_layer_position.x 
                        - self.nwell_contact.first_layer_position.x+drc["minwidth_metal1"],
                        self.nwell_contact_position.y)
        self.add_rect(layer="metal1",
                      offset=offset,
                      width=drc["minwidth_metal1"],
                      height=well_tap_length)

        well_tap_length = self.nmos1.active_height
        #offset = (self.pwell_contact_position.scale(1.05,-.61) 
                       
        
        offset=vector(self.pwell_contact_position.x,self.gnd_height_origin.y+drc["minwidth_metal1"])             
        self.add_rect(layer="metal1",
                      offset=offset, 
                      width=drc["minwidth_metal1"],
                      height=self.gnd_height)


   


   

    def constant_for_lenght(self):

       self.left_end_figure_x= -self.down_ptx_no*self.nmos1.width-self.no_read_only_port*self.nmos1.width
       self.right_end_figure_x= self.down_ptx_no*self.nmos1.width+self.no_read_only_port*self.nmos1.width+self.nmos1.width
       #self.down_ptx_no=8
       #self.no_read_only_port=6
       self.width_figure=self.right_end_figure_x-self.left_end_figure_x

    def add_and_create_down_ptx(self):
        self.WL_positions=[]
        self.BL_positions=[]
        self.BL_bar_positions=[]
        self.initial_cross_nmos_no=2
        self.nmos_down_ptx_names=[]
        for i in range(self.initial_cross_nmos_no+1,self.down_ptx_no+self.initial_cross_nmos_no+1):
            name= "nmos{0}".format(i)
               
            self.nmos_down_ptx_names.append(name)
       
        #for items in self.nmos_down_ptx_names:
            #print items            
       
        """Left ptx no *drc[metal1 to metal1]"""
        count_read_port = self.no_read_only_port
        # i = atleast 1   
        i=0
       
        # determine y offset for the first down nmos 
      
        yoffset=self.gnd_position.y
        while (i<=count_read_port):
            #print i
            yoffset=yoffset-drc["metal1_to_metal1"]*2-drc["minwidth_metal1"]
            self.nmos3_position=vector(self.nmos_position1.x- self.no_read_only_port*drc["metal1_to_metal1"],yoffset)
            i=i+1 
        


        """ mid point determine down"""
        midpoint_down=vector(self.pmos_position2.x+self.pmos2.poly_positions[0].x,self.nmos3_position.y) 

       

        """create down_ptx"""
        self.nmos_down_names= []
        self.nmos_down_positions= []
      
        self.nmos_down_drain_positions= []
        self.source_positions_down_ptx=[]
        """No of nmos access ptx down"""


        self.no_read_write_port= self.down_ptx_no
        count_rd_wr_port = self.no_read_write_port
        poly_length=0
    
        yoffset_poly= self.nmos3_poly_bar_position_y=self.nmos3_position.y-2*self.nmos1.height
       
        """ Adding BL nmos"""   
        viaoffset_y=  self.nmos3_position.y-2*self.nmos1.height+drc["well_enclosure_active"]
        #viaoffset_x=
        xoffset= self.nmos_position1.x+self.nmos1.active_contact_positions[1].x+ self.nmos1.poly_positions[0].x-self.nmos1.width
        yoffset= self.nmos3_position.y-self.nmos1.height
        self.start_of_ptx_position_left_x= xoffset-self.nmos1.width*.5
        #i for while loop i=1
        i=1
        while (i<=count_rd_wr_port and count_rd_wr_port>0):
            """creating down_ptx"""
            name_nmos = "nmos{0}".format(i+2)
            #print(" Creating"+ name_nmos)
            self.nmos_ptx= ptx(width=self.nmos_size,
                           mults=self.tx_mults,
                           tx_type= "nmos")
            self.add_mod (self.nmos_ptx)    
            #print (" Placing nmos{0}".format(i+2))

	    if (i%2==0):
               
                xoffset=xoffset-self.nmos_ptx.active_width-self.nmos_ptx.poly_width+self.nmos_ptx.active_contact.width
            
            else:
               
                xoffset=xoffset-self.nmos1.width
            
            self.nmos3_position=vector(xoffset,yoffset)
            self.nmos_down_positions.append(self.nmos3_position)
           
           
            self.add_inst(name=name_nmos,
                          mod=self.nmos_ptx,
                          offset= self.nmos3_position,
                          mirror="MX")
           
            self.connect_inst([ "BL{0}".format(i),"WL{0}".format(i), "Q_bar","gnd"])
           
            self.nmos_down_names.append(self.nmos_ptx)

            if(i%2!=0):
                
                 xoffset_BL_odd=xoffset+self.nmos_ptx.active_contact_positions[1].x+drc["minwidth_metal1"]*.33
                 self.add_rect(layer="metal2",
                               offset=[xoffset_BL_odd,viaoffset_y-(self.down_ptx_no+3)*drc["metal1_to_metal1"]-self.height],
                               width=drc["minwidth_metal2"],
                              
                               height= self.height*6 )
                 offset_BL=vector(xoffset_BL_odd,viaoffset_y-(self.down_ptx_no+3)*drc["metal1_to_metal1"]-self.height)
                 self.add_label(text="BL{0}".format(i),
                              layer="metal2",
                                offset=[xoffset_BL_odd,viaoffset_y-(self.down_ptx_no+3)*drc["metal1_to_metal1"]-self.height])
                 
                 self.BL_positions.append(offset_BL)

                 """ BL added and via2 only"""

                 via_offset = [xoffset_BL_odd, viaoffset_y]
                 layer_stack_via1 = ["metal1", "via1", "metal2"]   
                 self.add_via(layer_stack_via1,via_offset)            

            else:
                 xoffset_BL_even=xoffset+self.nmos_ptx.active_contact_positions[0].x
                 self.add_rect(layer="metal2",
                               offset=[xoffset_BL_even,viaoffset_y-self.height-(self.down_ptx_no+self.no_read_only_port+3)*drc["metal1_to_metal1"]*2],
                               width=drc["minwidth_metal2"],
                               #height=self.height*(self.down_ptx_no+1)*.5
                               height=self.height*6+(self.no_read_only_port+3)*drc["metal1_to_metal1"]+self.down_ptx_no*drc["metal1_to_metal1"]*2)
                 offset_BL=vector(xoffset_BL_even,viaoffset_y-self.height-(self.down_ptx_no+self.no_read_only_port+13)*drc["metal1_to_metal1"]*2)
                 self.add_label(text="BL{0}".format(i),
                              layer="metal2",
                                offset=[xoffset_BL_even,viaoffset_y-self.height-(self.down_ptx_no+self.no_read_only_port+3)*drc["metal1_to_metal1"]*2])
                 self.BL_positions.append(offset_BL)
                 """ BL_bar added and via2 only """
                 via_offset = [ xoffset_BL_even, viaoffset_y]
                 layer_stack_via1 = ["metal1", "via1", "metal2"]   
                 self.add_via(layer_stack_via1,via_offset)


            """ WL added to poly"""

            """ poly connection extend nmos3  and nmos[i]"""
            xoffset_poly = (xoffset+ self.nmos_ptx.poly_positions[0].x)
            
            
            yoffset_poly = yoffset_poly-3*drc["metal1_to_metal1"]
            poly_length = poly_length +3*drc["metal1_to_metal1"]

            #poly_length= abs(yoffset_poly)+abs(self.nmos_ptx.poly_positions[0].y)
           
           
            offset = vector (xoffset_poly,yoffset_poly )
            self.add_rect(layer="poly",
                          offset=offset,
                          width=drc["minwidth_poly"],
                          height=poly_length+1.3*drc["metal1_to_metal1"])
           
            yoffset_contact=yoffset_poly + drc["metal1_to_metal1"]

            xoffset_contact=xoffset_poly+drc["minwidth_poly"]
            offset_contact = [xoffset_contact, yoffset_contact]
            self.add_contact(layers=("poly", "contact", "metal1"),
                         offset=offset_contact,
                         size=(1,1),
                         rotate=90)
            """ via1 and via2 added to source of ptx"""

            if (i%2!=0):
                 self.source_positions_down_ptx.append(self.nmos3_position)   
                 "nmoS3 via1 and via2 added"
                 viaoffset_x=  self.nmos3_position.x+self.nmos_ptx.active_contact.width+drc["minwidth_metal1"]*.33
                
                 via_offset = vector(viaoffset_x,viaoffset_y)
                 layer_stack_via1 = ["metal1", "via1", "metal2"]   
                 self.add_via(layer_stack_via1,via_offset)
                 layer_stack_via2 = ["metal2", "via2", "metal3"] 
                 self.add_via(layer_stack_via2,via_offset)
                 start=  via_offset
                 end = vector (via_offset.x,self.nmos3_position.y+ drc["metal2_to_metal2"])
                 self.add_path("metal3",[start, end])   
                
            i=i+1

        

        self.end_of_ptx_position_left=vector(self.nmos3_position.x-self.nmos1.width,self.nmos3_position.y)



        """ Right Down nmos: Adding BL_bar nmos"""

        xoffset= midpoint_down.x-drc["minwidth_metal1"]*3
        self.start_of_ptx_position_right_x= xoffset+self.nmos1.width
        #j for while loop j=i for BL_bar ptx
        yoffset_poly_bar=self.nmos3_poly_bar_position_y

        poly_length_bar=0
        j=1
        while (j<=count_rd_wr_port and count_rd_wr_port>0):
            #print (" Placing nmos{0}".format(j))
            if (j%2==0):
               
                xoffset=xoffset+self.nmos_ptx.active_width*.8
            else:
               
                xoffset=xoffset+self.nmos1.width
            
            self.nmos3_position=vector(xoffset,yoffset)

            self.nmos_down_positions.append(self.nmos3_position)
            #creating down_ptx_bar
            name_nmos = "nmos{0}".format(i+j+2)
            #print(" Creating"+ name_nmos)
            self.nmos_ptx=ptx(width=self.nmos_size,
                           mults=self.tx_mults,
                           tx_type= "nmos")
            self.add_mod (self.nmos_ptx)
           
            self.add_inst(name=name_nmos,
                          mod=self.nmos_ptx,
                          offset= self.nmos3_position,
                          mirror="MX")
            self.connect_inst(["BL_bar{0}".format(j),"WL{0}".format(j), "Q","gnd"])
           
            self.nmos_down_names.append(self.nmos_ptx)

            self.nmos_down_names.append(self.nmos_ptx)
            """ Adding BL left and via2 for metal2"""
            if(j%2!=0):
                xoffset_BL_odd=xoffset+self.nmos_ptx.active_contact_positions[0].x
                self.BL_bar_offset=vector(xoffset_BL_odd,viaoffset_y-self.height-(self.down_ptx_no+3)*drc["metal1_to_metal1"])
                self.add_rect(layer="metal2",
                               offset=[xoffset_BL_odd,viaoffset_y-self.height-(self.down_ptx_no+3)*drc["metal1_to_metal1"]],
                               width=drc["minwidth_metal2"],
                             
                               height= self.height*6             )
                self.add_label(text="BL_bar{0}".format(j),
                              layer="metal2",
                               offset=[xoffset_BL_odd,viaoffset_y-self.height-(self.down_ptx_no+3)*drc["metal1_to_metal1"]])

                offset_BL_bar=vector(xoffset_BL_odd,viaoffset_y-self.height-(self.down_ptx_no+3)*drc["metal1_to_metal1"])
                self.BL_bar_positions.append(offset_BL_bar)
                via_offset = [xoffset_BL_odd, viaoffset_y]
                layer_stack_via1 = ["metal1", "via1", "metal2"]   
                self.add_via(layer_stack_via1,via_offset)
            else:
                xoffset_BL_even=xoffset+self.nmos_ptx.active_contact_positions[1].x
                self.BL_bar_offset=vector(xoffset_BL_even,viaoffset_y-self.height-(self.down_ptx_no+3)*drc["metal1_to_metal1"])
                self.add_rect(layer="metal2",
                               offset=[xoffset_BL_even,viaoffset_y-self.height-(self.down_ptx_no+3)*drc["metal1_to_metal1"]],
                               width=drc["minwidth_metal2"],
                              
                               height=self.height*6 )
                self.add_label(text="BL_bar{0}".format(j),
                              layer="metal2",
                               offset=[xoffset_BL_even,viaoffset_y-self.height-(self.down_ptx_no+3)*drc["metal1_to_metal1"]])

                offset_BL_bar=vector(xoffset_BL_even,viaoffset_y-self.height-(self.down_ptx_no+3)*drc["metal1_to_metal1"])
                self.BL_bar_positions.append(offset_BL_bar)
                via_offset = [ xoffset_BL_even, viaoffset_y]
                layer_stack_via1 = ["metal1", "via1", "metal2"]   
                self.add_via(layer_stack_via1,via_offset)
          

            """ Poly_bar added for BL_bar """

            """ poly_bar connection extend nmos3  and nmos[i]"""
            xoffset_poly_bar = (xoffset+ 
                            + self.nmos_ptx.poly_positions[0].x)
            
            yoffset_poly_bar = yoffset_poly_bar-3*drc["metal1_to_metal1"]
            poly_length_bar = poly_length_bar+3*drc["metal1_to_metal1"]
           
            offset_bar = vector (xoffset_poly_bar,yoffset_poly_bar )
            self.add_rect(layer="poly",
                          offset=offset_bar,
                          width=drc["minwidth_poly"],
                          height=poly_length_bar+1.3*drc["metal1_to_metal1"])
           
            yoffset_contact_bar=yoffset_poly_bar + drc["metal1_to_metal1"]

            xoffset_contact_bar=xoffset_poly_bar+drc["minwidth_poly"]
            offset_contact_bar = vector(xoffset_contact_bar, yoffset_contact_bar)
            self.add_contact(layers=("poly", "contact", "metal1"),
                         offset=offset_contact_bar,
                         size=(1,1),
                         rotate=90)

            
            " Word Line added to the left  "
        
            start=self.wordline_left=vector(self.left_end_figure_x,offset_contact_bar.y)

           
            offset_label=self.wordline_right=vector(start.x, offset_contact_bar.y)
          
            end =  vector(self.right_end_figure_x+self.nmos1.width*3+self.no_read_only_port*self.nmos1.width,offset_contact_bar.y)
           
            self.add_path("metal1",[start, end])
            offset=end



            #self.add_path("metal1",[start, end])
            self.add_label(text="WL{0}".format(j),
                           layer="metal1",
                           offset=offset_label)

            self.WL_positions.append(offset_label)
          

            if (j%2!=0):
                 self.source_positions_down_ptx.append(self.nmos3_position)   
                 "nmoS3 via1 and via2 added"
               
                 viaoffset_x=  self.nmos3_position.x+self.nmos_ptx.active_contact_positions[1].x
                
                 via_offset = vector(viaoffset_x,viaoffset_y)
                 layer_stack_via1 = ["metal1", "via1", "metal2"]   
                 self.add_via(layer_stack_via1,via_offset)
                 layer_stack_via2 = ["metal2", "via2", "metal3"] 
                 self.add_via(layer_stack_via2,via_offset)
                 start=  via_offset
                 end = vector (via_offset.x,self.nmos3_position.y+ drc["metal2_to_metal2"])
                 self.add_path("metal3",[start, end]) 
                
           
            j=j+1
        
        """ end of right loop"""
        self.end_of_ptx_position_right=vector(self.nmos3_position.x+2*self.nmos1.width,self.nmos3_position.y)
        self.BL_bar_position= self.BL_bar_offset

        """ Metal3 added from left to of the ptx positions"""

        start = self.source_line_left_start=vector(self.start_of_ptx_position_left_x,self.end_of_ptx_position_right.y+drc["metal2_to_metal2"])
        end =   vector(self.end_of_ptx_position_left.x+self.nmos1.width,self.end_of_ptx_position_right.y+drc["metal2_to_metal2"])
        self.add_path("metal3",[start, end])

        """ Metal3 added from  to right of the ptx positions"""
            
        start = self.source_line_right_start=vector(self.start_of_ptx_position_right_x,self.end_of_ptx_position_right.y+drc["metal2_to_metal2"])
        end =   vector(self.end_of_ptx_position_right.x+self.nmos1.width,self.end_of_ptx_position_right.y+drc["metal2_to_metal2"])
        self.add_path("metal3",[start, end])

        """ Metal3 via added to the drain of nmos1 and nmos2 """
        
        yoffset = self.nmos_position1.y
        via_offset=self.via_position_drain_left_inverter=self.via1_position=vector(self.nmos1.active_contact_positions[0].x  
                                                + self.nmos_position1.x 
                                                + self.nmos1.active_contact.first_layer_position.x 
                                                + self.nmos1.active_contact.width / 2
                                                - .5 * drc["minwidth_metal1"],
                                                 yoffset+drc["metal1_to_metal1"]+ drc["minwidth_metal1"])



       
        layer_stack_via1 = ["metal1", "via1", "metal2"]   
        self.add_via(layer_stack_via1,via_offset)
        layer_stack_via2 = ["metal2", "via2", "metal3"] 
        self.add_via(layer_stack_via2,via_offset)
        self.nmos2_drain_position=vector( self.nmos2.active_contact_positions[1].x+drc["minwidth_metal1"]+self.nmos_position2.x,self.nmos1.active_contact_positions[0].y-.8*drc["minwidth_metal1"])
        
        """nmos2 via1 and via2 added"""

        yoffset = self.nmos_position2.y
        via_offset=self.via_position_drain_right_inverter= vector(self.nmos2_drain_position.x - .7 * drc["minwidth_metal1"],self.via1_position.y)
        layer_stack_via1 = ["metal1", "via1", "metal2"]   
        self.add_via(layer_stack_via1,via_offset)
        layer_stack_via2 = ["metal2", "via2", "metal3"] 
        self.add_via(layer_stack_via2,via_offset)

        """Metal3 : drain of nmos 1 and sourceline Left start added """
        start = vector(self.via_position_drain_left_inverter.x+drc["minwidth_metal1"],self.via_position_drain_left_inverter.y+drc["minwidth_metal1"])
        end =   vector(self.via_position_drain_left_inverter.x-self.nmos1.width,self.source_line_left_start.y)
        self.add_path("metal3",[start, end]) 

        """Metal3 : drain of nmos 2 and sourceline Right added """
        start = vector(self.via_position_drain_right_inverter.x+drc["minwidth_metal1"],self.via_position_drain_right_inverter.y+drc["minwidth_metal1"])
        end = vector(self.source_line_right_start.x, self.source_line_right_start.y)
        self.add_path("metal3",[start, end])

    def Side_PTX_add_and_create_side_ptx(self):
       
        self.initial_cross_nmos_no=2
        self.side_ptx_start_no=self.initial_cross_nmos_no+self.down_ptx_no
        self.RBL_positions=[]
        self.RBL_bar_positions=[]
        self.NET_positions=[]
      
        self.nmos_side_ptx_names=[]
        for i in range (self.side_ptx_start_no+1,self.side_ptx_start_no+1+self.down_ptx_no):
            name= "nmos{0}".format(i)
               
            self.nmos_side_ptx_names.append(name)
       
        #for items in self.nmos_side_ptx_names:
            #print items            
    
        """create side left _ptx"""
        self.nmos_leftside_ptx_names= []
        self.nmos_leftside_ptx_positions= []
        self.nmos_rightside_ptx_names= []
        self.nmos_rightside_ptx_positions= []
       
        """No of nmos access ptx leftside"""

        poly_length=0
    
        yoffset_poly= self.nmos3_poly_bar_position_y=self.nmos3_position.y-2*self.nmos1.height
       
        """ Adding BL nmos"""   
        viaoffset_y=  self.nmos3_position.y-2*self.nmos1.height+drc["well_enclosure_active"]
        #viaoffset_x=
        xoffset= self.nmos_position1.x+self.nmos1.active_contact_positions[1].x+ self.nmos1.poly_positions[0].x
        yoffset= self.nmos3_position.y-self.nmos1.height
        self.start_of_ptx_position_left_x= xoffset-self.nmos1.width*.5
        
        xoffset_side_right=self.end_of_ptx_position_right.x
        R_Row_ptx_start_right=self.end_of_ptx_position_right.x
        xoffset_side_left=self.end_of_ptx_position_left.x
        R_Row_ptx_start_left=self.end_of_ptx_position_left.x
        R_Row_y=self.gnd_position.y-2.3*drc["metal1_to_metal1"]
        R_Row_y_bar=R_Row_y-2.3*drc["metal1_to_metal1"]
       
        yoffset_side_left=self.gnd_position.y+3.3*self.nmos1.height
        yoffset_side_right=self.gnd_position.y+3.3*self.nmos1.height
       
        viaoffset_side_left_y=yoffset_side_left
        viaoffset_side_right_y=yoffset_side_right
        i=1
        while (i<=self.no_read_only_port):
        
            """creating side_ptx"""
            name_nmos = "nmos{0}".format(i+self.side_ptx_start_no)
            #print(" Creating side Ptx "+ name_nmos)
            self.nmos_ptx= ptx(width=self.nmos_size,
                           mults=self.tx_mults,
                           tx_type= "nmos")
            self.add_mod (self.nmos_ptx)    
            
            #print (" Now Placing side left nmos{0}".format(i+self.side_ptx_start_no))
            if (i%2!=0):
                self.nmos_left_side_position=vector(xoffset_side_left,yoffset_side_left)
              
                self.add_inst(name=name_nmos,
                          mod=self.nmos_ptx,
                          offset= self.nmos_left_side_position,
                          mirror="MX")
                self.connect_inst([ "RBL{0}".format(i),"Q", "net{0}".format(i),"gnd"])
               

                poly_position_side_ptx=xoffset_side_left+self.nmos_ptx.poly_positions[0].x
              
                height=self.contact_Q_position.y-self.nmos_left_side_position.y+drc["minwidth_poly"]+drc["minwidth_metal3"]
                self.add_rect(layer="poly",
                               offset=vector(poly_position_side_ptx,self.nmos_left_side_position.y-3*drc["minwidth_poly"]),
                               width=drc["minwidth_poly"],
                               height=height+3*drc["minwidth_poly"])     
                
                self.add_contact (layers=("poly", "contact", "metal1"),
                                 
                                  offset=vector(poly_position_side_ptx+drc["minwidth_metal3"]*.5,self.contact_Q_position.y),
                                  size=(1,1),
                                  rotate=90)
                #via added to Q and poly :
                #########lima
                via_offset_poly = vector(poly_position_side_ptx,self.contact_Q_position.y)
                layer_stack_via1 = ["metal1", "via1", "metal2"]   
                self.add_via(layer_stack_via1,via_offset_poly,rotate=90)
                layer_stack_via2 = ["metal2", "via2", "metal3"] 
                self.add_via(layer_stack_via2,via_offset_poly,rotate=90)




                # Left RBL connected Adding via2 and  metal2  RBL
                xoffset_RBL_left=xoffset_side_left+self.nmos_ptx.active_contact_positions[1].x
                self.RBL_offset_old=vector(xoffset_RBL_left,viaoffset_side_left_y-self.height-(self.down_ptx_no+self.no_read_only_port)*drc["metal1_to_metal1"])
                self.RBL_offset= vector(self.RBL_offset_old.x,self.BL_bar_position.y)
                self.add_rect(layer="metal2",
                               
                               offset= vector(self.RBL_offset_old.x,self.BL_bar_position.y),
                               width=drc["minwidth_metal2"],
                              
                               height=self.height*6)
                self.add_label(text="RBL{0}".format(i),
                              layer="metal2",
                             
                               offset=self.RBL_offset)
                self.RBL_positions.append(self.RBL_offset)
                via_side_left_position_y= self.nmos_left_side_position.y-self.nmos_ptx.active_width
                via_offset = [xoffset_RBL_left, via_side_left_position_y+drc["minwidth_metal1"]]
                layer_stack_via1 = ["metal1", "via1", "metal2"]   
                self.add_via(layer_stack_via1,via_offset)
            


                # Left_RBL_bar connected
                xoffset_side_left_bar= self.nmos_left_side_position.x-self.nmos_ptx.active_width-self.nmos_ptx.poly_width+self.nmos_ptx.active_contact.width
                self.nmos_left_side_position_bar=vector(xoffset_side_left_bar,yoffset_side_left)
                #self.nmos_side_positions.append(self.nmos_side_position)
                name_nmos = "nmos{0}".format(i+self.side_ptx_start_no+1)
                #print(" Creating side Ptx "+ name_nmos)
                self.nmos_ptx= ptx(width=self.nmos_size,
                           mults=self.tx_mults,
                           tx_type= "nmos")
                self.add_mod (self.nmos_ptx) 
                self.add_inst(name=name_nmos,
                          mod=self.nmos_ptx,
                          offset= self.nmos_left_side_position_bar,
                          mirror="MX")
                self.connect_inst(["RBL_bar{0}".format(i),"Q_bar","net{0}".format(i),"gnd"])
                #print("Lines Creating RBL ****************************")
                #print("RBL{0}".format(i))
                self.nmos_side_position_left=self.nmos_left_side_position_bar
                #poly extension
                poly_position_side_ptx_bar=xoffset_side_left_bar+self.nmos_ptx.poly_positions[0].x
                
                height=self.contact_Q_bar_position.y-self.nmos_left_side_position_bar.y
                self.add_rect(layer="poly",
                               offset=vector(poly_position_side_ptx_bar,self.nmos_left_side_position_bar.y-3*drc["minwidth_poly"]),
                               width=drc["minwidth_poly"],
                               height=height+3*drc["minwidth_poly"])               
                
                self.add_contact (layers=("poly", "contact", "metal1"),
                                  offset=vector(poly_position_side_ptx_bar,self.contact_Q_bar_position.y-drc["minwidth_metal3"]),
                                  size=(1,1),
                                  rotate=270)
                #via added to Q_bar and poly :
                #########lima
                via_offset_poly = vector(poly_position_side_ptx_bar+drc["minwidth_metal1"]*.5,self.contact_Q_bar_position.y-drc["minwidth_metal3"])
                layer_stack_via1 = ["metal1", "via1", "metal2"]   
                self.add_via(layer_stack_via1,via_offset_poly,rotate=270)
                layer_stack_via2 = ["metal2", "via2", "metal3"] 
                self.add_via(layer_stack_via2,via_offset_poly,rotate=270)


                # Adding via2 and  metal2  RBL_bar
                xoffset_RBL_bar_left=self.nmos_left_side_position_bar.x+self.nmos_ptx.active_contact_positions[0].x
                self.RBL_bar_offset_old= vector(xoffset_RBL_bar_left,viaoffset_side_left_y-self.height-(self.down_ptx_no+self.no_read_only_port)*drc["metal1_to_metal1"])
                self.RBL_bar_offset=vector(self.RBL_bar_offset_old.x,self.BL_bar_position.y)
                self.add_rect(layer="metal2",
                               offset=self.RBL_bar_offset,
                               width=drc["minwidth_metal2"],
                              
                                height= self.height*6)
                self.add_label(text="RBL_bar{0}".format(i),
                              layer="metal2",
                             
                               offset=self.RBL_bar_offset)
                self.RBL_bar_positions.append(self.RBL_bar_offset)
                via_RBL_bar_left_position_y= self.nmos_left_side_position.y-self.nmos_ptx.active_width
                via_offset = [xoffset_RBL_bar_left, via_RBL_bar_left_position_y+drc["minwidth_metal1"]]
                layer_stack_via1 = ["metal1", "via1", "metal2"]   
                self.add_via(layer_stack_via1,via_offset)

            

                R_Row_ptx_origin=self.nmos_left_side_position.x
               
                xoffset_side_left= self.nmos_left_side_position_bar.x-self.nmos1.width
               
                """creating ptx connecting to gnd"""
                name_nmos = "nmos{0}".format(i+self.side_ptx_start_no+2)
                #print(" Creating R-Row Ptx "+ name_nmos)
                self.nmos_R_Row_ptx= ptx(width=self.nmos_size,
                           mults=self.tx_mults,
                             tx_type= "nmos")
                self.add_mod (self.nmos_R_Row_ptx)    
                      
                offset=vector(R_Row_ptx_origin,self.nmos_left_side_position_bar.y-self.nmos1.width-drc["minwidth_metal1"])
                self.add_inst(name=name_nmos,
                          mod=self.nmos_R_Row_ptx,
                          offset= offset,
                          mirror="MX")
               
                self.connect_inst([ "gnd","R_Row{0}".format(i),"net{0}".format(i),"gnd"])
                self.R_Row_position=offset
                #Connect Source of R-Row ptx to gnd  
                height=(7.5)*drc["metal1_to_metal1"]
              
               
                #Connect Source of  R-Row ptx to the above side_ptx
                    
                end= vector(R_Row_ptx_origin+self.nmos_R_Row_ptx.active_contact_positions[0].x,self.nmos_side_position_left.y-self.nmos_ptx.active_contact_positions[1].y)  
                start=vector(R_Row_ptx_origin+self.nmos_R_Row_ptx.active_contact_positions[0].x, self.R_Row_position.y-self.nmos_R_Row_ptx.active_contact.height-drc["minwidth_metal1"]*2.3)
                self.add_path("metal1",[start,end])
                #self.add_label(text="net{0}".format(i), layer="metal1",offset=vector(start.x,end.y-self.nmos1.width*.7))

                NET_offset_LEFT=vector(start.x,end.y-self.nmos1.width*.7)
                self.NET_positions.append(NET_offset_LEFT)
                #Connect drain of  R-Row ptx to the gnd
                end= vector(R_Row_ptx_origin+self.nmos_R_Row_ptx.active_contact_positions[1].x+drc["minwidth_metal1"],self.R_Row_position.y-self.nmos_ptx.active_width*.1)  
                start=vector(R_Row_ptx_origin+self.nmos_R_Row_ptx.active_contact_positions[1].x+drc["minwidth_metal1"], self.gnd_position.y)
                self.add_path("metal1",[start,end])

               
                poly_position_R_Row_ptx=R_Row_ptx_origin+self.nmos_R_Row_ptx.poly_positions[0].x
                
               
                    
                height=abs(R_Row_y-self.R_Row_position.y)
                self.add_contact (layers=("poly", "contact", "metal1"),
                                  offset=vector(poly_position_R_Row_ptx,R_Row_y+drc["minwidth_metal1"]),
                                  size=(1,1),
                                  rotate=270)
                offset=vector(poly_position_R_Row_ptx,R_Row_y)
                self.add_rect(layer="poly",
                      offset=offset,
		      width=drc["minwidth_poly"],                        
                      height= height)


                R_Row_y=R_Row_y-2.5*drc["metal1_to_metal1"]-2.5*drc["metal1_to_metal1"]
                

            """**************** added for right side ptx*******************************************************"""
            if (i%2==0):
                self.nmos_right_side_position=vector(xoffset_side_right,yoffset_side_right+drc["metal1_to_metal1"])
                #xoffset_side_left=xoffset_side_left-self.nmos_ptx.active_contact_positions[1].x
                self.add_inst(name=name_nmos,
                          mod=self.nmos_ptx,
                          offset= self.nmos_right_side_position,
                          mirror="MX")
                self.connect_inst([ "RBL{0}".format(i),"Q","net{0}".format(i),"gnd"])
              


                poly_position_side_ptx=xoffset_side_right+self.nmos_ptx.poly_positions[0].x
               
                height=self.contact_Q_position.y-self.nmos_right_side_position.y+drc["minwidth_poly"]+drc["minwidth_metal3"]
                self.add_rect(layer="poly",
                               offset=vector(poly_position_side_ptx,self.nmos_right_side_position.y-4*drc["minwidth_poly"]),
                               width=drc["minwidth_poly"],
                               height=height+6*drc["minwidth_poly"]) 
                    
                
                self.add_contact (layers=("poly", "contact", "metal1"),
                                 
                                  offset=vector(poly_position_side_ptx,self.contact_Q_position.y+drc["minwidth_metal1"]),
                                  size=(1,1),
                                  rotate=270)
                #Q to poly via added:rightside

                via_offset_poly = vector(poly_position_side_ptx+drc["minwidth_metal1"]*.5,self.contact_Q_position.y+drc["minwidth_metal3"])
                layer_stack_via1 = ["metal1", "via1", "metal2"]   
                self.add_via(layer_stack_via1,via_offset_poly,rotate=270)
                layer_stack_via2 = ["metal2", "via2", "metal3"] 
                #via_offset_poly_2 = vector(poly_position_side_ptx+drc[,self.contact_Q_position.y+drc["minwidth_metal1"]*1.5)
                self.add_via(layer_stack_via2,via_offset_poly,rotate=270)



               


                # Right RBL connected Adding via2 and  metal2  RBL
                xoffset_RBL_right=xoffset_side_right+self.nmos_ptx.active_contact_positions[0].x
                self.RBL_offset_old=vector(xoffset_RBL_right,viaoffset_side_right_y-self.height-(self.down_ptx_no+self.no_read_only_port)*drc["metal1_to_metal1"])
                self.RBL_offset= vector(self.RBL_offset_old.x,self.BL_bar_position.y)
                self.add_rect(layer="metal2",
                              
                               offset= vector(self.RBL_offset_old.x,self.BL_bar_position.y),
                               width=drc["minwidth_metal2"],
                               #height=(self.nmos1.height*self.down_ptx_no+1)+2*self.height)
                               height=self.height*6)
                self.add_label(text="RBL{0}".format(i),
                              layer="metal2",
                              
                               offset=self.RBL_offset)
                self.RBL_positions.append(self.RBL_offset)
                via_side_right_position_y= self.nmos_right_side_position.y-self.nmos_ptx.active_width
                via_offset = [xoffset_RBL_right, via_side_right_position_y]
                layer_stack_via1 = ["metal1", "via1", "metal2"]   
                self.add_via(layer_stack_via1,via_offset)
            


                # Right_RBL_bar connected
               
                xoffset_side_right_bar= self.nmos_right_side_position.x+self.nmos_ptx.active_width+self.nmos_ptx.poly_width-self.nmos_ptx.active_contact.width
                self.nmos_right_side_position_bar=vector(xoffset_side_right_bar,yoffset_side_left+drc["metal1_to_metal1"])
               
                name_nmos = "nmos{0}".format(i+self.side_ptx_start_no+1)
                #print(" Creating side Ptx "+ name_nmos)
                self.nmos_ptx= ptx(width=self.nmos_size,
                           mults=self.tx_mults,
                           tx_type= "nmos")
                self.add_mod (self.nmos_ptx) 
                self.add_inst(name=name_nmos,
                          mod=self.nmos_ptx,
                          offset= self.nmos_right_side_position_bar,
                          mirror="MX")
                self.connect_inst([ "RBL_bar{0}".format(i),"Q_bar","net{0}".format(i),"gnd"])
                
               
                self.nmos_side_position_right=self.nmos_right_side_position_bar
                #poly extension Q bar:right
                poly_position_side_ptx_bar=xoffset_side_right_bar+self.nmos_ptx.poly_positions[0].x
               
               

                height=self.contact_Q_bar_position.y-self.nmos_right_side_position_bar.y
                self.add_rect(layer="poly",
                               offset=vector(poly_position_side_ptx_bar,self.nmos_right_side_position_bar.y-3*drc["minwidth_poly"]),
                               width=drc["minwidth_poly"],
                               height=height+3*drc["minwidth_poly"])             
                
                self.add_contact (layers=("poly", "contact", "metal1"),
                                  offset=vector(poly_position_side_ptx_bar+drc["minwidth_metal1"]*.5,self.contact_Q_bar_position.y-2*drc["minwidth_metal3"]),
                                  size=(1,1),
                                  rotate=90)
                offset=vector(poly_position_side_ptx_bar+drc["minwidth_metal1"]*.5,self.contact_Q_bar_position.y-2*drc["minwidth_metal3"])
                via_offset_poly = vector(offset.x-drc["minwidth_metal1"]*.5,offset.y)
                layer_stack_via1 = ["metal1", "via1", "metal2"]   
                self.add_via(layer_stack_via1,via_offset_poly,rotate=90)
                layer_stack_via2 = ["metal2", "via2", "metal3"] 
                self.add_via(layer_stack_via2,via_offset_poly,rotate=90)


               

                """lima end for right ptx"""

            i=i+1
        #limaapril23    
        if(self.no_read_only_port>0):
            self.end_of_leftside_ptx=self.nmos_left_side_position_bar
            self.end_of_rightside_ptx=self.nmos_right_side_position_bar
        else:
             self.end_of_leftside_ptx=self.left_end_figure_x
             self.end_of_rightside_ptx=self.right_end_figure_x


    def extend_wells(self):
        """ Extension of well """
        middle_point = (self.nmos_position1.y + self.nmos1.pwell_position.y
                           + self.nmos1.well_height
                           + (self.pmos_position1.y + self.pmos1.nwell_position.y
                               - self.nmos_position1.y - self.nmos1.pwell_position.y
                               - self.nmos1.well_height) / 2)
        offset = self.nwell_position = vector(0, middle_point)
        self.nwell_height = self.height - middle_point+2*drc["minwidth_metal3"]
        self.add_rect(layer="nwell",
                      offset=offset,
                      width=self.well_width,                          
                      height=self.nwell_height)
        self.add_rect(layer="vtg",
                      offset=offset,
                      width=self.well_width,                        
                      height=self.nwell_height)

       
        offset = self.pwell_position = vector(self.end_of_ptx_position_left.x+self.nmos1.width,self.end_of_ptx_position_left.y-1.1*self.nmos1.height)
        self.pwell_height = middle_point-self.end_of_ptx_position_left.y+.3*self.nmos1.height
        pwell_right=self.pwell_rightlen=self.end_of_ptx_position_right.x+ self.nmos1.width*self.no_read_only_port
        pwell_left=self.pwell_leftlen=self.end_of_ptx_position_left.x-self.nmos1.width*self.no_read_only_port
        self.pwell_width = pwell_right- pwell_left
        
        #self.pwell_width = self.end_of_ptx_position_right.x-self.end_of_ptx_position_left.x
        offset=self.pwell_offset=vector( pwell_left+self.nmos1.width,self.end_of_ptx_position_left.y-1.1*self.nmos1.height)
	self.add_rect(layer="pwell",
                      offset=offset,
		      width=self.pwell_width,                        
                      height=self.pwell_height)
		     
        self.add_rect(layer="vtg",
                      offset=offset,
                      width=self.pwell_width,                             
                      height=self.pwell_height)
        #offset=vector(offset.x+self.end_of_ptx_position_left.x,offset.y+self.end_of_ptx_position_left.y),

    def extend_rails(self):
        """ add power rails """
        gnd_width =self.gnd_width= self.end_of_ptx_position_right.x-self.end_of_ptx_position_left.x+ self.down_ptx_no*.5*self.nmos1.width+self.no_read_only_port*.5*self.nmos1.width
        #gnd_width=self.wordline_right.x+self.wordline_left.x
        rail_height = drc["minwidth_metal1"]
        self.rail_height = rail_height
        # Relocate the origin
        self.gnd_position_extended = vector(self.end_of_ptx_position_left.x-2*drc["metal1_to_metal1"],self.gnd_position.y)
        self.gnd_position_real=vector(self.end_of_ptx_position_left.x-2*drc["metal1_to_metal1"]-self.no_read_only_port*.5*self.nmos1.width,self.gnd_position.y)
        
        self.add_rect(layer="metal1",
                      #offset=self.gnd_position_real,
                      offset=vector(self.left_end_figure_x,self.gnd_position_real.y),
                      width=self.width_figure+4*self.nmos1.width,
                      height=rail_height)
        self.add_label(text="gnd",
                       layer="metal1",
                       offset=vector(self.left_end_figure_x,self.gnd_position_real.y))

        self.vdd_position_extended = vector(self.end_of_ptx_position_left.x-2*drc["metal1_to_metal1"],self.vdd_position.y )
        self.add_rect(layer="metal1", 
                      offset=vector(self.left_end_figure_x,self.vdd_position_extended.y-drc["metal1_to_metal1"]),
                      width=self.width_figure+4*self.nmos1.width,
                      height=rail_height)
        self.vdd_position_label= vector(self.left_end_figure_x,self.vdd_position_extended.y-drc["metal1_to_metal1"])
        self.add_label(text="vdd",
                       layer="metal1", 
                       offset=self.vdd_position_label)

        
        pmos_to_vdd_height=self.pmos_position2.y-self.vdd_position_extended.y
        self.add_rect(layer="metal1", 
                      offset=vector(self.pmos_position2.x+1.5*drc["minwidth_metal1"],self.vdd_position_extended.y+drc["minwidth_metal1"]),
                      width=drc["minwidth_metal1"],
                      height=pmos_to_vdd_height)
       



    def extend_Q_and_Q_bar(self):
       
                        
        self.Q_end_left=self.end_of_ptx_position_left.x-(self.no_read_only_port-1)*self.nmos1.width
        self.Q_end_right=self.end_of_ptx_position_right.x+(self.no_read_only_port)*self.nmos1.width

        self.width_Q= self.Q_end_right-self.Q_end_left 
        if(self.no_read_only_port>=1):
           self.Q_offset= self.input_position_Q
           self.pwell_leftlen
           self.add_rect(layer="metal3",
                      #offset=vector(self.Q_offset.x+drc["minwidth_metal1"],self.Q_offset.y),
                         offset=vector(self.Q_end_left,self.contact_Q_position.y),	     
                      #width=self.end_of_leftside_ptx.x-3*self.nmos1.width,                       ,
                      width=self.width_Q,
                         height=drc["minwidth_metal3"])
    
        self.Q_offset_bar= self.input_position_Q_bar
        if(self.no_read_only_port>=1):
            self.add_rect(layer="metal3",
                          offset=vector(self.Q_end_left, self.input_position2.y),
		      #width=self.end_of_leftside_ptx.x-3*self.nmos1.width,                        
                      width=self.width_Q,
                          height=drc["minwidth_metal3"])
            

        
        #Space between gnd_metal1 and metal1 below ground:Left ptx no
        R_Row_cnt=1
        row_y=self.gnd_position.y-drc["metal1_to_metal1"]-1.3*drc["minwidth_metal1"]
        width=self.right_end_figure_x-self.left_end_figure_x
        while(R_Row_cnt<=self.no_read_only_port):
              
            self.add_rect(layer="metal1",
                      #offset=vector(self.gnd_position_real.x, row_y),
		      #width=self.gnd_width,                       
                      offset=vector(self.left_end_figure_x,row_y),
                      width=width+4*self.nmos1.width,
                      height=drc["minwidth_metal1"])
         

            self.add_label(text="R_Row{0}".format(R_Row_cnt),
                          layer="metal1",
                           offset=vector(self.left_end_figure_x, row_y))




            R_Row_cnt=R_Row_cnt+1
            row_y=row_y-drc["metal1_to_metal1"]-1.5*drc["minwidth_metal1"]
            

   
       
                         
                    
                       
        
       
                         
                        
       
                     


   
       
		     
                     

        
       
      
		      



 
