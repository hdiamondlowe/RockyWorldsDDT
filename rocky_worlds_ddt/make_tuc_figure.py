#! /usr/bin/env python
"""
Generate Targets Under Consideration Figure

Authors
-------
- Mees Fix

Use
---
>>> from rocky_worlds_ddt.make_tuc_figure import make_tuc_figure
"""

from jinja2 import Template
import pathlib

from astropy.io import ascii
from bokeh.embed import components
from bokeh.models import (
    PanTool,
    ResetTool,
    SaveTool,
    WheelPanTool,
    BoxZoomTool,
    HoverTool,
    Legend,
    LegendItem,
    Arrow,
    NormalHead,
    Label,
    TapTool,
    OpenURL,
)
from bokeh.models import ColumnDataSource, FixedTicker
from bokeh.plotting import figure
from bokeh.themes import Theme
from bokeh.resources import CDN
import numpy as np


class make_tuc_figure:
    """Make TUC Interactive Figure"""

    def __init__(self, filename):
        self.filename = pathlib.Path(filename)
        self.data = ascii.read(
            self.filename, format="fixed_width", header_rows=["name", "dtype"]
        )
        self.calculate_cosmic_shoreline()
        self.build_figure()

    def build_figure(self, width=1200, height=800):
        """Incrementally build TUC figure using Bokeh."""

        # Define Source Data Object
        # -------------------------
        source = ColumnDataSource(
            data=dict(
                v_esc=self.data["v_esc"],
                I=self.data["I"],
                planet_name=self.data["planet_name"],
                fill_color=self.data["fill_color"],
                line_color=self.data["line_color"],
            )
        )

        # Set theme for custom font type to match website.
        theme = Theme(
            json={
                "attrs": {
                    "Axis": {
                        "axis_label_text_font": "Oswald",
                    },
                    "Title": {
                        "text_font": "Oswald",
                    },
                    "Legend": {
                        "label_text_font": "Oswald",
                    },
                    "Label": {
                        "text_font": "Oswald",
                    },
                }
            }
        )

        # Generate figure object
        # ----------------------
        self.p = figure(
            width=width,
            height=height,
            x_axis_type="log",
            y_axis_type="log",
            tools=[
                HoverTool(),
                PanTool(),
                ResetTool(),
                SaveTool(),
                WheelPanTool(),
                BoxZoomTool(),
                TapTool(),
            ],
            tooltips=[
                ("Target Name", "@planet_name"),
                ("Escape Velocity", "@v_esc"),
                ("Irradiance", "@I"),
            ],
        )

        # Figure Configuration
        # --------------------
        # Axis Labels
        self.p.axis.axis_label_text_font_style = "bold"

        self.p.xaxis.axis_label = "Escape Velocity [km/s]"
        self.p.xaxis.axis_label_text_font_size = "25pt"

        self.p.yaxis.axis_label = "I (Relative Cummulative XUV Irradiation)"
        self.p.yaxis.axis_label_text_font_size = "20pt"

        self.p.title = "Rocky Worlds DDT -- Targets Under Consideration (TUC)"
        self.p.title.text_font_size = "25pt"

        url = f"https://exoplanetarchive.ipac.caltech.edu/overview/@planet_name#planet_{'@planet_name'.replace(' ', '-')}_collapsible"
        taptool = self.p.select(type=TapTool)
        taptool.callback = OpenURL(url=url)

        # Axis Tick Formatting
        self.p.xaxis.ticker = FixedTicker(ticks=[4, 5, 6, 7, 8, 9, 10, 20])
        self.p.yaxis.ticker = FixedTicker(ticks=[0.1, 1, 10, 100, 1000, 10000])
        self.p.xaxis.major_label_text_font_size = "15pt"
        self.p.yaxis.major_label_text_font_size = "15pt"

        # Set the x-axis limits
        self.p.x_range.start = 4
        self.p.x_range.end = 25

        # Set the x-axis limits
        self.p.y_range.start = 0.1
        self.p.y_range.end = 1e4

        # Data Plotting
        # -------------
        self.p.line(
            self.cosmic_shoreline_fit_x,
            self.cosmic_shoreline_fit_y,
            line_width=10,
            alpha=0.5,
            color="cornflowerblue",
        )

        scatter_glyph = self.p.scatter(
            "v_esc",
            "I",
            color="fill_color",
            line_color="line_color",
            line_width=2,
            size=15,
            source=source
        )

        self.p.hover.renderers = [scatter_glyph]  # hover only for scatters

        # Legend Settings
        # ---------------
        # Defining Custom Legend Items
        legend_items = [
            LegendItem(
                label="TUC List Object (Precise Mass Constraint)",
                renderers=[
                    self.p.scatter(
                        1,
                        1,
                        color="grey",
                        line_color="mediumseagreen",
                        line_width=2,
                        size=15,
                    )
                ],
            ),
            LegendItem(
                label="TUC List Object (No Mass Constraint)",
                renderers=[
                    self.p.scatter(
                        1,
                        1,
                        color="grey",
                        line_color="darkred",
                        line_width=2,
                        size=15,
                    )
                ],
            ),
            LegendItem(
                label="Rocky Worlds DDT Targets",
                renderers=[
                    self.p.scatter(
                        1,
                        1,
                        color="darkorange",
                        line_color="mediumseagreen",
                        line_width=2,
                        size=15,
                    )
                ],
            ),
            LegendItem(
                label="Solar System Planets",
                renderers=[
                    self.p.scatter(
                        1,
                        1,
                        color="lightblue",
                        line_color="mediumseagreen",
                        line_width=2,
                        size=15,
                    )
                ],
            ),
            LegendItem(
                label="Cosmic Shoreline",
                renderers=[
                    self.p.line(
                        1,
                        1,
                        color="cornflowerblue",
                        line_width=10,
                    )
                ],
            ),
        ]

        # Create a legend object
        legend = Legend(items=legend_items, location="bottom_right")
        self.p.add_layout(legend)

        # Configure legend
        self.p.legend.label_text_font_size = "15pt"
        self.p.legend.border_line_width = 3
        self.p.legend.border_line_color = "black"

        # Add Arrow Annotations
        # ---------------------
        # Less likely arrow
        nh = NormalHead(fill_color="darkorange", line_color="darkorange")
        self.p.add_layout(
            Arrow(
                end=nh,
                line_color="darkorange",
                line_width=5,
                x_start=5.75,
                y_start=1.25,
                x_end=5,
                y_end=1.5e1,
            )
        )
        self.p.add_layout(
            Label(
                x=5.0,
                y=2.0e1,
                text="Atmospheres Less Likely",
                text_color="darkorange",
                text_font_size="20pt",
            )
        )

        # More likely arrow
        nh = NormalHead(fill_color="darkblue", line_color="darkblue")
        self.p.add_layout(
            Arrow(
                end=nh,
                line_color="darkblue",
                line_width=5,
                x_start=9,
                y_start=4.5,
                x_end=10,
                y_end=5e-1,
            )
        )
        self.p.add_layout(
            Label(
                x=6.5,
                y=0.25,
                text="Atmospheres More Likely",
                text_color="darkblue",
                text_font_size="20pt",
            )
        )

        # HTML template that allow us to use custom fonts from Google.
        template = Template("""<!DOCTYPE html>
                                <html lang="en">
                                    <head>
                                        <meta charset="utf-8">
                                        <title>Basemap</title>
                                        <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Oswald" />
                                        {{ resources }}
                                        {{ script }}
                                    </head>
                                    <body>
                                        {{ div }}
                                    </body>
                                </html>
                                """)

        self.script, self.div = components(self.p, theme=theme)
        resources = CDN.render()
        self.html = template.render(
            resources=resources, script=self.script, div=self.div
        )

    def calculate_cosmic_shoreline(self):
        # instellation at bottom of CS in Zanle & atling
        I_x = 6.191017244909004
        # escape velocity at crossing
        ve_x = 9.382264934578679
        constant = I_x / (ve_x**4)

        self.cosmic_shoreline_fit_x = np.linspace(0.1, 200, 20000)
        self.cosmic_shoreline_fit_y = constant * (self.cosmic_shoreline_fit_x**4)

    def save_tuc_plot(self, outfile="tuc_figure.html"):
        """Save Targets Under Consideration plot"""
        with open(outfile, mode="w", encoding="utf-8") as f:
            f.write(self.html)
