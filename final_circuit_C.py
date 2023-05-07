# Copyright (C) 2020 Luceda Photonics
# Modified by Ongun Arisev to be used in the context of Silicon Photonics Design, Fabrication and Data Analysis EdX course

from siepic import all as pdk
from ipkiss3 import all as i3
from ipkiss3 import constants
from ipkiss.process.layer_map import GenericGdsiiPPLayerOutputMap
from pteam_library_siepic.all import UnitCellRectangular, UniformWBG
from wbg_cell import WBGCircuit

from datetime import datetime
import numpy as np
import pylab as plt

# We make a copy of the layer dictionary to freely modify it
pplayer_map = dict(i3.TECH.GDSII.LAYERTABLE)
# Write the content to be written on WG_P6NM on Silicon layer directly
pplayer_map[i3.TECH.PROCESS.WG_P6NM, i3.TECH.PURPOSE.DRAWING] = pplayer_map[i3.TECH.PROCESS.WG, i3.TECH.PURPOSE.DRAWING]
output_layer_map = GenericGdsiiPPLayerOutputMap(pplayer_map=pplayer_map)

x0 = 40.0
y0 = 15.0
spacing_x = 80.0

insts = dict()
specs = []

# Create the floor plan for EdX design area
floorplan = pdk.FloorPlan(name="FLOORPLAN", size=(605.0, 410.0))

# Add the floor plan to the instances dict and place it at (0.0, 0.0)
insts["floorplan"] = floorplan
specs.append(i3.Place("floorplan", (0.0, 0.0)))
# Initialize the text label dictionary
text_label_dict = {}  # Text labels dictionary for automated measurement labels
circuit_cell_names = []  # Constituent circuit cell names list

########################################################################################################################
# Set up the unit cell, WBG and then the full circuit.
########################################################################################################################

width = 0.5
deltawidth = 0.089
dc = 0.2
lambdab = 0.325

# First parameter variation
uc1 = UnitCellRectangular(
    width=width,
    deltawidth=deltawidth,
    length1=(1 - dc) * lambdab,
    length2=dc * lambdab,
)

wbg1 = UniformWBG(uc=uc1, n_uc=300)
wbg_circuit_name1 = "WBGc1"
wbg_circuit1 = WBGCircuit(wbg=wbg1, name=wbg_circuit_name1)
# Add the circuit
insts[wbg_circuit_name1] = wbg_circuit1
specs.append(i3.Place(wbg_circuit_name1, (x0, y0)))
# Put the measurement label
meas_label = f"{wbg_circuit1.measurement_label_pretext}{wbg_circuit_name1}"
meas_label_coord = wbg_circuit1.measurement_label_position + (x0, y0)
text_label_dict[wbg_circuit_name1] = [meas_label, meas_label_coord]
circuit_cell_names.append(wbg_circuit_name1)

###

x0 += 290
width = 0.49
deltawidth = 0.079
dc = 0.2
lambdab = 0.315

# First parameter variation
uc2 = UnitCellRectangular(
    width=width,
    deltawidth=deltawidth,
    length1=(1 - dc) * lambdab,
    length2=dc * lambdab,
)

wbg2 = UniformWBG(uc=uc2, n_uc=300)
wbg_circuit_name2 = "WBGc2"
wbg_circuit2 = WBGCircuit(wbg=wbg2, name=wbg_circuit_name2)
# Add the circuit
insts[wbg_circuit_name2] = wbg_circuit2
specs.append(i3.Place(wbg_circuit_name2, (x0, y0)))
# Put the measurement label
meas_label = f"{wbg_circuit2.measurement_label_pretext}{wbg_circuit_name2}"
meas_label_coord = wbg_circuit2.measurement_label_position + (x0, y0)
text_label_dict[wbg_circuit_name2] = [meas_label, meas_label_coord]
circuit_cell_names.append(wbg_circuit_name2)


# Create the final design with i3.Circuit
top_cell = i3.Circuit(
    name=f"EBeam_OngunArisev_C_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}",
    insts=insts,
    specs=specs,
)

# Bigger visualization
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['figure.dpi'] = 100

# Any number of layout primitives can be added here
text_elems = []
# For the GDS text elements for automated measurement
for cell in circuit_cell_names:
    text_label = text_label_dict[cell][0]
    text_label_coord = text_label_dict[cell][1]
    text_elems += i3.Label(layer=i3.TECH.PPLAYER.TEXT, text=text_label,
                          coordinate=text_label_coord,
                          alignment=(constants.TEXT.ALIGN.LEFT, constants.TEXT.ALIGN.BOTTOM), height=2)

# Layout
filename = "EBeam_Vesnog_C.gds"
cell_lv = top_cell.Layout()
cell_lv.append(text_elems)
cell_lv.visualize(annotate=True)
cell_lv.visualize_2d()
cell_lv.write_gdsii(filename, layer_map=output_layer_map)

# Circuit model
cell_cm = top_cell.CircuitModel()
wavelengths = np.linspace(1.52, 1.58, 4001)
S_total = cell_cm.get_smatrix(wavelengths=wavelengths)

print("Done")