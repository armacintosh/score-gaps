import streamlit as st
import pandas as pd

# Set page layout to wide
st.set_page_config(layout="wide")

# Load your dataframe
merged_df = pd.read_csv('merged_data.csv')

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

# Filtering the dataframe based on user selection
if not selected_subjects:
    selected_subjects = merged_df['Subject'].unique()
    
filtered_df = merged_df[
    (merged_df['Variable'].isin(selected_variables)) & 
    (merged_df['Jurisdiction'].isin(selected_jurisdictions)) &
    (merged_df['Subject'].isin(selected_subjects))
]

# Convert year into category using .loc to avoid SettingWithCopyWarning
filtered_df.loc[:, 'Year'] = filtered_df['Year'].astype('category')

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

# Create tabs for each combination of selected variables and jurisdictions within an expander
with st.expander("Effect Size Summary"):
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

                # Resetting the index for a cleaner look (optional)
                pivot_df = pivot_df.reset_index()

                # Apply a color gradient and highlight NaN values for Cohen's d table
                styled_df = pivot_df.style.background_gradient(cmap=color_map, axis=None).format("{:.2f}", subset=pd.IndexSlice[:, pivot_df.select_dtypes(include='number').columns])

                # Add title to the Cohen's d table
                styled_df = styled_df.set_caption(f"Cohen's d for {jurisdiction} - {variable}")

                # Display the styled dataframe for Cohen's d in Streamlit
                st.dataframe(styled_df)
    else:
        st.write("Please select at least one Variable and Jurisdiction.")



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