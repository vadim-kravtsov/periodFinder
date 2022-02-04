from cProfile import label
from dataclasses import field
from turtle import width
from urllib.parse import _NetlocResultMixinBase
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from numpy.lib.utils import source
import myplotlib.myplotlib as myplt
from astropy.timeseries import LombScargle 

from bokeh.io import curdoc
from bokeh.layouts import row, column
from bokeh.models import ColumnDataSource, BoxZoomTool, CrosshairTool, ResetTool
from bokeh.models import SaveTool, PanTool, FileInput, Div, DataTable, TableColumn
from bokeh.models.widgets import Slider, TextInput, Button
from bokeh.plotting import figure

''' Interactive tool for Lomb-Scargle analysis of time series. 
    Use the ``bokeh serve`` command to run the program by executing
    bokeh serve periodFinder.py at your command prompt.
    Then navigate to the URL http://localhost:5006/periodFinder in your browser.
'''


def calc_fi(t, t0, P):
    # print(t0, P)
    # print((t - t0).astype(int))
    fi = (t - (t0 + ((t - t0) / P).astype(int) * P)) / P
    return fi


def read_data(filename):
    try:
        data = pd.read_csv(filename,
                           delim_whitespace=True,
                           names=['time', 'value', 'error'])
        exitcode = 0
        return data, exitcode 
    except FileNotFoundError:
        exitcode = 1
        return None, exitcode
      

def errorbar(fig, x, y, xerr=None, yerr=None, color='red', 
             point_kwargs={}, error_kwargs={}):

    fig.circle(x, y, color=color, size=7, **point_kwargs)

    y_err_x = []
    y_err_y = []
    for px, py, err in zip(x, y, yerr):
        y_err_x.append((px, px))
        y_err_y.append((py - err, py + err))
    fig.multi_line(y_err_x, y_err_y, color=color, **error_kwargs)
    

def main(): 
    # Creating a basic bokeh layout with the plots and inputs 
    original_dataframe = ColumnDataSource({'time': [], 'value' : [], 'error' : []})
    
    
    original_data_panel = figure(plot_height=300, 
                                plot_width=500,
                                title="Original data",
                                tools=[BoxZoomTool(), PanTool(), CrosshairTool(), SaveTool()],
                                x_range=[0, 1], y_range=[0, 1])

    lomb_scargle_panel = figure(plot_height=300,
                               plot_width=500,
                               title="Lomb-Scargle Periodogram",
                               tools=[BoxZoomTool(dimensions='width'), PanTool(dimensions='width'), CrosshairTool(), SaveTool()],
                               y_range=[0, 1.1],
                               x_range=[0, 1])


    orbital_panel = figure(plot_height=300,
                          plot_width=500,
                          title="Data, folded with the best found period",
                          y_range=[0, 1],
                          x_range=[0, 2],
                          tools=[BoxZoomTool(dimensions='width'), PanTool(dimensions='width'), CrosshairTool(), SaveTool()])
    
               
    lomb_scargle_zoomed_panel = figure(plot_height=300,
                                 plot_width=500,
                                 title="Lomb-Scargle Periodogram",
                                 tools=[BoxZoomTool(dimensions='width'), PanTool(dimensions='width'), CrosshairTool(), SaveTool()],
                                 y_range=[0, 1.1], x_range=[0, 1])
    
    
    original_data_panel.xaxis.axis_label = "T - T0"
    original_data_panel.yaxis.axis_label = "Y"
    
    orbital_panel.xaxis.axis_label = "Orbital phase for the best period"
    orbital_panel.yaxis.axis_label = "Y"
           
    lomb_scargle_panel.xaxis.axis_label = "Period (in untits of time used)"
    lomb_scargle_panel.yaxis.axis_label = "Lomb-Scargle Power"

    lomb_scargle_zoomed_panel.xaxis.axis_label = "Period (in untits of time used)"
    lomb_scargle_zoomed_panel.yaxis.axis_label = "Lomb-Scargle Power"
    
    errors_div = Div(text="")
    
    
    def print_dataframe(event):
        try:
            print(original_dataframe.data)
            errors_div.text = ''
            errors_div.style = {'color': 'black'}
        except NameError:
            errors_div.text = 'Error: open the data file first!'
            errors_div.style = {'color': 'red'}


    def plot_original_data(event):
        try:
            time_shifted = original_dataframe.data['time'] - np.min(original_dataframe.data['time'])
            original_data_panel.renderers = []
            errorbar(original_data_panel, time_shifted, original_dataframe.data['value'], yerr = original_dataframe.data['error'], color='steelblue')
            original_data_panel.x_range.start = min(time_shifted)
            original_data_panel.x_range.end = max(time_shifted)
            
            min_y, max_y = min(original_dataframe.data['value']), max(original_dataframe.data['value'])
            original_data_panel.y_range.start = min_y - 0.1*(max_y - min_y)
            original_data_panel.y_range.end = max_y + 0.1*(max_y - min_y)
            
            # original_data_panel.circle(time_shifted, original_dataframe.data['value'], size=7)
            errors_div.text = ''
            errors_div.style = {'color': 'black'}
        except ValueError:
            errors_div.text = 'Error: open the data file first!'
            errors_div.style = {'color': 'red'}
    
    
    def plot_orbital(event):
        global ls_column_data
        try:
            time_shifted = original_dataframe.data['time'] - np.min(original_dataframe.data['time'])
            try:
                best_period = 1./float(ls_column_data.data['best_frequency'][0])
                phase = calc_fi(time_shifted, time_shifted[0], best_period)
                orbital_panel.renderers = []
                errorbar(orbital_panel, phase, original_dataframe.data['value'], yerr = original_dataframe.data['error'], color='steelblue')
                errorbar(orbital_panel, phase+1, original_dataframe.data['value'], yerr = original_dataframe.data['error'], color='steelblue')
                
                orbital_panel.xaxis.axis_label = f"Orbital phase for the best period P = {round(best_period, 4)}"
            
                min_y, max_y = min(original_dataframe.data['value']), max(original_dataframe.data['value'])
                orbital_panel.y_range.start = min_y - 0.2*(max_y - min_y)
                orbital_panel.y_range.end = max_y + 0.2*(max_y - min_y)
                errors_div.text = ''
                errors_div.style = {'color': 'black'}
            except ValueError:
                errors_div.text = 'Error: calculate periodogram first!'
                errors_div.style = {'color': 'red'}
        except ValueError:
            errors_div.text = 'Error: open the data file first!'
            errors_div.style = {'color': 'red'}

    
    file_source = ColumnDataSource({'time': [], 'value' : [], 'error' : []})
    
    def file_input_handler(attr, old, new):
        filename = new
        data, exitcode = read_data(filename)
        if exitcode == 1: 
            errors_div.text = 'Error: data file should be in the same folder with the python script!'
            errors_div.style = {'color': 'red'}
        else:
            errors_div.text = ''
            errors_div.style = {'color': 'black'}
            original_dataframe.data = original_dataframe.from_df(data)
            
    
    file_input = FileInput(accept=".csv,.txt", multiple=False)
    file_input.on_change('filename', file_input_handler)
    
    print_button  = Button(label='Print dataframe')
    print_button.on_click(print_dataframe)
    
    plot_original_button = Button(label='Plot data')
    plot_original_button.on_click(plot_original_data)
                   
    def plot_periodogram(event):
        global ls_column_data
        try:
            time = original_dataframe.data['time'] - np.min(original_dataframe.data['time'])
            value = original_dataframe.data['value']
            error = original_dataframe.data['error']
            
            lomb_scargle_panel.renderers = []
            lomb_scargle_zoomed_panel.renderers = []
            
            ls = LombScargle(time, value, error)
        
            freq, power = ls.autopower(nyquist_factor=5, samples_per_peak=100, minimum_frequency=1./(max(time) - min(time)))

            fap_level = ls.false_alarm_level(0.01)
            
            best_frequency = freq[np.argmax(power)]
            best_period = 1./best_frequency
            ls_column_data = ColumnDataSource(data=dict(x=freq, y=power, best_frequency=[best_frequency], fap=[fap_level]))
            
            lomb_scargle_panel.line('x', 'y', source=ls_column_data, line_width=3)
            lomb_scargle_panel.line(x=1/freq, y=power, line_width=1)
            
            lomb_scargle_zoomed_panel.line('x', 'y', source=ls_column_data, line_width=3)
            lomb_scargle_zoomed_panel.line(x=1/freq, y=power, line_width=1)
            
            lomb_scargle_panel.ray(x=0, y=float(fap_level), length=0, angle=0, line_width=1, color='firebrick', legend_label='FAP = 1%')
            lomb_scargle_zoomed_panel.ray(x=0, y=float(fap_level), length=0, angle=0, line_width=1, color='firebrick', legend_label='FAP = 1%')
            
            lomb_scargle_panel.ray(x=best_period, y=0., length=1.1, angle=np.pi/2, line_width=1, color='tomato', legend_label=f'P = {round(best_period, 4)}', line_dash='dashed')
            lomb_scargle_zoomed_panel.ray(x=best_period, y=0., length=1.1, angle=np.pi/2, line_width=1, color='tomato', legend_label=f'P = {round(best_period, 4)}', line_dash='dashed')
                
            lomb_scargle_panel.x_range.start = min(1/freq)
            lomb_scargle_panel.x_range.end = max(1/freq)
            
            lomb_scargle_panel.y_range.start = 0
            lomb_scargle_panel.y_range.end = max(power) + 0.05*max(power)
            
            lomb_scargle_zoomed_panel.x_range.start = min(1/freq)
            lomb_scargle_zoomed_panel.x_range.end = 2*1./best_frequency - min(1/freq)
            
            lomb_scargle_zoomed_panel.y_range.start = 0
            lomb_scargle_zoomed_panel.y_range.end = max(power) + 0.05*max(power)
            
            errors_div.text = ''
            errors_div.style = {'color': 'black'}
        except ValueError:
            errors_div.text = 'Error: open the data file first!'
            errors_div.style = {'color': 'red'}
     
    
    plot_periodogram_button = Button(label='Plot periodogram')
    plot_periodogram_button.on_click(plot_periodogram)
    
    logo = Div(text="""<b>Lomb-Scargle Period Searcher</b>""",
               style={'text-align': 'left', 'font-size': 'large'})
    
    instructions = Div(text="""Please, open ".txt" or ".csv" file with the data.""")
    
    orbital_plot_button = Button(label='Plot orbital lightcurve')
    orbital_plot_button.on_click(plot_orbital)
    
    columns = [TableColumn(field='time', title='Time'), 
               TableColumn(field='value', title='Value'),
               TableColumn(field='error', title='Error')]
    
    data_table = DataTable(source=original_dataframe, columns=columns, width=300, height=350, editable=True, selectable=True)

    inputs = column(logo, instructions, file_input, data_table)
    buttons = column(plot_original_button, plot_periodogram_button, orbital_plot_button, errors_div)
    
    curdoc().title = "Lomb-Scargle Periodograms"
    curdoc().add_root(row(column(original_data_panel, orbital_panel, width=500), 
                            column(lomb_scargle_panel, lomb_scargle_zoomed_panel, width=500), column(inputs, buttons, width=300)))
    
main()