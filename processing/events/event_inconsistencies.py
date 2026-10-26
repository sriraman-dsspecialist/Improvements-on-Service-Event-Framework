import os
import re
import enchant
import numpy as np
import pandas as pd
from utils.dbconnection import engine
from pathlib import Path
from utils.config import config
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
from pipeline.data_fetch import fetch_input_from_DB
from utils.utility import save_excel_sheets
from utils.logger import logger


def get_embeddings(events):
    """Generate semantic embeddings for a list of service event names."""
    event_list = [str(event) for event in events]
    model = SentenceTransformer('all-mpnet-base-v2')
    embeddings = model.encode(event_list)
    return embeddings

def event_similarity(events):
    """Compute pairwise event similarity and identify likely duplicate events."""
    embeddings = get_embeddings(events)
    similarity_matrix = cosine_similarity(embeddings)
    similarity_df = pd.DataFrame(
        similarity_matrix,
        columns=events,
        index=events
    ).round(3)
    similarity_df = similarity_df.sort_values(by=events[0], ascending=False).reset_index()
    similarity_df.rename(columns={'index': 'Serviceevent'}, inplace=True)

    # Detect duplicate events based on high similarity
    duplicates=[]
    for i in range(len(events)):
        for j in range(i+1,len(events)):

            score=similarity_matrix[i][j]

            if score > 0.50:
                duplicates.append({
                    'event1':events[i],
                    'event2':events[j],
                    'similarity':score
                })

    similarity_df_melt = pd.DataFrame(duplicates).sort_values(by='similarity', ascending=False)
    similarity_df_melt['similarity'] = np.round(similarity_df_melt['similarity'],2)
    return similarity_df_melt, embeddings

def event_clustering(events, embeddings):
    """Cluster service events into groups using agglomerative clustering."""
    cluster_model = AgglomerativeClustering(
        n_clusters=100,
        metric='l2',
        linkage='ward'
    )

    labels = cluster_model.fit_predict(embeddings)

    agg_clust_df = pd.DataFrame({
        'event':events,
        'cluster':labels
    }).sort_values('cluster')
    return agg_clust_df

def spellcheck_on_events(events, embeddings):
    """Check event names for likely misspellings while ignoring known domain terms."""
    agg_clust_df = event_clustering(events, embeddings)
    # Check all service events in the clustering dataframe, not just a subset.
    all_events = (
        agg_clust_df['event']
        .dropna()
        .astype(str)
        .unique()
    )

    d = enchant.Dict("en_US")

    # Domain-specific words that are valid even if they are not in the general English dictionary.
    excluded_words = {
        'busbar',
        'trafo',
        'scada',
        'ddau',
        'adaptor',
        # Add more here as needed
    }


    def english_word_tokens(name):
        tokens = [
            t for t in re.sub(r'[^a-zA-Z\s]', ' ', name.lower()).split()
            if t and len(t) > 1
        ]
        return [t for t in tokens if not re.fullmatch(r'[a-z]{1,3}', t)]

    rows = []
    for event in sorted(set(all_events)):
        bad_words = []
        for word in english_word_tokens(event):
            word = word.lower()

            # ignore domain-specific terms or uppercase abbreviations
            if word in excluded_words:
                continue
            if re.fullmatch(r'[A-Z]{2,}', word.upper()) and word.isupper():
                continue
            if not d.check(word):
                bad_words.append(word)

        rows.append({
            'event': event,
            'misspelled_words': bad_words,
            'review_required': bool(bad_words)
        })

    topic_15_spellcheck = pd.DataFrame(rows)
    topic_15_spellcheck = topic_15_spellcheck.sort_values('review_required', ascending=False)
    return topic_15_spellcheck

def get_event_distribution():
    """Load the service event distribution dataset and save it as a processed input."""
    # Get the distribution data
    eve_db = fetch_input_from_DB(config.input_files.serviceEvent_distribution, True)
    eve_db.to_excel(os.path.join(config.locations.inputs, config.input_files.serviceEvent_distribution +".xlsx"), index=False)
    logger.info(f"(1/2) Service Event Distribution data processed for {len(eve_db)} records")


def processing_events_allThreads(material_df=None):
    """Run the full event inconsistency workflow for clustering and spell-checking."""
    if material_df is None:
        material_file = os.path.join(
            config.locations.inputs,
            f"{config.input_files.serviceEvent_material}.xlsx"
        )
        if os.path.exists(material_file):
            logger.info(f"Using existing material file: {material_file}")
            material_df = pd.read_excel(material_file)
        else:
            logger.info(
                f"Material file not found at {material_file}. Fetching from DB instead."
            )
            material_df = fetch_input_from_DB(config.input_files.serviceEvent_material, True)

    events = material_df['ServiceEventName'].dropna().astype(str).unique().tolist()
    similarity_df_melt, embeddings = event_similarity(events)
    topic_15_spellcheck = spellcheck_on_events(events, embeddings)
    df_save_dict = {
        'Event Clustering': similarity_df_melt,
        'Spell Check': topic_15_spellcheck
    }
    save_excel_sheets(df_save_dict, os.path.join(config.locations.processed, config.processed_files.event_inconsistencies+ "_processed.xlsx"))
    logger.info(f"(2/2) Service Event Inconsistencies data processed for {len(material_df)} records")

    
    



