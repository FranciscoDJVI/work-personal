from django.contrib import admin
from django.urls import path
from django.urls import include


from . import views

urlpatterns = [
    path("", views.app, name="app"),
    path("main/", views.dashboard, name="main"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("register-product/", views.register_product, name="register_product"),
    path("list-product/", views.view_product, name="list-product"),
    path("delete-product/", views.delete_product, name="delete-product"),
    path("delete-product-done/", views.delete_product_done, name="delete-product-done"),
    path("update-product/", views.Update.as_view(), name="update-product"),
    path("update_product-done/", views.update_product_done, name="update_product_done"),
    path("sell-product/", views.SellProductView.as_view(), name="sell_product"),
    path("delete-sell-item/<int:pk>/", views.delete_sell_item, name="delete_sell_item"),
    path("stock-products/", views.register_stock, name="stock_products"),
    path("register-clients/", views.register_clients, name="register_client"),
    path(
        "list-all-sell-register/",
        views.listallsellregisterview,
        name="list_all_sell_register",
    ),
    path(
        "list-detail-sell-register/<int:pk>/",
        views.detailregisterview,
        name="list_detail_sell_register",
    ),
    path("error/", views.page_404, name="error"),
    path("assing-user-group/", views.assign_user_to_group, name="assing_user"),
]
