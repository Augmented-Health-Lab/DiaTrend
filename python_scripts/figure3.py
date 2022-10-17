#!/usr/bin/python

import pandas as pd
import numpy as np
import os, getopt
import sys
from time import time
from datetime import datetime, timedelta, time,date
import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as pltdates
import matplotlib.dates as dates
import matplotlib.ticker as ticker
from matplotlib.ticker import FuncFormatter
import matplotlib.gridspec as gridspec
from matplotlib.patches import Patch, Rectangle
from matplotlib.lines import Line2D

def setup_tables(dataset_path):
    print("Setting up tables")
    cleaned_files = os.listdir(dataset_path)

    # Read in CGM data
    cbg_df = pd.DataFrame()
    for file in cleaned_files:
        try:
            df = pd.read_excel(dataset_path + "/" + file, sheet_name='CGM')
            df['time'] = pd.to_datetime(df['date'], utc=True, infer_datetime_format=True)
            unique_df = df.drop_duplicates(subset=['time'])
            new_df = unique_df.dropna(subset=['time'])
            new_df['subject'] = file.replace('.xlsx', '')
            cbg_df = cbg_df.append(new_df)
        except:
            pass

    # Read in Bolus data
    bolus_df = pd.DataFrame()
    for file in cleaned_files:
        sub = file.replace('.xlsx', '')
        try:
            df = pd.read_excel(dataset_path + "/" + file, sheet_name='Bolus')
            df['time'] = pd.to_datetime(df['date'], utc=True, infer_datetime_format=True)
            unique_df = df.drop_duplicates(subset=['time'])
            new_df = unique_df.dropna(subset=['time'])
            new_df['Subject'] = [sub] * len(new_df)
            bolus_df = bolus_df.append(new_df)
        except:
            pass
    
    # Format CGM data
    cbg_df['date'] = pd.to_datetime(cbg_df['time'], utc=True, infer_datetime_format=True)
    cbg_df['day'] = cbg_df['date'].dt.strftime('%A')
    cbg_df['week'] = cbg_df['date'].dt.strftime('%W')
    cbg_df['time'] = cbg_df['date'].dt.time
    cbg_df['subject'] = cbg_df['subject'].str[7:].astype(int)
    cbg_df = cbg_df[['subject', 'date', 'day', 'week', 'time', 'mg/dl']]

    # Format Bolus data
    bolus_df = bolus_df[['Subject', 'time', 'normal', 'carbInput']]
    bolus_df['dt_date'] = pd.to_datetime(bolus_df['time']).dt.date

    return cbg_df, bolus_df
  


def make_figure(cgm_df, pump_df, figure_path):
    PURPLE = "#652CDF"
    LIGHTER_PURPLE = "#A291DB"
    LIGHT_PURPLE = "#B5ACF2"
    BRIGHT_YELLOW = "#F0C46E"
    LIGHT_YELLOW = "#F0D6A2"

    subjects_sorted = sorted(cgm_df['subject'].unique().tolist())
    pump_df['Subject'] = pump_df['Subject'].str[7:].astype(int)
    pump_df['dt_date'] = pd.to_datetime(pump_df['time']).dt.date
    pump_df.sort_values(by=["Subject", "dt_date"], ascending=True, inplace=True)
    carbs_df = pump_df[pump_df['carbInput'] > 0].copy()
    bolus_df = pump_df[pump_df['normal'] > 0].copy()

    pump_subjects = []
    bolus_doses = []

    for s in bolus_df['Subject'].unique():
        subject_df = bolus_df[bolus_df['Subject'] == s].copy()
        pump_subjects.append(s)
        bolus_doses.append(len(subject_df))
        
    carb_inputs = []
    for s in pump_subjects:
        subject_df = carbs_df[carbs_df['Subject'] == s].copy()
        carb_inputs.append(len(subject_df))    
    
    fig, axs = plt.subplots(nrows=2, ncols=1, figsize=(15, 10))
    fig.subplots_adjust(hspace=0.4)
    sns.set_theme(style="whitegrid")

    ax_bolus = axs[0]
    ax_carbs = axs[1]

    mean_bolus = np.nanmean(bolus_doses)
    mean_carbs = np.nanmean(carb_inputs)

    ax_bolus.bar(pump_subjects, bolus_doses, label='Bolus Doses', color=LIGHTER_PURPLE, alpha=1, zorder=5)
    ax_carbs.bar(pump_subjects, carb_inputs, label='Carb Inputs', color=BRIGHT_YELLOW, alpha=1, zorder=5)

    ax_bolus.set_xlim(-1, max(pump_subjects) + 1)
    ax_carbs.set_xlim(-1, max(pump_subjects) + 1)

    ax_bolus.xaxis.set_ticks(range(1, max(pump_subjects) + 1))
    ax_bolus.yaxis.set_minor_locator(ticker.MultipleLocator(500))
    ax_carbs.xaxis.set_ticks(range(1, max(pump_subjects) + 1))
    ax_carbs.yaxis.set_minor_locator(ticker.MultipleLocator(250))

    ax_bolus.tick_params(which='minor', left=True, labelleft=False)
    ax_carbs.tick_params(which='minor', left=True, labelleft=False)
    ax_bolus.tick_params(which='major', left=True, labelleft=True)
    ax_carbs.tick_params(which='major', left=True, labelleft=True)

    ax_bolus.set_xlabel('Subject', fontsize=14)
    ax_bolus.set_ylabel('Total Bolus Doses per Subject', fontsize=14)
    ax_carbs.set_ylabel('Total Carb Inputs per Subject', fontsize=14)

    ax_bolus.grid(True, which='both', axis='y', alpha=0.8, zorder=1)
    ax_carbs.grid(True, which='both', axis='y', alpha=0.8, zorder=1)
    ax_bolus.grid(True, which='both', axis='x', alpha=0.8, zorder=1)
    ax_carbs.grid(True, which='both', axis='x', alpha=0.8, zorder=1)

    ax_bolus.axhline(xmin=0, xmax=len(pump_subjects), y=mean_bolus, color=LIGHT_YELLOW, lw=4,
                label= "Mean: {:.1f} doses".format(mean_bolus), zorder=6)
    ax_carbs.axhline(xmin=0, xmax=len(pump_subjects), y=mean_carbs, color=LIGHT_PURPLE, lw=4,
                label= "Mean: {:.1f} inputs".format(mean_carbs), zorder=6)
    ax_bolus.text(len(pump_subjects) - 8, mean_bolus, "Mean: {:.0f} doses".format(mean_bolus), 
                ha="left", va="bottom", fontsize=12, zorder=3)
    ax_carbs.text(len(pump_subjects) - 8, mean_carbs, "Mean: {:.0f} inputs".format(mean_carbs), 
                ha="left", va="bottom", fontsize=12, zorder=3)

    ax_bolus.annotate('Min: {:.0f} doses'.format(min(bolus_doses)), xy=(54, min(bolus_doses)),  
                xytext=(len(pump_subjects) - 8, max(bolus_doses) - 1000),
                zorder=6,
                arrowprops=dict(color=LIGHT_YELLOW, #shrink=0.05, 
                                arrowstyle="simple", lw=1,
                                connectionstyle="angle3,angleA=0,angleB=-90"),
                horizontalalignment='left', verticalalignment='bottom',
                )
    ax_bolus.annotate('Max: {:.0f} doses'.format(max(bolus_doses)), xy=(5, max(bolus_doses)),  
                xytext=(len(pump_subjects) - 8, max(bolus_doses) - 500), 
                zorder=6,
                arrowprops=dict(color=LIGHT_YELLOW, #shrink=0.05, 
                                arrowstyle="simple", lw=1,
                                connectionstyle="angle3,angleA=-3,angleB=-90"),
                horizontalalignment='left', verticalalignment='bottom',
                )

    ax_carbs.annotate('Min: {:.0f} input'.format(min(carb_inputs)), xy=(2, min(carb_inputs)),  
                xytext=(len(pump_subjects) - 8, max(carb_inputs) - 500),
                zorder=6,
                arrowprops=dict(color=LIGHT_PURPLE, #shrink=0.05, 
                                arrowstyle="simple", lw=1,
                                connectionstyle="angle3,angleA=0,angleB=-90"),
                horizontalalignment='left', verticalalignment='bottom',
                )
    ax_carbs.annotate('Max: {:.0f} inputs'.format(max(carb_inputs)), xy=(4, max(carb_inputs)),  
                xytext=(len(pump_subjects) - 8, max(carb_inputs) - 250), 
                zorder=6,
                arrowprops=dict(color=LIGHT_PURPLE, #shrink=0.05, 
                                arrowstyle="simple", lw=1,
                                connectionstyle="angle3,angleA=-3,angleB=-90"),
                horizontalalignment='left', verticalalignment='bottom',
                )


    fig.savefig(figure_path, format='pdf', dpi=300)



def main(argv):
    datadir_path = ''
    figure_path = ''

    if (len(argv) != 4):
        print("Incorrent number of arguments: " + str(len(argv)))
        print('figure3.py -d <path to dataset directory> -f <path to image pdf>') 
        sys.exit(2)
    
    try:
        opts, args = getopt.getopt(argv,"hd:f:",["datasetDir=","figurePath="])
    except getopt.GetoptError:
        print('GetoptError:\t figure3.py -d <path to dataset directory> -f <path to image pdf>') 
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-h':
            print('figure3.py -d <path to dataset directory> -f <path to image pdf>') 
            print('Example:\t figure3.py -d ../dataset/ -f ../Figures/totaldays.pdf') 
            sys.exit()
        elif opt in ("-d", "--datasetDir"):
            datadir_path = arg
        elif opt in ("-f", "--figurePath"):
            figure_path = arg
        else:
            print('figure3.py -d <path to dataset directory> -f <path to image pdf>') 

    print('Path to dataset directory is ' + datadir_path) 
    print('Path to image file is ' + figure_path)

    cgm_df, bolus_df = setup_tables(datadir_path)
    make_figure(cgm_df, bolus_df, figure_path)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
