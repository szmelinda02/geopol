import os
import pickle
import pandas as pd
from tqdm import tqdm
tqdm.pandas()
from itertools import combinations
from collections import Counter
from fuzzywuzzy import fuzz
from utils.get_dates import *
from utils.nlp_utils import NLPClass

def create_df_from_urls(urls):
    df = pd.DataFrame(columns=['search_terms', 'url'])
    for key, values in urls.items():
        for value in values:
            row = [key, value]
            df.loc[len(df)] = row
    df = df.head(30)
    return df

def extract_article_info(df, nlp_class):
    df['article_infos'] = df.url.progress_apply(lambda x: nlp_class.get_article_infos(x))
    df['text'] = df.article_infos.progress_apply(lambda x: x.text if x is not None else None)
    df['publish_date'] = df.article_infos.progress_apply(lambda x: x.publish_date if x is not None else None)
    del df['article_infos']
    df['split_text'] = df['text'].progress_apply(lambda x: nlp_class.split_text(x))
    return df

def process_df_for_entities_and_sentiment(df, nlp_class):
    df_paragraph = df.explode('split_text').reset_index(drop=True)
    df_paragraph.drop('text', inplace=True, axis=1)
    df_paragraph = df_paragraph.head(700)
    df_paragraph['entities'] = df_paragraph.split_text.progress_apply(lambda x: nlp_class.return_ner_labels(x[0:10000]))
    df_paragraph['sentiment'] = df_paragraph['split_text'].progress_apply(lambda x: nlp_class.sentiment_scorer(x))
    df_paragraph['keyword'] = df_paragraph.search_terms.apply(lambda x: x[0])
    unique_search_terms = df_paragraph.search_terms.apply(lambda x: x[0]).unique()
    df_paragraph['site'] = df_paragraph.search_terms.apply(lambda x: x[1])
    columns_order = ['keyword', 'site', 'url', 'publish_date', 'sentiment', 'split_text', 'entities']
    df_paragraph = df_paragraph[columns_order]
    return df_paragraph

def handle_missing_dates(df, df_paragraph):
    missing_urls_df = df_paragraph[df_paragraph.publish_date.isnull()]
    not_missing = df_paragraph[df_paragraph.publish_date.isnull() == False]
    not_missing['publish_date'] = not_missing.publish_date.apply(lambda x: x.date())
    missing_urls_dates_dict = {}
    for url in tqdm(missing_urls_df['url'].unique()):
        date = get_date_for_url(url)
        missing_urls_dates_dict.update({url: date})
    missing_urls_df['publish_date'] = missing_urls_df.url.apply(lambda x: missing_urls_dates_dict[x])
    df = pd.concat([not_missing, missing_urls_df])
    df['publish_date'] = df.publish_date.apply(lambda x: x.date() if type(x) == datetime else x)
    df['publish_date'] = df.publish_date.apply(lambda x: None if x == '' else x)
    df['persons_ner'] = df.entities.apply(lambda entity_list: [x[0] for x in entity_list if x[1] == 'PERSON' ])
    df['gpe_ner'] = df.entities.apply(lambda entity_list: [x[0] for x in entity_list if x[1] == 'GPE' ])
    return df

def identify_duplicate_named_entities(df):
    LIMIT = 0
    person_cnt = [x for x in Counter([item for sublist in list(df['persons_ner']) for item in sublist]).most_common() if x[1] > LIMIT]
    persons = list(set([item.lower() for sublist in list(df['persons_ner']) for item in sublist if item in set([x[0] for x in person_cnt])]))

    duplications = []
    for name_tuple in tqdm(set(combinations(persons, 2))):
        similarity = fuzz.token_set_ratio(name_tuple[0], name_tuple[1])
        if similarity == 100:
            if name_tuple[0] == name_tuple[1]:
                continue
            duplications.append(sorted(name_tuple, key=len))

    return duplications

def normalize_duplicate_named_entities(duplications):
    duplication_dict = {x[0]: [] for x in duplications}
    for name in duplication_dict.keys():
        duplication_dict[name] = [x[1] for x in duplications if x[0] == name]

    normalization_dict = {}
    for key, value in duplication_dict.items():
        if len(value) == 1:
            normalization_dict[key] = value[0]
        elif len(value) > 1:
            reference_value = sorted(value, key=len, reverse=True)[0]
            normalization_dict[key] = reference_value
    return normalization_dict

def apply_normalization(df, normalization_dict):
    df['persons_ner_normalized'] = df.persons_ner.progress_apply(lambda entity_list: [normalization_dict.get(entity.lower(), entity.lower()) for entity in entity_list])
    df['persons_ner_normalized'] = df['persons_ner_normalized'].apply(lambda x: [re.sub(r"[^a-zA-Z\s]", "", str(item).replace("'s", "").replace("//n", "").strip()).title() for item in x])
    df['persons_ner_normalized_unique'] = df['persons_ner_normalized'].apply(lambda x: set(x))
    df['org_ner'] = df.entities.apply(lambda entity_list: [x[0] for x in entity_list if x[1] == 'ORG'])
    df['org_ner_unique'] = df['org_ner'].apply(lambda x: set(x))
    return df


def named_entity_normalization(df):
    duplications = identify_duplicate_named_entities(df)
    normalization_dict = normalize_duplicate_named_entities(duplications)
    df = apply_normalization(df, normalization_dict)
    return df

def process_org_ner_unique(df):
    orgs_to_exclude = ['euractiv', 'politico', 'dw', 'euronews', 'france24', 'getty images', 'reuters']
    replace_dict = {'Commission': 'European Commission', 'Parliament': 'European Parliament', 'Council': 'European Council', 'EU': "EuropeUnion"}
    df['org_ner_unique'] = df.org_ner_unique.apply(lambda entity_list: set(entity.replace('the', '').strip() for entity in entity_list if entity.lower() not in orgs_to_exclude))
    df['org_ner_unique'] = df.org_ner_unique.apply(lambda entity_list: set(replace_dict.get(entity, entity) for entity in entity_list))
    df['polarity_score'] = df.apply(lambda row: 0 if row['sentiment'][0]['label'] == 'neutral' else -row['sentiment'][0]['score'] if row['sentiment'][0]['label'] == 'negative' else row['sentiment'][0]['score'], axis=1)
    return df

def file_processer(file_name):
    nlp_class = NLPClass()
    path = os.path.join("scraped_files", file_name, "raw")
    updated_path = path.replace("raw", "processed")
    os.makedirs(updated_path, exist_ok=True)
    with open(f'{path}/article_urls.pkl', 'rb') as f:
        urls = pickle.load(f)
    df = create_df_from_urls(urls)
    df = extract_article_info(df, nlp_class)
    df_paragraph = process_df_for_entities_and_sentiment(df, nlp_class)
    df = handle_missing_dates(df, df_paragraph)
    df = named_entity_normalization(df)
    df = process_org_ner_unique(df)
    with open(f'{updated_path}/preprocessed_output.pkl', 'wb') as fp:
        pickle.dump(df, fp)

