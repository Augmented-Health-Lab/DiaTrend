# DiaTrend: A dataset from advanced diabetes technology to enable development of novel analytic solutions

Please cite this dataset as **Temiloluwa Prioleau, Abigail Bartolome, Catherine Stanger, and Richard Comi. (2022) DiaTrend: A dataset from advanced diabetes technology to enable development of novel analytic solutions** [![Generic badge](https://img.shields.io/badge/Scientific_Data-Data_Descriptor-blue.svg)](https://www.nature.com/sdata/articles?type=data-descriptor)

This repository contains references to data records for a Data descriptor submitted to *Scientific Data*. Any references to the dataset assume dataset files are stored in directory `dataset/` at this level.
Below is a description of the different folders and their content.

Please feel free to contact Abigail Bartolome (abigail.bartolome.gr@dartmouth.edu) if you need assistance navigating these documents.

### `python_scripts/`

* `figure1.py`:
  * Code for generating the plots in Figure 1.
  
        python figure1.py -s <path to subject data file> -f <path to image pdf>

* `figure2.py`:
  * Code for generating Figure 2.

        python figure2.py -d <path to dataset directory> -f <path to image pdf>

* `figure3.py`:
  * Code for generating Figure 3.
  
        python figure3.py -d <path to dataset directory> -f <path to image pdf>

* `figure4.py`:
  * Code for generating the plots in Figure 4.
  * Writes `figure4_cgm_daily_hist.pdf` and `figure4_times_in_ranges.pdf` to figure directory path.

        python figure4.py -s <path to subject data file> -f <path to figure directory>

* `figure5.py`:
  * Code for generating the plots in Figure 5.
  * Writes `figure5_bolusDose_boxplot.pdf`, `figure5_carbInput_boxplot_ymax200.pdf`, and `figure5_ip_daily_hist.pdf` to figure directory path.

        `python figure5.py -s <path to subject data file> -f <path to figure directory>`

### `Figures/`
* Files generated by the code in the `python_scripts` directory

