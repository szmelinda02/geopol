import streamlit as st
from google_scraper import google_scraper
from file_processer import file_processer
from streamlit_app import visualize
import os


class SessionState:
    def __init__(self):
        if not os.path.exists("scraped_files"):
            self.analyzed_topics = []
            return
        self.analyzed_topics = [name for name in os.listdir("scraped_files") if os.path.isdir(os.path.join("scraped_files", name))]

def main():
    session_state = SessionState()
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Analyze new topic", "Select analyzed topic"])

    if page == "Analyze new topic":
        st.title("Analyze New Topic")
        topic_input = st.text_area('Enter the name of the topic')
        keyword_input = st.text_area('Enter a list of search keywords separated by commas: ')
        site_list = st.multiselect('Choose from this list of sites:',['euractiv.com', 'dw', 'euronews.com', 'france24.com', 'politico.com'])
        if st.button("Analyze"):
            if topic_input and site_list and keyword_input:
                keyword_list = [keyword.strip() for keyword in keyword_input.split(',') if keyword.strip()]
                file_name = google_scraper(topic_input, keyword_list, site_list)
                file_processer(file_name)

                session_state.analyzed_topics.append(file_name)

                # Display analysis result on a new page
                st.success("Analysis finished!")
                visualize(file_name)
            else:
                st.warning("Choose topics and sites!")
    elif page == "Select analyzed topic":
        st.title("Select Analyzed Topic")
        selected_topic = st.sidebar.selectbox("Select topic:", session_state.analyzed_topics)

        if selected_topic:
            visualization_type = st.sidebar.radio("Select Visualization Type", ["Frequency", "Top", "Graph", "Time Series", "Spider Chart", "Mentions"])
            visualize(selected_topic, visualization_type)

if __name__ == "__main__":
    main()