from django.shortcuts import render, redirect
from rest_framework import viewsets,status,generics,permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Product, Category, Material,Inventory,InventoryTransaction,Order,Message,ProductQuery,Seller,Payout
from .serializers import ProductSerializer, CategorySerializer, MaterialSerializer, InventorySerializer,InventoryTransactionSerializer,OrderSerializer, OrderStatusSerializer,MessageSerializer,ProductQuerySerializer,PayoutSerializer
from rest_framework.decorators import action
from .permissions import IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated
from django.db import transaction as db_transaction
from django.db.models import Sum
from rest_framework.generics import ListAPIView
from .utils import generate_csv_response
from .forms import SellerRegistrationForm, ProductForm,SellerLoginForm
from django.contrib import messages
from django.contrib.auth.models import User
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .permissions import IsOwnerOrReadOnly

from rest_framework.decorators import action
from django.shortcuts import render
from .models import Product, Category, Material
from .serializers import ProductSerializer
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .permissions import IsOwnerOrReadOnly

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None):
        product = self.get_object()
        if 'image' in request.FILES:
            product.image = request.FILES['image']
            product.save()
            return Response({'status': 'image uploaded'})
        return Response({'error': 'No image uploaded'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='manage')
    def manage_products(self, request):
        seller = request.user.seller
        products = Product.objects.filter(seller=seller)
        categories = Category.objects.all()
        materials = Material.objects.all()

        selected_category = request.GET.get('category')
        selected_material = request.GET.get('material')

        if selected_category:
            products = products.filter(category__id=selected_category)
        if selected_material:
            products = products.filter(material__id=selected_material)

        return render(request, 'products.html', {
            'products': products,
            'categories': categories,
            'materials': materials,
            'selected_category': selected_category,
            'selected_material': selected_material,
        })



# class ProductViewSet(viewsets.ModelViewSet):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer
#     permission_classes = [permissions.IsAuthenticated,IsOwnerOrReadOnly]

#     @action(detail=True, methods=['post'], url_path='upload-image')
#     def upload_image(self, request, pk=None):
#         product = self.get_object()
#         if 'image' in request.FILES:
#             product.image = request.FILES['image']
#             product.save()
#             return Response({'status': 'image uploaded'})
#         return Response({'error': 'No image uploaded'}, status=status.HTTP_400_BAD_REQUEST)

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

from datetime import datetime

class SalesReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        seller = request.user.seller
        orders = Order.objects.filter(seller=seller)

        # Date range filtering
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            orders = orders.filter(created_at__gte=start_date)
        if end_date:
            orders = orders.filter(created_at__lte=end_date)

        total_sales = sum([order.quantity * order.price for order in orders])
        total_orders = orders.count()
        total_quantity = sum([order.quantity for order in orders])

        return Response({
            'total_sales': total_sales,
            'total_orders': total_orders,
            'total_quantity_sold': total_quantity
        })
        
class BestSellingProductsView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def get_queryset(self):
        seller = self.request.user.seller

        return Product.objects.filter(order__seller=seller)\
            .annotate(total_sold=Sum('order__quantity'))\
            .order_by('-total_sold')
            
class TrafficReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        seller = request.user.seller
        products = Product.objects.filter(seller=seller)

        traffic_data = []
        for product in products:
            traffic_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'views': product.views.count() if hasattr(product, 'views') else 0
            })

        return Response(traffic_data)
    
class SalesReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        seller = request.user.seller
        orders = Order.objects.filter(seller=seller)

        # Filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            orders = orders.filter(created_at__gte=start_date)
        if end_date:
            orders = orders.filter(created_at__lte=end_date)

        # CSV Export
        if request.query_params.get('export') == 'csv':
            rows = [[o.id, o.product.name, o.quantity, o.price, o.created_at] for o in orders]
            headers = ['Order ID', 'Product', 'Quantity', 'Price', 'Date']
            return generate_csv_response(rows, 'sales_report.csv', headers)

        # JSON Response
        total_sales = sum([o.quantity * o.price for o in orders])
        return Response({
            "total_sales": total_sales,
            "total_orders": orders.count(),
            "total_quantity_sold": sum([o.quantity for o in orders])
        })
        
class BestSellingChartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        seller = request.user.seller
        products = Product.objects.filter(order__seller=seller)\
            .annotate(total_sold=Sum('order__quantity'))\
            .order_by('-total_sold')

        labels = []
        values = []
        for product in products:
            labels.append(product.name)
            values.append(product.total_sold or 0)

        return Response({
            'chart_data': {
                'labels': labels,
                'values': values
            }
        })



from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.cache import never_cache

def seller_landing(request):
    return render(request, 'landing.html')

def register_seller(request):
    if request.method == 'POST':
        form = SellerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('seller_login')
    else:
        form = SellerRegistrationForm()
    return render(request, 'register.html', {'form': form})
            
def seller_login(request):
    if request.method == 'POST':
        form = SellerLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                # Get user by email
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email.')
                return redirect('seller_login')

            # Check if the user is a seller
            if not Seller.objects.filter(user=user).exists():
                messages.error(request, 'This user is not registered as a seller.')
                return redirect('seller_login')

            # Authenticate credentials
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard_home')  # ✅ Change to your seller dashboard URL name
            else:
                messages.error(request, 'Incorrect password.')
                return redirect('seller_login')
    else:
        form = SellerLoginForm()

    return render(request, 'login.html', {'form': form})
            
            
def dashboard_home(request):
    return render(request, 'dashboard_home.html')

# def products(request):
#     return render(request, 'products.html')

def inventory(request):
    return render(request, 'inventory.html')

def orders(request):
    return render(request, 'orders.html')

def interactions(request):
    return render(request, 'interactions.html')

def transactions(request):
    return render(request, 'transactions.html')

def reports(request):
    return render(request, 'sreports.html')


# def product_list_view(request):
#     products = Product.objects.filter(seller__user=request.user)
#     categories = Category.objects.all()
#     materials = Material.objects.all()

#     selected_category = request.GET.get('category')
#     selected_material = request.GET.get('material')

#     if selected_category:
#         products = products.filter(category__id=selected_category)
#     if selected_material:
#         products = products.filter(material__id=selected_material)

#     return render(request, 'seller/products.html', {
#         'products': products,
#         'categories': categories,
#         'materials': materials,
#         'selected_category': selected_category,
#         'selected_material': selected_material,
#     })

def add_product_view(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user.seller
            product.save()
            return redirect('products')
    else:
        form = ProductForm()
    return render(request, 'seller/add_product.html', {'form': form})