from fastapi import FastAPI, Depends, HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
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
    logging.basicConfig(level=logging.INFO, format='    %(levelname)s %(message)s')
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
    return {"message": "API is working! Head to /docs for more info."}

@app.get("/status")
async def status(searcher: AsyncSearchService = Depends(get_searcher)):
    try:
        return await searcher.status()
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred."
        )

@app.get("/tf_idf_similarity/{company_id}")
async def tf_idf_similarity(company_id: int,
                            size: int = 10, 
                            page: int = 1, 
                            searcher: AsyncSearchService = Depends(get_searcher)):
    try:
        return await searcher.tf_idf_similarity(company_id, size, page)
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred."
        )

@app.get("/semantic_similarity/{company_id}")
async def semantic_similarity(company_id: int, 
                              size: int = 10, 
                              page: int = 1,
                              searcher: AsyncSearchService = Depends(get_searcher)):
    try:
        return await searcher.semantic_similarity(company_id, size, page)
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred."
        )

@app.get("/dense_vector_similarity/{company_id}")
async def dense_vector_similarity(company_id: int, 
                                  size: int = 10, 
                                  page: int = 1,
                                  searcher: AsyncSearchService = Depends(get_searcher)):
    try:
        return await searcher.dense_vector_similarity(company_id, size, page)
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred."
        )