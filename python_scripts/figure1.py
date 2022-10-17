#!/usr/bin/python

import sys, getopt
import pandas as pd
from datetime import timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import matplotlib.ticker as ticker
import matplotlib.gridspec as gridspec
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

def make_figure(subject_path, figure_path):
    
    weekstr = '20'
    weekday = 'Thursday'

    cgm_df = pd.read_excel(subject_path, index_col=False, sheet_name='CGM')
    cgm_df.loc[:,'date'] = pd.to_datetime(cgm_df['date'])
    cgm_df['day'] = cgm_df['date'].dt.strftime('%A')
    cgm_df['week'] = cgm_df['date'].dt.strftime('%W')
    cgm_df['time'] = cgm_df['date'].dt.time
    weekday_df = cgm_df.loc[(cgm_df.day == weekday) & (cgm_df.week == weekstr)].copy()
    weekday_df.loc[:,'time'] = pd.to_datetime(weekday_df['date'], format='%M:%S.%f') 

    bolus_df = pd.read_excel(subject_path, index_col=False, sheet_name='Bolus')
    bolus_df.loc[:,'date'] = pd.to_datetime(bolus_df['date'])
    bolus_df['day'] = bolus_df['date'].dt.strftime('%A')
    bolus_df['week'] = bolus_df['date'].dt.strftime('%W')
    bolus_df['time'] = bolus_df['date'].dt.time

    basal_df = pd.read_excel(subject_path, index_col=False, sheet_name='Basal')
    basal_df.loc[:,'date'] = pd.to_datetime(basal_df['date'])
    basal_df['day'] = basal_df['date'].dt.strftime('%A')
    basal_df['week'] = basal_df['date'].dt.strftime('%W')
    basal_df['time'] = basal_df['date'].dt.time

    fig = plt.figure(figsize=(15, 10))
    gs = gridspec.GridSpec(nrows=3, ncols=1, height_ratios=[7,7,2])
    fig.subplots_adjust(hspace=0.5, wspace=0.1)

    ax = fig.add_subplot(gs[0])
    xmin = min(weekday_df['time'])
    xmax = max(weekday_df['time'])
    ymin = int(min(weekday_df['mg/dl'])) - 3
    ymax = int(max(weekday_df['mg/dl'])) + 3

    bg = ax.plot(weekday_df['time'], weekday_df['mg/dl'], marker='o', color='#652CDF', linestyle='none')
    ax.plot([xmin, xmax], [180, 180], 'k', linewidth=2, label = 'high')
    ax.plot([xmin, xmax], [70, 70], 'k', linewidth=2, label = 'low')

    ax.annotate('180', (xmax, 180), fontsize=12)
    ax.annotate('70', (xmax, 70), fontsize=12)

    ax.set_xlabel("Time of Day", fontsize=18)
    ax.set_ylabel("Blood Glucose (mg/dL)", fontsize=18)

    ax.set_ylim(0, 400)
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.yaxis.set_major_locator(ticker.MultipleLocator(base=100))
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%d"))

    h_loc = dates.HourLocator(byhour=range(0,24,3))
    ax.xaxis.set_minor_locator(dates.HourLocator())
    ax.xaxis.set_major_locator(h_loc)
    xfmt = dates.DateFormatter('%l %p')
    ax.xaxis.set_major_formatter(xfmt)
    ax.grid(True)
    ax.tick_params(axis='both', which='major', labelsize=14)

    weekday_bolus = bolus_df.loc[(bolus_df.day == weekday) & (bolus_df.week == weekstr)].copy()
    weekday_bolus.loc[:,'time'] = pd.to_datetime(weekday_bolus['date'], format='%M:%S.%f') 
    weekday_bolus = weekday_bolus[weekday_bolus['normal'].notna()]

    ratio_times = []
    ratio_insulinCarbRatios = []
    curr = bolus_df.at[295, 'insulinCarbRatio']
    ratio_times.append(xmin)
    ratio_insulinCarbRatios.append(bolus_df.at[295, 'insulinCarbRatio'])

    for i in weekday_bolus.iloc[::-1].index:
        if curr != weekday_bolus.at[i, 'insulinCarbRatio']:
            curr = weekday_bolus.at[i, 'insulinCarbRatio']
            ratio_insulinCarbRatios.append(curr)
            ratio_times.append(weekday_bolus.at[i, 'time'])
            
    ratios_df = pd.DataFrame({"time":ratio_times,
                            "ratio":ratio_insulinCarbRatios})

    weekday_basal = basal_df.loc[(basal_df.day == weekday) & (basal_df.week == weekstr)].copy()
    weekday_basal.loc[:,'time'] = pd.to_datetime(weekday_basal['date'], format='%M:%S.%f') 
    weekday_basal['rate'] = weekday_basal['rate'].fillna(0)
    rates = weekday_basal['rate'].tolist()
    rates.reverse()
    rates = [0.3] + rates
    basal_rates = []
    for r in rates:
        basal_rates.append(r)
        basal_rates.append(r)

    times = weekday_basal['time'].tolist()
    times.reverse()
    basal_times = [xmin]
    for t in times:
        basal_times.append(t)
        basal_times.append(t)
    basal_times.append(xmax)
    basal_times = pd.to_datetime(basal_times)

    ax_bolus = fig.add_subplot(gs[1])
    ax_basal = ax_bolus.twinx()

    bolus = ax_bolus.bar(weekday_bolus['time'], weekday_bolus['normal'], color='#B5ACF2', width=0.03)
    basal = ax_basal.plot(basal_times, basal_rates, color='#F06688', linewidth=2)

    ax_bolus.set_xlabel("Time of Day", fontsize=18)
    ax_bolus.set_ylabel("Bolus (units)", fontsize=18)
    ax_basal.set_ylabel("Basal (units)", fontsize=18)

    ax_bolus.set_xlim(xmin - timedelta(hours=1), xmax + timedelta(hours=1))
    ax_bolus.set_ylim(0, 1.75)
    h_loc = dates.HourLocator(byhour=range(0,24,3))
    ax_bolus.xaxis.set_minor_locator(dates.HourLocator())
    ax_bolus.xaxis.set_major_locator(h_loc)
    xfmt = dates.DateFormatter('%l %p')
    ax_bolus.xaxis.set_major_formatter(xfmt)
    ax_basal.set_ylim(0, 1)

    ax_bolus.grid(True)
    ax_bolus.tick_params(axis='both', which='major', labelsize=14)
    ax_basal.tick_params(axis='y', which='major', labelsize=14)
    ax_bolus.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax_basal.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax_basal.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.2f"))

    bolus_carb_map = dict(zip(list(range(len(weekday_bolus.carbInput))), weekday_bolus.carbInput))

    i = 0
    for bar in ax_bolus.patches:
        carb_input = bolus_carb_map[i]
        i += 1
        if carb_input > 0:
            ax_bolus.annotate(format(carb_input, '.0f'),
                            (bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2), 
                            ha='center', va='center', 
                            bbox=dict(boxstyle="circle", ec='#F0C46E', fc="#F0C46E", pad=0.5),
                            size=12, xytext=(-0.2, -1.5),
                            textcoords='offset points')

    ax_ratio = fig.add_subplot(gs[2], sharex=ax_bolus)

    ax_ratio.set_xlim(xmin - timedelta(hours=1), xmax + timedelta(hours=1))
    ax_ratio.set_ylim(0, 2)
    ax_ratio.hlines(1, ratios_df.at[0,'time'], ratios_df.at[1,'time'], colors='#F0D6A2', lw=20)
    ax_ratio.hlines(1, ratios_df.at[1,'time'], ratios_df.at[2,'time'], colors='#F0D6A2', lw=20)
    ax_ratio.hlines(1, ratios_df.at[2,'time'], xmax, colors='#F0D6A2', lw=20)
    ax_ratio.vlines([ratios_df.at[1,'time'], ratios_df.at[2,'time']], 0, 2, colors='#eccc8c')
    ax_ratio.text(
        ratios_df.at[0,'time'] + timedelta(seconds=(ratios_df.at[1,'time'] - ratios_df.at[0,'time']).seconds / 2), 1, 
        str(ratios_df.at[0,'ratio']), color='black', ha='center', va='center', weight='bold', size='large')
    ax_ratio.text(
        ratios_df.at[1,'time'] + timedelta(seconds=(ratios_df.at[2,'time'] - ratios_df.at[1,'time']).seconds / 2), 1, 
        str(ratios_df.at[1,'ratio']), color='black', ha='center', va='center', weight='bold', size='large')
    ax_ratio.text(
        ratios_df.at[2,'time'] + timedelta(seconds=(xmax - ratios_df.at[2,'time']).seconds / 2), 1, 
        str(ratios_df.at[2,'ratio']), color='black', ha='center', va='center', weight='bold', size='large')


    h_loc = dates.HourLocator(byhour=range(0,24,3))
    ax_ratio.xaxis.set_major_locator(h_loc)
    xfmt = dates.DateFormatter('%l %p')
    ax_ratio.xaxis.set_major_formatter(xfmt)
    ax_ratio.tick_params(which='minor', left=False, labelleft=False, 
                        bottom=False, labelbottom=False, 
                        top=False, labeltop=False)
    ax_ratio.tick_params(which='major', left=False, labelleft=False, 
                        bottom=False, labelbottom=False, 
                        top=False, labeltop=False)
    ax_ratio.grid(True, axis='x')

    legend_elements = [Line2D([0], [0], color='#652CDF', marker='o', lw=1, label='Blood Glucose'),
                    Line2D([0], [0], marker='o', color='white', label='Carb Input (g)',
                            markerfacecolor='#F0C46E', markersize=15),
                    Line2D([0], [0], marker='s', color='white', label='Bolus', 
                            markerfacecolor='#B5ACF2', markersize=13),
                    Line2D([0], [0], color='#F06688', lw=2, label='Basal'),
                    Patch(facecolor='#F0D6A2', edgecolor='#eccc8c',
                            label='Insulin Carb Ratio')]

    ax.legend(handles=legend_elements, loc='center', fontsize='large',
            ncol=5, bbox_to_anchor=(0., 1.02, 1., .102))
    plt.savefig(figure_path, bbox_inches='tight', format='pdf')
    # plt.show()


def main(argv):
    subject_path = ''
    figure_path = ''

    try:
        opts, args = getopt.getopt(argv,"hs:f:",["subjectPath=","figurePath="])
    except getopt.GetoptError:
        print('figure1.py -s <path to subject data file> -f <path to image pdf>') 
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-h':
            print('figure1.py -s <path to subject data file> -f <path to image pdf>') 
            print('figure1.py -s ../dataset/Subject31.xlsx -f ../Figures/sub31_week20_thursday.pdf') 
            sys.exit()
        elif opt in ("-s", "--subjectPath"):
            subject_path = arg
        elif opt in ("-f", "--figurePath"):
            figure_path = arg
        else:
            print('figure1.py -s <path to subject data file> -f <path to image pdf>') 
    if (len(argv) != 4):
        print('figure1.py -s <path to subject data file> -f <path to image pdf>') 
        sys.exit()

    print('Path to subject file is ' + subject_path) 
    print('Path to image file is ' + figure_path)
    make_figure(subject_path, figure_path)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
