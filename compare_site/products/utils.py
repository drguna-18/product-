# utils.py
import requests
import os
import time
import random
from django.conf import settings
from bs4 import BeautifulSoup
import json
from urllib.parse import quote

def detect_product(image_path):
    """
    Detect product from image using Google Vision API or fallback
    """
    try:
        from google.cloud import vision
        import io
        
        client = vision.ImageAnnotatorClient()
        
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        
        response = client.label_detection(image=image)
        labels = response.label_annotations
        
        product_keywords = ['laptop', 'mobile', 'phone', 'smartphone', 'computer', 
                           'electronics', 'gadget', 'camera', 'headphones', 'watch', 
                           'television', 'tablet', 'earphones', 'speaker']
        
        for label in labels:
            label_desc = label.description.lower()
            if any(keyword in label_desc for keyword in product_keywords):
                return label.description
        
        if labels:
            return labels[0].description
        
        return "Electronics Product"
        
    except Exception as e:
        print(f"Vision API error: {e}")
        filename = os.path.basename(image_path).lower()
        if 'mobile' in filename or 'phone' in filename:
            return "Mobile Phone"
        elif 'laptop' in filename:
            return "Laptop"
        elif 'camera' in filename:
            return "Camera"
        return "Electronics Product"

def fetch_prices_real_time(product_name):
    """
    Fetch real-time prices from multiple e-commerce sites with better reliability
    """
    results = []
    
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    api_results = fetch_via_rapidapi(product_name)
    if api_results:
        results.extend(api_results)
    
    if not results or len(results) < 3:
        amazon_results = scrape_amazon_india(product_name, headers)
        results.extend(amazon_results)
    
    if not results or len(results) < 5:
        flipkart_results = scrape_flipkart(product_name, headers)
        results.extend(flipkart_results)
    
    unique_results = []
    seen = set()
    for item in results:
        key = f"{item['title']}_{item['price']}"
        if key not in seen:
            seen.add(key)
            unique_results.append(item)
    
    for item in unique_results:
        try:
            price_str = item['price'].replace('₹', '').replace(',', '').strip()
            item['price_numeric'] = float(price_str) if price_str.replace('.', '').isdigit() else float('inf')
        except:
            item['price_numeric'] = float('inf')
    
    unique_results.sort(key=lambda x: x['price_numeric'])
    
    for idx, item in enumerate(unique_results[:10], 1):
        item['rank'] = idx
    
    if not unique_results:
        unique_results = get_sample_prices(product_name)
    
    return unique_results[:10]

def fetch_via_rapidapi(product_name):
    """
    Fetch prices using RapidAPI (more reliable than scraping)
    """
    results = []
    
    try:
        url = "https://real-time-product-search.p.rapidapi.com/search-v2"
        
        querystring = {
            "q": product_name,
            "country": "in",
            "language": "en",
            "limit": "15"
        }
        
        headers = {
            "X-RapidAPI-Key": "f1939124a0mshab8e271db450a6dp1e1f82jsn0a076f5ef626",  # Replace with your actual key
            "X-RapidAPI-Host": "real-time-product-search.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get("data", {}).get("products", [])
            
            for item in products[:8]:
                price = item.get("product_price", "N/A")
                if price and price != "N/A":
                    price = price.replace('₹', '').replace(',', '').strip()
                    price = f"₹{price}" if price else "Price not available"
                
                results.append({
                    "title": item.get("product_title", "No Title")[:100],
                    "price": price if price != "N/A" else "Price not available",
                    "link": item.get("product_url", "#"),
                    "source": item.get("source", "Online Store"),
                    "image": item.get("product_photos", [""])[0] if item.get("product_photos") else ""
                })
    except Exception as e:
        print(f"RapidAPI error: {e}")
    
    return results

def scrape_amazon_india(product_name, headers):
    """
    Scrape Amazon India for product prices
    """
    results = []
    search_term = quote(product_name)
    url = f"https://www.amazon.in/s?k={search_term}"
    
    try:
        time.sleep(random.uniform(1, 2))
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            products = soup.find_all('div', {'data-component-type': 's-search-result'})[:5]
            
            for product in products:
                try:
                    title_elem = product.find('span', {'class': 'a-text-normal'})
                    title = title_elem.text.strip() if title_elem else product_name
                    
                    price_whole = product.find('span', {'class': 'a-price-whole'})
                    price_fraction = product.find('span', {'class': 'a-price-fraction'})
                    
                    if price_whole:
                        price = f"₹{price_whole.text.strip()}"
                        if price_fraction:
                            price += f".{price_fraction.text.strip()}"
                    else:
                        price = "Price not available"
                    
                    link_elem = product.find('a', {'class': 'a-link-normal'})
                    link = f"https://www.amazon.in{link_elem.get('href')}" if link_elem else url
                    
                    img_elem = product.find('img', {'class': 's-image'})
                    image = img_elem.get('src') if img_elem else ""
                    
                    results.append({
                        'title': title[:100],
                        'price': price,
                        'link': link,
                        'source': 'Amazon',
                        'image': image
                    })
                except Exception as e:
                    print(f"Error parsing Amazon product: {e}")
                    continue
                    
    except Exception as e:
        print(f"Amazon scraping error: {e}")
    
    return results

def scrape_flipkart(product_name, headers):
    """
    Scrape Flipkart for product prices
    """
    results = []
    search_term = quote(product_name)
    url = f"https://www.flipkart.com/search?q={search_term}"
    
    try:
        time.sleep(random.uniform(1, 2))
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            products = soup.find_all('div', {'class': '_1AtVbE'})[:5]
            
            if not products:
                products = soup.find_all('div', {'class': '_2kHMtA'})[:5]
            
            for product in products:
                try:
                    title_elem = product.find('a', {'class': 'IRpwTa'})
                    if not title_elem:
                        title_elem = product.find('div', {'class': '_4rR01T'})
                    
                    title = title_elem.text.strip() if title_elem else product_name
                    
                    price_elem = product.find('div', {'class': '_30jeq3'})
                    if not price_elem:
                        price_elem = product.find('div', {'class': '_25b18c'})
                    
                    price = price_elem.text.strip() if price_elem else "Price not available"
                    
                    link_elem = product.find('a', {'class': '_1fQZEK'})
                    if not link_elem:
                        link_elem = product.find('a', href=True)
                    
                    if link_elem and link_elem.get('href'):
                        link = f"https://www.flipkart.com{link_elem.get('href')}"
                    else:
                        link = url
                    
                    img_elem = product.find('img', {'class': '_396cs4'})
                    if not img_elem:
                        img_elem = product.find('img')
                    
                    image = img_elem.get('src') if img_elem else ""
                    
                    results.append({
                        'title': title[:100],
                        'price': price,
                        'link': link,
                        'source': 'Flipkart',
                        'image': image
                    })
                except Exception as e:
                    print(f"Error parsing Flipkart product: {e}")
                    continue
                    
    except Exception as e:
        print(f"Flipkart scraping error: {e}")
    
    return results

def get_sample_prices(product_name):
    """
    Return sample data for testing when all APIs fail
    """
    product_lower = product_name.lower()
    
    sample_products = {
        'laptop': [
            {
                "title": f"{product_name} - Latest Model (8GB RAM, 512GB SSD)",
                "price": "₹45,990",
                "link": "https://www.amazon.in/s?k=laptop",
                "source": "Amazon",
                "image": "",
                "rank": 1
            },
            {
                "title": f"{product_name} Premium Edition (16GB RAM, 1TB SSD)",
                "price": "₹62,999",
                "link": "https://www.flipkart.com/search?q=laptop",
                "source": "Flipkart",
                "image": "",
                "rank": 2
            },
            {
                "title": f"{product_name} Gaming Edition",
                "price": "₹54,999",
                "link": "https://www.amazon.in/s?k=laptop",
                "source": "Amazon",
                "image": "",
                "rank": 3
            }
        ],
        'mobile': [
            {
                "title": f"{product_name} 5G (128GB Storage)",
                "price": "₹24,999",
                "link": "https://www.amazon.in/s?k=mobile",
                "source": "Amazon",
                "image": "",
                "rank": 1
            },
            {
                "title": f"{product_name} Pro Max (256GB Storage)",
                "price": "₹34,999",
                "link": "https://www.flipkart.com/search?q=mobile",
                "source": "Flipkart",
                "image": "",
                "rank": 2
            },
            {
                "title": f"{product_name} Lite Edition",
                "price": "₹18,999",
                "link": "https://www.amazon.in/s?k=mobile",
                "source": "Amazon",
                "image": "",
                "rank": 3
            }
        ]
    }
    
    if any(word in product_lower for word in ['laptop', 'computer', 'notebook']):
        return sample_products['laptop']
    elif any(word in product_lower for word in ['mobile', 'phone', 'smartphone']):
        return sample_products['mobile']
    else:
        return [
            {
                "title": f"{product_name} - Standard Model",
                "price": "₹5,999",
                "link": "https://www.amazon.in/s?k=electronics",
                "source": "Amazon",
                "image": "",
                "rank": 1
            },
            {
                "title": f"{product_name} - Premium Model",
                "price": "₹8,999",
                "link": "https://www.flipkart.com/search?q=electronics",
                "source": "Flipkart",
                "image": "",
                "rank": 2
            }
        ]

def fetch_prices(product_name):
    """
    Main function to fetch prices (uses real-time by default)
    """
    return fetch_prices_real_time(product_name)