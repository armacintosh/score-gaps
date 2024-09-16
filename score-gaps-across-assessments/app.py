import pandas as pd
import streamlit as st
from utils_app import *

# Set page layout to wide
st.set_page_config(layout="wide")


# Inject custom CSS for Montserrat font
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Montserrat', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# Example content to see the font change
st.title("Score Gaps Across Assessments")

# Create a two-column layout
st.markdown('<div class="clearfix">', unsafe_allow_html=True)

from utils_app import get_legend_html

# Initialize font size in session state if not already set
if "font_size" not in st.session_state:
    st.session_state.font_size = "16px"  # Default font size

# Function to update font size
def update_font_size(size):
    st.session_state.font_size = size

# Get the updated legend HTML with the selected font size
legend_html = get_legend_html(st.session_state.font_size)
      
# Load your dataframe
merged_df = load_original_data()

# Sidebar for user input
st.sidebar.header("Choose Groupings and Subjects")

# Convert year into category using .loc to avoid SettingWithCopyWarning
merged_df.loc[:, 'Year'] = merged_df['Year'].astype('Int64')

# Create the index
merged_df['Assessment'] = merged_df['Subject'] + ' - ' + merged_df['Jurisdiction'] + ' - ' + merged_df['Year'].astype(str)

# Set default values for the multiselects
all_variables = merged_df['Variable'].unique()
selected_variables = st.sidebar.multiselect("Select Variable", all_variables, default= var_defaults)
all_subjects = merged_df['Assessment'].unique()
selected_subjects = st.sidebar.multiselect("Select Subjects", all_subjects, default= sub_defaults)

# Initialize font size in session state if not already set
if "font_size" not in st.session_state:
    st.session_state.font_size = 16  # Default font size (in px)

# Create a slider in the right sidebar to adjust the font size
with st.sidebar:
    st.session_state.font_size = st.slider(
        "Adjust Legend Font Size", min_value=8, max_value=24, value=16, step=1
    )


# Filtering the dataframe based on user selection
filtered_df = merged_df[
    (merged_df['Variable'].isin(selected_variables)) & 
    (merged_df['Assessment'].isin(selected_subjects))
]


# create full data table for reference
summary_df = create_full_table(filtered_df)


# Expander with the explainer HTML
with st.expander("**Cohen's d Explainer**"):
    explainer_html = get_explainer_html()
    st.markdown(explainer_html, unsafe_allow_html=True)

# Get unique values of 'Variable'
unique_variables = filtered_df['Variable'].unique().tolist()

# Create tabs dynamically for each unique 'Variable'
tabs = st.tabs(unique_variables)

# Display content in each tab
for i, var in enumerate(unique_variables):
    
    # Filter the dataframe for the current 'Variable'
    v_df = filtered_df[filtered_df['Variable'] == var]

    with tabs[i]:
        # Creating tabs in the main column
        tab1, tab2 = st.tabs(['Effect sizes', 'Data'])

        with tab1:

            # Get the comparison group for the given variable
            comparison_group = comparison.get(var, 'Unknown')  # 'Unknown' is a fallback if the variable is not in the dictionary

            # write what the groupings are compared to
            st.write(f"The comparison group for {var} is '{comparison_group}'")
                        
            # create, clean, pivot df for effect size table
            pivot_df = var_clean_df(v_df)

            # Reorder columns if the variable is 'race/ethnicity'
            pivot_df = reorder_columns_by_variable(pivot_df, var, order_dict)

            # Apply the effect_size_color_scale to all columns except the first one
            styled_df = pivot_df.style.map(effect_size_color_scale, 
                                                subset=pd.IndexSlice[:, pivot_df.columns[1:]]) \
                            .format("{:.2f}", subset=pd.IndexSlice[:, pivot_df.select_dtypes(include=['float', 'int']).columns])
            

            # Display the styled dataframe with horizontal scrolling
            st.dataframe(styled_df, 
                        use_container_width=True,
                        hide_index=True
                        )
            
                
            with st.expander("**Effect Size Interpretation**", expanded=True):

                # Get the updated legend HTML with the selected font size
                legend_html = get_legend_html(f"{st.session_state.font_size}px")

                # Display the legend``
                st.markdown(legend_html, unsafe_allow_html=True)
           
        with tab2:
            summary_df = create_full_table(v_df)
            
            st.dataframe(summary_df.style.format(format_dict),
                         use_container_width=True,
                        hide_index=True
                        )
            
# Notes section
with st.expander("**Assessment Information & Sources**", expanded=False):
    st.markdown(Notes_html)
    
