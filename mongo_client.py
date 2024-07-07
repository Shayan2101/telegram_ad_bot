import pymongo
from bson import ObjectId


class AdsMongoClient:
    def __init__(
        self,
        host: str,
        port: int,
        db_name: str = "telegram_bot",
        ads_collection_name: str = "ads",
        categories_collection_name: str = "categories",
    ):
        self.client = pymongo.MongoClient(host, port)
        self.db = self.client.get_database(db_name)
        self.ads_collection = self.db.get_collection(ads_collection_name)
        self.categories_collection = self.db.get_collection(categories_collection_name)

    def add_category(self, category: str):
        self.categories_collection.insert_one(
            {
                "category": category,
            }
        )

    def get_categories(self) -> list:
        results = self.categories_collection.find()
        return [
            result["category"]
            for result in results
        ]

    def add_advertising(self, user_id: int, photo_url: str, category: str, description: str):
        self.ads_collection.insert_one(
            {
                "user_id": user_id,
                "photo_url": photo_url,
                "category": category,
                "description": description
            }
        )

    def delete_advertising(self, user_id: int, doc_id: str):
        self.ads_collection.delete_one({"user_id": user_id, "_id": ObjectId(doc_id)})

    def get_ads_by_user_id(self, user_id: int):
        results = self.ads_collection.find({"user_id": user_id})
        return [
            {
                "id": str(result["_id"]),
                "photo_url": result["photo_url"],
                "category": result["category"],
                "description": result["description"],
            }
            for result in results
        ]

    def get_ads_by_category(self, category: str):
        # My answer, perform an exact match on the category field and don't care about case sensitivity or partial matches
        # results = self.ads_collection.find({"category": category})
        # Main answer, perform a case-insensitive search or match categories that contain the search term as a substring
        results = self.ads_collection.find({"category": {"$regex": ".*" + category + ".*"}})
        return [
            {
                "id": str(result["_id"]),
                "photo_url": result["photo_url"],
                "category": result["category"],
                "description": result["description"],
            }
            for result in results
        ]
    
    def update_description(self, doc_id: str, edited_description: str):
        self.ads_collection.update_one({"_id": ObjectId(doc_id)}, {"$set": {"description": edited_description}})