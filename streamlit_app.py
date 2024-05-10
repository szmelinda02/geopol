import copy
import streamlit as st
import pandas as pd
import pickle
import plotly.express as px
import os
from utils.utils import *
import streamlit.components.v1 as components
from pyvis import network as net
import datetime
import utils.parties_utils as pu
import json

def visualize_frequency(df):
    st.header("Frequency barplot")
    col_dic = {"Keywords": 'keyword', "Websites": 'site'}
    col = st.selectbox("I'd like to see the frequency of:", list(col_dic.keys()))
    value_counts = df[col_dic[col]].value_counts()
    data_df = pd.DataFrame({'Value': value_counts.index, 'Frequency': value_counts.values})
    fig = px.bar(data_df, x='Value', y='Frequency', title=f"{col} frequency", color='Value')
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

def visualize_top(path):
    # file_path = os.path.join(path, 'top_chart.csv')
    # with open(file_path, 'rb') as f:
    #         df = pickle.load(f)
    with open(f'{path}/preprocessed_output.pkl', 'rb') as f:
        df = pickle.load(f)
    st.header("Barplot of most common things with sentiments")
    col_dic = {"People": 'persons_ner_normalized_unique',
               "Organizations": 'org_ner_unique',
               "Geopolitical entities": 'gpe_ner'}
    col = st.selectbox("Top what?", list(col_dic.keys()))
    num = st.slider('How much?', 0, 50)
    kw = st.multiselect("Select keywords", df['keyword'].unique())

    if col and num and kw:
        filtered_rows = [(obj, polarity) for obj, polarity, keyword in
                        zip(df[col_dic[col]], df['polarity_score'], df['keyword']) if obj and keyword in kw]
        object_polarity_counts = {}

        # Accumulate polarity scores and counts for each object
        for obj, polarity in filtered_rows:
            obj_str = obj.pop()  # Extracting string from set
            if obj_str in object_polarity_counts:
                object_polarity_counts[obj_str]['polarity_sum'] += polarity
                object_polarity_counts[obj_str]['count'] += 1
            else:
                object_polarity_counts[obj_str] = {'polarity_sum': polarity, 'count': 1}

        # Calculate the mean polarity score for each object
        objects = []
        mean_polarities = []
        counts = []
        for obj_str, data in object_polarity_counts.items():
            mean_polarity = data['polarity_sum'] / data['count']
            objects.append(obj_str)
            mean_polarities.append(mean_polarity)
            counts.append(data['count'])

        # Combine objects, mean polarities, and counts into a DataFrame
        df_most_common = pd.DataFrame({'obj': objects, 'polarity_score': mean_polarities, 'count': counts})
        df_most_common = df_most_common.sort_values(by='count', ascending=True).tail(num)
        colorscale = [[0, 'red'], [0.5, 'white'], [1, 'green']]

        fig = px.bar(df_most_common, x='count', y="obj", orientation='h', title=f"Top {num} {col} with sentiments",
                    hover_data=['obj', 'count', 'polarity_score'], color='polarity_score', height=400,
                    color_continuous_scale=colorscale, range_color=[-1, 1])

        fig.update_layout(coloraxis_colorbar=dict(
            title="Polarity Score",
            tickvals=[-1, 0, 1],
            ticktext=["-1 (Negative)", "0 (Neutral)", "1 (Positive)"]
        ))

        st.plotly_chart(fig, use_container_width=True)

def graph(df, path):
    def load_occurrences(file_path):
        with open(file_path, 'r') as file:
            occurrences = json.load(file)
        return occurrences
    st.header("Relationship graph")
    col_dic = {"People": 'occurences_persons',
               "Organizations": 'occurences_org',
               "Geopolitical entities": 'occurences_gpe'}
    col = st.selectbox("See the connections of people with ", list(col_dic.keys()))
    #try:
    file_path = os.path.join(path, col_dic[col])
    occurrences = load_occurrences(file_path)
    if (col == "People"):
        filename = create_graph2(occurrences)
    else:
        persons = set([item for sublist in df['persons_ner_normalized_unique'] for item in sublist])
        filename = create_graph_w_mixed_entity2(occurrences, persons)

    HtmlFile = open(filename, 'r', encoding='utf-8')
    # Load HTML into HTML component for display on Streamlit
    components.html(HtmlFile.read(), height=800, width=800)
    # except:
    #     st.error('Not enough data')

def time_series(df):
    #df = df.dropna(subset=['publish_date'])
    st.header("Time series")
    kw1 = st.multiselect("Select keywords for time series", df['keyword'].unique())
    #df['Month_Level'] = df['publish_date'].apply(lambda x: x.replace(day=1))
    #df['Month_Level'] = df.Month_Level.apply(lambda x: str(x))
    filtered_df = df[df['keyword'].isin(kw1)]
    event_count = filtered_df['Month_Level'].value_counts().sort_index()
    event_count = event_count.reset_index()
    event_count.columns = ['Month', 'Frequency']
    fig = px.line(event_count, x='Month', y="Frequency", title=f"Timeline of articles")
    st.plotly_chart(fig, use_container_width=True)

def spider_chart(path):
    st.header("Spiderchart")
    col = st.selectbox("Create spiderchart of :", ['parties', 'groups'])
    pu.create_spider_chart(col, path)

def visualize_mentions(path):
    st.header("Barplot of party/group")
    col = st.selectbox("Number of mentions of :", ['parties', 'groups'])
    fig = pu.create_parties_plot(col, path)
    st.plotly_chart(fig, use_container_width=True)

def visualize(topic, visualization_type):
    path = os.path.join("scraped_files", topic, "processed")
    with open(f'{path}/preprocessed_output.pkl', 'rb') as f:
        df = pickle.load(f)
    
    if visualization_type == "Frequency":
        visualize_frequency(df)
    elif visualization_type == "Top":
        visualize_top(path)
    elif visualization_type == "Graph":
        graph(df, path)
    elif visualization_type == "Time Series":
        time_series(df)
    elif visualization_type == "Spider Chart":
        #PG = pu.Party_and_Group(df)
        spider_chart(path)
    elif visualization_type == "Mentions":
        #PG = pu.Party_and_Group(df)
        visualize_mentions(path)