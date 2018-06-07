import contact
import design
import debug
from tech import drc
from ptx import ptx
from vector import vector
from globals import OPTS

class cell_multiport(design.design):
    """
    This module generates gds of a 8T cell
    """

    c = reload(__import__(OPTS.config.bitcell))
    bitcell = getattr(c, OPTS.config.bitcell)

    def __init__(self, name, nmos_width=1, height=bitcell.chars["height"]):
        """ Constructor """
        design.design.__init__(self, name)
        debug.info(2, "create nand_2 strcuture {0} with size of {1}".format(
            name, nmos_width))

        self.nmos_width = nmos_width
        self.height = height
        self.add_pins()
        self.create_layout()
        self.DRC_LVS()

    def add_pins(self):
        """ Add pins """
        self.add_pin_list(["WL1", "WL2", "BL1","BL2","BL1_bar","BL2_bar","Q","Q_bar","vdd", "gnd"])

    def create_layout(self):
        """ Layout """
        self.determine_sizes()
        self.create_ptx_lima()
        self.setup_layout_constants()
        self.add_rails()
        self.add_ptx()
        self.add_well_contacts()

        # This isn't instantiated, but we use it to get the dimensions
        self.poly_contact = contact.contact(("poly", "contact", "metal1"))

        self.connect_well_contacts()
        self.connect_rails_lima()
        self.connect_tx()
        self.route_pins()
        self.extend_wells()
        self.extend_active()
        self.connect_sources_access_nmos_lima()
        self.connect_wordline_bitline_lima()      
        self.route_output_gate_WordLine1_lima()
       
    # Determine transistor size
    def determine_sizes(self):
        """ Determine the size of the transistors """
        self.nmos_size = self.nmos_width
        self.pmos_size = self.nmos_width
        self.tx_mults = 1

    
       # transistors are created here but not yet placed or added as a module
    def create_ptx_lima(self):
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

        self.nmos3 = ptx(width=self.nmos_size,
                         mults=self.tx_mults,
                         tx_type="nmos")
        self.add_mod(self.nmos3)
        self.nmos4 = ptx(width=self.nmos_size,
                         mults=self.tx_mults,
                         tx_type="nmos")
        self.add_mod(self.nmos4)

        self.nmos5 = ptx(width=self.nmos_size,
                         mults=self.tx_mults,
                         tx_type="nmos")
        self.add_mod(self.nmos5)
        self.nmos6 = ptx(width=self.nmos_size,
                         mults=self.tx_mults,
                         tx_type="nmos")
        self.add_mod(self.nmos6)

    def setup_layout_constants(self):
        """ Calculate the layout constraints """
        self.well_width = self.pmos1.active_position.x \
            + 2 * self.pmos1.active_width \
            + drc["active_to_body_active"] + \
            drc["well_enclosure_active"]

        self.width = self.well_width

    def add_rails(self):
        """ add power rails """ 
        rail_width = self.width+3* drc["minwidth_metal1"]
        rail_height = drc["minwidth_metal1"]
        self.rail_height = rail_height
        # Relocate the origin
        self.gnd_position = vector(0, - 0.5 * drc["minwidth_metal1"])
        self.add_rect(layer="metal1",
                      offset=self.gnd_position,
                      width=rail_width,
                      height=rail_height)
        self.add_label(text="gnd",
                       layer="metal1",
                       offset=self.gnd_position)

        self.vdd_position = vector(0, self.height - 0.5 * drc["minwidth_metal1"])
        self.add_rect(layer="metal1", 
                      offset=self.vdd_position,
                      width=rail_width+drc["minwidth_metal1"],
                      height=rail_height)
        self.add_label(text="vdd",
                       layer="metal1", 
                       offset=self.vdd_position)

    def add_ptx(self):
        """  transistors are added and placed inside the layout         """

        # determines the spacing between the edge and nmos (rail to active
        # metal or poly_to_poly spacing)
        edge_to_nmos = max(drc["metal1_to_metal1"]
                            - self.nmos1.active_contact_positions[0].y,
                           0.5 * (drc["poly_to_poly"] - drc["minwidth_metal1"])
                             - self.nmos1.poly_positions[0].y)

        # determine the position of the first transistor from the left
        self.nmos_position1 = vector(2*drc["minwidth_metal1"], 0.5 * drc["minwidth_metal1"] + edge_to_nmos)
        offset = self.nmos_position1+ vector(0,self.nmos1.height)
        self.add_inst(name="nmos1",
                      mod=self.nmos1,
                      offset=offset,
                      mirror="MX")
        self.connect_inst(["Q_bar", "Q", "gnd", "gnd"])

        self.nmos_position2 = vector(self.nmos2.active_width - self.nmos2.active_contact.width+3*drc["minwidth_metal1"], 
                                     self.nmos_position1.y)
        offset = self.nmos_position2 + vector(0,self.nmos2.height)
        self.add_inst(name="nmos2",
                      mod=self.nmos2,
                      offset=offset,
                      mirror="MX")
        self.connect_inst(["Q", "Q_bar", "gnd", "gnd"])

       #lima: nmos3 and nmos4
       
        edge_to_nmos = max(drc["metal1_to_metal1"]
                            - self.nmos3.active_contact_positions[0].y,
                           0.5 * (drc["poly_to_poly"] - drc["minwidth_metal1"])
                             - self.nmos3.poly_positions[0].y)

        # lima:determine the position of the 3rdtransistor from the left
        self.nmos_position3 = vector(0, 6*drc["minwidth_metal1"])
        offset = self.nmos_position3+ vector(0,self.nmos3.height-12* drc["minwidth_metal1"])
        self.nmos_position3= offset
        self.add_inst(name="nmos3",
                      mod=self.nmos3,
                      offset=offset,
                      mirror="MX")
        self.connect_inst(["Q_bar", "WL1", "BL1_bar", "gnd"])
        layer_stack = ("metal1", "via1", "metal2")
        via_offset=vector(self.nmos3.active_contact_positions[0].x+drc["minwidth_metal1"]/2, self.nmos3.height-10* drc["minwidth_metal1"])
        self.add_via(layer_stack,via_offset)

        self.nmos_position4 = vector(0, 6 * drc["minwidth_metal1"] )
        offset = self.nmos_position4+ vector(self.nmos3.poly_positions[0].x+.06,self.nmos4.height-12* drc["minwidth_metal1"])
        self.nmos_position4=offset
        self.add_inst(name="nmos4",
                      mod=self.nmos4,
                      offset=offset,
                      mirror="MX")
        self.connect_inst(["Q_bar", "WL2", "BL2_bar", "gnd"])
        layer_stack = ("metal1", "via1", "metal2")
        via_offset=vector(self.nmos4.active_contact_positions[1].x + 3.1*drc["minwidth_metal1"],self.nmos3.height-10* drc["minwidth_metal1"])
        self.add_via(layer_stack,via_offset)
       
       # lima nmos5 and nmos 6 added

        self.nmos_position5 = vector(self.nmos5.width, 6 * drc["minwidth_metal1"] )
        offset = self.nmos_position5+ vector(self.nmos5.width/2+drc["active_to_body_active"],self.nmos5.height-12* drc["minwidth_metal1"])
        self.nmos_position5 =offset
        self.add_inst(name="nmos5",
                      mod=self.nmos5,
                      offset=offset,
                      mirror="MX")
        self.connect_inst(["Q", "WL1", "BL1", "gnd"])
        layer_stack = ("metal1", "via1", "metal2")
        via_offset=vector(self.nmos5.active_contact_positions[0].x + 11*drc["minwidth_metal1"],self.nmos5.height-10* drc["minwidth_metal1"])
        self.add_via(layer_stack,via_offset)

        self.nmos_position6 = vector(0, 6* drc["minwidth_metal1"] )
        offset = self.nmos_position6+ vector(self.nmos5.width+self.nmos5.poly_positions[0].x+self.nmos5.width/2+drc["active_to_body_active"]+.03,self.nmos5.height-12* drc["minwidth_metal1"])   
        self.nmos_position6 = offset
        self.add_inst(name="nmos6",
                      mod=self.nmos6,
                      offset=offset,
                      mirror="MX")
        self.connect_inst(["Q", "WL2", "BL2", "gnd"])
        layer_stack = ("metal1", "via1", "metal2")
        via_offset=vector(self.nmos6.active_contact_positions[1].x + 12.5* drc["minwidth_metal2"],self.nmos3.height-10* drc["minwidth_metal1"])
        self.add_via(layer_stack,via_offset)

        # determines the spacing between the edge and pmos
        edge_to_pmos = max(drc["metal1_to_metal1"] \
                               - self.pmos1.active_contact_positions[0].y,
                           0.5 * drc["poly_to_poly"] - 0.5 * drc["minwidth_metal1"] \
                               - self.pmos1.poly_positions[0].y)

        self.pmos_position1 = vector(2*drc["minwidth_metal1"], self.height - 0.5 * drc["minwidth_metal1"]- edge_to_pmos - self.pmos1.height)
        self.add_inst(name="pmos1",
                      mod=self.pmos1,
                      offset=self.pmos_position1)
        self.connect_inst(["vdd", "Q", "Q_bar", "vdd"])

        self.pmos_position2 = vector(self.nmos_position2.x, self.pmos_position1.y)
        self.add_inst(name="pmos2",
                      mod=self.pmos2,
                      offset=self.pmos_position2)
        self.connect_inst(["vdd", "Q_bar", "Q", "vdd"])

    def add_well_contacts(self):
        """  Create and add well copntacts """
        # create well contacts
        layer_stack = ("active", "contact", "metal1")

        xoffset = (self.nmos_position2.x + self.pmos1.active_position.x 
                   + self.pmos1.active_width + drc["active_to_body_active"]+drc["minwidth_metal1"]*.5)
        yoffset = (self.pmos_position1.y +
                  self.pmos1.active_contact_positions[0].y)
        offset = self.nwell_contact_position = vector(xoffset, yoffset)
        self.pwell_contact=self.add_contact(layer_stack,offset,(1,self.nmos1.num_of_tacts))

        xoffset = (self.nmos_position2.x + self.nmos1.active_position.x
                   + self.nmos1.active_width + drc["active_to_body_active"]+drc["minwidth_metal1"]*.5)
        yoffset = (self.nmos_position1.y + self.nmos1.height
                   - self.nmos1.active_contact_positions[0].y
                   - self.nmos1.active_contact.height)
        offset = self.pwell_contact_position = vector(xoffset, yoffset)
        self.nwell_contact=self.add_contact(layer_stack,offset,(1,self.pmos1.num_of_tacts))

    def connect_well_contacts(self):
        """  Connect well contacts to vdd and gnd rail """
        well_tap_length = (self.height - self.nwell_contact_position.y)
        offset = vector(self.nwell_contact_position.x 
                        + self.nwell_contact.second_layer_position.x 
                        - self.nwell_contact.first_layer_position.x+drc["minwidth_metal1"],
                        self.nwell_contact_position.y)
        self.add_rect(layer="metal1",
                      offset=offset,
                      width=drc["minwidth_metal1"],
                      height=well_tap_length)

        well_tap_length = self.nmos1.active_height
        offset = (self.pwell_contact_position.scale(1.05,-.11) 
                        + self.pwell_contact.second_layer_position.scale(1.05,-.11) 
                        - self.pwell_contact.first_layer_position.scale(1.05,-.11)) 
        self.add_rect(layer="metal1",
                      offset=offset, width=drc["minwidth_metal1"],
                      height=well_tap_length+drc["minwidth_metal1"])

    def connect_rails(self):
        """  Connect transistor pmos drains to vdd and nmos drains to gnd rail """
        correct = vector(self.pmos1.active_contact.width - drc["minwidth_metal1"],
                         0).scale(.5,0)
        poffset = self.pmos_position1 + self.pmos1.active_contact_positions[0] + correct
        temp_height = self.height - poffset.y
        self.add_rect(layer="metal1",
                      offset=poffset, width=drc["minwidth_metal1"],
                      height=temp_height)

        poffset = vector(2 * self.pmos_position2.x + correct.x
                         + self.pmos2.active_contact_positions[0].x , poffset.y)
        self.add_rect(layer="metal1",
                      offset=poffset,
                      width=drc["minwidth_metal1"],
                      height=temp_height)

        poffset = self.nmos_position1 + self.nmos1.active_contact_positions[0] + correct
        self.add_rect(layer="metal1",
                      offset=poffset.scale(1,0),
                      width=drc["minwidth_metal1"],
                      height=temp_height)

    def connect_tx(self):
        """ Connect tx poly znd drains """
        self.connect_poly()
        self.connect_drains_lima_working()

    def connect_poly(self):
        """ poly connection """
        yoffset_nmos1 = (self.nmos_position1.y 
                            + self.nmos1.poly_positions[0].y 
                            + self.nmos1.poly_height)
        poly_length = (self.pmos_position1.y + self.pmos1.poly_positions[0].y 
                          - yoffset_nmos1 + drc["minwidth_poly"])
        for position in self.pmos1.poly_positions:
            offset = vector(position.x+2*drc["minwidth_metal1"],
                            yoffset_nmos1 - 0.5 * drc["minwidth_poly"])
            self.add_rect(layer="poly",
                          offset=offset, width=drc["minwidth_poly"],
                          height=poly_length)
            self.add_rect(layer="poly",
                          offset=[offset.x + self.pmos1.active_contact.width + 3.3 * drc["minwidth_poly"],
                                  offset.y],
                          width=drc["minwidth_poly"],
                          height=poly_length)

    def connect_drains_lima_working(self):
       
        """yoffset = self.nmos_position1.y
        start = self.drain_position = vector(self.pmos1.active_contact_positions[0].x + 0.5 * drc["minwidth_metal1"] 
                                                + self.pmos_position1.x 
                                                + self.pmos1.active_contact.first_layer_position.x 
                                                + self.pmos1.active_contact.width / 2
                                                - .5 * drc["minwidth_metal1"],
                                                 yoffset)
        end = vector(self.pmos1.active_contact_positions[0].x + 0.5 * drc["minwidth_metal1"]
                       + self.pmos1.active_contact.second_layer_position.x,
                       self.pmos_position1.y + self.pmos1.active_contact_positions[0].y)
           

        self.add_path("metal1",[start, end])"""
       
        yoffset = self.nmos_position1.y
        start = vector(self.pmos1.active_contact_positions[0].x + 0.25 * drc["minwidth_metal1"]+ 2*drc["minwidth_metal1"],
                            self.pmos1.active_contact_positions[0].y +drc["minwidth_metal1"]) 
        end = vector(self.pmos1.active_contact_positions[0].x + 0.25 * drc["minwidth_metal1"]+ 2*drc["minwidth_metal1"]
                        ,self.pmos_position1.y+drc["minwidth_metal1"]*3 )
           
        self.add_path("metal1",[start, end])
       

        yoffset = self.nmos_position1.y+ drc["minwidth_metal1"]
        start = vector(self.pmos2.active_contact_positions[1].x
                             +  drc["minwidth_metal1"]
                             + drc["minwidth_metal1"] * 4
                             + self.pmos2.active_contact.second_layer_position.x+ drc["minwidth_metal1"] +drc["minwidth_metal1"],
                             yoffset + drc["minwidth_metal1"]) 
        end = vector(self.pmos2.active_contact_positions[1].x + 0.5 * drc["minwidth_metal1"]
                        + self.pmos2.active_contact.second_layer_position.x
                        + drc["minwidth_metal1"] * 4 + drc["minwidth_metal1"]+ drc["minwidth_metal1"],
                        self.pmos_position2.y + self.pmos2.active_contact_positions[1].y+ drc["minwidth_metal1"])
           
        self.add_path("metal1",[start, end])

   

    def route_pins(self):
        """ Routing """
        self.route_input_gate()
        

    def route_input_gate(self):
        """ Gate routing """
        self.route_input_gate_A_lima()
        self.route_input_gate_B_lima()



    def route_output_gate_WordLine1_lima(self):
        """ routing for input Wordline1 """

    
        """ poly connection extend nmos3  and nmos5"""
        yoffset_nmos3 = (self.nmos_position3.y 
                            + self.nmos3.poly_positions[0].y 
                            + self.nmos3.poly_height+drc["minwidth_tx"])
        poly_length = (self.nmos_position3.y + self.nmos3.poly_positions[0].y 
                          - yoffset_nmos3 - 2*drc["minwidth_poly"])
       
        offset = vector (self.nmos3.poly_positions[0].x,
                            yoffset_nmos3 - 11 * drc["minwidth_poly"])
        self.add_rect(layer="poly",
                          offset=offset, width=drc["minwidth_poly"],
                          height=poly_length)
       
        

        xoffset=self.nmos3.poly_positions[0].x+ drc["minwidth_poly"]
        yoffset=self.nmos_position3.y + self.nmos3.poly_positions[0].y-yoffset_nmos3 - 7 * drc["minwidth_poly"]
       
        offset = [xoffset, yoffset]
        self.add_contact(layers=("poly", "contact", "metal1"),
                         offset=offset,
                         size=(1,1),
                         rotate=90)

        """ poly connection extend nmos5 """
        yoffset_nmos5 = (self.nmos_position5.y 
                            + self.nmos5.poly_positions[0].y 
                            + self.nmos5.poly_height+drc["minwidth_tx"])
        poly_length =  (self.nmos_position5.y + self.nmos5.poly_positions[0].y 
                          - yoffset_nmos5 - 2*drc["minwidth_poly"])
       
        offset = vector (self.nmos5.poly_positions[0].x +9.7* drc["minwidth_poly"]+2*drc["minwidth_tx"],
                            yoffset_nmos5 - 11 * drc["minwidth_poly"])
        self.add_rect(layer="poly",
                          offset=offset, width=drc["minwidth_poly"],
                          height=poly_length)

        xoffset=self.nmos_position5.y + self.nmos5.poly_positions[0].y + 3.5*yoffset_nmos5 + drc["minwidth_poly"]-drc["contact_to_poly"]
        yoffset=self.nmos_position5.y + self.nmos5.poly_positions[0].y-yoffset_nmos5 - 7 * drc["minwidth_poly"]
       
        offset = [xoffset, yoffset]
        self.add_contact(layers=("poly", "contact", "metal1"),
                         offset=offset,
                         size=(1,1),
                         rotate=90)


        
        """ poly connection extend nmos4 and nmos6"""
        yoffset_nmos4 = (self.nmos_position4.y 
                            + self.nmos4.poly_positions[0].y 
                            + self.nmos4.poly_height+drc["minwidth_tx"])
        poly_length = (self.nmos_position4.y + self.nmos4.poly_positions[0].y 
                          - yoffset_nmos4 + drc["minwidth_poly"])
       
        offset = vector (self.nmos4.poly_positions[0].x+3.4*drc["minwidth_poly"]+.01+.05,
                            yoffset_nmos4 - 11 * drc["minwidth_poly"])
        self.add_rect(layer="poly",
                          offset=offset, width=drc["minwidth_poly"],
                         height=poly_length)
        xoffset=self.nmos_position4.y + self.nmos4.poly_positions[0].y + yoffset_nmos4 + 5*drc["minwidth_poly"]+drc["contact_to_poly"]/2
        yoffset=self.nmos_position4.y + self.nmos4.poly_positions[0].y-yoffset_nmos4 - 4.5 * drc["minwidth_poly"]
       
        offset = [xoffset, yoffset]
        self.add_contact(layers=("poly", "contact", "metal1"),
                         offset=offset,
                         size=(1,1),
                         rotate=90)

        """ poly connection extend nmos6 """
        yoffset_nmos6 = (self.nmos_position6.y 
                            + self.nmos5.poly_positions[0].y 
                            + self.nmos5.poly_height+drc["minwidth_tx"])
       
        poly_length = (self.nmos_position6.y + self.nmos6.poly_positions[0].y 
                          - yoffset_nmos6 + drc["minwidth_poly"])
        offset = vector (self.nmos6.poly_positions[0].x +9.9* drc["minwidth_poly"]+2*drc["minwidth_tx"]+3.25*drc["minwidth_poly"]+.03,
                            yoffset_nmos6 - 11 * drc["minwidth_poly"])
        self.add_rect(layer="poly",
                          offset=offset, 
                          width=drc["minwidth_poly"],
                          height=poly_length)

        xoffset=self.nmos_position6.y + self.nmos6.poly_positions[0].y + 3*yoffset_nmos6 + 7*drc["minwidth_poly"]
        yoffset=self.nmos_position6.y + self.nmos6.poly_positions[0].y-yoffset_nmos6 - 4.5 * drc["minwidth_poly"]
       
        offset = [xoffset, yoffset]
        self.add_contact(layers=("poly", "contact", "metal1"),
                         offset=offset,
                         size=(1,1),
                         rotate=90)
        
        """ routing for WL1 and WL2 """

       
        #def add_rails(self):
        """ add WL2 """
        WL2_width = self.nmos_position6.y + self.nmos6.poly_positions[0].y + 3*yoffset_nmos6 + 9*drc["minwidth_poly"]
        WL2_height = drc["minwidth_metal1"]
        self.WL2_height = WL2_height
        # Relocate the origin

        self.WL2_position = vector(0, self.nmos_position6.y + self.nmos6.poly_positions[0].y - 4.3 * drc["minwidth_poly"]-yoffset_nmos6 )
        self.add_rect(layer="metal1",
                      offset=self.WL2_position,
                      width=WL2_width,
                      height=WL2_height)
        self.add_label(text="WL2",
                       layer="metal1",
                       offset=self.WL2_position)

        """ add WL1 """
        WL1_width = self.nmos_position6.y + self.nmos6.poly_positions[0].y + 3*yoffset_nmos6 + 9*drc["minwidth_poly"]
        WL1_height = drc["minwidth_metal1"]
        self.WL2_height = WL2_height
        # Relocate the origin

        self.WL1_position = vector(0,self.nmos_position5.y + self.nmos5.poly_positions[0].y-yoffset_nmos5 - 7 * drc["minwidth_poly"] )
        self.add_rect(layer="metal1",
                      offset=self.WL1_position,
                      width=WL1_width,
                      height=WL1_height)
        self.add_label(text="WL1",
                       layer="metal1",
                       offset=self.WL1_position)




   

    def extend_wells(self):
        """ Extension of well """
        middle_point = (self.nmos_position1.y + self.nmos1.pwell_position.y
                           + self.nmos1.well_height
                           + (self.pmos_position1.y + self.pmos1.nwell_position.y
                               - self.nmos_position1.y - self.nmos1.pwell_position.y
                               - self.nmos1.well_height) / 2)
        offset = self.nwell_position = vector(0, middle_point)
        self.nwell_height = self.height - middle_point
        self.add_rect(layer="nwell",
                      offset=offset,
                      width=self.well_width*1.8,
                      height=self.nwell_height)
        self.add_rect(layer="vtg",
                      offset=offset,
                      width=self.well_width*1.8,
                      height=self.nwell_height)

       

        #def extend_wells_access_nmos_lima(self):
        """ Extension of well """
        
        yoffset_nmos3=self.nmos_position3+ vector(0,self.nmos3.height-12* drc["minwidth_metal1"])
        offset = self.pwell_position_1 = vector(0, yoffset_nmos3 )
      

       
        """ Extension of well"""
        middle_point = (self.nmos_position1.y + self.nmos1.pwell_position.y
                           + self.nmos1.well_height
                           + (self.pmos_position1.y + self.pmos1.nwell_position.y
                               - self.nmos_position1.y - self.nmos1.pwell_position.y
                               - self.nmos1.well_height) / 2)
       

        offset = self.pwell_position = vector(0,(self.nmos3.height-7.5*drc["minwidth_metal1"]-self.nmos3.height))
       
        self.pwell_height = self.nmos3.height+drc["minwidth_well"]+self.well_width-self.nmos1.height*1.3
        self.add_rect(layer="pwell",
                      offset=offset,
                      width=self.well_width*1.8,
                      height=self.pwell_height)
        self.add_rect(layer="vtg",
                      offset=offset,
                      width=self.well_width*1.8,
                      height=self.pwell_height)

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
        """ Defining the position of i/o pins for the two input nand gate """
        self.A_position = self.A_position = self.input_position1
        self.B_position = self.B_position = self.input_position2
        self.Z_position = self.Z_position = self.output_position
        self.vdd_position = self.vdd_position
        self.gnd_position = self.gnd_position

    def connect_drains_lima(self):
        """Connects the drains of the nmos/pmos together"""
        # Determines the top y-coordinate of the nmos drain metal layer
       
        yoffset = self.nmos_position1.y
        
       
        start = self.drain_position = vector(self.pmos1.active_contact_positions[0].x + 0.1 * drc["minwidth_metal1"] 
                                                + self.pmos_position1.x 
                                                + self.pmos1.active_contact.first_layer_position.x 
                                                + self.pmos1.active_contact.width / 2
                                                -  drc["minwidth_metal1"],
                                                 yoffset)
                                          
           
        end = vector(self.pmos1.active_contact_positions[0].x + 0.1 * drc["minwidth_metal1"]
                       + self.pmos1.active_contact.second_layer_position.x,
                       self.pmos_position1.y + self.pmos1.active_contact_positions[0].y)
           

        self.add_path("metal1",[start, end])

       
        start = vector(self.pmos2.active_contact_positions[1].x
                             + 0.5 * drc["minwidth_metal1"]
                             + drc["minwidth_metal1"] * 6.6
                             + self.pmos2.active_contact.second_layer_position.x,
                             yoffset)
                   
           
        end = vector(self.pmos2.active_contact_positions[1].x + 0.5 * drc["minwidth_metal1"]
                        + self.pmos2.active_contact.second_layer_position.x
                        + drc["minwidth_metal1"] * 7.5,
                        self.pmos_position2.y + self.pmos2.active_contact_positions[1].y)
           

        self.add_path("metal1",[start, end])

    def connect_sources_access_nmos_lima(self):
       
        """ Connecting drain of nmos1 and nmos3 sources"""

        yoffset = self.nmos_position1.y+3.5*drc["minwidth_metal1"]
        start = self.nmos_3_source_position = vector(self.pmos1.active_contact_positions[0].x + 0.5 * drc["minwidth_metal1"] 
                                                + self.pmos_position1.x 
                                                + self.pmos1.active_contact.first_layer_position.x 
                                                + self.pmos1.active_contact.width / 2
                                                - .5 * drc["minwidth_metal1"],
                                                 yoffset)
        end = vector(self.nmos3.active_contact_positions[1].x + drc["minwidth_metal1"],self.nmos_position4.y + self.nmos4.active_contact_positions[1].y)
      
        layer_stack_via1 = ["metal1", "via1", "metal2"]   
       
        via_offset=vector(self.pmos1.active_contact_positions[0].x  
                                                + self.pmos_position1.x 
                                                + self.pmos1.active_contact.first_layer_position.x 
                                                + self.pmos1.active_contact.width / 2
                                                - .5 * drc["minwidth_metal1"],
                                                 yoffset- 2*drc["minwidth_metal1"])
        self.add_via(layer_stack_via1,via_offset)
        layer_stack_via2 = ["metal2", "via2", "metal3"] 
        self.add_via(layer_stack_via2,via_offset)
      
        #layer_stack_via2 = ["metal2", "via2", "metal3"]  
       

        layer_stack_via1 = ["metal1", "via1", "metal2"]  
        via_offset=vector(self.nmos3.active_contact_positions[1].x +.1*drc["minwidth_metal2"],self.nmos_position4.y + self.nmos4.active_contact_positions[1].y-3.5*drc["minwidth_metal2"])
        
        self.add_via(layer_stack_via1,via_offset)
      

        layer_stack_via2 = ["metal2", "via2", "metal3"] 
        self.add_via(layer_stack_via2,via_offset)
        
        self.add_path("metal3",[start, end])


        start = vector(self.nmos3.active_contact_positions[1].x+ .5 * drc["minwidth_metal1"],self.nmos_position4.y + self.nmos4.active_contact_positions[1].y)
        end =  vector(self.nmos3.active_contact_positions[1].x +.5 * drc["minwidth_metal1"] ,self.nmos_position4.y + self.nmos4.active_contact_positions[1].y- 4.5*drc["minwidth_metal1"])

       


        self.add_path("metal3",[start, end])

        """ Connecting drain of nmos2 and nmos6 sources"""
        yoffset = self.nmos_position2.y+3.5*drc["minwidth_metal1"]
        start = self.nmos_2_source_position = vector(self.pmos2.active_contact_positions[1].x + 0.5 * drc["minwidth_metal1"] 
                                                + self.pmos_position2.x 
                                                + self.pmos2.active_contact.first_layer_position.x 
                                                + self.pmos2.active_contact.width / 2
                                                - .5 * drc["minwidth_metal1"],
                                                 yoffset)
        end =  vector(self.nmos6.active_contact_positions[1].x + 11* drc["minwidth_metal1"] ,self.nmos_position5.y + self.nmos4.active_contact_positions[1].y+3*drc["minwidth_metal1"])

        self.add_path("metal3",[start, end])

        """ Connecting the extension of drain of nmos2 and nmos6 sources"""

    
        "nmos2 via added"

        layer_stack_via1 = ["metal1", "via1", "metal2"]   
       
        via_offset=vector(self.pmos1.active_contact_positions[0].x  
                                                + self.pmos_position1.x 
                                                + self.pmos1.active_contact.first_layer_position.x 
                                                + self.pmos1.active_contact.width / 2
                                                + 6 * drc["minwidth_metal1"],
                                                 yoffset- 2*drc["minwidth_metal1"])
        self.add_via(layer_stack_via1,via_offset)


        layer_stack_via2 = ["metal2", "via2", "metal3"]  
        self.add_via(layer_stack_via2,via_offset)

        "nmos6 and nmos2 via added"
        end =  vector(self.nmos6.active_contact_positions[1].x + 10.7* drc["minwidth_metal1"] ,self.nmos_position5.y + self.nmos4.active_contact_positions[1].y-4.5*drc["minwidth_metal1"])
        layer_stack_via1 = ["metal1", "via1", "metal2"]   
       
        via_offset= end
        self.add_via(layer_stack_via1,via_offset)


        layer_stack_via2 = ["metal2", "via2", "metal3"]  
        self.add_via(layer_stack_via2,via_offset)

        start =  vector(self.nmos6.active_contact_positions[1].x + 10.79* drc["minwidth_metal1"] ,self.nmos_position5.y + self.nmos4.active_contact_positions[1].y+3.5*drc["minwidth_metal1"])
        end =  vector(self.nmos6.active_contact_positions[1].x + 10.79* drc["minwidth_metal1"] ,self.nmos_position5.y + self.nmos4.active_contact_positions[1].y-4.5*drc["minwidth_metal1"])
        self.add_path("metal3",[start, end])
       


    def connect_wordline_bitline_lima(self):    
        " BL1_bar:nmos3"
        start = vector(self.nmos3.active_contact_positions[0].x+drc["minwidth_metal1"]*.3 ,self.pmos_position1.y + self.pmos1.active_contact_positions[0].y+6*drc["minwidth_metal2"])
        
        end =   vector(self.nmos3.active_contact_positions[0].x+drc["minwidth_metal1"]*.3  ,self.nmos_position3.y + self.nmos3.active_contact_positions[0].y- 13.5*drc["minwidth_metal2"])
      
        offset = end
        self.add_path("metal2",[start, end])
        self.add_label(text="BL1_bar",
                      layer="metal2",
                      offset=offset)


        "BL2_bar:nmos4"

        start = vector(self.nmos4.active_contact_positions[1].x + 3.1*drc["minwidth_metal1"],self.pmos_position1.y + self.pmos1.active_contact_positions[0].y+6*drc["minwidth_metal2"])
        
        end =   vector(self.nmos4.active_contact_positions[1].x + 3.1*drc["minwidth_metal1"],self.nmos_position4.y + self.nmos4.active_contact_positions[1].y- 13.5*drc["minwidth_metal2"])
        
        self.add_path("metal2",[start, end])
        offset = end
        self.add_path("metal2",[start, end])
        self.add_label(text="BL2_bar",
                      layer="metal2",
                      offset=offset)


        " BL1:nmos5"
        start = vector(self.nmos5.active_contact_positions[0].x + 12*drc["minwidth_metal1"],self.pmos_position1.y + self.pmos1.active_contact_positions[0].y+6*drc["minwidth_metal2"])
        
        end =   vector(self.nmos5.active_contact_positions[0].x + 13*drc["minwidth_metal1"],self.nmos_position5.y + self.nmos5.active_contact_positions[0].y- 13.5*drc["minwidth_metal2"])
        
        self.add_path("metal2",[start, end])
        offset = end
        self.add_path("metal2",[start, end])
        self.add_label(text="BL1",
                      layer="metal2",
                      offset=offset)

        start = vector(self.nmos5.active_contact_positions[0].x + 10*drc["minwidth_metal1"],self.nmos5.height-10* drc["minwidth_metal1"])
        
        end =   vector(self.nmos5.active_contact_positions[0].x + 12*drc["minwidth_metal1"],self.nmos5.height-10* drc["minwidth_metal1"])
        
       
        "BL2:nmos6"

        start = vector(self.nmos6.active_contact_positions[1].x + 13.5*drc["minwidth_metal1"],self.pmos_position1.y + self.pmos1.active_contact_positions[0].y+6*drc["minwidth_metal2"])
        
        end =   vector(self.nmos6.active_contact_positions[1].x + 13.5*drc["minwidth_metal1"],self.nmos_position6.y + self.nmos6.active_contact_positions[1].y- 13.5*drc["minwidth_metal2"])
        
        self.add_path("metal2",[start, end])
        offset = end
        self.add_path("metal2",[start, end])
        self.add_label(text="BL2",
                      layer="metal2",
                      offset=offset)

    def route_input_gate_A_lima(self):
        """ routing for input A """

        xoffset = self.pmos1.poly_positions[0].x
        yoffset = (self.height 
                       - (drc["minwidth_metal1"] 
                              + drc["metal1_to_metal1"] 
                              + self.pmos2.active_height 
                              + drc["metal1_to_metal1"] 
                              + self.pmos2.active_contact.second_layer_width
                              + 2*drc["metal1_to_metal1"]))

        if (self.nmos_width == drc["minwidth_tx"]):
            yoffset = (self.pmos_position1.y 
                        + self.pmos1.poly_positions[0].y
                        + drc["poly_extend_active"] 
                        - (self.pmos1.active_contact.height 
                               - self.pmos1.active_height) / 2 
                        - drc["metal1_to_metal1"]  
                        - self.poly_contact.width)
        #lima
        offset = [xoffset+2.2*drc["minwidth_metal1"], yoffset]
        self.add_contact(layers=("poly", "contact", "metal1"),
                         offset=offset,
                         size=(1,1),
                         rotate=270)
        
        yoffset = yoffset - drc["metal1_to_metal1"]
        offset = [xoffset+2*drc["minwidth_metal1"], yoffset]
        offset = offset - self.poly_contact.first_layer_position.rotate_scale(-1,0)
        #lima
      
        #lima
        input_length = (self.pmos2.poly_positions[0].x + self.pmos1.poly_positions[0].x+2*drc["minwidth_metal1"]) 
                        #- self.poly_contact.height)
        yoffset += self.poly_contact.via_layer_position.x
        offset = self.input_position1 = vector(xoffset+.05+1.25*drc["minwidth_metal1"], yoffset)
        self.add_rect(layer="metal1",
                      offset=offset,
                      width=input_length-drc["minwidth_metal1"],
                      height=drc["minwidth_metal1"])
        self.add_label(text="Q",
                       layer="metal1",
                       offset=offset)

    def route_input_gate_B_lima(self):
        """ routing for input B """
        xoffset = (self.pmos2.poly_positions[0].x
                       + self.pmos_position2.x + .6*drc["minwidth_poly"])
        yoffset = (drc["minwidth_metal1"] 
                       + drc["metal1_to_metal1"]
                       + self.nmos2.active_height
                       + drc["minwidth_metal1"])
        if (self.nmos_width == drc["minwidth_tx"]):
            yoffset = (self.nmos_position1.y 
                        + self.nmos1.poly_positions[0].y 
                        + self.nmos1.poly_height 
                        + drc["metal1_to_metal1"])
        offset = [xoffset, yoffset]
        self.add_contact(layers=("poly", "contact", "metal1"),
                         offset=offset,
                         size=(1,1),
                         rotate=90)

       
        input_length = self.pmos_position2.x
        xoffset= self.pmos1.active_contact_positions[0].x
        self.input_position2 = vector(xoffset+5*drc["minwidth_metal1"],
                                      # + 3*self.poly_contact.width, 
                                      yoffset + self.poly_contact.via_layer_position.x)
        self.add_rect(layer="metal1",
                      offset=self.input_position2.scale(.5,1),
                      width=input_length,
                      height=drc["minwidth_metal1"])

        self.add_label(text="Q_bar",
                       layer="metal1",
                       offset=self.input_position2.scale(.5,1))
      

   
    def connect_rails_lima(self):
        """  Connect transistor pmos drains to vdd and nmos drains to gnd rail """
        correct = vector(self.pmos1.active_contact.width ,
                         0).scale(.5,0)
        poffset = self.pmos_position1 + self.pmos1.active_contact_positions[1] + correct
        temp_height = self.height - poffset.y
        self.add_rect(layer="metal1",
                      offset=poffset, width=drc["minwidth_metal1"],
                      height=temp_height)

        poffset = vector(2 * self.pmos_position2.x + correct.x
                         + self.pmos2.active_contact_positions[1].x , poffset.y)
       

        poffset = self.nmos_position1 + self.nmos1.active_contact_positions[1] + correct
        self.add_rect(layer="metal1",
                      offset=poffset.scale(1,0),
                      width=drc["minwidth_metal1"],
                      height=temp_height)
   

    def extend_wells_access_nmos_lima(self):
        """ Extension of well """
        
        yoffset_nmos3=self.nmos_position3+ vector(0,self.nmos3.height-12* drc["minwidth_metal1"])
        offset = self.pwell_position_1 = vector(0, yoffset_nmos3 )
      

       
        """ Extension of well"""
        middle_point = (self.nmos_position1.y + self.nmos1.pwell_position.y
                           + self.nmos1.well_height
                           + (self.pmos_position1.y + self.pmos1.nwell_position.y
                               - self.nmos_position1.y - self.nmos1.pwell_position.y
                               - self.nmos1.well_height) / 2)
      

        offset = self.pwell_position = vector(0,(self.nmos3.height-12*drc["minwidth_metal1"]-self.nmos3.height))
        self.pwell_height = self.nmos3.height+drc["minwidth_well"]-2*drc["minwidth_metal1"]
        self.add_rect(layer="pwell",
                      offset=offset,
                      width=self.well_width*1.8,
                      height=self.pwell_height)
        self.add_rect(layer="vtg",
                      offset=offset,
                      width=self.well_width*1.8,
                      height=self.pwell_height)

    
        
