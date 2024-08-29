import streamlit as st
import pandas as pd
import requests
from io import StringIO
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# Set page layout to wide
# Apply custom CSS for consistent font
st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    /* Apply font family to the whole app */
    * {
        font-family: 'Helvetica', sans-serif;  /* Change 'Arial' to your preferred font */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Add custom CSS to style the right-hand sidebar
st.markdown("""
    <style>
    /* Main content on the left */
    .main-content {
        width: 75%;
        float: left;
    }

    /* Sidebar on the right */
    .sidebar-content {
        width: 23%;
        float: right;
        background-color: #b3b8c7;
        padding: 1rem;
        border-radius: 10px;
    }

    /* Clear floats */
    .clearfix::after {
        content: "";
        clear: both;
        display: table;
    }
    </style>
    """, unsafe_allow_html=True)

# Example content to see the font change
st.title("Streamlit App with Consistent Font")


# Create a two-column layout
st.markdown('<div class="clearfix">', unsafe_allow_html=True)
main_col, sidebar_col = st.columns([3, 1])

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
st.sidebar.header("Choose Groupings and Subjects")

# Convert year into category using .loc to avoid SettingWithCopyWarning
merged_df.loc[:, 'Year'] = merged_df['Year'].astype('Int64')

# Create the index
merged_df['Index'] = merged_df['Subject'] + ' - ' + merged_df['Jurisdiction'] + ' - ' + merged_df['Year'].astype(str)

all_variables = merged_df['Variable'].unique()
selected_variables = st.sidebar.multiselect("Select Variable", all_variables, default= "Race/Ethnicity")
all_subjects = merged_df['Index'].unique()
selected_subjects = st.sidebar.multiselect("Select Subjects", all_subjects, default="SAT - Total - US - 2023")

# Define colors for cells based on custom logic
def color_scale(value):
    abs_value = abs(value)
    if abs_value <= 0.2:
        return '#FFF2CD'
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

# Filtering the dataframe based on user selection
if not selected_subjects:
    selected_subjects = merged_df['Subject'].unique()
    
filtered_df = merged_df[
    (merged_df['Variable'].isin(selected_variables)) & 
    (merged_df['Index'].isin(selected_subjects))
]

# Create the table with the desired columns
summary_df = filtered_df[['Variable','Subject', 'Jurisdiction', 'Year', 'Grouping', 'Mean', 'SD', 'N', "Cohen's d"]]


# Sort the dataframe to merge 'Selected Variable' across rows
summary_df = summary_df.sort_values(by=['Variable', 
                                        'Jurisdiction', 
                                        'Year', 
                                        'Grouping'])

with main_col:
    # Create combinations of selected variables and jurisdictions
    with st.expander("**Effect Size Summary**", expanded=True):

    # Create a two-column layout
        col1, col2 = st.columns([3, 1])  # Adjust the width ratio as needed
        
    with col1:                
        df = filtered_df.copy()   
        
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

        # make numeric cols 
        numeric_cols = pivot_df.select_dtypes(include=['number']).columns

    # Round numeric columns to 2 decimals for display
        pivot_df[numeric_cols] = pivot_df[numeric_cols].round(2)
        
        # Apply the color scale to only numeric columns
        cell_colors = [['white'] * len(pivot_df)] + [[color_scale(round(value,2)) for value in pivot_df[col]] for col in numeric_cols]

        # Format numeric columns to show two decimal places, even for whole numbers
        pivot_df[numeric_cols] = pivot_df[numeric_cols].map(lambda x: f'{x:.2f}')
            
        # Create the Plotly table
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=pivot_df.columns.tolist(),
                fill_color='white',
                align='left',
                font=dict(family="Helvetica", size=14, color="black")
            ),
            cells=dict(
                values=[pivot_df[col].tolist() for col in pivot_df.columns],
                fill_color=cell_colors,
                align='left',
                font=dict(family="Helvetica", size=12, color="black"),
            )
        )])
        

        # Display the figure in Streamlit
        st.plotly_chart(fig)


    # Create the legend for the color coding
    with col2:
        # Define the color coding legend using HTML and CSS
        legend_html = """
        <div style="display: flex; flex-direction: column; align-items: flex-start;">
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="width: 20px; height: 20px; background-color: #FFF2CD; margin-right: 10px;"></div>
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

        # Display the legend in the right-hand column
        st.markdown("**Effect Size Interpretation**")
        st.markdown(legend_html, unsafe_allow_html=True)    
    
    # Display the summary dataframe in Streamlit
    # Display the styled header for the Summary Table
    with st.expander("**Full Data Table**", expanded=False):
        st.dataframe(summary_df)
    

with sidebar_col:     
    # Notes section
    with st.expander("**Notes**", expanded=True):
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