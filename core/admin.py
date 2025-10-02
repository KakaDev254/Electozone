from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ManyToManyWidget
from .models import Product, Category


# Category resource
class CategoryResource(resources.ModelResource):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug')


class CategoryAdmin(ImportExportModelAdmin):
    resource_class = CategoryResource


# Product resource
class ProductResource(resources.ModelResource):
    # Handle ManyToMany categories (comma-separated slugs)
    categories = fields.Field(
        column_name='categories',
        attribute='categories',
        widget=ManyToManyWidget(Category, field='slug', separator=',')
    )

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'price',
            'main_image',  # URL to Cloudinary image
            'image_1',
            'image_2',
            'image_3',
            'image_4',
            'spec_1',
            'spec_2',
            'spec_3',
            'spec_4',
            'categories',  # ManyToMany
            'is_featured',
            'is_new',
            'created_at',
        )


class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource


admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
