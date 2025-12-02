from django.contrib import admin
from .models import AboutPage

@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
    list_display = ("banner_title",)
    fieldsets = (
        ("Banner", {
            "fields": ("banner_image", "banner_title"),
        }),
        ("Images", {
            "fields": ("image1", "image2", "image3"),
        }),
        ("Content", {
            "fields": ("description_top", "description_bottom"),
        }),
        ("Why Choose Us", {
            "fields": ("why_title", "why_collection", "why_affordable", "why_hygiene", "why_convenient"),
        }),
    )


# contact 
from django.contrib import admin
from .models import ContactPage

@admin.register(ContactPage)
class ContactPageAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "phone")


# products


from django.contrib import admin
from .models import ParentCategory, ParentCategoryAssignment
# import ProductCategory only if you want to show it
from .models import ProductCategory  # adjust import path if needed

@admin.register(ParentCategory)
class ParentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'is_active')  # if you added these fields on ParentCategory
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
from django.contrib import admin
from .models import ProductCategory, Product
@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')   # keep it to actual fields on ProductCategory
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "user", "price_per_day", "rating", "size", "metal")
    list_filter = ("category", "user", "metal")
    search_fields = ("name", "name_description", "short_description", "description")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        ("Basic Info", {
            "fields": ("user", "category", "name", "name_description", "short_description", "description", "slug")
        }),
        ("Media", {
            "fields": ("image", "thumbnail1", "thumbnail2", "thumbnail3", "video")
        }),
        ("Attributes", {
            "fields": ("price_per_day", "rating", "size", "metal")
        }),
    )

@admin.register(ParentCategoryAssignment)
class ParentCategoryAssignmentAdmin(admin.ModelAdmin):
    list_display = ('parent', 'category', 'order', 'is_active')
    search_fields = ('parent__name', 'category__name')
    autocomplete_fields = ('parent', 'category')



# promo banner and trending now
from django.contrib import admin
from .models import PromoBanner, FeaturedSection

@admin.register(PromoBanner)
class PromoBannerAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "code", "button_text")

@admin.register(FeaturedSection)
class FeaturedSectionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "position", "order", "button_text")
    list_editable = ("order", "position")
    ordering = ("order",)

# services
from django.contrib import admin
from .models import Service

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "subtitle", "order")
    ordering = ("order",)


# carosal
from django.contrib import admin
from .models import Testimonial

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "order")
    ordering = ("order",)

# category banner
from .models import CategoryBanner

@admin.register(CategoryBanner)
class CategoryBannerAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "title")
