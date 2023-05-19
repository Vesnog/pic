import ipkiss3.all as i3
# From: https://docs.lucedaphotonics.com/reference/technology/
# Define a Donut pcell


class Donut(i3.PCell):
    radius = i3.PositiveNumberProperty(default=10.0)
    inner_radius = i3.PositiveNumberProperty(default=5.0)

    class Layout(i3.LayoutView):
        def _generate_elements(self, elems):
            elems += i3.Circle(layer=i3.Layer(0), radius=self.radius)
            elems += i3.Circle(layer=i3.Layer(1), radius=self.inner_radius)
            elems += i3.Rectangle(layer=i3.Layer(2), center=(-10, 0), box_size=(1, 1))
            elems += i3.Rectangle(layer=i3.Layer(2), center=(10, 0), box_size=(1, 1))
            return elems


# instantiate the cell and visualize its layout
donut = Donut(radius=15.0, inner_radius=5.0)
donut_lo = donut.Layout()
donut_lo.visualize()


# Define materials, material stacks and virtual fabrication

from pysics.basics.material.material import Material
from pysics.basics.material.material_stack import MaterialStack
from ipkiss.visualisation.display_style import DisplayStyle
from ipkiss.visualisation.color import *
from ipkiss.plugins.vfabrication.process_flow import VFabricationProcessFlow

oxide = Material(name="oxide", display_style=DisplayStyle(color=COLOR_SCARLET))
air = Material(name="air", display_style=DisplayStyle(color=COLOR_BLUE))
metal = Material(name="metal", display_style=DisplayStyle(color=COLOR_SILVER))

stack_oxide = MaterialStack(name="oxide slab",
                            materials_heights=[
                                (air, 1.0),
                                (oxide, 0.5),
                                (air, 1.0)
                            ],
                            display_style=DisplayStyle(color=COLOR_SCARLET)
                            )

stack_air = MaterialStack(name="all air",
                            materials_heights=[
                                (air, 1.0),
                                (air, 0.5),
                                (air, 1.0)
                            ],
                            display_style=DisplayStyle(color=COLOR_BLUE)
                            )

stack_metal = MaterialStack(name="metal",
                                materials_heights=[
                                    (air, 0.5),
                                    (metal, 0.2),
                                    (air, 0.3),
                                    (oxide, 0.5),
                                    (air, 1.0),
                                ],
                                display_style=DisplayStyle(color=COLOR_SILVER)
                            )

oxide_dep = i3.ProcessLayer(name="oxide", extension="OX")
oxide_etch = i3.ProcessLayer(name="oxide etch", extension="NOX")
metalization = i3.ProcessLayer(name="metalization", extension="M")

vfab = VFabricationProcessFlow(
    active_processes=[oxide_dep, oxide_etch, metalization],
    process_layer_map={
        oxide_dep: i3.Layer(0),
        oxide_etch: i3.Layer(1),
        metalization: i3.Layer(2),
    },
    is_lf_fabrication={
        oxide_dep: False,
        oxide_etch: False,
        metalization: False,
    },
    process_to_material_stack_map=[
        ((0, 0, 0), stack_air),    # When we have nothing (the background)
        ((1, 0, 0), stack_oxide),  # When we only have the first layer
        ((1, 1, 0), stack_air),  # When we have the first two layers
        ((1, 1, 1), stack_metal),  # When we have all the layers
        ((1, 0, 1), stack_metal),  # When we only have the first and last layer
    ]
)

# visualize virtual fabrication of the layout: top-down and cross-section

donut_lo.visualize_2d(process_flow=vfab)
# The cross-section start/end points in x and y coordinates
xs = donut_lo.cross_section(cross_section_path=i3.Shape([(-20.0, 0.0), (20.0, 0.0)]),
                            process_flow=vfab)
xs.visualize()
