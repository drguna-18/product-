# utils.py
import requests
import os
from django.conf import settings

def detect_product(image_path):
    """
    Detect product from image using Google Vision API
    You need to set up Google Cloud credentials first:
    1. Create a service account at https://console.cloud.google.com
    2. Download JSON key file
    3. Set environment variable: GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json
    """
    try:
        from google.cloud import vision
        import io
        
        # Initialize client
        client = vision.ImageAnnotatorClient()
        
        # Read image
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        
        # Get labels
        response = client.label_detection(image=image)
        labels = response.label_annotations
        
        # Look for product-related labels
        product_keywords = ['laptop', 'mobile', 'phone', 'smartphone', 'computer', 
                           'electronics', 'gadget', 'camera', 'headphones', 'watch']
        
        for label in labels:
            label_desc = label.description.lower()
            if any(keyword in label_desc for keyword in product_keywords):
                return label.description
        
        # Fallback to first label if available
        if labels:
            return labels[0].description
        
        return "Electronics Product"
        
    except Exception as e:
        print(f"Vision API error: {e}")
        # Fallback to keyword extraction from filename
        filename = os.path.basename(image_path).lower()
        if 'mobile' in filename or 'phone' in filename:
            return "Mobile Phone"
        elif 'laptop' in filename:
            return "Laptop"
        elif 'camera' in filename:
            return "Camera"
        return "Electronics Product"

def fetch_prices(product_name):
    """
    Fetch product prices from various e-commerce sites
    Using RapidAPI - replace with your own API key
    """
    results = []
    
    # Try multiple APIs for better results
    # Option 1: RapidAPI Product Search
    try:
        url = "https://real-time-product-search.p.rapidapi.com/search-v2"
        
        querystring = {
            "q": product_name,
            "country": "in",
            "language": "en",
            "limit": "10"
        }
        
        headers = {
            "X-RapidAPI-Key": "f1939124a0mshab8e271db450a6dp1e1f82jsn0a076f5ef626",  # Replace with your key
            "X-RapidAPI-Host": "real-time-product-search.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get("data", {}).get("products", [])
            
            for item in products[:5]:
                # Clean up price formatting
                price = item.get("product_price", "N/A")
                if price and price != "N/A":
                    price = price.replace('₹', '').strip()
                
                results.append({
                    "title": item.get("product_title", "No Title")[:100],  # Limit title length
                    "price": f"₹{price}" if price != "N/A" else "Price not available",
                    "link": item.get("product_url", "#"),
                    "source": item.get("source", "Online Store"),
                    "image": item.get("product_photos", [""])[0] if item.get("product_photos") else ""
                })
    except Exception as e:
        print(f"RapidAPI error: {e}")
    
    # If no results, provide sample data for testing
    if not results:
        results = get_sample_prices(product_name)
    
    # Categorize by source
    amazon_products = [p for p in results if 'amazon' in p['link'].lower()]
    flipkart_products = [p for p in results if 'flipkart' in p['link'].lower()]
    other_products = [p for p in results if p not in amazon_products and p not in flipkart_products]
    
    # Return combined results with priority to Amazon/Flipkart
    return amazon_products + flipkart_products + other_products[:5]

def get_sample_prices(product_name):
    """Return sample data for testing when API fails"""
    product_lower = product_name.lower()
    
    # Sample data based on product type
    if 'laptop' in product_lower:
        return [
            {
                "title": f"{product_name} - Latest Model",
                "price": "₹45,990",
                "link": "https://www.amazon.in/s?k=laptop",
                "source": "Amazon",
                "image": ""
            },
            {
                "title": f"{product_name} Premium Edition",
                "price": "₹52,999",
                "link": "https://www.flipkart.com/search?q=laptop",
                "source": "Flipkart",
                "image": ""
            },
            {
                "title": f"{product_name} Basic Model",
                "price": "₹38,500",
                "link": "https://www.amazon.in/s?k=laptop",
                "source": "Amazon",
                "image": ""
            }
        ]
    elif 'mobile' in product_lower or 'phone' in product_lower:
        return [
            {
                "title": f"{product_name} 5G",
                "price": "₹24,999",
                "link": "https://www.amazon.in/s?k=mobile",
                "source": "Amazon",
                "image": ""
            },
            {
                "title": f"{product_name} Pro",
                "price": "₹29,999",
                "link": "https://www.flipkart.com/search?q=mobile",
                "source": "Flipkart",
                "image": ""
            }
        ]
    else:
        return [
            {
                "title": f"{product_name} - Standard",
                "price": "₹5,999",
                "link": "https://www.amazon.in/s?k=electronics",
                "source": "Amazon",
                "image": ""
            }
        ]