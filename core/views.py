from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product, Category
from django.core.paginator import Paginator


def home(request):
    # Fetch all categories from the Category model
    categories = Category.objects.all()
    selected_category_slug = request.GET.get('category')

    if selected_category_slug == "all" or selected_category_slug is None:
        featured_products = Product.objects.filter(is_featured=True).order_by('-created_at')[:12]
        new_arrivals = Product.objects.filter(is_new=True).order_by('-created_at')[:8]
    else:
        # Filter by category slug using ManyToMany relation
        featured_products = Product.objects.filter(
            is_featured=True,
            categories__slug=selected_category_slug
        ).distinct().order_by('-created_at')[:10]

        new_arrivals = Product.objects.filter(
            is_new=True,
            categories__slug=selected_category_slug
        ).distinct().order_by('-created_at')[:8]

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'selected_category': selected_category_slug,
    }

    return render(request, 'core/home.html', context)



def products_list(request):
    # Get all categories from the Category model
    categories = Category.objects.all()

    # Get selected category slug from query parameter (e.g., ?category=vibrators)
    selected_category_slug = request.GET.get('category')

    if selected_category_slug == "all" or selected_category_slug is None:
        products = Product.objects.all()
    else:
        # Filter products by related category slug
        products = Product.objects.filter(categories__slug=selected_category_slug)

    # Paginate products (20 per page)
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': categories,
        'products': page_obj,
        'selected_category': selected_category_slug,
    }
    return render(request, 'core/products.html', context)


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Get related products that share at least one category
    related_products = Product.objects.filter(
        categories__in=product.categories.all()
    ).exclude(pk=product.pk).distinct()[:4]  # distinct() to avoid duplicates

    return render(request, 'core/product_detail.html', {
        'product': product,
        'related_products': related_products,
    })
    
def product_search(request):
    query = request.GET.get('q', '')
    products = []

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(categories__icontains=[query])  # Assuming input matches category key
        )

    return render(request, 'core/search_results.html', {
        'products': products,
        'query': query,
    })


