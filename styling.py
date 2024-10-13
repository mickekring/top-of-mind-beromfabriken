
import streamlit as st
import config as c

def page_configuration():
    
    # Page configuration
    st.set_page_config(
        page_title = c.app_name,
        layout = "wide",
        page_icon = ":material/thumb_up:",
        initial_sidebar_state = "collapsed"
        )
    

def page_styling():

    # CSS styling
    st.markdown("""
    <style>
                
    h1 {
        padding: 0rem 0px 1rem;
    }
    
    h2 {
        padding: 0rem 0px 1rem;
    }
        
    .st-emotion {
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: rgb(255 255 255);
    }

    [data-testid="block-container"] {
        padding-left: 3rem;
        padding-right: 3rem;
        padding-top: 0rem;
        padding-bottom: 0rem;
        margin-bottom: -7rem;
    }
                
    .block-container {
        padding-top: 3rem;
        padding-bottom: 2rem;
    }

    </style>
    """, unsafe_allow_html=True)