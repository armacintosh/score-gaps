"Module containing helper functions for the ETL pipeline."
import tempfile
import time
import streamlit as st
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
    # Check if value is numeric (int, float) and not NaN
    if isinstance(value, (int, float)) and not pd.isnull(value):
        abs_value = abs(value)
        if abs_value <= 0.2:
            return 'background-color: #96D377'  # Light green
        elif 0.2 < abs_value <= 0.4:
            return 'background-color: #D9EAD3'  # Light green variant
        elif 0.4 < abs_value <= 0.6:
            return 'background-color: #ECEED0'  # Yellow variant
        elif 0.6 < abs_value <= 0.8:
            return 'background-color: #FEF2CC'  # Light yellow
        elif 0.8 < abs_value <= 1.0:
            return 'background-color: #F9DFCC'  # Light orange
        elif 1.0 < abs_value <= 1.2:
            return 'background-color: #F4CCCC'  # Light red
        elif abs_value > 1.2:
            return 'background-color: #EFB9CC'  # Strong red
    # Return no styling if value is not numeric or is NaN
    return ''

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
    
    # fix 'Year' to be an integer
    summary_df['Year'] = summary_df['Year'].astype(int)
    
    return summary_df

def var_clean_df(df):
    """
    Pivot and clean the DataFrame.

    Args:
        df (pandas.DataFrame): The input DataFrame.

    Returns:
        tuple: A tuple containing the pivoted and cleaned DataFrame and the cell colors.

    """

    # Copy the filtered DataFrame
    # df = filtered_df.copy()

    # Pivot the DataFrame
    pivot_df = df.pivot_table(index='Assessment',
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
    
    # Format numeric columns to show two decimal places, even for whole numbers
    # pivot_df[numeric_cols] = pivot_df[numeric_cols].applymap(lambda x: f'{x:.2f}')

    return pivot_df

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

# Create the format dictionary with specified formatting for each column by name
format_dict = {
    'Year': '{:.0f}',          # No decimal places for Year
    'Mean': '{:.2f}',          # 2 decimal places for Mean
    'SD': '{:.2f}',            # 2 decimal places for SD
    'N': '{:.0f}',             # Integer format for N (no decimal places)
    "Cohen's d": '{:.2f}'      # 2 decimal places for Cohen's d
}

# Define custom column order lists for different variables
order_dict = {
    'Race/Ethnicity': [
        'Black',
        'Hispanic',
        'Asian',
        'Indigenous/Native',
        'Native Hawaiian/Other Pacific Islander',
        'Another Race/Ethnicity',
        'Multiple Races/Ethnicities',
        'No Response'
    ],
    'Gender': [
        'Male',
        'Another gender',
        'No Response'
    ],
    # Add more variables and their corresponding column orders here
}


# Dictionary to map the comparison group based on the variable
comparison = {
    'Race/Ethnicity': 'White',
    'Gender': 'Female'
}

def reorder_columns_by_variable(pivot_df, variable, order_dict=None):
    """
    Reorder the columns of the DataFrame based on the variable and the provided order list.
    Keeps the index column and removes other columns that are not in the order list.
    Adds 'Assessment' as the first element of the order list if it exists in the DataFrame.

    :param pivot_df: DataFrame to reorder
    :param variable: Value of the 'variable' field
    :param order_dict: Dictionary defining the custom order of columns for each variable
    :return: Reordered DataFrame with only the columns in the order list, plus 'Assessment' if present
    """

    # If the variable is in the order_dict and the order_list is provided
    if variable in order_dict:
        order_list = order_dict[variable]

        # Add 'Assessment' to the order list if it exists in the DataFrame and is not already in the list
        if 'Assessment' in pivot_df.columns and 'Assessment' not in order_list:
            order_list.insert(0, 'Assessment')

        # Filter columns that are in the order list
        ordered_columns = [col for col in order_list if col in pivot_df.columns]

        # Keep only the ordered columns
        pivot_df = pivot_df[ordered_columns]

    return pivot_df

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

    
def get_explainer_html():
    explainer_html = """
    <div style="font-size: 16px; line-height: 1.6;">
        <ul>
            The pivot table shows Cohen’s d values, which are used to measure the difference between two groups.
            <li>A smaller Cohen’s d means the groups are more similar, with less difference between them.</li>
            <li>A larger Cohen’s d means there is a bigger difference between the groups.</li>
            In simple terms, Cohen's d helps us see how much two groups differ from each other in test scores.
        </ul>
        <ul>
            Systemic biases and barriers exist in the education system, and standardized tests often reveal those biases in our society and systems.
            <br>Well-constructed tests should have the least amount of bias possible - and Casper shows much lower demographic differences overall compared to academic tests.
            <br>As research shows better ways to construct and deliver the test, we evolve to continuously improve and make Casper more fair.
        </ul>
        <p>For more information, see <a href="https://rpsychologist.com/cohend/" target="_blank">Cohen’s d interactive visualization</a>.</p>
    </div>
    """
    return explainer_html

# Define the color coding legend using HTML and CSS
# HTML legend for effect size interpretation with dynamic font size
def get_legend_html(font_size):
    # HTML legend for effect size interpretation with dynamic font size and horizontal layout
    legend_html = f"""
    <div style="display: flex; flex-direction: row; align-items: center; justify-content: flex-start; font-size: {font_size};">
        <div style="display: flex; align-items: center; margin-right: 20px;">
            <div style="width: 20px; height: 20px; background-color: #96D377; margin-right: 10px;"></div>
            <span>Negligible <br>(< 0.2)</span>
        </div>
        <div style="display: flex; align-items: center; margin-right: 20px;">
            <div style="width: 20px; height: 20px; background-color: #D9EAD3; margin-right: 10px;"></div>
            <span>Small <br>(0.2 - 0.4)</span>
        </div>
        <div style="display: flex; align-items: center; margin-right: 20px;">
            <div style="width: 20px; height: 20px; background-color: #ECEED0; margin-right: 10px;"></div>
            <span>Small-Moderate <br>(0.4 - 0.6)</span>
        </div>
        <div style="display: flex; align-items: center; margin-right: 20px;">
            <div style="width: 20px; height: 20px; background-color: #FEF2CC; margin-right: 10px;"></div>
            <span>Moderate <br>(0.6 - 0.8)</span>
        </div>
        <div style="display: flex; align-items: center; margin-right: 20px;">
            <div style="width: 20px; height: 20px; background-color: #F9DFCC; margin-right: 10px;"></div>
            <span>Moderate-Large <br>(0.8 - 1.0)</span>
        </div>
        <div style="display: flex; align-items: center; margin-right: 20px;">
            <div style="width: 20px; height: 20px; background-color: #F4CCCC; margin-right: 10px;"></div>
            <span>Large <br>(1.0 - 1.2)</span>
        </div>
        <div style="display: flex; align-items: center; margin-right: 20px;">
            <div style="width: 20px; height: 20px; background-color: #EFB9CC; margin-right: 10px;"></div>
            <span>Very Large <br>(> 1.2)</span>
        </div>
    </div>
    """
    return legend_html

Notes_html1 = """
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

Notes_html = """
        (in alphabetical order)

        - **AAMC**: 
            - The AAMC provides data on GPA and MCAT scores for applicants and matriculants to US medical schools.
            - MCAT is a knowledge-based standardized exam with the sections: Biological and Biochemical Foundations, Chemical and Physical Foundations, Psychological and Social Foundations, and Critical Analysis and Reasoning.
            - GPA data reflects undergraduate academic performance for applicants to US medical schools.
            - Data source: [AAMC 2023 Facts - Applicants and Matriculants Data](https://www.aamc.org/data-reports/students-residents/data/2023-facts-applicants-and-matriculants-data)

        - **Casper**: 
            - Casper is a situational judgment test used across ~500 higher education programs to assess social intelligence and professionalism.
            - It is used in conjunction with traditional cognitive assessments like GPA or MCAT.
            - Data source: [Casper Technical Manual](https://acuityinsights.com/resource/casper-technical-manual/)

        - **GMAT**: 
            - The GMAT is a standardized test usually for MBA programs and other business graduate programs.
            - GMAT Sections: Analytical Writing, Integrated Reasoning, Quantitative, and Verbal.
            - Data source: [GMAT Test Taker Data](https://www.gmac.com/-/media/files/gmac/research/gmat-test-taker-data/profile-of-gmat-testing-north-america-ty2019-ty2023.pdf)

        - **GRE**: 
            - The GRE is a standardized test required for admissions to many graduate programs.
            - GRE Sections: Analytical Writing, Quantitative Reasoning, and Verbal Reasoning.
            - Data source: [GRE Snapshot Report](https://www.ets.org/pdfs/gre/snapshot.pdf#page=11.09)

        - **LSAT**: 
            - The LSAT is a standardized test used for law school admissions, assessing reading comprehension, logical reasoning, and analytical reasoning.
            - LSAT Sections: Logical Reasoning, Analytical Reasoning, and Reading Comprehension.
            - Data source: [LSAT Research Report](https://www.lsac.org/sites/default/files/research/TR-24-01.pdf)

        - **NAEP**: 
            - The NAEP (National Assessment of Educational Progress), also called the "Nation’s Report Card," measures student performance in the US, typically for 4th, 8th, and 12th graders.
            - NAEP Sections: Reading, Mathematics, Science, and other subject assessments.
            - Data source: [NAEP API Documentation](https://www.nationsreportcard.gov/api_documentation.aspx)

        - **SAT**: 
            - The SAT is a standardized test used for college admissions in the US, typically taken by high school students.
            - SAT Sections: Math and Evidence-Based Reading and Writing (ERW).
            - Data source: [SAT Suite Program Results](https://reports.collegeboard.org/sat-suite-program-results)
        """

