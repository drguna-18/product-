# views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ProductImage
from .utils import detect_product, fetch_prices
from django.shortcuts import render, redirect
from django.contrib import messages

def home(request):
    # Handle POST request from the form
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            # Save the uploaded image
            img = request.FILES['image']
            obj = ProductImage.objects.create(image=img)
            
            # Detect product from image
            product_name = detect_product(obj.image.path)
            
            # Fetch prices from e-commerce sites
            prices = fetch_prices(product_name)
            
            # Pass data to template
            return render(request, "index.html", {
                'product': product_name,
                'prices': prices,
                'image_url': obj.image.url
            })
        except Exception as e:
            messages.error(request, f"Error processing image: {str(e)}")
            return render(request, "index.html")
    
    # GET request - just show the form
    return render(request, "index.html")

# API VIEW for AJAX/React calls
@api_view(['POST'])
def upload_image_api(request):
    try:
        img = request.FILES['image']
        obj = ProductImage.objects.create(image=img)
        
        product_name = detect_product(obj.image.path)
        prices = fetch_prices(product_name)
        
        return Response({
            "product": product_name,
            "prices": prices,
            "image_url": obj.image.url
        })
    except Exception as e:
        return Response({"error": str(e)}, status=400)