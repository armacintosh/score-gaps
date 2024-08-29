import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from utils_app import *

# Set page layout to wide
st.set_page_config(layout="wide")

## Set fonr to Helvetica
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

# Example content to see the font change
st.title("Score Gaps Across Assessments")

# Create a two-column layout
st.markdown('<div class="clearfix">', unsafe_allow_html=True)
main_col, sidebar_col = st.columns([3, 1])
      
# Load your dataframe
merged_df = load_original_data()

# Sidebar for user input
st.sidebar.header("Choose Groupings and Subjects")

# Convert year into category using .loc to avoid SettingWithCopyWarning
merged_df.loc[:, 'Year'] = merged_df['Year'].astype('Int64')

# Create the index
merged_df['Index'] = merged_df['Subject'] + ' - ' + merged_df['Jurisdiction'] + ' - ' + merged_df['Year'].astype(str)

# Set default values for the multiselects
all_variables = merged_df['Variable'].unique()
selected_variables = st.sidebar.multiselect("Select Variable", all_variables, default= var_defaults)
all_subjects = merged_df['Index'].unique()
selected_subjects = st.sidebar.multiselect("Select Subjects", all_subjects, default= sub_defaults)

# Filtering the dataframe based on user selection
filtered_df = merged_df[
    (merged_df['Variable'].isin(selected_variables)) & 
    (merged_df['Index'].isin(selected_subjects))
]

# create full data table for reference
summary_df = create_full_table(filtered_df)

# create, clean, pivot df for effect size table
pivot_df, cell_colors = pivot_clean_df(filtered_df, effect_size_color_scale)

with main_col:
    # Creating tabs in the main column
    tab1, tab2 = st.tabs(['Pivot Table', 'Summary Table'])
    
    with tab1:
        
        # Create a two-column layout within the Effect Size section
        table_col, legend_col = st.columns([3, 1])  # 3:1 ratio    
        
        with table_col:                
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

        with legend_col:
            # Display the styled header for the Effect Size Table
            st.markdown("**Effect Size Interpretation**")
            st.markdown(legend_html, unsafe_allow_html=True)

        
    with tab2:
        st.dataframe(summary_df)
      

with sidebar_col:     
    # Notes section
    with st.expander("**Notes**", expanded=True):
        st.markdown(Notes_html)