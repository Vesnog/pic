# Copyright (C) 2020 Luceda Photonics
# Modified by Ongun Arisev to be used in the context of Silicon Photonics Design, Fabrication and Data Analysis EdX course

from siepic import all as pdk
from ipkiss3 import all as i3
import numpy as np
import pylab as plt
from mzi_pcell_ybranch import MZI_YB
from mzi_pcell_bdc import MZI_BDC
from datetime import datetime

# The optimization functions to determine the lenghts of the long arm of the interferometers
def define_control_point_mzi_bdc(delay_length, bend_radius, control_point_y):
    """Defines a control point based on the desired delay_length for MZI with BDC"""

    def f(x):
        device = MZI_BDC(
            control_point=(x[0], control_point_y),
            bend_radius=bend_radius,
        )
        right_arm_length = device.get_connector_instances()[1].reference.trace_length()
        left_arm_length = device.get_connector_instances()[0].reference.trace_length()
        current_delay_length = right_arm_length - left_arm_length
        cost = current_delay_length - delay_length
        return np.abs(cost)

    from scipy.optimize import minimize

    control_point_x = minimize(f, x0=np.array(70.0), tol=1e-2, bounds=((45.0, 200.0),)).x[0]
    return control_point_x, control_point_y


def define_control_point_mzi_yb(delay_length_tuple, bend_radius, cp_y_tup):
    """Defines a control point based on the desired delay_length for MZI with Y-branch"""

    def f(x):
        device = MZI_YB(
            control_point1=(x[0], cp_y_tup[0]),
            control_point2=(x[1], cp_y_tup[1]),
            bend_radius=bend_radius,
        )
        mzi1_long_arm_length = device.get_connector_instances()[0].reference.trace_length()
        mzi1_short_arm_length = device.get_connector_instances()[1].reference.trace_length()
        mzi2_long_arm_length = device.get_connector_instances()[2].reference.trace_length()
        mzi2_short_arm_length = device.get_connector_instances()[3].reference.trace_length()
        mzi1_delay_length = mzi1_long_arm_length - mzi1_short_arm_length
        mzi2_delay_length = mzi2_long_arm_length - mzi2_short_arm_length
        cost1 = mzi1_delay_length - delay_length_tuple[0]
        cost2 = mzi2_delay_length - delay_length_tuple[1]
        cost = cost1**2 + cost2**2
        return np.abs(cost)

    from scipy.optimize import minimize

    cp_x_tup = minimize(f, x0=np.array([70.0, 70.0]), tol=1e-2).x
    return [(x , cp_y_tup[i]) for i, x in enumerate(cp_x_tup)]


# Parameters for the MZI Y-branch sweep
delay_lengths_tuples = [(50.0, 100.0), (150.0, 200.0)]
bend_radius = 5.0
x0 = 40.0
y0 = 20.0
spacing_x = 80.0

insts = dict()
specs = []

# Create the floor plan for EdX design area
floorplan = pdk.FloorPlan(name="FLOORPLAN", size=(605.0, 410.0))

# Add the floor plan to the instances dict and place it at (0.0, 0.0)
insts["floorplan"] = floorplan
specs.append(i3.Place("floorplan", (0.0, 0.0)))

# Create the MZI sweep for MZIs with Y-branches
for ind, delay_length in enumerate(delay_lengths_tuples, start=1):
    cp = define_control_point_mzi_yb(
        delay_length_tuple=delay_length,
        bend_radius=bend_radius,
        cp_y_tup=(77, 177),
    )

    # Instantiate the MZI
    mzi_yb = MZI_YB(
        name="MZI_YB{}".format(ind),
        control_point1=cp[0],
        control_point2=cp[1],
        bend_radius=bend_radius,
    )

    # Calculate the actual delay length and print the results
    mzi1_long_arm_length = mzi_yb.get_connector_instances()[0].reference.trace_length()
    mzi1_short_arm_length = mzi_yb.get_connector_instances()[1].reference.trace_length()
    mzi2_long_arm_length = mzi_yb.get_connector_instances()[2].reference.trace_length()
    mzi2_short_arm_length = mzi_yb.get_connector_instances()[3].reference.trace_length()
    mzi1_delay_length = mzi1_long_arm_length - mzi1_short_arm_length
    mzi2_delay_length = mzi2_long_arm_length - mzi2_short_arm_length

    print(
        mzi_yb.name,
        "Desired delay length = {} um".format(delay_length),
        "Actual delay length = {} um".format((mzi1_delay_length, mzi2_delay_length)),
        "Control points 1 = {}".format(cp[0]),
        "Control points 2 = {}".format(cp[1]),
    )

    # Add the MZI to the instances dict and place it
    mzi_cell_name = "mzi_yb{}".format(ind)
    insts[mzi_cell_name] = mzi_yb
    specs.append(i3.Place(mzi_cell_name, (x0, y0)))

    x0 += spacing_x


x0 += 40
spacing_x = 120
# The MZIs with BDC
delay_lengths = [100.0, 200.0]

# Create the MZI sweep for MZIs with BDCs
for ind, delay_length in enumerate(delay_lengths, start=1):
    cp = define_control_point_mzi_bdc(
        delay_length=delay_length,
        bend_radius=bend_radius,
        control_point_y=240.0,
    )

    # Instantiate the MZI
    mzi_bdc = MZI_BDC(
        name="MZI_BDC{}".format(ind),
        control_point=cp,
        bend_radius=bend_radius,
    )

    # Calculate the actual delay length and print the results
    right_arm_length = mzi_bdc.get_connector_instances()[1].reference.trace_length()
    left_arm_length = mzi_bdc.get_connector_instances()[0].reference.trace_length()
    actual_delay_length = right_arm_length - left_arm_length

    print(
        mzi_bdc.name,
        "Desired delay length = {} um".format(delay_length),
        "Actual delay length = {} um".format(actual_delay_length),
        "Control point = {}".format(cp),
    )

    # Add the MZI to the instances dict and place it
    mzi_cell_name = "mzi_bdc{}".format(ind)
    insts[mzi_cell_name] = mzi_bdc
    specs.append(i3.Place(mzi_cell_name, (x0, y0)))

    x0 += spacing_x


# Create the final design with i3.Circuit
cell = i3.Circuit(
    name=f"EBeam_OngunArisev_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}",
    insts=insts,
    specs=specs,
)

# Bigger visualization
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['figure.dpi'] = 100

# Layout
cell_lv = cell.Layout()
cell_lv.visualize(annotate=True)
cell_lv.visualize_2d()
cell_lv.write_gdsii("EBeam_Vesnog_IPKISS.gds")

# Circuit model
cell_cm = cell.CircuitModel()
wavelengths = np.linspace(1.52, 1.58, 4001)
S_total = cell_cm.get_smatrix(wavelengths=wavelengths)

# Plotting
fig, axs = plt.subplots(4, sharex="all", figsize=(12, 18))

for ind, delay_length in enumerate(delay_lengths_tuples, start=1):
    # After the colon the mode is selected (two modes) / for the particular examples S-matrix has 12x12x2 entries
    # not counting the ones due to wavelength
    tr_out1 = i3.signal_power_dB(S_total["mzi_yb{}_out1:0".format(ind), "mzi_yb{}_in:0".format(ind)])
    tr_out2 = i3.signal_power_dB(S_total["mzi_yb{}_out2:0".format(ind), "mzi_yb{}_in:0".format(ind)])

    # Indices of the axes will be zero based
    ax_idx = ind - 1
    axs[ax_idx].plot(wavelengths, tr_out1, "-", linewidth=2.2, label="TE - MZI_YB{}:out1".format(ind))
    axs[ax_idx].plot(wavelengths, tr_out2, "-", linewidth=2.2, label="TE - MZI_YB{}:out2".format(ind))

    axs[ax_idx].set_ylabel("Transmission [dB]", fontsize=16)
    axs[ax_idx].set_title("MZI_YB{} - Delay length {} um".format(ind, delay_length), fontsize=16)
    axs[ax_idx].legend(fontsize=14, loc=4)

for ind2, delay_length in enumerate(delay_lengths, start=1):
    tr_out1 = i3.signal_power_dB(S_total["mzi_bdc{}_out1:0".format(ind2), "mzi_bdc{}_in:0".format(ind2)])
    tr_out2 = i3.signal_power_dB(S_total["mzi_bdc{}_out2:0".format(ind2), "mzi_bdc{}_in:0".format(ind2)])

    # Indices of the axes will be zero based
    ax_idx2 = ind2 + ax_idx
    axs[ax_idx2].plot(wavelengths, tr_out1, "-", linewidth=2.2, label="TE - MZI_BDC{}:out1".format(ind2))
    axs[ax_idx2].plot(wavelengths, tr_out2, "-", linewidth=2.2, label="TE - MZI_BDC{}:out2".format(ind2))

    axs[ax_idx2].set_ylabel("Transmission [dB]", fontsize=16)
    axs[ax_idx2].set_title("MZI_BDC{} - Delay length {} um".format(ind2, delay_length), fontsize=16)
    axs[ax_idx2].legend(fontsize=14, loc=4)

axs[-1].set_xlabel("Wavelength [um]", fontsize=16)
plt.show()

print("Done")
