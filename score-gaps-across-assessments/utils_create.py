"Module containing helper functions for the ETL pipeline."
import time
from datetime import datetime, timedelta

import pandas as pd
import numpy as np


from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

import config

GOOGLE_SERVICE_ACCOUNT_CREDENTIALS = config.GOOGLE_SERVICE_ACCOUNT_CREDENTIALS

def connect_to_google(type):
    """Connect to Google Drive or Google Sheets API.
    
    Args:
        type (str): 'drive' or 'sheets'
        
    Returns:
        service: Google Drive or Google Sheets API service instance.
    """
    
    creds = service_account.Credentials.from_service_account_info(GOOGLE_SERVICE_ACCOUNT_CREDENTIALS)
    if type == 'drive':
        service = build('drive', 'v3', credentials = creds)
    elif type == 'sheets':
        service = build('sheets', 'v4', credentials = creds)
    else:
        raise ValueError('Type must be "drive" or "sheets"')
        
    return service

def read_google_sheet(service, spreadsheet_id, sheet_name = None, max_retries = 5,
                      retry_delay = 60):
    """Read Google Sheet to pandas DataFrame
    
    Args:
        service (googleapiclient.discovery.Resource): Google Sheets service
        spreadsheet_id (str): Google Sheet ID
        sheet_name (str): Name of sheet to read; defaults to None
        max_retries (int): Maximum number of times to retry reading the sheet; defaults to 5
        retry_delay (int): Number of seconds to wait between retries; defaults to 60
        
    Returns:
        pandas.DataFrame: Dataframe of Google Sheet
    """
    
    if sheet_name is None:
        file = service.spreadsheets().get(spreadsheetId = spreadsheet_id).execute()
        sheet_name = file['sheets'][0]['properties']['title']
    range_name = f"{sheet_name}!A1:ZZ"
    
    # sometimes the API fails to read the sheet, so we'll try a few times
    for attempt in range(max_retries):
        try:
            result = service.spreadsheets().values().get(spreadsheetId = spreadsheet_id,
                                                          range = range_name).execute()
            values = result.get('values', [])
            df = pd.DataFrame(values[1:], columns = values[0])
            break
        except HttpError as e:
            if e.resp.status in [408, 504]:  # 408 Request Timeout, 504 Gateway Timeout
                print(f"Timeout error encountered. Attempt {attempt + 1} of {max_retries}. \
                    Retrying in {retry_delay} seconds.")
                time.sleep(retry_delay)
            else:
                raise  # Re-raise the exception if it's not a timeout error
            
    return df


def descriptive_counts_and_percents(df, group_var, target_var):
    """
    Create a descriptive DataFrame with counts and percent for each level of a grouping variable by a target variable.

    Parameters:
    - df: pandas DataFrame containing the data.
    - group_var: string, the name of the column to group by (e.g., 'Age Group').
    - target_var: string, the name of the target column (e.g., 'offered').

    Returns:
    - A pandas DataFrame with counts and percent for each level of group_var by target_var.
    """
    # Group by group_var and target_var, then count
    counts = df.groupby([group_var, target_var]).size()

    # Unstack for better readability
    counts_unstacked = counts.unstack(level=target_var, fill_value=0)

    # Calculate percent
    percent = counts_unstacked.div(counts_unstacked.sum(axis=1), axis=0) * 100

    # Combine counts and percent into a single DataFrame for descriptive purposes
    descriptive_df = pd.concat([counts_unstacked, percent], axis=1, keys=['Count', 'Percent'])

    # Optional: Round the percent values to 2 decimal places
    descriptive_df = descriptive_df.round(2)

    return descriptive_df


def calculate_cohens_d(df, group_var, target_var, subset_var=None, subset_val=None):
    """
    Calculate Cohen's d effect size for a target variable across groups defined in a grouping variable,
    using the most frequently occurring group as the reference, for the whole sample and a subset,
    and return a DataFrame with both Cohen's d values and their difference.

    Parameters:
    - df: pandas DataFrame containing the data
    - group_var: string, the name of the column in df that contains the grouping variable
    - target_var: string, the name of the column in df for which to calculate Cohen's d
    - subset_var: string, the name of the column in df for subsetting (optional)
    - subset_val: value, the value in subset_var to filter by (optional)

    Returns:
    A pandas DataFrame with group comparisons as rows, Cohen's d values for the whole sample and the subset,
    and the difference between the two Cohen's d values, rounded to 2 decimal places.
    """
    # Find the most frequent group in the grouping variable
    most_frequent_group = df[group_var].mode()[0]
    
    # Initialize a list to store results
    results = []
    
    # Get unique groups excluding the most frequent one
    unique_groups = df[group_var].unique()
    unique_groups = [group for group in unique_groups if group != most_frequent_group]
    
    # Reference group data
    reference_data = df[df[group_var] == most_frequent_group][target_var]
    
    # Calculate Cohen's d for each group compared to the most frequent group for the whole sample
    for group in unique_groups:
        group_data = df[df[group_var] == group][target_var]
        d_whole = pg.compute_effsize(group_data, reference_data, eftype='cohen')
        
        # Calculate Cohen's d for the subset if specified
        if subset_var and subset_val is not None:
            subset_df = df[df[subset_var] == subset_val]
            subset_reference_data = subset_df[subset_df[group_var] == most_frequent_group][target_var]
            subset_group_data = subset_df[subset_df[group_var] == group][target_var]
            d_subset = pg.compute_effsize(subset_group_data, subset_reference_data, eftype='cohen')
        else:
            d_subset = None
        
        # Append results
        results.append({
            "Comparison": f"{most_frequent_group} vs {group}",
            "Cohen's d (Whole Sample)": d_whole,
            "Cohen's d (Subset)": d_subset,
            "Difference": d_whole - d_subset if d_subset is not None else None
        })
        
    # Convert results to DataFrame and round values
    results_df = pd.DataFrame(results).round({'Cohen\'s d (Whole Sample)': 2, 'Cohen\'s d (Subset)': 2, 'Difference': 2})

        
    return results_df

def load_original_data():
    url = 'https://raw.githubusercontent.com/armacintosh/score-gaps/main/score-gaps-across-assessments/merged_data.csv'
    response = requests.get(url)
    if response.status_code == 200:
        return pd.read_csv(StringIO(response.text))
    else:
        st.error("Failed to load data from GitHub.")
        return None

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
    'Multiple Races/Ethnicities',
    'White'
]

