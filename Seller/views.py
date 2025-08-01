from rest_framework import viewsets,status,generics,permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Product, Category, Material,Inventory,InventoryTransaction,Order,Message,ProductQuery,Seller,Payout
from .serializers import ProductSerializer, CategorySerializer, MaterialSerializer, InventorySerializer,InventoryTransactionSerializer,OrderSerializer, OrderStatusSerializer,MessageSerializer,ProductQuerySerializer,PayoutSerializer
from rest_framework.decorators import action
from .permissions import IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated
from django.db import transaction as db_transaction

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated,IsOwnerOrReadOnly]

    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None):
        product = self.get_object()
        if 'image' in request.FILES:
            product.image = request.FILES['image']
            product.save()
            return Response({'status': 'image uploaded'})
        return Response({'error': 'No image uploaded'}, status=status.HTTP_400_BAD_REQUEST)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer

def get_queryset(self):
        # 👇 Only return products for the logged-in user
        return Product.objects.filter(seller=self.request.user)

def perform_create(self, serializer):
        # 👇 Automatically set the logged-in user as the seller
        serializer.save(seller=self.request.user)
        
# GET - View Inventory
class InventoryListView(generics.ListAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Inventory.objects.filter(product__seller=self.request.user)
# PATCH - Update stock count
class UpdateStockView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, product_id):
        try:
            inventory = Inventory.objects.get(product__id=product_id, product__seller=request.user)
        except Inventory.DoesNotExist:
            return Response({'error': 'Inventory not found or access denied'}, status=status.HTTP_404_NOT_FOUND)

        serializer = InventorySerializer(inventory, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateInventoryTransaction(APIView):
    def post(self, request):
        serializer = InventoryTransactionSerializer(data=request.data)
        if serializer.is_valid():
            with db_transaction.atomic():
                trans = serializer.save(seller=request.user)

                # update inventory stock
                inventory = Inventory.objects.get(product=trans.product)

                if trans.transaction_type in ['restock', 'return']:
                    inventory.stock_count += trans.quantity
                elif trans.transaction_type == 'sale':
                    inventory.stock_count -= trans.quantity
                elif trans.transaction_type == 'adjustment':
                    inventory.stock_count = trans.quantity  # assume quantity is the new count
                inventory.save()

            return Response({'message': 'Transaction recorded & stock updated'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# GET /api/orders/ - list all orders
class OrderListView(generics.ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(seller__user=self.request.user)

# GET /api/orders/<id>/ - order detail
class OrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Order.objects.filter(seller__user=self.request.user)

# PATCH /api/orders/<id>/status/ - update order status
class OrderStatusUpdateView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderStatusSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Order.objects.filter(seller__user=self.request.user)
    
class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
         # Check if user is a Seller
        try:
            seller = Seller.objects.get(user=user)
            return Message.objects.filter(seller=seller)
        except Seller.DoesNotExist:
            return Message.objects.filter(customer=user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)
    
class ProductQueryListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductQuerySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        try:
            seller = Seller.objects.get(user=user)
            return ProductQuery.objects.filter(seller=seller)
        except Seller.DoesNotExist:
            return ProductQuery.objects.filter(customer=user)
        
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)  

class PayoutViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PayoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payout.objects.filter(seller=self.request.user)
