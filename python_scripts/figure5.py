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
    
    # Format Bolus data
    bolus_df = bolus_df[['Subject', 'time', 'normal', 'carbInput']]
    bolus_df['dt_date'] = pd.to_datetime(bolus_df['time']).dt.date

    return bolus_df

def make_histograms(bolus_df, figure_dir):
    PURPLE = "#652CDF"
    LIGHTER_PURPLE = "#A291DB"
    LIGHT_PURPLE = "#B5ACF2"
    BRIGHT_YELLOW = "#F0C46E"
    LIGHT_YELLOW = "#F0D6A2"

    bolus_df['date'] = pd.to_datetime(bolus_df['time']).dt.date

    daily_carbs = []
    for subject in bolus_df['Subject'].unique():
        sub_df = bolus_df[bolus_df['Subject'] == subject].copy()
        for dt_date in sub_df['date'].unique():
            date_df = sub_df[sub_df['date'] == dt_date].copy()
            if len(date_df) > 0:
                carbSum = (date_df['carbInput'].sum())
                daily_carbs.append(carbSum)
                
    daily_bolus = []
    for subject in bolus_df['Subject'].unique():
        sub_df = bolus_df[bolus_df['Subject'] == subject].copy()
        for dt_date in sub_df['date'].unique():
            date_df = sub_df[sub_df['date'] == dt_date].copy()
            if len(date_df) > 0:
                bolusSum = (date_df['normal'].sum())
                daily_bolus.append(bolusSum)

    fig, (ax_bolus, ax_carb) = plt.subplots(1, 2, figsize=(15, 5))
    sns.set_theme(style="whitegrid")

    sns.histplot(x=daily_bolus, color=LIGHTER_PURPLE, ax=ax_bolus)
    ax_bolus.set_xlim(0, 100)
    ax_bolus.set_ylim(0, 600)
    mean_bolus = np.nanmean(daily_bolus)
    ax_bolus.axvline(ymin=0, ymax=300, x = mean_bolus, color = LIGHT_YELLOW, lw=3)
    ax_bolus.text(mean_bolus + 2, 550, "Mean: {:.0f} units".format(mean_bolus), 
                ha="left", va="bottom", fontsize=12)
    ax_bolus.set_ylabel('Frequency')
    ax_bolus.set_xlabel('Total Daily Bolus (units)')

    sns.histplot(x=daily_carbs, color=BRIGHT_YELLOW, ax=ax_carb)
    ax_carb.set_xlim(0, 500)
    ax_carb.set_ylim(0, 1500)
    mean_carbs = np.nanmean(daily_carbs)
    ax_carb.axvline(ymin=0, ymax=1400, x = mean_carbs, color = LIGHT_PURPLE, lw=3)
    ax_carb.text(mean_carbs + 10, 1400, "Mean: {:.0f} g".format(mean_carbs), 
                ha="left", va="bottom", fontsize=12)
    ax_carb.set_ylabel('')
    ax_carb.set_xlabel('Total Daily Carbs (g)')


    fig.savefig(figure_dir + "/figure5_ip_daily_hist.pdf", dpi=300, format='pdf')


def make_boxplots(pump_df, figure_dir):
    PURPLE = "#652CDF"
    LIGHTER_PURPLE = "#A291DB"
    LIGHT_PURPLE = "#B5ACF2"
    BRIGHT_YELLOW = "#F0C46E"
    LIGHT_YELLOW = "#F0D6A2"

    pump_df['Subject'] = pump_df['Subject'].str[7:].astype(int)
    pump_df['dt_date'] = pd.to_datetime(pump_df['time']).dt.date
    pump_df.sort_values(by=["Subject", "dt_date"], ascending=True, inplace=True)
    carbs_df = pump_df[pump_df['carbInput'] > 0].copy()
    bolus_df = pump_df[pump_df['normal'] > 0].copy()

    fig = plt.figure(figsize=(15, 5))
    sns.set_theme(style="whitegrid")
    ax = plt.gca()
    ax.set_xlim(0, len(bolus_df['Subject'].unique()) + 2)
    sns.boxplot(data=bolus_df, x="Subject", y="normal", color=LIGHTER_PURPLE, ax = ax)
    plt.ylabel('Bolus Dose (units)', fontsize=14)
    plt.xlabel('Subject', fontsize=14)
    fig.savefig(figure_dir + 'figure5_bolusDose_boxplot.pdf', format='pdf', dpi=300)

    fig = plt.figure(figsize=(15, 5))
    sns.set_theme(style="whitegrid")
    ax = plt.gca()
    sns.boxplot(data=carbs_df, x="Subject", y="carbInput", color=BRIGHT_YELLOW, ax = ax)
    ax.set_ylim(0, 200)
    plt.ylabel('Carb Input (g)', fontsize=14)
    plt.xlabel('Subject', fontsize=14)
    fig.savefig(figure_dir + 'figure5_carbInput_boxplot_ymax200.pdf', format='pdf', dpi=300)
  

def main(argv):
    datadir_path = ''
    figure_dir = ''

    if (len(argv) != 4):
        print("Incorrent number of arguments: " + str(len(argv)))
        print('figure5.py -d <path to dataset directory> -f <path to figure directory>') 
        sys.exit(2)
    
    try:
        opts, args = getopt.getopt(argv,"hd:f:",["datasetDir=","figureDir="])
    except getopt.GetoptError:
        print('GetoptError:\t figure5.py -d <path to dataset directory> -f <path to figure directory>') 
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-h':
            print('figure5.py -d <path to dataset directory> -f <path to figure directory>') 
            print('Example:\t figure5.py -d ../dataset/ -f ../Figures/') 
            sys.exit()
        elif opt in ("-d", "--datasetDir"):
            datadir_path = arg
        elif opt in ("-f", "--figureDir"):
            figure_dir = arg
        else:
            print('figure5.py -d <path to dataset directory> -f <path to figure directory>') 

    print('Path to dataset directory is ' + datadir_path) 
    print('Path to image file is ' + figure_dir)

    bolus_df = setup_tables(datadir_path)
    make_histograms(bolus_df, figure_dir)
    make_boxplots(bolus_df, figure_dir)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
