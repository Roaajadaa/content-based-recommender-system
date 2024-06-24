from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple
import uvicorn
import arabic_reshaper
from bidi.algorithm import get_display

# Import the recommend_similar_products function
from recommendation import recommend_similar_products

# Initialize FastAPI app
app = FastAPI()

# Define the response model
class ProductRecommendation(BaseModel):
    name: str
    id: str

@app.get("/get-recommend/{user_id}", response_model=List[ProductRecommendation])
def get_recommend(user_id: str):
    recommendations = recommend_similar_products(user_id)

    if not recommendations:
        raise HTTPException(status_code=404, detail="No recommendations found for this user.")

    # Reshape 'name' field in each recommendation
    for product in recommendations:
        reshaped_text = arabic_reshaper.reshape(product['name'])
        bidi_text = get_display(reshaped_text)
        product['name'] = bidi_text

    return recommendations
# Run the app with uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
