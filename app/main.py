from fastapi import FastAPI, Depends
from typing import AsyncGenerator
from app.searcher import AsyncSearchService
from dotenv import load_dotenv
import os
from contextlib import asynccontextmanager
import asyncio
import app.indexer as indexer
import logging

load_dotenv()
es_index = str(os.getenv("ELASTIC_INDEX"))

logger = logging.getLogger("uvicorn.error")
if not logger.hasHandlers():
    logger = logging.getLogger(__name__)

async def get_searcher() -> AsyncGenerator[AsyncSearchService, None]:
    searcher = AsyncSearchService(es_index)
    try:
        yield searcher
    finally:
        await searcher.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This runs on application startup and shutdown.
    """
    logger.info("Application startup initiated.")
    # Run the indexer task in the background
    asyncio.create_task(asyncio.to_thread(indexer.index_if_needed))
    logger.info("Application is now ready to receive requests.")
    yield
    logger.info("Application shutdown initiated.")
    # Add any shutdown logic here if needed

app = FastAPI(root_path='/v1', lifespan=lifespan)

@app.get("/")
def read_root():
    # TODO check if index is good in /status
    return {"message": "API is working! Head to /docs for more info."}

@app.get("/status")
async def status(searcher: AsyncSearchService = Depends(get_searcher)):
    return await searcher.status()

@app.get("/tf_idf_similarity/{company_id}")
async def tf_idf_similarity(company_id: int,
                            size: int = 10, 
                            page: int = 1, 
                            searcher: AsyncSearchService = Depends(get_searcher)):
    return await searcher.tf_idf_similarity(company_id, size, page)

@app.get("/semantic_similarity/{company_id}")
async def semantic_similarity(company_id: int, 
                              size: int = 10, 
                              page: int = 1,
                              searcher: AsyncSearchService = Depends(get_searcher)):
    return await searcher.semantic_similarity(company_id, size, page)

@app.get("/dense_vector_similarity/{company_id}")
async def dense_vector_similarity(company_id: int, 
                                  size: int = 10, 
                                  page: int = 1,
                                  searcher: AsyncSearchService = Depends(get_searcher)):
    return await searcher.dense_vector_similarity(company_id, size, page)