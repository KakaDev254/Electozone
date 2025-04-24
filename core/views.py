from django.shortcuts import render
from django.db.models import Q
from .models import Product
from django.core.paginator import Paginator


def home(request):
    # Get all categories
    categories = dict(Product.CATEGORY_CHOICES)

    # Check if a category is selected in the query parameter
    selected_category = request.GET.get('category')

    # Filter products based on selected category or "All"
    if selected_category == "all" or selected_category is None:
        # If "All" is selected or no category is selected, show all featured and new arrival products
        featured_products = Product.objects.filter(is_featured=True)
        new_arrivals = Product.objects.filter(is_new=True)
    else:
        # If a category is selected, filter products by that category
        featured_products = Product.objects.filter(is_featured=True, category=selected_category)
        new_arrivals = Product.objects.filter(is_new=True, category=selected_category)

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'selected_category': selected_category,  # Pass selected category to the template
    }

    return render(request, 'core/home.html', context)


def products_list(request):
    # Get all categories
    categories = dict(Product.CATEGORY_CHOICES)

    # Get the selected category from query parameter
    selected_category = request.GET.get('category')

    # Filter products based on selected category
    if selected_category == "all" or selected_category is None:
        products = Product.objects.all()
    else:
        products = Product.objects.filter(category=selected_category)

    # Paginate products (20 per page)
    paginator = Paginator(products, 20)  # 20 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': categories,
        'products': page_obj,  # Pass the paginated products
        'selected_category': selected_category,
    }
    return render(request, 'core/products.html', context)


def product_detail(request, pk):
    product = Product.objects.get(id=pk)
  

    context = {
        'product': product,
    
    }
    return render(request, 'core/product_detail.html', context)

def product_search(request):
    query = request.GET.get('q', '')  # Search term for product name or category
    products = []

    if query:
        # Filter products by name or category
        products = Product.objects.filter(
            Q(name__icontains=query) |  # Search in product name
            Q(category__icontains=query)  # Search in product category
        )

    return render(request, 'core/search_results.html', {
        'products': products,
        'query': query,
    })
    


