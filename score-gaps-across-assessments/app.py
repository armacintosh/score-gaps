import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode, JsCode
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

# Creating tabs in the main column
tab1, tab2 = st.tabs(['Pivot Table', 'Summary Table'])

with tab1:
    
    # Create a two-column layout within the Effect Size section
    table_col, legend_col = st.columns([5, 1])  # 3:1 ratio    
    
    with table_col:                
        # Create the table
        # Create GridOptions
        gb = GridOptionsBuilder.from_dataframe(pivot_df)
        gb.configure_pagination(paginationAutoPageSize=True) # Add pagination
        gb.configure_side_bar()  # Add a sidebar
        gb.configure_default_column(editable=True, groupable=True)

        # Apply the custom cell color function to all columns except 'Index'
        for col in pivot_df.columns:
            if col != 'Index':
                gb.configure_column(col, cellStyle=js_code)
    
        gridOptions = gb.build()

        # Display the DataFrame using AgGrid
        AgGrid(
            pivot_df,
            gridOptions=gridOptions,
            enable_enterprise_modules=True, 
            allow_unsafe_jscode=True, 
            theme='light',
            height=450,
        )            
        
    with legend_col:
        # Display the styled header for the Effect Size Table
        st.markdown("**Effect Size Interpretation**")
        st.markdown(legend_html, unsafe_allow_html=True)

    
with tab2:
    # Create GridOptions for the summary_df
    summary_df = summary_df.round(2)
    gb2 = GridOptionsBuilder.from_dataframe(summary_df)
    gb2.configure_side_bar()  # Optional: Add a sidebar for grid options
    gb2.configure_default_column(editable=False, groupable=False, autoWidth=True)  # Enable autoWidth for all columns

    gridOptions2 = gb2.build()
    
    AgGrid(
        summary_df, 
        gridOptions=gridOptions2,
        enable_enterprise_modules=True, 
        allow_unsafe_jscode=True, 
        theme='light',
        height=450,
    )
        
# Notes section
with st.expander("**Notes**", expanded=False):
    st.markdown(Notes_html)