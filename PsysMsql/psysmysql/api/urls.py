"""
URL Configuration for PsysMsql API

This module defines all API endpoints and their routing.
Includes authentication endpoints and API documentation.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from .viewsets import (
    UserViewSet,
    ProductViewSet,
    StockViewSet,
    ClientViewSet,
    SellViewSet,
    RegisterSellDetailViewset,
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"stock", StockViewSet, basename="stock")
router.register(r"clients", ClientViewSet, basename="client")
router.register(r"sales", SellViewSet, basename="sell")
router.register(r"selldetails", RegisterSellDetailViewset, basename="selldetails")

app_name = "api"
urlpatterns = [
    # API Root - includes all viewset routes
    path("", include(router.urls)),
    # Authentication endpoints
    path(
        "auth/",
        include(
            [
                path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
                path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
                path("verify/", TokenVerifyView.as_view(), name="token_verify"),
            ]
        ),
    ),
    # API Documentation with Swagger
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="api:schema"),
        name="swagger-ui",
    ),
    path("redoc/", SpectacularRedocView.as_view(url_name="api:schema"), name="redoc"),
]

# Additional URL patterns for specific endpoints that don't fit the ViewSet pattern
# These could include custom analytics endpoints, bulk operations, etc.

"""
API Endpoints Summary:

AUTHENTICATION:
- POST /api/v1/auth/login/         - Login (get JWT tokens)
- POST /api/v1/auth/refresh/       - Refresh access token
- POST /api/v1/auth/verify/        - Verify token validity

USERS:
- GET    /api/v1/users/            - List users
- POST   /api/v1/users/            - Create user
- GET    /api/v1/users/{id}/       - Get user details
- PUT    /api/v1/users/{id}/       - Update user
- PATCH  /api/v1/users/{id}/       - Partial update user
- DELETE /api/v1/users/{id}/       - Delete user
- GET    /api/v1/users/me/         - Get current user profile
- PATCH  /api/v1/users/update_profile/ - Update current user profile

PRODUCTS:
- GET    /api/v1/products/         - List products (with filters)
- POST   /api/v1/products/         - Create product
- GET    /api/v1/products/{id}/    - Get product details
- PUT    /api/v1/products/{id}/    - Update product
- PATCH  /api/v1/products/{id}/    - Partial update product
- DELETE /api/v1/products/{id}/    - Delete product
- GET    /api/v1/products/low_stock/ - Get low stock products
- GET    /api/v1/products/out_of_stock/ - Get out of stock products
- GET    /api/v1/products/{id}/stock_history/ - Get stock history for product

STOCK:
- GET    /api/v1/stock/            - List stock entries
- POST   /api/v1/stock/            - Create stock entry
- GET    /api/v1/stock/{id}/       - Get stock details
- PUT    /api/v1/stock/{id}/       - Update stock
- PATCH  /api/v1/stock/{id}/       - Partial update stock
- DELETE /api/v1/stock/{id}/       - Delete stock entry
- GET    /api/v1/stock/summary/    - Get stock summary statistics
- POST   /api/v1/stock/{id}/adjust/ - Adjust stock quantity

CLIENTS:
- GET    /api/v1/clients/          - List clients
- POST   /api/v1/clients/          - Create client
- GET    /api/v1/clients/{id}/     - Get client details
- PUT    /api/v1/clients/{id}/     - Update client
- PATCH  /api/v1/clients/{id}/     - Partial update client
- DELETE /api/v1/clients/{id}/     - Delete client
- GET    /api/v1/clients/{id}/purchase_history/ - Get client purchase history
- GET    /api/v1/clients/{id}/stats/ - Get client statistics

SALES:
- GET    /api/v1/sales/            - List sales (with filters)
- POST   /api/v1/sales/            - Create sale
- GET    /api/v1/sales/{id}/       - Get sale details
- PUT    /api/v1/sales/{id}/       - Update sale
- PATCH  /api/v1/sales/{id}/       - Partial update sale
- DELETE /api/v1/sales/{id}/       - Delete sale
- POST   /api/v1/sales/{id}/cancel/ - Cancel sale
- GET    /api/v1/sales/analytics/  - Get sales analytics
- GET    /api/v1/sales/daily_summary/ - Get daily sales summary

SALES DETAILS:
- GET    /api/v1/selldetails/            - Details of sales (with filters)

DOCUMENTATION:
- GET    /api/v1/docs/             - API documentation
- GET    /api/v1/schema/           - API schema

FILTERING AND SEARCH:
All list endpoints support filtering, searching, and ordering:
- ?search={query}                  - Search across relevant fields
- ?ordering={field}                - Order by field (use - for descending)
- ?page={number}                   - Pagination
- ?page_size={size}                - Results per page (max 100)

Product filters:
- ?name={name}                     - Filter by name (contains)
- ?price_min={amount}              - Minimum price
- ?price_max={amount}              - Maximum price
- ?in_stock=true/false             - Products in stock
- ?low_stock=true/false            - Products with low stock
- ?out_of_stock=true/false         - Out of stock products

Sales filters:
- ?client_name={name}              - Filter by client name
- ?payment_method={method}         - Filter by payment method
- ?total_price_min={amount}        - Minimum total price
- ?total_price_max={amount}        - Maximum total price
- ?created_after={date}            - Sales after date (YYYY-MM-DD)
- ?created_before={date}           - Sales before date (YYYY-MM-DD)
- ?today=true                      - Today's sales
- ?this_week=true                  - This week's sales
- ?this_month=true                 - This month's sales
- ?last_30_days=true               - Last 30 days sales

Client filters:
- ?name={name}                     - Filter by name
- ?email={email}                   - Filter by email
- ?has_purchases=true/false        - Clients with/without purchases
- ?active_last_days={days}         - Clients active in last N days

RESPONSE FORMAT:
All responses follow a consistent format:

Success responses:
{
    "count": 25,
    "next": "http://api.example.com/products/?page=2",
    "previous": null,
    "results": [...]
}

Error responses:
{
    "error": "Error Type",
    "message": "User-friendly message",
    "details": {...},
    "code": "error_code"
}

AUTHENTICATION:
All endpoints except /auth/login/ require authentication.
Include the JWT token in the Authorization header:
Authorization: Bearer <your-jwt-token>
"""
