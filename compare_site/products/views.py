from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ProductImage
from .utils import detect_product, fetch_prices
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.cache import cache
import hashlib
import json

def home(request):
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            img = request.FILES['image']
            obj = ProductImage.objects.create(image=img)
            
            product_name = detect_product(obj.image.path)
            
            cache_key = f"prices_{hashlib.md5(product_name.encode()).hexdigest()}"
            prices = cache.get(cache_key)
            
            if not prices:
                prices = fetch_prices(product_name)
                cache.set(cache_key, prices, 3600)
            
            return render(request, "index.html", {
                'product': product_name,
                'prices': prices,
                'image_url': obj.image.url,
                'total_results': len(prices)
            })
        except Exception as e:
            messages.error(request, f"Error processing image: {str(e)}")
            return render(request, "index.html")
    
    return render(request, "index.html")

@api_view(['POST'])
def upload_image_api(request):
    try:
        img = request.FILES['image']
        obj = ProductImage.objects.create(image=img)
        
        product_name = detect_product(obj.image.path)
        
        cache_key = f"prices_{hashlib.md5(product_name.encode()).hexdigest()}"
        prices = cache.get(cache_key)
        
        if not prices:
            prices = fetch_prices(product_name)
            cache.set(cache_key, prices, 3600)
        
        return Response({
            "product": product_name,
            "prices": prices,
            "image_url": obj.image.url,
            "total_results": len(prices)
        })
    except Exception as e:
        return Response({"error": str(e)}, status=400)