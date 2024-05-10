import matplotlib.pyplot as plt
import pandas as pd
import pickle
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from transformers import pipeline
from transformers import AutoTokenizer, BertForTokenClassification
#import spacy
from tqdm import tqdm
tqdm.pandas()
import syntok.segmenter as segmenter
import warnings
warnings.filterwarnings("ignore")
from collections import Counter
from itertools import combinations, product
from itertools import combinations
from fuzzywuzzy import fuzz
import unidecode
import newspaper
from newspaper import Article
from newspaper import Source
import pandas as pd
import re
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import networkx as nx
import glob
from PIL import Image


def transform_sentiment_score(score, sentiment):
    if sentiment == 'neutral':
        score = 0
    elif sentiment == 'negative':
        score = -score
    return score

def transform_sentiment_df(df):
    
    df['persons_ner'] = df.entities.apply(lambda entity_list: [x[0] for x in entity_list if x[1] == 'PERSON' ])
    person_cnt = [x for x in Counter([item for sublist in list(df['persons_ner']) for item in sublist]).most_common() if x[1] > 50]

    #df['persons_ner'] = df.persons_ner.apply(lambda x: [unidecode(element) for element in x])
    persons = list(set([item.lower() for sublist in list(df['persons_ner']) for item in sublist if item in set([x[0] for x in person_cnt])]))

    duplications = []
    for name_tuple in tqdm(set(combinations(persons, 2))):
        #if len(name_tuple[0]) < 3 or len(name_tuple[1]) < 3:
        #    continue
        similarity = fuzz.token_set_ratio(name_tuple[0], name_tuple[1])
        if similarity == 100:
            if name_tuple[0] == name_tuple[1]:
                continue
            duplications.append(sorted(name_tuple, key = len))

    duplication_dict = {x[0] : [] for x in duplications }
    for name in duplication_dict.keys():
        duplication_dict[name] = [x[1] for x in duplications if x[0] == name]

    normalization_dict = {}

    for key, value in duplication_dict.items():
        if len(value) == 1:
            normalization_dict[key] = value[0]
        elif len(value) > 1:
            reference_value = sorted(value, key = len, reverse = True)[0]

            #for new_key in sorted(value, key = len)[1:]:
            #    flattened_dict.update({new_key : reference_value})
            normalization_dict[key] = reference_value


    df['persons_ner_normalized'] = df.persons_ner.progress_apply(lambda entity_list: [normalization_dict.get(entity.lower(), entity.lower()) for entity in entity_list])
    df['persons_ner_normalized'] = df['persons_ner_normalized'].apply(lambda x: [re.sub(r"[^a-zA-Z\s]", "", str(item).replace("'s", "").replace("//n", "").strip()).title() for item in x])
    df['persons_ner_normalized_unique'] = df['persons_ner_normalized'].apply(lambda x: set(x))
    
    return df 

def sentiment_plot(df,df_parag, col, title):
    TOP_N = 10
    persons_sentiment_scores = {}

    plt.figure(figsize=(12,8))


    for person in [x[0] for x in Counter([item for sublist in list(df[col]) for item in sublist]).most_common()][0:TOP_N]:
        persons_sentiment_scores.update({person : np.mean([float(x) for x in list(df_parag[df_parag[col].apply(lambda x: person in x)]['polarity_score'])])})

    print(persons_sentiment_scores)
    keys = list(persons_sentiment_scores.keys())
    # get values in the same order as keys, and parse percentage values
    vals = list(persons_sentiment_scores.values())

    sent_by_pers = pd.DataFrame({'name': keys, 'avg_sent': vals}).sort_values(by=['avg_sent'], ascending=False)

    #sent_by_pers = sent_by_pers[sent_by_pers["name"] != "Baltic Sea"].reset_index(drop=True)

    base_color = 'darkgreen'
    palette = sns.light_palette(base_color, n_colors=TOP_N, reverse=True)

    plot = sns.barplot(
        x=sent_by_pers['avg_sent'], 
        y=sent_by_pers['name'],
        palette=palette
        )

    plot.set_xticklabels(plot.get_xticklabels(), rotation=0)
    #plot.invert_xaxis()

    for container in plot.containers:
        plot.bar_label(container, size=10, fmt='%.2f')

    plot.set_title(title)
    plot.set(xlabel='Average sentiment score', ylabel='Top events')

    plt.tight_layout()

    # Show the plot
    plt.show()
    
    
def sentiment_plot(df_parag, col, title):
    TOP_N = 10
    persons_sentiment_scores = {}

    plt.figure(figsize=(12,8))


    for person in [x[0] for x in Counter([item for sublist in list(df_parag[col]) for item in sublist]).most_common()][0:TOP_N]:
        persons_sentiment_scores.update({person : np.nanmean([float(x) for x in list(df_parag[df_parag[col].apply(lambda x: person in x)]['polarity_score']) ])})

    print(persons_sentiment_scores)
    keys = list(persons_sentiment_scores.keys())
    # get values in the same order as keys, and parse percentage values
    vals = list(persons_sentiment_scores.values())

    sent_by_pers = pd.DataFrame({'name': keys, 'avg_sent': vals}).sort_values(by=['avg_sent'], ascending=False)

    #sent_by_pers = sent_by_pers[sent_by_pers["name"] != "Baltic Sea"].reset_index(drop=True)

    base_color = 'darkgreen'
    palette = sns.light_palette(base_color, n_colors=TOP_N, reverse=True)

    plot = sns.barplot(
        x=sent_by_pers['avg_sent'], 
        y=sent_by_pers['name'],
        palette=palette
        )

    plot.set_xticklabels(plot.get_xticklabels(), rotation=0)
    #plot.invert_xaxis()

    for container in plot.containers:
        plot.bar_label(container, size=10, fmt='%.2f')

    plot.set_title(title)
    plot.set(xlabel='Average sentiment score', ylabel='Top events')

    plt.tight_layout()

    # Show the plot
    plt.show()

