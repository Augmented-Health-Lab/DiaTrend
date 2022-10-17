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
    
    # Format CGM data
    cbg_df['date'] = pd.to_datetime(cbg_df['time'], utc=True, infer_datetime_format=True)
    cbg_df['day'] = cbg_df['date'].dt.strftime('%A')
    cbg_df['week'] = cbg_df['date'].dt.strftime('%W')
    cbg_df['time'] = cbg_df['date'].dt.time
    cbg_df['subject'] = cbg_df['subject'].str[7:].astype(int)
    cbg_df = cbg_df[['subject', 'date', 'day', 'week', 'time', 'mg/dl']]
    cbg_df['dt_date'] = cbg_df['date'].dt.date

    return cbg_df

def make_histograms(cbg_df, figure_dir):
    PURPLE = "#652CDF"
    LIGHTER_PURPLE = "#A291DB"
    LIGHT_PURPLE = "#B5ACF2"
    BRIGHT_YELLOW = "#F0C46E"
    LIGHT_YELLOW = "#F0D6A2"

    # Mean Glucose
    daily_means = []
    for subject in cbg_df['subject'].unique():
        sub_df = cbg_df[cbg_df['subject'] == subject].copy()
        for dt_date in sub_df['dt_date'].unique():
            date_df = sub_df[sub_df['dt_date'] == dt_date].copy()
            if len(date_df) > 10:
                meanBG = (date_df['mg/dl'].mean())
                daily_means.append(meanBG)

    # Glycemic Variability
    daily_covs = []
    for subject in cbg_df['subject'].unique():
        sub_df = cbg_df[cbg_df['subject'] == subject].copy()
        for dt_date in sub_df['dt_date'].unique():
            date_df = sub_df[sub_df['dt_date'] == dt_date].copy()
            if len(date_df) > 10:
                meanBG = (date_df['mg/dl'].mean())
                std_dev = (date_df['mg/dl'].std())
                cov = std_dev / meanBG
                daily_covs.append(cov)

    # Time in Range
    conditions = [
        (cbg_df['mg/dl'] < 70),
        (cbg_df['mg/dl'] >= 70) & (cbg_df['mg/dl'] <= 180),
        (cbg_df['mg/dl'] > 180)
    ]
    values = ['BelowRange', 'InRange', 'AboveRange']
    cbg_df['bgCategory'] = np.select(conditions, values)
    cbg_df['dt_date'] = cbg_df['date'].dt.date
    daily_TIRs = []
    for subject in cbg_df['subject'].unique():
        sub_df = cbg_df[cbg_df['subject'] == subject].copy()
        for dt_date in sub_df['dt_date'].unique():
            date_df = sub_df[sub_df['dt_date'] == dt_date].copy()
            if len(date_df) > 10:
                tir = (len(date_df[date_df['bgCategory'] == 'InRange']) / max(288, len(date_df))) * 100
                daily_TIRs.append(tir)
                
                
    fig, (ax_mean, ax_var, ax_tir) = plt.subplots(1, 3, figsize=(15, 5))
    sns.set_theme(style="whitegrid")

    sns.histplot(x=daily_means, color=PURPLE, ax=ax_mean)
    ax_mean.set_xlim(0, 400)
    ax_mean.set_ylim(0, 1150)
    mean_mean = np.nanmean(daily_means)
    ax_mean.axvline(ymin=0, ymax=1150, x = mean_mean, color = LIGHT_YELLOW, lw=3)
    ax_mean.text(mean_mean - 13, 1070, "Mean: {:.0f} mg/dL".format(mean_mean), 
                ha="right", va="bottom", fontsize=12)
    ax_mean.set_ylabel('Frequency')
    ax_mean.set_xlabel('Daily Mean Blood Glucose')

    sns.histplot(x=daily_covs, color=PURPLE, ax=ax_var)
    ax_var.set_xlim(0, 0.8)
    ax_var.set_ylim(0, 1150)
    mean_var = np.nanmean(daily_covs)
    ax_var.axvline(ymin=0, ymax=1150, x = mean_var, color = LIGHT_YELLOW, lw=3)
    ax_var.text(mean_var - 0.02, 1070, "Mean: {:.2f}".format(mean_var), 
                ha="right", va="bottom", fontsize=12)
    ax_var.set_ylabel('')
    ax_var.set_xlabel('Daily Glycemic Variability (coefficient of variation)')

    sns.histplot(x=daily_TIRs, color=PURPLE, ax=ax_tir)
    ax_tir.set_ylabel('')
    ax_tir.set_ylim(0, 1150)
    mean_tir = np.nanmean(daily_TIRs)
    ax_tir.axvline(ymin=0, ymax=1150, x = mean_tir, color = LIGHT_YELLOW, lw=3)
    ax_tir.text(mean_tir - 2, 1070, "Mean: {:.0f}%".format(mean_tir), 
                ha="right", va="bottom", fontsize=12)
    ax_tir.set_xlabel('Daily Time in Range (%)')

    fig.savefig(figure_dir + "/figure4_cgm_daily_hist.pdf", dpi=300, format='pdf')
  


def make_figure(cgm_df, figure_path):
    PURPLE = "#652CDF"
    LIGHT_PURPLE = "#B5ACF2"
    SALMON = "#F06688"
    LIGHT_SALMON = "#f9c2cf"
    GREEN = "#76D3A5"

    subjects_sorted = sorted(cgm_df['subject'].unique().tolist())
    subjects = []
    t_targets = []
    t_highs = []
    t_lows = []
    t_veryhighs = []
    t_verylows = []


    for subject in subjects_sorted:
        sub_df = cgm_df[cgm_df['subject'] == subject].copy()
        sub_veryhigh = (len(sub_df[sub_df["mg/dl"] > 250]) / len (sub_df)) * 100 
        sub_high = (len(sub_df[(sub_df["mg/dl"] > 180) & (sub_df["mg/dl"] <= 250)]) / len (sub_df)) * 100 
        sub_target = (len(sub_df[(sub_df["mg/dl"] >= 70) & (sub_df["mg/dl"] <= 180)]) / len (sub_df)) * 100 
        sub_low = (len(sub_df[(sub_df["mg/dl"] >= 54) & (sub_df["mg/dl"] < 70)]) / len (sub_df)) * 100 
        sub_verylow = (len(sub_df[sub_df["mg/dl"] < 54]) / len (sub_df)) * 100 
        
        subjects.append(subject)
        t_targets.append(sub_target)
        t_highs.append(sub_high)
        t_lows.append(sub_low)
        t_veryhighs.append(sub_veryhigh)
        t_verylows.append(sub_verylow)

    from matplotlib.colors import ListedColormap

    df_ranges = pd.DataFrame(data = {'Very Low (< 54 mg/dL)': t_verylows,
                                    'Low (54-69 mg/dL)': t_lows,
                                    'Target Range (70-180 mg/dL)': t_targets,
                                    'High (181-250 mg/dL)': t_highs,
                                    'Very High (> 250 mg/dL)': t_veryhighs,
                                    }, index = subjects)

    fig = plt.figure(figsize=(17, 6))
    sns.set_theme(style="whitegrid")
    ax = plt.gca()

    cmap = mpl.colors.ListedColormap([SALMON, LIGHT_SALMON, GREEN, LIGHT_PURPLE, PURPLE])
    df_ranges.plot.bar(stacked=True, cmap=cmap, ax=ax)
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(5))

    ax.legend(fontsize='medium', ncol=5, bbox_to_anchor=(0., 0.98, 0.97, 0.1))

    plt.xticks(rotation=0)

    # plt.title("Times in Ranges")
    plt.xlabel('Subject', fontsize=14)
    plt.ylabel('Percent (%) ', fontsize=14)
    plt.grid(which='both', axis='y', alpha=0.8)
    fig.savefig(figure_path + '/figure4_times_in_ranges.pdf', format='pdf', dpi=300)


def main(argv):
    datadir_path = ''
    figure_path = ''

    if (len(argv) != 4):
        print("Incorrent number of arguments: " + str(len(argv)))
        print('figure4.py -d <path to dataset directory> -f <path to figure directory>') 
        sys.exit(2)
    
    try:
        opts, args = getopt.getopt(argv,"hd:f:",["datasetDir=","figurePath="])
    except getopt.GetoptError:
        print('GetoptError:\t figure4.py -d <path to dataset directory> -f <path to figure directory>') 
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-h':
            print('figure4.py -d <path to dataset directory> -f <path to image pdf>') 
            print('Example:\t figure2.py -d ../dataset/ -f ../Figures/') 
            sys.exit()
        elif opt in ("-d", "--datasetDir"):
            datadir_path = arg
        elif opt in ("-f", "--figurePath"):
            figure_path = arg
        else:
            print('figure4.py -d <path to dataset directory> -f <path to figure directory>') 

    print('Path to dataset directory is ' + datadir_path) 
    print('Path to image file is ' + figure_path)

    cgm_df= setup_tables(datadir_path)
    make_histograms(cgm_df, figure_path)
    make_figure(cgm_df, figure_path)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
