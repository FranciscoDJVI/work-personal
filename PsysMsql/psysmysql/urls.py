from django.urls import path
from django.urls import include

from . import views
from . import dashboard_views

urlpatterns = [
    path("", views.app, name="app"),
    path("main/", views.dashboard, name="main"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("register-product/", views.register_product, name="register_product"),
    path("list-product/", views.view_product, name="list-product"),
    path("delete-product/", views.delete_product, name="delete-product"),
    path("update-product/", views.Update.as_view(), name="update-product"),
    path("update_product-done/", views.update_product_done, name="update_product_done"),
    path("sell-product/", views.SellProductView.as_view(), name="sell_product"),
    path(
        "update_quantity/",
        views.update_quantity_view,
        name="update_quantity",
    ),
    path(
        "search-products-ajax/", views.search_products_ajax, name="search_products_ajax"
    ),
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
    path("select2/", include("django_select2.urls")),
    # Dashboard URLs
    path("dashboard/", dashboard_views.DashboardView.as_view(), name="dashboard"),
    path(
        "dashboard/api/",
        dashboard_views.DashboardAPIView.as_view(),
        name="dashboard_api",
    ),
    path(
        "dashboard/realtime/",
        dashboard_views.RealtimeStatsView.as_view(),
        name="realtime_stats",
    ),
    path("dashboard/quick-stats/", dashboard_views.quick_stats, name="quick_stats"),
    path(
        "dashboard/refresh-cache/",
        dashboard_views.refresh_dashboard_cache,
        name="refresh_dashboard_cache",
    ),
]
