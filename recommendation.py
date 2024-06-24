from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from bson import ObjectId
import numpy as np
import arabic_reshaper
from bidi.algorithm import get_display
import random
from pymongo import MongoClient


def connect_database():
    mongo_uri = "mongodb+srv://toptools1:toptools1234@cluster0.7rz2win.mongodb.net/toptools"
    client = MongoClient(mongo_uri)
    try:
        client.toptools1.command('ping')
        print("successfully connected to MongoDbB!")
    except Exception as e:
        print(e)
    db = client["toptools"]
    collections = db.list_collection_names()
    favorites_collection = db["favorites"]
    products_collection = db["products"]

    return (favorites_collection , products_collection )

def compute_tfidf_matrix(products, field):
    texts = [product[field] for product in products]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(texts)
    return tfidf_matrix, vectorizer

def compute_cosine_similarity(user_product_vector, product_vectors):
    cosine_similarities = cosine_similarity(user_product_vector, product_vectors)
    return cosine_similarities

def recommend_similar_products(user_id):
    try:
        favorites_collection, products_collection = connect_database()
        # Fetch user's favorite products
        user_object_id = ObjectId(user_id)
        user = favorites_collection.find_one({"userId": user_object_id})
        #print(user)

        if not user:
            print(f"User with ID {user_id} does not exist.")
            return []

        favorite_product_ids = user.get('products', [])
        #print(favorite_product_ids)

        # Fetch all favorite products from products collection
        favorite_products = []
        for product in favorite_product_ids:
            product = products_collection.find_one({"_id": ObjectId(product['productId'])})
            if product:
                favorite_products.append(product)

        #print(favorite_products)

        for favorite_product in favorite_products:
            reshaped_text = arabic_reshaper.reshape(favorite_product['name'])
            bidi_text = get_display(reshaped_text)
            favorite_product['name'] = bidi_text

        # Fetch all products
        all_products = list(products_collection.find())
        for product in all_products:
            reshaped_text = arabic_reshaper.reshape(product['name'])
            bidi_text = get_display(reshaped_text)
            product['name'] = bidi_text

        # Compute TF-IDF matrix for names and brands
        name_tfidf_matrix, name_vectorizer = compute_tfidf_matrix(all_products, 'name')

        # Compute user's TF-IDF vectors
        user_product_names = [product['name'] for product in favorite_products]
        print(f"all favorite Products for user with id = {user_id}" , user_product_names)


        user_name_vector = name_vectorizer.transform(user_product_names)

        name_cosine_similarities = compute_cosine_similarity(user_name_vector, name_tfidf_matrix)
        # Fetch the top 2 similar products
        top_similar_products = []
        num_top_products = 2  # Number of top products to retrieve per favorite product

        for i, user_product_name in enumerate(user_product_names):
            # Sort cosine similarities for the current user product name
            cosine_similarities = name_cosine_similarities[i]
            sorted_indices = np.argsort(cosine_similarities)[::-1]

            # Select top similar products (excluding itself)
            similar_product_indices = sorted_indices[1:num_top_products + 1]  # start with 1 to Exclude the product itself
            similar_products = [all_products[idx] for idx in similar_product_indices]

            top_similar_products.append({
                'user_product': favorite_products[i],
                'similar_products': similar_products
            })

        """
        for similar_product in top_similar_products:
            similar_product_name = [item['name'] for item in similar_product['similar_products']]
            print(similar_product['user_product']['name'] ,similar_product_name )
        """

        list_prodects= []
        for similar_products in top_similar_products:
            for similar_product in similar_products['similar_products']:
                product_dict = {
                    'name': similar_product['name'],
                    'id': str(similar_product['_id'])  # Convert ObjectId to string
                }
                list_prodects.append(product_dict)

        return list_prodects

    except Exception as e:
        print(f"Error: {str(e)}")
        return []

print(recommend_similar_products('66718a8e096c2a3061ad01d6'))




