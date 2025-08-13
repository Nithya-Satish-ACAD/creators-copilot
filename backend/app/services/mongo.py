from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from uuid import uuid4

uri = "mongodb+srv://acad:nPyjuhmdeIgTxySD@creators-copilot-demo.aoq6p75.mongodb.net/?retryWrites=true&w=majority&appName=creators-copilot-demo&tls=true&tlsAllowInvalidCertificates=true"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["creators-copilot-demo"]

def add_to_collection(collection_name: str, data: dict):
    collection = db[collection_name]
    collection.insert_one(data)

def get_one_from_collection(collection_name: str, query: dict):
    collection = db[collection_name]
    doc = collection.find_one(query)
    if doc and '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

def get_many_from_collection(collection_name: str, query: dict):
    docs = []
    collection = db[collection_name]
    for doc in collection.find(query):
        # Convert ObjectId to string for JSON serialization
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        docs.append(doc)
    return docs

def update_in_collection(collection_name: str, query: dict, data: dict):
    collection = db[collection_name]
    collection.update_one(query, {"$set": data})

def delete_from_collection(collection_name: str, query: dict):
    collection = db[collection_name]
    collection.delete_one(query)

# Courses
def create_course(data: dict):
    course_id = str(uuid4())
    add_to_collection("courses", {"_id": course_id, **data})
    return course_id

def get_course(course_id: str):
    return get_one_from_collection("courses", {"_id": course_id})

def get_courses_by_user_id(user_id: str):
    return get_many_from_collection("courses", {"user_id": user_id})

def update_course(course_id: str, data: dict):
    update_in_collection("courses", {"_id": course_id}, data)

def delete_course(course_id: str):
    delete_from_collection("courses", {"_id": course_id})

# Resources
def create_resource(course_id: str, resource_name: str):
    add_to_collection("resources", {"course_id": course_id, "resource_name": resource_name})

def get_resources_by_course_id(course_id: str):
    return get_many_from_collection("resources", {"course_id": course_id})

def delete_resource(course_id: str, resource_name: str):
    delete_from_collection("resources", {"course_id": course_id, "resource_name": resource_name})

# Assets
def create_asset(course_id: str, asset_name: str, asset_category: str, asset_type: str, asset_content: str, asset_last_updated_by: str, asset_last_updated_at: str):
    add_to_collection("assets", {"course_id": course_id, "asset_name": asset_name, "asset_category": asset_category, "asset_type": asset_type, "asset_content": asset_content, "asset_last_updated_by": asset_last_updated_by, "asset_last_updated_at": asset_last_updated_at})

def get_assets_by_course_id(course_id: str):
    return get_many_from_collection("assets", {"course_id": course_id})

def get_asset_by_course_id_and_asset_name(course_id: str, asset_name: str):
    return get_one_from_collection("assets", {"course_id": course_id, "asset_name": asset_name})