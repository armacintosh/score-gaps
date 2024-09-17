import pandas as pd
import streamlit as st
from utils_app import *

# Set page layout to wide
st.set_page_config(layout="wide")

# Example content to see the font change
st.title("Score Gaps Across Assessments")

# Initialize font size in session state if not already set
if "font_size" not in st.session_state:
    st.session_state.font_size = "16px"  # Default font size

# Get the updated legend HTML with the selected font size
legend_html = get_legend_html(st.session_state.font_size)
      
# Load your dataframe
df = load_original_data()

# Sidebar for user input
st.sidebar.header("Choose Assessments")


####
# Create the dictionary for assessment groups
assessment_dict = {}
for assessment in df['Assessment'].unique():
    key = assessment.split(' ')[0]  # Extract the first part of the string
    if key not in assessment_dict:
        assessment_dict[key] = []
    assessment_dict[key].append(assessment)
    
# reorder the dictionary according to: assessment_group_order
assessment_dict = reorder_assessment_dict(assessment_dict, assessment_group_order)


# Display the resulting dictionary for assessment groups
assessments_available = list(assessment_dict.keys())

# Get all assessments
assessments_all = df['Assessment'].unique()

# Check if session state for selected assessments exists, if not set it to all assessments
if 'selected_assessments' not in st.session_state:
    st.session_state.selected_assessments = []

# Initialize session state for specific assessments to 'assessments_available'
if 'selected_all_assessments' not in st.session_state:
    st.session_state.selected_all_assessments = assessments_default

# Add a reset button to the sidebar for assessment groups
if st.sidebar.button("All Assessment Groups"):
    st.session_state.selected_assessments = assessments_available
    
# Add a button to reset specific assessments to the default list from `utils_app.py`
if st.sidebar.button("Default Assessments"):
    # Reset specific assessments to the default from utils_app.py
    valid_default_assessments = [a for a in assessments_default if a in assessments_all]
    st.session_state.selected_assessments = []
    st.session_state.selected_all_assessments = valid_default_assessments
    

# Sidebar multiselect widget for assessment groups
selected_assessments = st.sidebar.multiselect(
    "Select Assessment Groups", 
    assessments_available, 
    default=st.session_state.selected_assessments
)
    
# Sidebar multiselect widget for specific assessments, initialized to 'assessments_available'
selected_all_assessments = st.sidebar.multiselect(
    "Select Specific Assessments", 
    assessments_all, 
    default=st.session_state.selected_all_assessments
)

# Update session state with the current selections from both multiselects
st.session_state.selected_assessments = selected_assessments
st.session_state.selected_all_assessments = selected_all_assessments

# Filter DataFrame based on selected assessment groups and specific assessments
df_filtered_by_assessment = df[
    df['Assessment'].str.startswith(tuple(selected_assessments)) | 
    df['Assessment'].isin(selected_all_assessments)
]


####
# Initialize font size in session state if not already set
if "font_size" not in st.session_state:
    st.session_state.font_size = 16  # Default font size (in px)

# Create a slider in the right sidebar to adjust the font size
with st.sidebar:
    st.session_state.font_size = st.slider(
        "Adjust Legend Font Size", min_value=8, max_value=24, value=16, step=1
    )
    
####
# Initialize session state to track the active tab
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = list(tabs_dicts.keys())[0]  # Set default to the first tab


# Create the tabs
tab_selection = st.tabs(list(tabs_dicts.keys()))

# Detect the selected tab and put up the data
for i, tab_name in enumerate(tabs_dicts.keys()):
    with tab_selection[i]:
        if st.session_state.active_tab != tab_name:
            st.session_state.active_tab = tab_name
        
        # Update the multiselect based on the active tab
        if len(tabs_dicts[st.session_state.active_tab]) > 1:
            
            with st.expander (f"Select Variables for {st.session_state.active_tab}"):
                available_variables = tabs_dicts[st.session_state.active_tab]
                selected_vars = st.multiselect("", available_variables, default=available_variables)
        else :
            selected_vars = tabs_dicts[st.session_state.active_tab]
        
        # Filter DataFrame based on the selected variables and selected assessments
        filtered_df = df_filtered_by_assessment[df_filtered_by_assessment['Variable'].isin(selected_vars)]
        
        # Creating tabs in the main column
        tab1, tab2 = st.tabs(['Effect sizes', 'Data'])

        with tab1:                     
            # Check if the filtered_df has any rows
            if filtered_df.empty:
                # Show an error message if there are no rows in the DataFrame
                st.error("No data to show. Please select an Assessment or Assessment Group.")
            else:
                # Create, clean, and pivot df for the effect size table
                df_dict = var_clean_df(filtered_df, assessment_dict, order_dict)

                # Iterate over each variable-specific DataFrame in the dictionary
                for variable, pivot_df in df_dict.items():
                    
                    # Apply the effect_size_color_scale to all columns except the first one
                    styled_df = pivot_df.style.map(effect_size_color_scale, 
                                                subset=pd.IndexSlice[:, pivot_df.columns[1:]]) \
                                            .format("{:.2f}", subset=pd.IndexSlice[:, pivot_df.select_dtypes(include=['float', 'int']).columns])

                    # Display the styled dataframe with horizontal scrolling
                    st.subheader(f"{variable}")
                    st.dataframe(styled_df, 
                                use_container_width=True,
                                hide_index=True)

                    # Create the footnote for this variable
                    ftnt = make_footnote(comparison, [variable])
                    
                    # Write the accumulated footnote text with custom styling
                    st.markdown(f"<div class='footnote-text'>{ftnt}</div>", unsafe_allow_html=True)
            
        with tab2:
            summary_df = create_full_table(filtered_df)
            
            st.dataframe(summary_df.style.format(format_dict),
                         use_container_width=True,
                        hide_index=True
                        )            
            
        with st.expander("**Effect Size Interpretation**", expanded=True):

            # Get the updated legend HTML with the selected font size
            legend_html = get_legend_html(f"{st.session_state.font_size}px")

            # Display the legend``
            st.markdown(legend_html, unsafe_allow_html=True)



####
# Expander with the explainer HTML
with st.expander("**Cohen's d Explainer**"):
    explainer_html = get_explainer_html()
    st.markdown(explainer_html, unsafe_allow_html=True)

# Notes section
with st.expander("**Assessment Information & Sources**", expanded=False):
    st.markdown(Notes_html)
    
