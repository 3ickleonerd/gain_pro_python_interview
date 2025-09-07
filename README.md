## Objectives and Initial Assumptions

The objective is to create an API endpoint that returns a list of companies similar to a specified company_id. This API can serve as a recommender system for companies within the dataset.

As the concept of "similarity" is not fully specified in the task description, therefore I will assume a text-based or semantic approach. This means the similarity search will focus on matching companies by their industries, specialities, and overall business functions. Attributes such as location and company size will be considered irrelevant for this purpose.

Companies info are not real-time data. It should be totally fine if the database of companies is updated about every month with an offline approach. This offline approach simplifies the system by eliminating concerns about immediate update availability and complex data-loading mechanisms. In contrast, the API's performance is a critical design priority. We must ensure it is both fast and scalable, capable of serving a high volume of concurrent requests in milliseconds, and designed to scale efficiently to millions of companies.

I also assume diversity is an important factor for this recommender system. In my opinion, the end-user probably knows only a few companies of interest. Assuming the end-user requests similar companies to those few known companies frequently, it's essential that the system provides a variety of similar companies across different aspects. Consistently returning the same list of results would likely diminish the user experience and the system's overall utility.

## Technologies

I've decided to use FastAPI for the API's development due to its native asynchronous capabilities. This is essential for our system, as searching and retrieving companies from the database is generally an I/O-bound task that can be awaited, allowing the system to handle other requests concurrently. Furthermore, FastAPI's built-in Swagger UI simplifies the presentation and documentation of the API's endpoints.

I chose Elasticsearch as the underlying data store/retrieval engine for the following reasons: 

1. Advanced Vector Search for Semantic Similarity: As the core requirement is to find companies based on semantic similarity, a traditional relational database would be inefficient. Elasticsearch, with its native support for dense vector fields and K-Nearest Neighbor (kNN) search, is specifically designed for this type of query. This functionality allows us to index the company text data as high-dimensional vectors and perform highly efficient similarity searches, which is the cornerstone of our recommender system.

2. Exceptional Speed and Scalability: The system must be fast and capable of scaling to millions of companies under heavy load. Elasticsearch is a horizontally scalable, distributed search and analytics engine. It can be deployed across multiple nodes, automatically distributing data and search load, which guarantees low-latency responses even as the company database grows exponentially.

3. Powerful Querying/Scoring: Elasticsearch provides a rich Query DSL that enables complex queries. We can combine vector similarity with other factors, such as company size, to influence the final score and rank of the search results. This flexibility allows us to implement custom scoring algorithms that can introduce variety into the recommended list, ensuring the system provides a dynamic and engaging user experience.

An alternative solution for data store/retrieval engine of this system would be to use PostgreSQL with the pgvector extension, however I prefer Elasticsearch because of its scalable distributed nature and powerful query language for scoring and re-ranking.

## Workflow

The system's workflow is designed to be a two-part process that separates the offline data ingestion pipeline from the online, real-time API.

### Part 1: Offline Data Ingestion and Processing

This part of the workflow is executed periodically (e.g. once a month) to update the database.

The process begins by extracting the raw company data from the provided json files. The extracted text data undergoes a cleansing and preparation phase. The cleaned text for each company is fed into a pre-trained embedding model (BAAI/bge-large-en-v1.5 by default, but can be changed in `.env`). This model converts the text into a high-dimensional dense vector that captures its semantic meaning.

The generated vector embeddings, along with the other company attributes, are bulk-indexed into our Elasticsearch cluster. This is an efficient process that populates the main data store, making the new data available for search.

### Part 2: Online API for Real-Time Search

This is the user-facing part of the system, designed for speed and scalability.

An end-user sends a GET request to the FastAPI endpoint, providing a company_id. The API service retrieves the pre-computed vector embedding for the requested company_id from the Elasticsearch database. This is a very fast lookup operation. The retrieved vector is used as the query vector for a k-NN search against all other company vectors stored in Elasticsearch. This operation is highly optimized and returns a ranked list of the most similar company vectors. The final list of similar companies is formatted into a JSON response and sent back to the client. 

## Install/Run

TBD

## Online Instance

TBD

## Results

TBD

## Future

a mechanism for index updates

Query Enhancement for Diversity: To ensure the diversity requirement is met, the initial search results are filtered and re-scored based on additional criteria. This might involve applying filters to exclude companies from the exact same sub-industry or boosting companies with specific, desired attributes. This ensures the results are not repetitive.