import streamlit as st
import pandas as pd
import requests
from io import StringIO
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# Set page layout to wide
st.set_page_config(layout="wide")

def load_original_data():
    url = 'https://raw.githubusercontent.com/armacintosh/score-gaps/main/score-gaps-across-assessments/merged_data.csv'
    response = requests.get(url)
    if response.status_code == 200:
        return pd.read_csv(StringIO(response.text))
    else:
        st.error("Failed to load data from GitHub.")
        return None
      
# Load your dataframe
merged_df = load_original_data()

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

# Sidebar for user input
st.sidebar.header("Filter Data")
selected_variables = st.sidebar.multiselect("Select Variable", merged_df['Variable'].unique())
selected_jurisdictions = st.sidebar.multiselect("Select Jurisdiction", merged_df['Jurisdiction'].unique())
selected_subjects = st.sidebar.multiselect("Select Subjects", merged_df['Subject'].unique())
 

# Add a selector for color gradient
color_map = st.sidebar.selectbox("Select Color Gradient (cmap)", 
    ['PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu', 'RdYlBu', 
     'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic'])

# Custom color map function
def custom_color_map(value):
    abs_value = abs(value)
    if 0 < abs_value <= 0.2:
        return 'background-color: #CFE2F3'
    elif 0.2 < abs_value <= 0.4:
        return 'background-color: #D9EAD3'
    elif 0.4 < abs_value <= 0.6:
        return 'background-color: #ECEED0'
    elif 0.6 < abs_value <= 0.8:
        return 'background-color: #FEF2CC'
    elif 0.8 < abs_value <= 1.0:
        return 'background-color: #F9DFCC'
    elif 1.0 < abs_value <= 1.2:
        return 'background-color: #F4CCCC'
    elif abs_value > 1.2:
        return 'background-color: #EFB9CC'
    else:
        return ''  # Return empty string if no color should be applied

# Function to clean the df apply the custom color map only to non-index columns
def apply_custom_colormap(df):
    # Remove columns where all values are 0.00
    df = df.loc[:, (df != 0.00).any(axis=0)]
    
    # Get the Styler object and apply the custom colormap only to non-index columns
    non_index_columns = df.columns.difference(df.index.names)
    return df.style.applymap(custom_color_map).format("{:.2f}", subset=pd.IndexSlice[:, non_index_columns])

# Filtering the dataframe based on user selection
if not selected_subjects:
    selected_subjects = merged_df['Subject'].unique()
    
filtered_df = merged_df[
    (merged_df['Variable'].isin(selected_variables)) & 
    (merged_df['Jurisdiction'].isin(selected_jurisdictions)) &
    (merged_df['Subject'].isin(selected_subjects))
]

# Convert year into category using .loc to avoid SettingWithCopyWarning
filtered_df.loc[:, 'Year'] = filtered_df['Year'].astype(str)

# Create the table with the desired columns
summary_df = filtered_df[['Variable','Subject', 'Jurisdiction', 'Year', 'Grouping', 'Mean', 'SD', 'N']]

# Rename columns for clarity
summary_df = summary_df.rename(columns={
    'Variable': 'Selected Variable',
    'Jurisdiction': 'Selected Jurisdiction'
})

# Sort the dataframe to merge 'Selected Variable' across rows
summary_df = summary_df.sort_values(by=['Selected Variable', 'Selected Jurisdiction', 'Year', 'Grouping'])

# Display the summary dataframe in Streamlit
with st.expander("Summary Table"):
    st.dataframe(summary_df)

# Create combinations of selected variables and jurisdictions
combinations = [(var, jur) for var in selected_variables for jur in selected_jurisdictions]

with st.expander("Effect Size Summary"):
    # Create a two-column layout
    col1, col2 = st.columns([3, 1])  # Adjust the width ratio as needed

# Create tabs for each combination of selected variables and jurisdictions within an expander
with col1:    
    if combinations:
        tabs = st.tabs([f"{var} - {jur}" for var, jur in combinations])
        for idx, (variable, jurisdiction) in enumerate(combinations):
            with tabs[idx]:
                # Filter the dataframe for the current combination of variable and jurisdiction
                combination_df = filtered_df[(filtered_df['Variable'] == variable) & (filtered_df['Jurisdiction'] == jurisdiction)]
                
                # Creating a pivot table for Cohen's d
                pivot_df = combination_df.pivot_table(
                    index=['Subject', 'Year'], 
                    columns='Grouping', 
                    values="Cohen's d",
                    aggfunc='first'
                )

                # Reindex the rows to match the specified order
                pivot_df = pivot_df.reindex(subjects_ordered, level=0)

                # Conditionally reorder columns if the variable is 'Race/Ethnicity'
                if variable == 'Race/Ethnicity' and jurisdiction == 'US':
                    pivot_df = pivot_df[race_order]
                    

                # Combine 'Subject' and 'Year' into a single column for the index
                pivot_df.index = pivot_df.index.map(lambda x: f'{x[0]} ({x[1]})')
                
                # Apply a formatting 
                styled_df = apply_custom_colormap(pivot_df)

                # Add title to the Cohen's d table
                styled_df = styled_df.set_caption(f"Cohen's d for {jurisdiction} - {variable}")

                # Display the styled dataframe for Cohen's d in Streamlit
                st.dataframe(styled_df)

    else:
        st.write("Please select at least one Variable and Jurisdiction.")
  
with col2:
    # Define the color coding legend using HTML and CSS
    legend_html = """
    <div style="display: flex; flex-direction: column; align-items: flex-start;">
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 20px; background-color: #CFE2F3; margin-right: 10px;"></div>
            <span>Negligible</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 20px; background-color: #D9EAD3; margin-right: 10px;"></div>
            <span>Small</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 20px; background-color: #ECEED0; margin-right: 10px;"></div>
            <span>Small-Moderate</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 20px; background-color: #FEF2CC; margin-right: 10px;"></div>
            <span>Moderate</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 20px; background-color: #F9DFCC; margin-right: 10px;"></div>
            <span>Moderate-Large</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 20px; background-color: #F4CCCC; margin-right: 10px;"></div>
            <span>Large</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 20px; background-color: #EFB9CC; margin-right: 10px;"></div>
            <span>Very Large</span>
        </div>
    </div>
    """

    # Display the legend in the right-hand column
    st.markdown("### Effect Size Interpretation")
    st.markdown(legend_html, unsafe_allow_html=True)
    
# Notes section
with st.expander("Notes"):
    st.markdown("""
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
    """)
    
    
    
        # Clean the DataFrame
    # Function to clean the DataFrame
    def clean_dataframe(df):
        # Remove columns where all values are 0.00
        df_cleaned = df.loc[:, (df != 0.00).any(axis=0)]
        return df_cleaned

    cleaned_df = clean_dataframe(pivot_df)