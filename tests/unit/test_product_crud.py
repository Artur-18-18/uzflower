import pytest
from sqlalchemy.orm import Session
from main import Product, Category

@pytest.mark.unit
class TestProductCreate:
    def test_create_product_success(self, db_session: Session, sample_category: Category):
        product = Product(name="Roses", price=50000.0, stock=20, category_id=sample_category.id)
        db_session.add(product)
        db_session.commit()
        assert product.id is not None
        assert product.name == "Roses"

@pytest.mark.unit
class TestProductRead:
    def test_read_product_by_id(self, db_session: Session, sample_product: Product):
        product = db_session.query(Product).filter(Product.id == sample_product.id).first()
        assert product is not None

@pytest.mark.unit
class TestProductUpdate:
    def test_update_product_name(self, db_session: Session, sample_product: Product):
        sample_product.name = "Premium Roses"
        db_session.commit()
        updated = db_session.query(Product).filter(Product.id == sample_product.id).first()
        assert updated.name == "Premium Roses"

@pytest.mark.unit
class TestProductDelete:
    def test_delete_product(self, db_session: Session, sample_product: Product):
        product_id = sample_product.id
        db_session.delete(sample_product)
        db_session.commit()
        deleted = db_session.query(Product).filter(Product.id == product_id).first()
        assert deleted is None
