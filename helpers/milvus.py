import os
from pymilvus import MilvusClient, DataType
from typing import Dict, Any

# Initialize Milvus client
milvus_uri = os.getenv("MILVUS_URI")
token = os.getenv("MILVUS_TOKEN")
milvus_client = MilvusClient(uri=milvus_uri, token=token)
print(f"Connected to DB: {milvus_uri} successfully")

# Collection configuration
collection_name = "pdf_vector"
dim_img = 512
dim_txt = 384
metric="COSINE"
index="HNSW"

# milvus_client.drop_collection("prod_vectors_flat_cosine")
def create_Collection():
    # Clean up existing collection
	if milvus_client.has_collection(collection_name):
		milvus_client.drop_collection(collection_name)
	print(f"Dropped existing collection {collection_name}")
     
	# Create proper schema for image vectors
	schema = milvus_client.create_schema(
	    auto_id=True,  # We'll provide our own IDs
	    enable_dynamic_field=False
	)

	# Add fields matching your data structure
	schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True, auto_id=True,)
	schema.add_field(field_name="prod_id", datatype=DataType.VARCHAR, max_length=30)
	schema.add_field(field_name="type", datatype=DataType.VARCHAR, max_length=10)
	schema.add_field(field_name="prod_name", datatype=DataType.VARCHAR, max_length=100)
	schema.add_field(field_name="collection_name", datatype=DataType.VARCHAR, max_length=300)
	schema.add_field(field_name="main_image", datatype=DataType.VARCHAR, max_length=1024)
	schema.add_field(field_name="cat_key", datatype=DataType.VARCHAR, max_length=300)
	schema.add_field(field_name="cat_disp_name", datatype=DataType.VARCHAR, max_length=100)
	schema.add_field(field_name="subcat_key", datatype=DataType.VARCHAR, max_length=300)
	schema.add_field(field_name="subcat_disp_name", datatype=DataType.VARCHAR, max_length=100)
	schema.add_field(field_name="sub2cat_key", datatype=DataType.VARCHAR, max_length=300)
	schema.add_field(field_name="sub2cat_disp_name", datatype=DataType.VARCHAR, max_length=100)
	schema.add_field(field_name="owner_type", datatype=DataType.VARCHAR, max_length=10)
	schema.add_field(field_name="owner_name", datatype=DataType.VARCHAR, max_length=100)
	schema.add_field(field_name="owner_id", datatype=DataType.VARCHAR, max_length=300)
	schema.add_field(field_name="owner_score", datatype=DataType.INT64)
	schema.add_field(field_name="owner_plan", datatype=DataType.VARCHAR, max_length=10)
	schema.add_field(field_name="short_desc_vector", datatype=DataType.FLOAT_VECTOR, dim=dim_txt)
	schema.add_field(field_name="big_desc_vector", datatype=DataType.FLOAT_VECTOR, dim=dim_txt)
	schema.add_field(field_name="main_img_hist", datatype=DataType.FLOAT_VECTOR, dim=dim_img)
	schema.add_field(field_name="main_img_vector", datatype=DataType.FLOAT_VECTOR, dim=dim_img)

	# Create index parameters for cosine similarity (CLIP vectors are normalized)
	index_params = milvus_client.prepare_index_params()
	index_params.add_index(
	    field_name="main_img_vector",
	    metric_type=metric, 
	    index_type=index,
	)
	index_params.add_index(
	    field_name="big_desc_vector",
	    metric_type=metric, 
	    index_type=index,
	)
	index_params.add_index(
	    field_name="short_desc_vector",
	    metric_type=metric, 
	    index_type=index,
	)
	index_params.add_index(
	    field_name="main_img_hist",
	    metric_type=metric, 
	    index_type=index,
	)
	index_params.add_index(
    	field_name="prod_id",
    	index_type="AUTOINDEX",
    	index_name="prod_id",
	)
 
	# Create collection
	milvus_client.create_collection(
	    collection_name=collection_name,
	    schema=schema,
	    index_params=index_params
	)
	print(f"Collection {collection_name} created successfully")


## check if collection exists and create if not
if not milvus_client.has_collection(collection_name):
	create_Collection()


## insert data into milvus, same as insert_data
## [{"prod_id": key, "url": url, "img_vector": img_emb, "txt_vector": txt_emb}]
def insert_vector_data(entities) -> Dict[str, Any] | str:
    try:
        result = milvus_client.insert(collection_name, entities)
        print(result)
        # milvus_client.flush(collection_name)
        return result
    except Exception as e:
        return (f"Error inserting data: {e}")

# Search image function
def search_similar_images(query_vector, top_k=5):
    res = milvus_client.search(
    collection_name=collection_name,
    anns_field="main_img_vector",
    data=[query_vector],
    limit=top_k,
    search_params={"metric_type": metric},
    output_fields=["url", "prod_id"]  # Return URL field
	)
    ret = [
    f'{hit["distance"]}, {hit["entity"]["url"]}, {hit["entity"]["prod_id"]}'
    for hit in res[0]
	]
    return ret


# Search text function
def search_similar_text(query_vector, top_k=5):
    res = milvus_client.search(
    collection_name=collection_name,
    anns_field="big_desc_vector",
    data=[query_vector],
    limit=top_k,
    search_params={"metric_type": metric},
    output_fields=["url", "prod_id", "prod_desc"]  # Return URL field
	)
    ret = [
    f'{hit["distance"]}, {hit["entity"]["url"]}, {hit["entity"]["prod_id"]}, {hit["entity"]["prod_desc"]}'
    for hit in res[0]
	]
    return ret
