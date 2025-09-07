import app.helper as helper
import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from sentence_transformers import SentenceTransformer
import json
import logging

logger = logging.getLogger("uvicorn.error")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='    %(levelname)s %(message)s')
    logger = logging.getLogger(__name__)

def index_if_needed():
    load_dotenv()

    es_pass = os.getenv("ELASTIC_PASSWORD")
    es_host = os.getenv("ELASTIC_HOST")
    es_index = os.getenv("ELASTIC_INDEX")
    crt_path = os.getenv("CERT_PATH")
    model_name = str(os.getenv("EMBEDDING_MODEL"))

    client = Elasticsearch(
        str(es_host),
        ca_certs=str(crt_path),
        basic_auth=("elastic", str(es_pass)),
        request_timeout=600,
        verify_certs=False
    )

    if client.indices.exists(index=str(es_index)):
        # client.indices.delete(index=str(es_index), ignore_unavailable=True)
        return

    mappings = {}

    with open('mappings/full.json') as m:
        mappings = json.load(m)

    client.indices.create(
        index=str(es_index),
        mappings=mappings['mappings']
    )

    logger.info(f"Loading embedding model: {model_name}...")
    model = SentenceTransformer(model_name)
    logger.info("Model loaded successfully.")

    companies = helper.read_csv_to_dict_by_id('data/companies.csv', str(es_index))
    company_industries_aggregated = helper.aggregate_attributes_by_id('data/company_industries.csv')
    company_specialities_aggregated = helper.aggregate_attributes_by_id('data/company_specialities.csv')

    logger.info(f'Number of companies: {len(companies)}')
    logger.info(f'Number of industries: {len(company_industries_aggregated)}')
    logger.info(f'Number of specialities: {len(company_specialities_aggregated)}')

    hits = 0
    misses = 0
    for c, l in company_industries_aggregated.items():
        if c in companies:
            hits += 1
            companies[c]['industries'] = helper.process_field(l)
            companies[c]['full_description'] = helper.process_field(str(companies[c]['industries'])) + \
                                            companies[c]['full_description']
        else:
            misses += 1

    logger.info(f'{(misses/hits)*100}% of industries are invalid and ignored')

    hits = 0
    misses = 0
    for c, l in company_specialities_aggregated.items():
        if c in companies:
            hits += 1
            companies[c]['specialities'] = helper.process_field(l)
            companies[c]['full_description'] = helper.process_field(str(companies[c]['specialities'])) + \
                                            companies[c]['full_description']
        else:
            misses += 1

    logger.info(f'{(misses/hits)*100}% of specialities are invalid and ignored')

    counter = 0
    for c, l in companies.items():
        l['full_description_embedding'] = model.encode(l['full_description'], convert_to_numpy=True).tolist()
        counter += 1
        if counter % 100 == 0:
            logger.info(f'vectorizing company_id: {c}. This is the #{counter} company vectorized so far.')

    logger.warning('indexing... it might take hours!')
    r = helpers.bulk(client, (c for c in companies.values()))
    logger.warning('indexing done!')