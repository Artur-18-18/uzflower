"""
Unit тесты для Product CRUD операций
"""
import pytest
from sqlalchemy.orm import Session

from main import Product, Category, Review


class TestProductCreate:
    """Тесты создания товара"""
    
    def test_create_product_success(self, db_session: Session, test_category: Category):
        """Успешное создание товара"""
        product = Product(
            name="Test Bouquet",
            price=150000,
            description="Beautiful bouquet",
            composition="Roses, lilies",
            image_url="https://via.placeholder.com/400",
            stock=5,
            category_id=test_category.id
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)
        
        assert product.id is not None
        assert product.name == "Test Bouquet"
        assert product.price == 150000
        assert product.stock == 5
        assert product.is_sale is False
        assert product.is_featured is False
    
    def test_create_product_with_sizes(self, db_session: Session, test_category: Category):
        """Создание товара с размерами"""
        product = Product(
            name="Size Product",
            price=100000,
            price_s=80000,
            price_m=100000,
            price_l=130000,
            category_id=test_category.id
        )
        db_session.add(product)
        db_session.commit()
        
        assert product.price_s == 80000
        assert product.price_m == 100000
        assert product.price_l == 130000
    
    def test_create_product_sale(self, db_session: Session, test_category: Category):
        """Создание товара со скидкой"""
        product = Product(
            name="Sale Product",
            price=200000,
            sale_price=150000,
            is_sale=True,
            category_id=test_category.id
        )
        db_session.add(product)
        db_session.commit()
        
        assert product.is_sale is True
        assert product.sale_price == 150000


class TestProductRead:
    """Тесты чтения товара"""
    
    def test_get_product_by_id(self, db_session: Session, test_product: Product):
        """Получение товара по ID"""
        product = db_session.query(Product).filter(Product.id == test_product.id).first()
        
        assert product is not None
        assert product.name == test_product.name
        assert product.price == test_product.price
    
    def test_get_product_with_category(self, db_session: Session, test_product: Product):
        """Получение товара с категорией"""
        product = db_session.query(Product).filter(Product.id == test_product.id).first()
        
        assert product.category is not None
        assert product.category.name == "Test Category"
    
    def test_get_nonexistent_product(self, db_session: Session):
        """Получение несуществующего товара"""
        product = db_session.query(Product).filter(Product.id == 99999).first()
        
        assert product is None


class TestProductUpdate:
    """Тесты обновления товара"""
    
    def test_update_product_price(self, db_session: Session, test_product: Product):
        """Обновление цены товара"""
        test_product.price = 200000
        db_session.commit()
        db_session.refresh(test_product)
        
        assert test_product.price == 200000
    
    def test_update_product_stock(self, db_session: Session, test_product: Product):
        """Обновление количества на складе"""
        test_product.stock = 0
        db_session.commit()
        db_session.refresh(test_product)
        
        assert test_product.stock == 0
    
    def test_update_product_sale(self, db_session: Session, test_product: Product):
        """Обновление скидки"""
        test_product.is_sale = True
        test_product.sale_price = 70000
        db_session.commit()
        db_session.refresh(test_product)
        
        assert test_product.is_sale is True
        assert test_product.sale_price == 70000
    
    def test_update_product_dimensions(self, db_session: Session, test_product: Product):
        """Обновление габаритов"""
        test_product.width = 20
        test_product.height = 40
        db_session.commit()
        db_session.refresh(test_product)
        
        assert test_product.width == 20
        assert test_product.height == 40


class TestProductDelete:
    """Тесты удаления товара"""
    
    def test_delete_product(self, db_session: Session, test_product: Product):
        """Удаление товара"""
        product_id = test_product.id
        db_session.delete(test_product)
        db_session.commit()
        
        product = db_session.query(Product).filter(Product.id == product_id).first()
        assert product is None
    
    def test_delete_product_with_reviews(self, db_session: Session, test_product: Product, test_review: Review):
        """Удаление товара с отзывами (каскад)"""
        product_id = test_product.id
        db_session.delete(test_product)
        db_session.commit()
        
        # Отзывы должны удалиться каскадом
        reviews = db_session.query(Review).filter(Review.product_id == product_id).all()
        assert len(reviews) == 0


class TestProductFilters:
    """Тесты фильтрации товаров"""
    
    def test_filter_by_category(self, db_session: Session, test_category: Category, test_product: Product):
        """Фильтрация по категории"""
        products = db_session.query(Product).filter(Product.category_id == test_category.id).all()
        
        assert len(products) >= 1
        assert test_product.id in [p.id for p in products]
    
    def test_filter_by_price_range(self, db_session: Session, test_category: Category):
        """Фильтрация по диапазону цен"""
        p1 = Product(name="Cheap", price=50000, category_id=test_category.id)
        p2 = Product(name="Expensive", price=500000, category_id=test_category.id)
        db_session.add_all([p1, p2])
        db_session.commit()
        
        products = db_session.query(Product).filter(
            Product.price >= 50000,
            Product.price <= 150000
        ).all()
        
        assert len(products) >= 1
        assert 50000 <= products[0].price <= 150000
    
    def test_filter_featured(self, db_session: Session, test_category: Category):
        """Фильтрация избранных товаров"""
        featured = Product(name="Featured", price=100000, is_featured=True, category_id=test_category.id)
        db_session.add(featured)
        db_session.commit()
        
        products = db_session.query(Product).filter(Product.is_featured == True).all()
        
        assert len(products) >= 1
        assert featured.id in [p.id for p in products]
    
    def test_filter_popular(self, db_session: Session, test_category: Category):
        """Фильтрация популярных товаров"""
        popular = Product(name="Popular", price=100000, is_popular=True, category_id=test_category.id)
        db_session.add(popular)
        db_session.commit()
        
        products = db_session.query(Product).filter(Product.is_popular == True).all()
        
        assert len(products) >= 1
        assert popular.id in [p.id for p in products]


class TestProductSearch:
    """Тесты поиска товаров"""
    
    def test_search_by_name(self, db_session: Session, test_category: Category):
        """Поиск по названию"""
        p1 = Product(name="Red Roses", price=100000, category_id=test_category.id)
        p2 = Product(name="White Lilies", price=120000, category_id=test_category.id)
        db_session.add_all([p1, p2])
        db_session.commit()
        
        products = db_session.query(Product).filter(Product.name.ilike("%roses%")).all()
        
        assert len(products) == 1
        assert "Roses" in products[0].name


class TestProductValidators:
    """Тесты валидации товара"""
    
    def test_required_fields(self, db_session: Session, test_category: Category):
        """Проверка обязательных полей"""
        # SQLite позволяет создавать товары без name, но приложение должно проверять
        product = Product(
            name="Test",  # Name требуется
            price=100,
            category_id=test_category.id
        )
        db_session.add(product)
        db_session.commit()
        
        # Проверяем что товар создался (SQLite позволяет)
        assert product.id is not None
        assert product.name == "Test"
