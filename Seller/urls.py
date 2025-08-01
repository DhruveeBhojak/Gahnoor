
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet, MaterialViewSet,InventoryListView, UpdateStockView,CreateInventoryTransaction,OrderListView, OrderDetailView, OrderStatusUpdateView,MessageListCreateView,ProductQueryListCreateView,PayoutViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'materials', MaterialViewSet)
router.register(r'payouts', PayoutViewSet, basename='payout')

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
    
]

