"Module containing helper functions for the ETL pipeline."
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests
from io import StringIO


def load_original_data():
    url = 'https://raw.githubusercontent.com/armacintosh/score-gaps/main/score-gaps-across-assessments/merged_data.csv'
    response = requests.get(url)
    if response.status_code == 200:
        return pd.read_csv(StringIO(response.text))
    else:
        st.error("Failed to load data from GitHub.")
        return None

# Define colors for cells based on effect size
def effect_size_color_scale(value):
    abs_value = abs(value)
    if abs_value <= 0.2:
        return '#96D377'
    elif 0.2 < abs_value <= 0.4:
        return '#D9EAD3'
    elif 0.4 < abs_value <= 0.6:
        return '#ECEED0'
    elif 0.6 < abs_value <= 0.8:
        return '#FEF2CC'
    elif 0.8 < abs_value <= 1.0:
        return '#F9DFCC'
    elif 1.0 < abs_value <= 1.2:
        return '#F4CCCC'
    elif abs_value > 1.2:
        return '#EFB9CC'
    else:
        return '#FFFFFF'

def create_full_table(df):
    """
    Create a full table with the desired columns from the input dataframe.

    Args:
        df (pandas.DataFrame): The input dataframe containing the data.

    Returns:
        pandas.DataFrame: The resulting dataframe with the desired columns.

    """
    
    # Create the table with the desired columns
    summary_df = df[['Variable','Subject', 'Jurisdiction', 'Year', 'Grouping', 
                          'Mean', 'SD', 'N', "Cohen's d"]]

    # Sort the dataframe to merge 'Selected Variable' across rows
    summary_df = summary_df.sort_values(by=['Variable', 
                                        'Jurisdiction', 
                                        'Year', 
                                        'Grouping'])
    
    return summary_df

def pivot_clean_df(df, color_scale):
    """
    Pivot and clean the DataFrame.

    Args:
        df (pandas.DataFrame): The input DataFrame.
        color_scale (function): The color scale function to apply.

    Returns:
        tuple: A tuple containing the pivoted and cleaned DataFrame and the cell colors.

    """

    # Copy the filtered DataFrame
    # df = filtered_df.copy()

    # Pivot the DataFrame
    pivot_df = df.pivot_table(index='Index',
                              columns='Grouping',
                              values=["Cohen's d"],
                              aggfunc='first')

    # Flatten the MultiIndex columns
    pivot_df.columns = [f'{col[1]}' for col in pivot_df.columns]
    pivot_df.reset_index(inplace=True)

    # Remove columns where all values are zero
    pivot_df = pivot_df.loc[:, (pivot_df != 0).any(axis=0)]

    # Select numeric columns
    numeric_cols = pivot_df.select_dtypes(include=['number']).columns

    # Round numeric columns to 2 decimals for display
    pivot_df[numeric_cols] = pivot_df[numeric_cols].round(2)

    # Apply the color scale to only numeric columns
    cell_colors = [['white'] * len(pivot_df)] + [[color_scale(round(value, 2)) for value in pivot_df[col]] for col in numeric_cols]

    # Format numeric columns to show two decimal places, even for whole numbers
    pivot_df[numeric_cols] = pivot_df[numeric_cols].applymap(lambda x: f'{x:.2f}')

    return pivot_df, cell_colors

# Order of subjects for the table
subjects_ordered = [
    'NAEP - Science - 4',
    'NAEP - Reading - 4',
    'NAEP - Reading - 8',
    'NAEP - Science - 8',
    'NAEP - Science - 12',
    'NAEP - Reading - 12',
    'SAT - Total',
    'SAT - Math',
    'SAT - ERW',
    'Casper',
    'MCAT Total',
    'MCAT CPBS',
    'MCAT CARS',
    'MCAT BBLS',
    'MCAT PSBB',
    'AAMC - GPA Total',
    'AAMC - GPA Science',
    'AAMC - GPA Non-Science',
    'GRE - Analytical Writing',
    'GRE - Quantitative',
    'GRE - Verbal',
    'GMAT - Total Score',
    'LSAT'
]

# Define the race order
race_order = [
    'Black',
    'Hispanic',
    'Asian',
    'American Indian/Alaska Native',
    'Native Hawaiian/Other Pacific Islander',
    'Another Race/Ethnicity',
    'Multiple Races/Ethnicities',
    'White'
]

# Define defaults
var_defaults = ["Race/Ethnicity", "Gender"]
sub_defaults = [
    'NAEP - Science - 4 - US - 2019',
    'NAEP - Science - 8 - US - 2019',
    'NAEP - Science - 12 - US - 2019',
    'SAT - Total - US - 2023',
    'Casper - US - 2024',
    'Casper - CA - 2024',
    'MCAT Total - US - 2023',
    'AAMC - GPA Total - US - 2023',
    'GRE - Quantitative - US - 2023',
    'GMAT - Total Score - US - 2023',
    'LSAT - US - 2023'
    ]

# Define the color coding legend using HTML and CSS
legend_html = """
<div style="display: flex; flex-direction: column; align-items: flex-start;">
    <div style="display: flex; align-items: center; margin-bottom: 5px;">
        <div style="width: 20px; height: 20px; background-color: #96D377; margin-right: 10px;"></div>
        <span>Negligible (< 0.2)</span>
    </div>
    <div style="display: flex; align-items: center; margin-bottom: 5px;">
        <div style="width: 20px; height: 20px; background-color: #D9EAD3; margin-right: 10px;"></div>
        <span>Small (0.2 - 0.4)</span>
    </div>
    <div style="display: flex; align-items: center; margin-bottom: 5px;">
        <div style="width: 20px; height: 20px; background-color: #ECEED0; margin-right: 10px;"></div>
        <span>Small-Moderate (0.4 - 0.6)</span>
    </div>
    <div style="display: flex; align-items: center; margin-bottom: 5px;">
        <div style="width: 20px; height: 20px; background-color: #FEF2CC; margin-right: 10px;"></div>
        <span>Moderate (0.6 - 0.8)</span>
    </div>
    <div style="display: flex; align-items: center; margin-bottom: 5px;">
        <div style="width: 20px; height: 20px; background-color: #F9DFCC; margin-right: 10px;"></div>
        <span>Moderate-Large (0.8 - 1.0)</span>
    </div>
    <div style="display: flex; align-items: center; margin-bottom: 5px;">
        <div style="width: 20px; height: 20px; background-color: #F4CCCC; margin-right: 10px;"></div>
        <span>Large (1.0 - 1.2)</span>
    </div>
    <div style="display: flex; align-items: center; margin-bottom: 5px;">
        <div style="width: 20px; height: 20px; background-color: #EFB9CC; margin-right: 10px;"></div>
        <span>Very Large (> 1.2)</span>
    </div>
</div>
"""

Notes_html = """
        **Data Sources**  
        Annual reports for the following sources were available. Most recent data used where possible.

        **Assessment Sources:**
        - **SAT**: [SAT Suite Program Results](https://reports.collegeboard.org/sat-suite-program-results)  
        - Using Pooled SD: [Total Group SAT Suite of Assessments Annual Report](https://reports.collegeboard.org/media/pdf/2023-total-group-sat-suite-of-assessments-annual-report%20ADA.pdf)
        - **NAEP**: [NAEP API Documentation](https://www.nationsreportcard.gov/api_documentation.aspx)  
        - See information below for pooled sample size
        - **LSAT**: [LSAT Research Report](https://www.lsac.org/sites/default/files/research/TR-24-01.pdf)
        - **GRE**: [GRE Snapshot Report](https://www.ets.org/pdfs/gre/snapshot.pdf#page=11.09)
        - **GMAT**: [GMAT Test Taker Data](https://www.gmac.com/-/media/files/gmac/research/gmat-test-taker-data/profile-of-gmat-testing-north-america-ty2019-ty2023.pdf)  
        - Using Pooled SD: [GMAT Validity and Testing Report](https://www.gmac.com/-/media/files/gmac/research/validity-and-testing/rr-17-01-differential-validity-talento-miller-web-release-2.pdf#page=6.09)
        - **Casper**: [Casper Technical Manual](https://acuityinsights.com/resource/casper-technical-manual/)  
        - More detailed information derived from Qlik
        - **AAMC - MCAT GPA**: [AAMC 2023 Facts - Applicants and Matriculants Data](https://www.aamc.org/data-reports/students-residents/data/2023-facts-applicants-and-matriculants-data)

        **NAEP Sample Size:**
        - **2019 Reading**
        - Grade 12: N = 26,700 ([Source](https://www.nationsreportcard.gov/highlights/reading/2019/))
        - Grade 8: N = 143,100 ([Source](https://www.nationsreportcard.gov/highlights/reading/2019/))
        - Grade 4: N = 150,600 ([Source](https://www.nationsreportcard.gov/highlights/reading/2019/))
        - **2019 Science**
        - Grade 4: N = 30,400 ([Source](https://www.nationsreportcard.gov/science/?grade=4))
        - Grade 8: N = 31,400 ([Source](https://www.nationsreportcard.gov/science/?grade=4))
        - Grade 12: N = 26,400 ([Source](https://www.nationsreportcard.gov/science/?grade=4))
        """