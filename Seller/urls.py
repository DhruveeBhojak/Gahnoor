
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet, MaterialViewSet,InventoryListView, UpdateStockView,CreateInventoryTransaction,OrderListView, OrderDetailView, OrderStatusUpdateView,MessageListCreateView,ProductQueryListCreateView,PayoutViewSet,SalesReportView,BestSellingProductsView,TrafficReportView,BestSellingChartView,seller_landing
from . import views

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet)
router.register(r'materials', MaterialViewSet)
router.register(r'payouts', PayoutViewSet, basename='payout')
product_list = ProductViewSet.as_view({'get': 'list', 'post': 'create'})
manage_products = ProductViewSet.as_view({'get': 'manage_products'})
product_detail = ProductViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})

urlpatterns = [
    path('api/', include(router.urls)),  # no need for 'api/' prefix here
    path('inventory/', InventoryListView.as_view(), name='inventory-list'),
    path('inventory/<int:product_id>/update/', UpdateStockView.as_view(), name='inventory-update'),
    path('inventory/transaction/', CreateInventoryTransaction.as_view(), name='inventory-transaction'),
    path('api/orders/', OrderListView.as_view(), name='order-list'),
    path('api/orders/<int:id>/', OrderDetailView.as_view(), name='order-detail'),
    path('api/orders/<int:id>/status/', OrderStatusUpdateView.as_view(), name='order-status-update'),
    path('api/messages/', MessageListCreateView.as_view(), name='messages'),
    path('api/queries/', ProductQueryListCreateView.as_view(), name='product-queries'),
    path('reports/sales/', SalesReportView.as_view(), name='sales-report'),
    path('reports/products/', BestSellingProductsView.as_view(), name='best-products-report'),
    path('reports/traffic/', TrafficReportView.as_view(), name='traffic-report'), 
    path('reports/chart/best-selling/', BestSellingChartView.as_view(), name='best-selling-chart'),
    
    path('api/products/manage/', product_list, name='product-list'),
    path('api/products/<int:pk>/', product_detail, name='product-detail'),
    path('', views.seller_landing, name='seller_landing'),
    path('register/', views.register_seller, name='seller_register'),
    path('login/', views.seller_login, name='seller_login'), 
    path('dashboard/', views.dashboard_home, name='dashboard_home'),
    # path('dashboard/products/', views.products, name='products'),
    path('dashboard/inventory/', views.inventory, name='inventory'),
    path('dashboard/orders/', views.orders, name='orders'),
    path('dashboard/interactions/', views.interactions, name='interactions'),
    path('dashboard/transactions/', views.transactions, name='transactions'),
    path('dashboard/reports/', views.reports, name='reports'),
    # path('products/', views.product_list_view, name='products'),
    path('products/add/', views.add_product_view, name='add_product'),
]

