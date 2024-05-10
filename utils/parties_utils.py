import random
import plotly.express as px
import pandas as pd
from tqdm import tqdm
import streamlit as st
import json
import os

class Party_and_Group:
    def __init__(self, df):
        self.groups_dict = {'ECR': ['European Conservatives and Reformists', 'ECR'],
                        'ID': ['Identity and Democracy', ' ID '], 
                        'EPP': ['European People Party', ' EPP', ' PPE'],
                        'PES': ['Party of European Socialists', ' PES', ' S&D'],
                        'ALDE': ['Renew Europe', 'Alliance of Liberals', ' Democrats for Europe', ' ALDE ', ' Renew'],
                        'The greens': ['Green Party', 'The greens'],
                        'The left': ['Party of the European Left', ' The Left', 'Leftist Block']}
        self.parties_list = [
            ["Fratelli D'Italia", 'Law and Justice', 'Vox'],
            ['Rassemblement National', 'Alternative für Deutschland', 'Lega'],
            ['Christlich-Demokratische Union', 'Partido Popular', 'Österreichische Volkspartei'],
            ['Sozialdemokratische Partei Deutschlands', 'Partido Socialista Obrero Español', 'Partidul Social Democrat'],
            ['Freie Demokratische Partei', 'Fianna Fáil', 'Eesti Reformierakond'],
            ['Bündnis 90', 'Green Party', 'Die Grünen', 'Die Grüne Alternative'],
            ['Syriza', 'Die Linke', 'Bloco de Esquerda']
        ]
        self.parties_dict = dict(zip(self.groups_dict.keys(), self.parties_list))
        self.parties_df = self.create_parties_df(df)
        self.only_parties_df = self.create_only_parties_df()
        self.only_groups_df = self.create_only_groups_df()

    def create_only_parties_df(self):
        filtered_df = self.parties_df[self.parties_df.parties.apply(lambda x: len(x) > 0)]
        parties_df2 = pd.DataFrame(columns=['polarity_score','sentiment', 'url', 'party'])
        for i in  tqdm(range(len(filtered_df))):
            for party in filtered_df.iloc[i]['parties']:
                altered_row = [filtered_df.iloc[i].polarity_score, filtered_df.iloc[i].sentiment, filtered_df.iloc[i].url, party]
                parties_df2.loc[len(parties_df2)] = altered_row
        return parties_df2
    
    def create_only_groups_df(self):
        filtered_df = self.parties_df[self.parties_df.parties.apply(lambda x: len(x) > 0)]
        parties_df2 = pd.DataFrame(columns=['polarity_score','sentiment', 'url', 'group'])
        for i in  tqdm(range(len(filtered_df))):
            for group in filtered_df.iloc[i]['groups']:
                altered_row = [filtered_df.iloc[i].polarity_score, filtered_df.iloc[i].sentiment, filtered_df.iloc[i].url, group]
                parties_df2.loc[len(parties_df2)] = altered_row
        return parties_df2

    def create_parties_df(self,df):
        columns_to_keep = ['sentiment', 'polarity_score', 'persons_ner_normalized_unique', 'url', 'split_text']
        parties_df = df[columns_to_keep]
        parties_df['split_text'] = parties_df.split_text.apply(lambda x: x.replace('AfD', 'Alternative für Deutschland') if x is not None else x)
        parties_df['split_text'] = parties_df.split_text.apply(lambda x: x.replace('PiS', 'Law and Justice') if x is not None else x)
        parties_df['groups'] = parties_df.split_text.progress_apply(lambda x: self.return_corresponding_groups(x))
        parties_df['parties'] = parties_df.split_text.progress_apply(lambda x: self.return_corresponding_parties(x))
        return parties_df


    def create_spider_chart(self, col):
        if col == 'parties':
            df = self.only_parties_df
            theta_column = "party"
        else:
            df = self.only_groups_df
            theta_column = "group"
        r_column = 'url_num'
        plot_df_positive = df[(df['sentiment'].apply(lambda x: x[0]['label']) == 'positive')].groupby(theta_column).agg({'url': set}).reset_index()
        plot_df_negative = df[(df['sentiment'].apply(lambda x: x[0]['label']) == 'negative')].groupby(theta_column).agg({'url': set}).reset_index()
        #plot_df_neutral = self.only_parties_df[(self.only_parties_df.sentiment[0]['label'] == 'neutral')].groupby('party').agg(set).reset_index()

        # Combine the positive and negative DataFrames
        combined_df = pd.concat([plot_df_positive, plot_df_negative]).reset_index(drop=True)

        # Create a new column to indicate sentiment type
        combined_df['sentiment'] = ['Positive'] * len(plot_df_positive) + ['Negative'] * len(plot_df_negative)
        combined_df['url_num'] = combined_df.url.apply(lambda x: len(x))
        # Plot the spider chart
        title = f'Number of  mentions in articles of the different <br>political {col}'
        combined_df.loc[len(combined_df.index)] = ['Lega', {}, "Positive", 2] 
        fig = px.line_polar(combined_df, r=r_column, theta=theta_column, color='sentiment',
                            line_close=True, title=title, color_discrete_map={'Positive': 'green', 'Negative': 'red'})

        fig.update_traces(fill='toself')
        try:
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        range=[min(combined_df[r_column]) - 1, max(combined_df[r_column]) + 1]
                    )
                )
            )
            fig.update_layout(
            legend=dict(
                x=0.9,  # Adjust the x-coordinate (0 to 1) to position the legend horizontally
                y=0.9,  # Adjust the y-coordinate (0 to 1) to position the legend vertically
                bgcolor='rgba(255, 255, 255, 0.7)',  # Set a background color for the legend
                bordercolor='gray',  # Set a border color for the legend
                borderwidth=1,  # Set the border width
            ))
            st.plotly_chart(fig)
        except:
            st.error("Not enough data to plot")
        
        
    def return_corresponding_groups(self, text):
        if text is None:
            return []
        
        founded_groups = []
        
        for group_name, group_synonyms in self.groups_dict.items():
            if any([group_synonym in text for group_synonym in group_synonyms]):
                founded_groups.append(group_name)
        if len(founded_groups) == 0:
            return []
        else:
            return founded_groups

    def return_corresponding_parties(self, text):        
        if text is None:
            return []
        
        founded_parties = []
        
        for parties_list in self.parties_dict.values():
            for party in parties_list:
                
                if party in text:
                    founded_parties.append(party)
        if len(founded_parties) == 0:
            return []
        else:
            return founded_parties
        
    def create_data_for_ts(df):
        df_grouped = df.groupby('publish_date').agg(set)[['url']].reset_index()
        df_grouped['url_num'] = df_grouped.url.apply(lambda x: len(x))
        df_grouped = df_grouped[df_grouped.publish_date.apply(lambda x: x > date(2023, 1, 1) and x < date(2024, 3, 1))]
        df_grouped['Month_Level'] = df_grouped['publish_date'].apply(lambda x: x.replace(day=1))
        df_grouped['Month_Level'] = df_grouped.Month_Level.apply(lambda x: str(x))
        df_grouped = df_grouped.groupby('Month_Level').sum()[['url_num']].reset_index()
        return dict(zip(df_grouped['Month_Level'], df_grouped['url_num']))


    def create_parties_plot(self, col):
        party_mention_dict = {}
        if col=='parties':
            for party in [item for sublist in self.parties_list for item in sublist]:
                url_num = self.parties_df[self.parties_df[col].apply(lambda x: party in x)]['url'].nunique()
                if url_num > 0:
                    party_mention_dict.update({party.strip() : url_num})
            df = pd.DataFrame({'Party name': list(party_mention_dict.keys()), 'Number of articles': list(party_mention_dict.values())})
            fig = px.bar(df, x='Party name', y='Number of articles', labels={'x':'Party name', 'y':'Number of articles'}, color='Party name')
        else:
            for group in self.groups_dict.keys():
                url_num = self.parties_df[self.parties_df[col].apply(lambda x: group in x)]['url'].nunique()
                if url_num > 0:
                    party_mention_dict.update({group.strip() : url_num})   
            df = pd.DataFrame({'Group name': list(party_mention_dict.keys()), 'Number of articles': list(party_mention_dict.values())})
            fig = px.bar(df, x='Group name', y='Number of articles', labels={'x':'Group name', 'y':'Number of articles'}, color='Group name')
        fig.update_layout(showlegend=False)
        return fig
    
def create_spider_chart(col, path):
        # Load preprocessed data from file
        if col == 'parties':
            file_path = os.path.join(path, 'spider_chart_data_parties.json')
            theta_column = "party"
        else:
            file_path = os.path.join(path, 'spider_chart_data_groups.json')
            theta_column = "group"
        with open(file_path, 'r') as file:
            combined_df = pd.read_json(file, orient='records')
        r_column = 'url_num'
        
        # Plot the spider chart
        title = f'Number of mentions in articles of the different <br>political {col}'
        fig = px.line_polar(combined_df, r=r_column, theta=theta_column, color='sentiment',
                            line_close=True, title=title, color_discrete_map={'Positive': 'green', 'Negative': 'red'})
        fig.update_traces(fill='toself')
        try:
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        range=[min(combined_df[r_column]) - 1, max(combined_df[r_column]) + 1]
                    )
                )
            )
            fig.update_layout(
                legend=dict(
                    x=0.9,
                    y=0.9,
                    bgcolor='rgba(255, 255, 255, 0.7)',
                    bordercolor='gray',
                    borderwidth=1,
                )
            )
            st.plotly_chart(fig)
        except:
            st.error("Not enough data to plot")

def create_parties_plot(col, path):
    if col == 'parties':
        file_path = os.path.join(path, 'parties_plot_data_parties.json')
        with open(file_path, 'r') as file:
            party_mention_dict = json.load(file)
        df = pd.DataFrame({'Party name': list(party_mention_dict.keys()), 'Number of articles': list(party_mention_dict.values())})
        fig = px.bar(df, x='Party name', y='Number of articles', labels={'x':'Party name', 'y':'Number of articles'}, color='Party name')
    else:
        file_path = os.path.join(path, 'parties_plot_data_groups.json')
        with open(file_path, 'r') as file:
            party_mention_dict = json.load(file)
        df = pd.DataFrame({'Group name': list(party_mention_dict.keys()), 'Number of articles': list(party_mention_dict.values())})
        fig = px.bar(df, x='Group name', y='Number of articles', labels={'x':'Group name', 'y':'Number of articles'}, color='Group name')
    fig.update_layout(showlegend=False)
    return fig