"Module containing helper functions for the ETL pipeline."
from io import StringIO
import pandas as pd
import requests
import streamlit as st
from collections import OrderedDict


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


def var_clean_df(df, assessment_dict, order_dict_param):
    """
    Pivot and clean the DataFrame, handling multiple variables and ensuring the rows and columns
    are ordered according to the provided dictionaries. Returns a dictionary of DataFrames where
    each key is a 'Variable'.

    Args:
        df (pandas.DataFrame): The input DataFrame containing multiple variables.
        assessment_dict (dict): Dictionary that specifies the order of assessments.
        order_dict_param (dict): Dictionary that specifies the order of the columns.

    Returns:
        dict: A dictionary of cleaned and pivoted DataFrames, one for each 'Variable'.
    """

    # Initialize an empty dictionary to store the DataFrames for each variable
    df_dict = {}

    # Group the DataFrame by 'Variable' if it exists in the DataFrame
    if 'Variable' in df.columns:
        grouped = df.groupby('Variable')
    else:
        grouped = [(None, df)]  # If there's no 'Variable' column, treat the whole DataFrame as one group

    # Iterate over each variable group
    for variable, group_df in grouped:
        # Pivot the DataFrame with 'Assessment' as index and 'Grouping' as columns
        pivot_df = group_df.pivot_table(index='Assessment',
                                        columns='Grouping',
                                        values="Cohen's d",
                                        aggfunc='first')

        # Reset the index to keep 'Assessment' as a column
        pivot_df.reset_index(inplace=True)

        # Filter and order rows based on assessment_dict
        ordered_assessments = []
        for key, values in assessment_dict.items():
            # Keep only assessments that are in both the DataFrame and the dictionary
            matching_assessments = [val for val in values if val in pivot_df['Assessment'].values]
            ordered_assessments.extend(matching_assessments)

        # Order the rows by the ordered assessments
        pivot_df['Assessment'] = pd.Categorical(pivot_df['Assessment'], categories=ordered_assessments, ordered=True)
        pivot_df.sort_values('Assessment', inplace=True)
        # Create an ordered list of columns based on order_dict
        ordered_columns = ['Assessment']  # Start with 'Assessment' as the first column
        if variable in order_dict_param:  # Only proceed if the variable has a corresponding order
            for grouping in order_dict_param[variable]:
                if grouping in pivot_df.columns:
                    ordered_columns.append(grouping)

        # Reorder the columns based on the ordered_columns
        pivot_df = pivot_df[ordered_columns]

        # Add the cleaned DataFrame to the dictionary with the variable as the key
        df_dict[variable] = pivot_df

    # Return the dictionary of DataFrames
    return df_dict




# Function to filter DataFrame based on the tab selected
def filter_df_by_tab(df, tab_name):
    filtered_values = tabs_dicts[tab_name]
    return df[df['Variable'].isin(filtered_values)]


def make_footnote (comparison_param, variables):

    # Initialize an empty string to accumulate the footnote text
    footnote_text = '<b>Footnotes:</b><br>'

    # Loop through each variable in the current tab's variables list
    for var in variables:
        # Get the comparison group for the given variable
        comparison_group = comparison_param.get(var, 'Unknown')  # 'Unknown' is a fallback if the variable is not in the dictionary
        
        # Option 2: Code block style
        footnote_text += f"The comparison group for <code>{var}</code> is <b>{comparison_group}</b><br>"
        
    
    # Inject custom CSS for smaller font size and reduced line spacing
    st.markdown(
        """
        <style>
        .footnote-text {
            font-size: 14px;
            line-height: 1.1;
            margin-top: 0px;  /* Adjust margin-top */
            margin-bottom: 0px;  /* Adjust margin-bottom */
            padding-top: 0px;  /* Adjust padding-bottom */
            padding-bottom: 40px;  /* Adjust padding-bottom */
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    return footnote_text


def reorder_columns_by_variable(pivot_df, variables_in_tab, order_dict=None):
    """
    Reorder the columns of the DataFrame based on the variable and the provided order list.
    Keeps the index column and removes other columns that are not in the order list.
    Adds 'Assessment' as the first element of the order list if it exists in the DataFrame.

    :param pivot_df: DataFrame to reorder
    :param variable: Value of the 'variable' field
    :param order_dict: Dictionary defining the custom order of columns for each variable
    :return: Reordered DataFrame with only the columns in the order list, plus 'Assessment' if present
    """
    for variable in variables_in_tab:
            
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

# Function to update font size
def update_font_size(size):
    st.session_state.font_size = size

def reorder_assessment_dict(assessment_dict, order_list):
    """
    Reorder the keys in assessment_dict based on the specified assessment_group_order.

    Args:
        assessment_dict (dict): The dictionary containing assessments grouped by key.
        assessment_group_order (list): The desired order of assessment groups.

    Returns:
        Ordered dict: A new dictionary with keys reordered according to assessment_group_order.
    """
    # Create a new ordered dictionary to hold the reordered assessments
    reordered_assessment_dict = OrderedDict()

    # Add the assessments to the new dictionary in the specified order
    for group in order_list:
        if group in assessment_dict:
            reordered_assessment_dict[group] = assessment_dict[group]

    # Optionally, append any remaining groups that were not in the specified order
    for group, values in assessment_dict.items():
        if group not in reordered_assessment_dict:
            reordered_assessment_dict[group] = values

    return reordered_assessment_dict

##############################################
assessment_group_order = ['NAEP','SAT','Casper','MCAT','AAMC','GRE','GMAT','LSAT']

assessments_default = [
    'NAEP - Reading - 4 - US - 2019', 
    'NAEP - Science - 4 - US - 2019', 
    'NAEP - Reading - 8 - US - 2019',
    'NAEP - Science - 8 - US - 2019', 
    'NAEP - Reading - 12 - US - 2019',
    'NAEP - Science - 12 - US - 2019',
    'SAT - Total - US - 2023', 
    'Casper - US - 2024', 
    'MCAT Total - US - 2023', 
    'AAMC - GPA Total - US - 2023', 
    'GRE - Analytical Writing - US - 2023',
    'GRE - Quantitative - US - 2023', 
    'GRE - Verbal - US - 2023',
    'GMAT - Total Score - US - 2023', 
    'LSAT - US - 2023'
]

# Create the format dictionary with specified formatting for each column by name
format_dict = {
    'Year': '{:.0f}',          # No decimal places for Year
    'Mean': '{:.2f}',          # 2 decimal places for Mean
    'SD': '{:.2f}',            # 2 decimal places for SD
    'N': '{:.0f}',             # Integer format for N (no decimal places)
    "Cohen's d": '{:.2f}'      # 2 decimal places for Cohen's d
}

tabs_dicts = {
    'Gender':['Gender'],
    'Race/Ethnicity':['Race/Ethnicity'],
    'SES':['Family Income', 'Parent Education','National School Lunch Program eligibility'],
    'Language & Citizenship':['Home Language', 'English Proficiency','Citizenship']
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
    'Parent Education': [
        'No High School Diploma',
        'High School Diploma',
        'Associate Degree', 
        'Graduate Degree',   
        'No Response'
    ],
    'Family Income': [
        '< $50,000', 
        '$50,000 to $74,999',
        '$75,000 to $99,999', 
        '> $100,000',
        'No Response'
    ],
    'National School Lunch Program eligibility': [
        'Eligible',
        'Information not available'
    ],
    'Citizenship': [
        'International',
        'Domestic',
        'No Response'
    ],
    'Home Language': [
        'Another Language',
        'English',
        'No Response'
    ],
    'English Proficiency': [
        'Basic/Fair/Competent',
        'No Response'
    ]
    # Add more variables and their corresponding column orders here
}

# Dictionary to map the comparison group based on the variable
comparison = {
    'Race/Ethnicity': 'White',
    'Gender': 'Female',
    'Family Income': '> $100,000',
	'Parent Education': 'Bachelor\'s Degree',
	'English Proficiency': 'Advanced/Functionally Native/Native',
	'Home Language': 'English',
	'Citizenship': 'Domestic',
	'National School Lunch Program eligibility': 'Not eligible',
}

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

