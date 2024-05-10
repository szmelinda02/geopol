import pickle
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
tqdm.pandas()
import warnings
warnings.filterwarnings("ignore")
from collections import Counter
from itertools import combinations, product
from itertools import combinations
from fuzzywuzzy import fuzz
#import unidecode
import newspaper
from newspaper import Article
from newspaper import Source
import pandas as pd
import re
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import networkx as nx
from pyvis.network import Network



def count_plot(person_cnt,plot_ax, title, y_label , filename, save=True):

    person_cnt = pd.DataFrame(person_cnt)
    person_cnt.columns = ['name', 'count']

    #person_cnt = person_cnt[person_cnt["name"] != "Baltic Sea"].reset_index(drop=True)

    plot = sns.barplot(
        ax=plot_ax,
        x=person_cnt['count'], 
        y=person_cnt['name'],
        color='royalblue'
        )

    for i in plot.containers:
        plot.bar_label(i,)

    plot.set_title(title)
    plot.set(xlabel='Count', ylabel=y_label)

    plot.set_xticklabels(plot.get_xticklabels(), rotation=0)
    if save:
        
        plt.savefig(filename, bbox_inches = 'tight')


def get_occurrences(list_1, list_2, size=20):
    occurrences = defaultdict(int)
    for person_list, org_list in zip(list_1, list_2):
        pairs = product(set(person_list), set(org_list))   

        for pair in pairs:
            if len(pair[0]) < len(pair[1]) or pair[0] == pair[1]:
                continue

            occurrences[pair] += 1

    occurrences = sorted(occurrences.items(), key=lambda x: x[1], reverse=True)[0:size]

    return occurrences

def create_graph(occurrences, title, filename="", save=True):
    graph = nx.Graph()

    for (person1, person2), count in occurrences:
        graph.add_edge(person1, person2, weight=count)

    # Visualize the graph
    #pos = nx.spring_layout(graph, k=1/100)  # Positions for all nodes
    #pos = nx.spring_layout(graph, scale=2)
    #pos = nx.random_layout(graph)
    #pos = nx.circular_layout(graph)
    #pos = nx.nx_agraph.graphviz_layout(graph, prog="neato")
    #pos = nx.fruchterman_reingold_layout(graph)
    pos = nx.shell_layout(graph)
    #pos = nx.spectral_layout(graph)

    # Extract edge weights
    edge_weights = [graph[u][v]['weight'] for u, v in graph.edges()]

    #pos = nx.spring_layout(graph)


    # Define the range of edge thicknesses
    min_weight = min(edge_weights)
    max_weight = max(edge_weights)

    plt.figure(figsize=(20, 10))

    ax = plt.gca()
    ax.set_title(title)

    mentions_dict = {item : 0 for sublist in [x[0] for x in occurrences] for item in sublist}

    for (person_a, person_b), count in occurrences:
        mentions_dict[person_a] += count
        mentions_dict[person_b] += count
                
    node_sizes = [mentions_dict[node] * 10 for node in graph.nodes()]

    nx.draw_networkx_nodes(graph, 
                        pos, 
                        node_size=node_sizes, 
                        node_color='skyblue')


    for (u, v, d) in graph.edges(data=True):
        width = (d['weight'] - min_weight) / (max_weight - min_weight) * 5 + 1  
        nx.draw_networkx_edges(graph, pos, edgelist=[(u, v)], width=width/2, alpha=0.5, edge_color='green', node_size=node_sizes)

    nx.draw_networkx_labels(graph, pos=pos, font_size=10, font_color='black')
    # Draw edge weights
    edge_labels = nx.get_edge_attributes(graph, 'weight')
    edge_labels = {k: '' for k in edge_labels}
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_color='red')
    
    if save:
        plt.savefig(filename, bbox_inches = 'tight')

    return graph

def create_graph2(occurrences):

    #Create a NetworkX graph
    G = nx.Graph()
    for (person1, person2), count in occurrences:
        G.add_edge(person1, person2, weight=count*0.1, color='green', width=count*0.01)
    
    # Initiate PyVis network object
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")

    # Translate NetworkX graph to PyVis graph format
    net.from_nx(G)


    # Save the PyVis graph to HTML file
    filename = 'graph.html'
    net.save_graph(filename)
    return filename

def create_graph_w_mixed_entity2(occurrences, persons):
    # Create a NetworkX graph
    G = nx.Graph()
    for (person1, person2), count in occurrences:
        G.add_edge(person1, person2, weight=count*0.1, color='green')
    
    # Initiate PyVis network object
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")

    # Translate NetworkX graph to PyVis graph format
    net.from_nx(G)

    # Add node attributes based on persons
    for node in net.nodes:
        if node["label"] in persons:
            node["color"] = "skyblue"
            node["size"] = 20
            node["font_size"] = 20
        else:
            node["color"] = "red"
            node["size"] = 20
            node["font_size"] = 20

    # Save the PyVis graph to HTML file
    filename = 'graph.html'
    net.save_graph(filename)
    return filename
