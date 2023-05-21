# Copyright (C) 2020 Luceda Photonics

from siepic import all as pdk
from siepic import technology
from ipkiss3 import all as i3
from ipkiss.process.layer_map import GenericGdsiiPPLayerOutputMap
from bond_pads import BondPad, Heater, pplayer_map, wire_template
import pylab as plt
import numpy as np


class MZI_YB_thermo(i3.Circuit):
    bend_radius = i3.PositiveNumberProperty(default=5.0, doc="Bend radius of the waveguides")
    heater_width = i3.PositiveNumberProperty(default=4.0, doc="Heater width")
    heater_length = i3.PositiveNumberProperty(default=100.0, doc="Heater length in microns")
    heater_size = i3.Coord2Property(default=(4.0, 100.0), doc="Heater size")
    arm_spacing = i3.PositiveNumberProperty(default=20, doc="MZI arms spacing")
    fgc = i3.ChildCellProperty(doc="PCell for the fiber grating coupler")
    splitter = i3.ChildCellProperty(doc="PCell for the Y-Branch")
    fgc_spacing_y = i3.PositiveNumberProperty(default=127.0, doc="Fiber separation")
    bond_pad_spacing_y = i3.PositiveNumberProperty(default=125.0, doc="Electrical bond pad separation")
    bond_pad_GC_dist = i3.PositiveNumberProperty(default=350.0, doc="Bond pad GC distance")
    measurement_label_position = i3.Coord2Property(doc="Placement of automated measurement label")
    measurement_label_pretext = "opt_in_TE_1550_device_Vesnog_"
    elec_meas_label_position = i3.Coord2Property(doc="Placement of automated measurement label for electrical interface")
    bond_pad1 = BondPad(name="Bond_Pad_1")
    bond_pad2 = BondPad(name="Bond_Pad_2")
    heater = Heater(name="Heater")

    def _default_elec_meas_label_position(self):
        return self.bond_pad2.measurement_label_position + (self.bond_pad_GC_dist, self.bond_pad_spacing_y)

    def _default_measurement_label_position(self):
        return 0.0, self.fgc_spacing_y

    def _default_fgc(self):
        return pdk.EbeamGCTE1550()

    def _default_splitter(self):
        return pdk.EbeamY1550()

    def _default_insts(self):
        insts = {
            "fgc_1": self.fgc,
            "fgc_2": self.fgc,
            "yb_s1": self.splitter,
            "yb_c1": self.splitter,
            "bp_1": self.bond_pad1,
            "bp_2": self.bond_pad2,
            "heater": self.heater,
        }
        return insts

    def _default_specs(self):
        fgc_spacing_y = self.fgc_spacing_y
        mzi_splitter_x = 150
        # Instantiate the heater
        hl = self.heater.Layout(size=(self.heater_width, self.heater_length))
        x_pos = mzi_splitter_x + self.arm_spacing / 2
        y_pos = fgc_spacing_y / 2

        specs = [
            i3.Place("fgc_1:opt1", (0, 0)),
            i3.PlaceRelative("fgc_2:opt1", "fgc_1:opt1", (0.0, fgc_spacing_y)),
            # Adhere by the placement rules to avoid metal burning damaging the fiber array
            i3.PlaceRelative("yb_s1:opt1", "fgc_2:opt1", (mzi_splitter_x, 40.0), angle=90),
            i3.PlaceRelative("yb_c1:opt1", "fgc_1:opt1", (mzi_splitter_x, -40.0), angle=-90),
            # Place the electrical bond pads
            i3.Place("bp_1", (self.bond_pad_GC_dist, 0)),
            i3.Place("bp_2", (self.bond_pad_GC_dist, self.bond_pad_spacing_y)),
            # Place the heater
            i3.Place("heater", (x_pos, y_pos))
        ]

        specs += [
            i3.ConnectManhattan("fgc_2:opt1", "yb_s1:opt1", control_points=[i3.V(15)]),
            i3.ConnectManhattan("yb_c1:opt1", "fgc_1:opt1", control_points=[i3.V(15)]),
            i3.ConnectManhattan("yb_s1:opt3", "yb_c1:opt2", control_points=[i3.V(mzi_splitter_x - self.arm_spacing/2)]),
            i3.ConnectManhattan("yb_s1:opt2", "yb_c1:opt3", control_points=[i3.V(mzi_splitter_x + self.arm_spacing/2)]),
            i3.ConnectManhattan("bp_1:e_out", "heater:e_in1", rounding_algorithm=None,
                                trace_template=wire_template, control_points=[i3.V(225)]),
            i3.ConnectManhattan("bp_2:e_out", "heater:e_in2", rounding_algorithm=None,
                                trace_template=wire_template, control_points=[i3.V(225)]),
        ]
        return specs

    def _default_exposed_ports(self):
        exposed_ports = {
            "fgc_2:fib1": "in",
            "fgc_1:fib1": "out",
        }
        return exposed_ports

    class CircuitModel(i3.CircuitModelView):
        def _generate_model(self):
            # Remove the electrical layers
            to_remove = ['bp_1', 'bp_2', 'heater']
            new_instances = {}
            netlist_view = self.netlist_view
            for key, value in netlist_view.netlist.instances.items():
                flag = map(lambda x: x in key, to_remove)
                if not any(flag):
                    new_instances[key] = value
            netlist_view.netlist.instances = new_instances
            return i3.HierarchicalModel.from_netlistview(netlist_view)


if __name__ == "__main__":

    # Layout
    mzi = MZI_YB_thermo(
        name="MZI",
        bend_radius=5.0,
    )
    output_layer_map = GenericGdsiiPPLayerOutputMap(pplayer_map=pplayer_map)
    mzi_layout = mzi.Layout()
    fig = mzi_layout.visualize(annotate=True)
    mzi_layout.visualize_2d()
    mzi_layout.write_gdsii("mzi_heater.gds", layer_map=output_layer_map)

    # Circuit model
    my_circuit_cm = mzi.CircuitModel()
    wavelengths = np.linspace(1.52, 1.58, 4001)
    S_total = my_circuit_cm.get_smatrix(wavelengths=wavelengths)

    # Plotting
    fig, ax = plt.subplots()
    ax.plot(wavelengths, i3.signal_power_dB(S_total["out:0", "in:0"]), "-", linewidth=2.2, label="TE-out1")
    ax.set_xlabel("Wavelength [um]", fontsize=16)
    ax.set_ylabel("Transmission [dB]", fontsize=16)
    ax.legend(fontsize=14, loc=4)
    plt.show()