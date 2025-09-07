from elasticsearch import AsyncElasticsearch
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger("uvicorn.error")
if not logger.hasHandlers():
    logger = logging.getLogger(__name__)

class AsyncSearcher():

    def __init__(self, index_name):
        load_dotenv()
        es_host = os.getenv("ELASTIC_HOST")
        es_pass = os.getenv("ELASTIC_PASSWORD")
        crt_path = os.getenv("CERT_PATH")
        self.client = AsyncElasticsearch(
            str(es_host),
            ca_certs=str(crt_path),
            basic_auth=("elastic", str(es_pass)),
            request_timeout=600
        )
        self.index_name = index_name

    async def status(self):
        # return await self.client.indices.get(index=self.index_name)
        try:
            return await self.client.indices.stats(index=self.index_name)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return {"message": "please wait for the index to be ready"}

    async def search_index(self, query: dict, size: int = 10, from_: int = 0, fields: list|None = None):
        """
        Searches a given index with a specified query asynchronously.
        """
        try:
            response = await self.client.search(index=self.index_name, query=query, size=size, from_=from_)
            return response
        except Exception as e:
            logger.error(f"An error occurred during the search: {e}")
            return {}
        
    async def knn_index(self, knn: dict, size: int = 10, from_: int = 0):
        """
        Searches a given index with a specified query asynchronously.
        """
        try:
            response = await self.client.search(index=self.index_name, knn=knn, size=size, from_=from_)
            return response
        except Exception as e:
            logger.error(f"An error occurred during the search: {e}")
            return {}

    async def close(self):
        """
        Closes the Elasticsearch client connection.
        """
        await self.client.close()


class AsyncSearchService(AsyncSearcher):

    def __init__(self, index_name):
        super().__init__(index_name)

    async def tf_idf_similarity(self, company_id: int, size: int = 10, page: int = 1):
        from_ = page*size - size
        match_query = {
            "terms": {
                "company_id.keyword": [company_id]
            }
        }
        match_result = await super().search_index(match_query)
        match_id = match_result['hits']['hits'][0]['_id']
        mlt_query = {
            "more_like_this": {
                "fields": ["industries", "specialities", "description"],
                "like": [
                    {
                        "_index": self.index_name,
                        "_id": match_id
                    }
                ],
                "min_term_freq": 1,
                "max_query_terms": 12,
                "include": True
            }
        }
        mlt_result = await super().search_index(mlt_query, size, from_)
        return mlt_result
    
    async def semantic_similarity(self, company_id: int, size: int = 10, page: int = 1):
        from_ = page*size - size
        match_query = {
            "terms": {
                "company_id.keyword": [company_id]
            }
        }
        match_result = await super().search_index(match_query)
        full_description = match_result['hits']['hits'][0]['_source']['full_description']
        industries = match_result['hits']['hits'][0]['_source']['industries']
        semantic_query = {
            "bool": {
                "must": {
                    "multi_match": {
                        "fields": ["industries"],
                        "query": str(industries),
                        "boost": 2,
                    }
                },
                "should": {
                    "semantic": {
                        "field": "full_description_semantic",
                        "query": full_description,
                        "boost": 1.5,
                    }
                },
            }
        }
        semantic_result = await super().search_index(semantic_query, size, from_)
        return semantic_result
    
    async def dense_vector_similarity(self, company_id: int, size: int = 10, page: int = 1):
        from_ = page*size - size
        match_query = {
            "terms": {
                "company_id.keyword": [company_id]
            }
        }
        match_result = await super().search_index(match_query, fields=['full_description_embedding'])
        full_description_embedding = match_result['hits']['hits'][0]['_source']['full_description_embedding']
        knn_query = {
            "field": 'full_description_embedding',
            "query_vector": full_description_embedding,
            "k": size,
            "num_candidates": 100
        }
        knn_result = await super().knn_index(knn_query, size, from_)
        return knn_result

