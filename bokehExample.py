''' Present an interactive function explorer with slider widgets.

Scrub the sliders to change the properties of the ``sin`` curve, or
type into the title text box to update the title of the plot.

Use the ``bokeh serve`` command to run the example by executing:

    bokeh serve sliders.py

at your command prompt. Then navigate to the URL

    http://localhost:5006/sliders

in your browser.

'''
import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, TextInput
# from bokeh.plotting import figure, output_file, show, save

import bokeh.plotting as plt

import checkRemote  

# Generate the output file in the browser
plt.output_file("bokeh_plot.html", title="Bokeh Sine Wave Plot")

# Set up data
N = 200
x = np.linspace(0, 4*np.pi, N)
y = np.sin(x)+5
source = ColumnDataSource(data=dict(x=x, y=y))


# Set up plot
plot = plt.figure(y_range=(-10,10),height=400, title="", sizing_mode='stretch_width')
# Set up plot
# plot = figure(height=400, width=400, title="my sine wave", tools="crosshair,pan,reset,save,wheel_zoom", x_range=[0, 4*np.pi], y_range=[-2.5, 2.5])

plot.line('x', 'y', source=source, line_width=3, line_alpha=0.6)


# Set up widgets
text = TextInput(title="title", value='my sine wave')
offset = Slider(title="offset", value=0.0, start=-5.0, end=5.0, step=0.1)
amplitude = Slider(title="amplitude", value=1.0, start=-5.0, end=5.0, step=0.1)
phase = Slider(title="phase", value=0.0, start=0.0, end=2*np.pi)
freq = Slider(title="frequency", value=1.0, start=0.1, end=5.1, step=0.1,)


# Set up callbacks
def update_title(attrname, old, new):
    plot.title.text = text.value

text.on_change('value', update_title)

def update_data(attrname, old, new):

    # Get the current slider values
    a = amplitude.value
    b = offset.value
    w = phase.value
    k = freq.value

    # Generate the new curve
    x = np.linspace(0, 4*np.pi, N)
    y = a*np.sin(k*x + w) + b

    source.data = dict(x=x, y=y)

for w in [offset, amplitude, phase, freq]:
    w.on_change('value', update_data)


# Set up layouts and add to document
inputs = column(text, offset, amplitude, phase, freq)  

curdoc().add_root(row(plot, inputs, width=800))
curdoc().title = "Sliders"

# # Show the plot in the browser tab
# if not checkRemote.is_running_remotely():
#     plt.show(plot)
# else:    
#     plt.save(plot) 