import csv
import re
import json
from typing import AsyncGenerator
import logging

logger = logging.getLogger("uvicorn.error")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='    %(levelname)s %(message)s')
    logger = logging.getLogger(__name__)

def aggregate_attributes_by_id(file_path: str) -> dict:
    """
    Reads a CSV file with "ID, attribute" format and aggregates
    attributes for each ID into a dictionary.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        dict: A dictionary where keys are IDs and values are lists of attributes.
    """
    aggregated_data = {}
    
    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            
            # Skip the header row
            next(reader, None)
            
            for row in reader:
                if True: # len(row) == 2:
                    # Strip any whitespace from the ID and attribute
                    id_val = row[0].strip()
                    attribute = row[1].strip()
                    
                    # If ID already exists, append the new attribute
                    if id_val in aggregated_data:
                        aggregated_data[id_val].append(attribute)
                    # If ID is new, create a new list with the attribute
                    else:
                        aggregated_data[id_val] = [attribute]
                        
    except FileNotFoundError:
        logger.error(f"Error: The file at '{file_path}' was not found.")
        return {}
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return {}
        
    return aggregated_data

def read_csv_to_dict_by_id(file_path: str, index_name: str) -> dict:
    """
    Reads a CSV file and returns a dictionary where each key is the ID
    from the first column, and the value is a dictionary of the row's data.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        dict: A dictionary with IDs as keys and row dictionaries as values.
              Returns None if the file is not found.
    """
    data_dict = {}
    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Check if the header exists and if 'ID' is the first column
            if not reader.fieldnames:
                logger.error("Error: The CSV file must have 'ID' as the first column header.")
                return {}
            
            for row in reader:
                # The ID is the value of the first key in the row's dictionary
                row_id = row.get(reader.fieldnames[0])
                row['_index'] = index_name
                row['industries'] = []
                row['specialities'] = []
                row['full_description'] = process_field(row['description'])
                if row_id:
                    data_dict[row_id] = row
    
    except FileNotFoundError:
        logger.error(f"Error: The file '{file_path}' was not found.")
        return {}
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return {}
        
    return data_dict

def remove_urls(text: str) -> str:
    """
    Removes URLs from a given string using a regular expression.

    Args:
        text (str): The input string that may contain URLs.

    Returns:
        str: The string with all identified URLs removed.
    """
    # A regular expression pattern to match common URL formats.
    # It looks for URLs starting with http://, https://, or www.
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    
    # Use re.sub() to find all matches of the pattern and replace them with an empty string.
    # The \S+ part matches one or more non-whitespace characters, effectively capturing the
    # entire URL until a space is encountered.
    cleaned_text = url_pattern.sub('', text)
    return cleaned_text

def process_field(field):
    # Check if the input is a string
    if isinstance(field, str):
        return process_text(field)
    elif isinstance(field, list):
        processed_list = []
        for v in field:
            processed_list.append(process_text(v))
        return processed_list


def process_text(any_text: str) -> str:
    # Convert to lowercase
    processed_text = any_text.lower()

    # remove urls
    processed_text = remove_urls(processed_text)

    # remove brackets
    processed_text = processed_text.replace('[', ' ').replace(']', ' ')

    # Replace unwanted characters with a space.
    # We use a regular expression to find characters that are not
    # a-z, 0-9, or hyphens, and replace them with a single space.
    # This also helps in handling "unwanted" characters by making them
    # a word separator. You can adjust this regex based on your specific needs.
    processed_text = re.sub(r'[^a-z0-9-]+', ' ', processed_text)
    return processed_text

def pretty_search_response(response: dict):
    if len(response["hits"]["hits"]) == 0:
        print("Your search returned no results.")
    else:
        for hit in response["hits"]["hits"]:
            id = hit["_id"]
            score = hit["_score"]
            name = hit["_source"]["name"]
            description = hit["_source"]["description"]
            company_id = hit["_source"]["company_id"]
            pretty_output = f"\nID: {id}\nScore: {score}\nName: {name}\nDescription: {description}\nCompany ID: {company_id}\n"
            print(pretty_output)


def get_company_ids_list_from_response(response: dict) -> list:
    company_ids_list = []
    for hit in response["hits"]["hits"]:
        company_ids_list.append(int(hit["_source"]["company_id"]))
    return company_ids_list


async def yield_ground_truth(ground_truth_file_path: str) -> AsyncGenerator[str, None]:
    with open(ground_truth_file_path) as gt:
        for line in gt:
            yield line


async def get_overlap_percentage(async_client, method) -> float:
    count = 0
    overlap_count = 0
    async for ground_truth in yield_ground_truth('data/ground_truth.json'):
        json_gt = json.loads(ground_truth)
        response = await async_client.get(f'/v1/{method}/{json_gt['id']}')
        company_ids_list = get_company_ids_list_from_response(json.loads(response.text))
        count += len(json_gt['similar_companies'])
        overlap_count += sum(1 for x in company_ids_list if x in json_gt['similar_companies'])
    hit_percent = (overlap_count/count)*100
    logger.info(overlap_count, count, hit_percent)
    return hit_percent