#!/usr/bin/python

import sys, getopt
import pandas as pd
import numpy as np
import os
import math
import json
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
    subject = []
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
    cbg_df['date'] = pd.to_datetime(cbg_df['date'], utc=True, infer_datetime_format=True)
    cbg_df = cbg_df[['subject', 'date', 'time', 'mg/dl']]
    cbg_df['dt_date'] = pd.to_datetime(cbg_df['date']).dt.date

    days_with_cgm_data = {}

    for subject in cbg_df['subject'].unique():
        sub_df = cbg_df[cbg_df['subject'] == subject].copy()
        for dt_date in sub_df['dt_date'].unique():
            unique_date_df = sub_df[sub_df['dt_date'] == dt_date].copy()
            if len(unique_date_df) > 10:
                if subject in days_with_cgm_data:
                    days_with_cgm_data[subject] += 1 
                else:
                    days_with_cgm_data[subject] = 1 
    
    cgm_days = pd.DataFrame.from_dict(days_with_cgm_data, orient='index', columns=['DaysCollected'])
    cgm_days.sort_values(by='DaysCollected', ascending=False, inplace=True)
    cgm_days = cgm_days.reset_index().rename(columns={"index": "CohortID"})
    cgm_days.index = range(1, len(days_with_cgm_data) + 1)
    cgm_days = cgm_days.rename_axis("Key")
    # cgm_days.to_csv('tables/cgm_days_collected.csv')

    # Format Bolus data
    bolus_df = bolus_df[['Subject', 'time', 'normal', 'carbInput']]
    bolus_df['dt_date'] = pd.to_datetime(bolus_df['time']).dt.date

    days_with_bolus_data = {}
    for subject in bolus_df['Subject'].unique():
        sub_df = bolus_df[bolus_df['Subject'] == subject].copy()
        for dt_date in sub_df['dt_date'].unique():
            unique_date_df = sub_df[sub_df['dt_date'] == dt_date].copy()
            if subject in days_with_bolus_data:
                days_with_bolus_data[subject] += 1 
            else:
                days_with_bolus_data[subject] = 1 

    bolus_days = pd.DataFrame.from_dict(days_with_bolus_data, orient='index', columns=['DaysCollected'])
    bolus_days.sort_values(by='DaysCollected', ascending=False, inplace=True)
    bolus_days = bolus_days.reset_index().rename(columns={"index": "CohortID"})
    bolus_days.index = range(1, len(days_with_bolus_data) + 1)
    # bolus_days = bolus_days.rename_axis("Key")

    cgm_days.rename(columns={'DaysCollected':'CGM_DaysCollected'}, inplace=True)
    bolus_days.rename(columns={'DaysCollected':'Bolus_DaysCollected'}, inplace=True)

    # bolus_days.drop(columns=['Key'], inplace=True)

    cgm_days = cgm_days[cgm_days['CGM_DaysCollected'] >= 30]
    bolus_days = bolus_days[bolus_days['CohortID'].isin(cgm_days['CohortID'].unique())]

    bolus_days = bolus_days[bolus_days['Bolus_DaysCollected'] >= 30]
    cgm_days = cgm_days[cgm_days['CohortID'].isin(bolus_days['CohortID'].unique())]

    days_collected = cgm_days.merge(bolus_days, how='outer', on='CohortID')
    days_collected['Key'] = range(1, len(days_collected) + 1)
    # days_collected.to_csv('tables/days_collected.csv', index=False)

    return days_collected
  


def make_figure(days_collected, figure_path):
    
    fig, axs = plt.subplots(nrows=2, ncols=1, figsize=(15, 10))
    fig.subplots_adjust(hspace=0.4)
    sns.set_theme(style="whitegrid")

    cgm_keys = [k for k in days_collected.Key]
    cgm_values = [v for v in days_collected['CGM_DaysCollected']]

    cgm_mean = np.nanmean(cgm_values)

    sns.barplot(x=cgm_keys, y=cgm_values, label="# Days with CGM Data", color="#652CDF", 
                ax=axs[0], zorder=2)
    axs[0].axhline(xmin=0, xmax=len(cgm_keys), y=cgm_mean, color="#F0C46E", lw=3, 
                label= "Mean: {:.1f}".format(cgm_mean))
    axs[0].text(len(cgm_keys) - 8, cgm_mean, "Mean: {:.0f} days".format(cgm_mean), 
                ha="left", va="bottom", fontsize=12)

    axs[0].yaxis.set_minor_locator(ticker.MultipleLocator(125))
    axs[0].grid(zorder=1, which='both', axis='both', alpha=0.8)
    axs[0].set_title("Total Days of CGM Data: {:.0f} days".format(np.nansum(cgm_values)))
    axs[0].set_xlabel('Subject', fontsize=14)
    axs[0].set_ylabel('# Days with CGM Data', fontsize=14)

    axs[0].annotate('Min: {:.0f} days'.format(min(cgm_values)), xy=(53, min(cgm_values)),  
                xytext=(len(cgm_keys) - 8, max(cgm_values) - 500),
                arrowprops=dict(color='#F0C46E', #shrink=0.05, 
                                arrowstyle="simple", lw=1,
                                connectionstyle="angle3,angleA=0,angleB=-90"),
                horizontalalignment='left', verticalalignment='bottom',
                )
    axs[0].annotate('Max: {:.0f} days'.format(max(cgm_values)), xy=(0, max(cgm_values)),  
                xytext=(len(cgm_keys) - 8, max(cgm_values) - 250), 
                arrowprops=dict(color='#F0C46E', #shrink=0.05, 
                                arrowstyle="simple", lw=1,
                                connectionstyle="angle3,angleA=-3,angleB=90"),
                horizontalalignment='left', verticalalignment='bottom',
                )

    bolus_keys = [k for k in days_collected.Key]
    bolus_values = [v for v in days_collected['Bolus_DaysCollected']]

    bolus_mean = np.nanmean(bolus_values)

    sns.barplot(x=bolus_keys, y=bolus_values, label="# Days with Insulin Pump Data", 
                color="#A291DB", ax=axs[1], zorder=2)
    axs[1].axhline(xmin=0, xmax=len(bolus_keys), y=bolus_mean, color="#F0C46E", lw=3,
                label= "Mean: {:.1f}".format(bolus_mean))
    axs[1].text(len(bolus_keys) - 8, bolus_mean, "Mean: {:.0f} days".format(bolus_mean), 
                ha="left", va="bottom", fontsize=12)

    axs[1].yaxis.set_minor_locator(ticker.MultipleLocator(50))
    axs[1].grid(zorder=1, which='both', axis='both', alpha=0.8)
    axs[1].set_title("Total Days of Insulin Pump Data: {:.0f} days".format(np.nansum(bolus_values)))
    axs[1].set_xlabel('Subject', fontsize=14)
    axs[1].set_ylabel('# Days with Insulin Pump Data', fontsize=14)

    axs[1].annotate('Min: {:.0f} days'.format(min(bolus_values)), xy=(53, min(bolus_values)),  
                xytext=(len(bolus_keys) - 8, max(bolus_values) - 200),
                arrowprops=dict(color='#F0C46E', #shrink=0.05, 
                                arrowstyle="simple", lw=1,
                                connectionstyle="angle3,angleA=0,angleB=-90"),
                horizontalalignment='left', verticalalignment='bottom',
                )
    axs[1].annotate('Max: {:.0f} days'.format(max(bolus_values)), xy=(4, max(bolus_values)),  
                xytext=(len(bolus_keys) - 8, max(bolus_values) - 100), 
                arrowprops=dict(color='#F0C46E', #shrink=0.05, 
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
        print('figure2.py -d <path to dataset directory> -f <path to image pdf>') 
        sys.exit(2)
    
    try:
        opts, args = getopt.getopt(argv,"hd:f:",["datasetDir=","figurePath="])
    except getopt.GetoptError:
        print('GetoptError:\t figure2.py -d <path to dataset directory> -f <path to image pdf>') 
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-h':
            print('figure2.py -d <path to dataset directory> -f <path to image pdf>') 
            print('Example:\t figure2.py -d ../dataset/ -f ../Figures/totaldays.pdf') 
            sys.exit()
        elif opt in ("-d", "--datasetDir"):
            datadir_path = arg
        elif opt in ("-f", "--figurePath"):
            figure_path = arg
        else:
            print('figure2.py -d <path to dataset directory> -f <path to image pdf>') 

    print('Path to dataset directory is ' + datadir_path) 
    print('Path to image file is ' + figure_path)

    days_collected = setup_tables(datadir_path)
    make_figure(days_collected, figure_path)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
