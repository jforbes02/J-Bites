from Database.dbConnect import SessionLocal, engine, Base
from Database.dbModels import User, Item, Order, Review, OrderStatus, ReviewStatus, OrderItem
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_database():
    """Seed the database with initial test data"""

    # Create a new session
    db = SessionLocal()

    try:
        logger.info("Starting database seeding...")

        # Clear existing data
        logger.info("Clearing existing data...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        # Seed Users
        logger.info("Seeding users...")
        users = [
            User(name="John Doe", email="john@example.com", password="password123"),
            User(name="Jane Smith", email="jane@example.com", password="password123"),
            User(name="Bob Wilson", email="bob@example.com", password="password123"),
            User(name="Alice Johnson", email="alice@example.com", password="password123"),
            User(name="Charlie Brown", email="charlie@example.com", password="password123"),
        ]
        db.add_all(users)
        db.commit()
        logger.info(f"Created {len(users)} users")

        # Seed Items
        logger.info("Seeding items...")
        items = [
            Item(name="Classic Burger", price=8.99,
                 description="Juicy beef patty with lettuce, tomato, and special sauce"),
            Item(name="Chicken Sandwich", price=7.99, description="Crispy chicken breast with mayo and pickles"),
            Item(name="Veggie Wrap", price=6.99, description="Fresh vegetables wrapped in a whole wheat tortilla"),
            Item(name="French Fries", price=3.99, description="Crispy golden fries with sea salt"),
            Item(name="Onion Rings", price=4.99, description="Beer-battered onion rings"),
            Item(name="Caesar Salad", price=7.49, description="Romaine lettuce with parmesan and croutons"),
            Item(name="Milkshake", price=4.99, description="Thick and creamy - vanilla, chocolate, or strawberry"),
            Item(name="Soda", price=1.99, description="Coca-Cola, Sprite, or Fanta"),
            Item(name="Pizza Slice", price=3.49, description="New York style cheese pizza"),
            Item(name="Hot Dog", price=4.49, description="All-beef hot dog with your choice of toppings"),
        ]
        db.add_all(items)
        db.commit()
        logger.info(f"Created {len(items)} items")

        # Seed Orders WITH OrderItems
        logger.info("Seeding orders with items...")

        # Order 1
        order1 = Order(status=OrderStatus.DONE, user_id=1, phone_num="555-0101")
        db.add(order1)
        db.flush()  # Get order1.id

        # Order 2
        order2 = Order(status=OrderStatus.DONE, user_id=2, phone_num="555-0102")
        db.add(order2)
        db.flush()  # Get order2.id

        # Order 3
        order3 = Order(status=OrderStatus.PENDING, user_id=3, phone_num="555-0103")
        db.add(order3)
        db.flush()  # Get order3.id

        # Order 4
        order4 = Order(status=OrderStatus.DONE, user_id=4, phone_num="555-0104")
        db.add(order4)
        db.flush()

        # Order 5
        order5 = Order(status=OrderStatus.CANCELLED, user_id=1, phone_num="555-0101")
        db.add(order5)
        db.flush()

        # Order 6
        order6 = Order(status=OrderStatus.DONE, user_id=5, phone_num="555-0105")
        db.add(order6)
        db.flush()

        # Order 7
        order7 = Order(status=OrderStatus.PENDING, user_id=2, phone_num="555-0102")
        db.add(order7)
        db.flush()

        # Add items to orders WITH PRICES
        logger.info("Adding items to orders...")
        order_items = [
            # Order 1 items
            OrderItem(order_id=order1.id, item_id=1, quantity=2, price_at_order=8.99),  # 2 burgers
            OrderItem(order_id=order1.id, item_id=4, quantity=1, price_at_order=3.99),  # 1 fries

            # Order 2 items
            OrderItem(order_id=order2.id, item_id=2, quantity=1, price_at_order=7.99),  # 1 chicken sandwich
            OrderItem(order_id=order2.id, item_id=7, quantity=1, price_at_order=4.99),  # 1 milkshake

            # Order 3 items
            OrderItem(order_id=order3.id, item_id=3, quantity=1, price_at_order=6.99),  # 1 veggie wrap
            OrderItem(order_id=order3.id, item_id=5, quantity=1, price_at_order=4.99),  # 1 onion rings
            OrderItem(order_id=order3.id, item_id=8, quantity=2, price_at_order=1.99),  # 2 sodas

            # Order 4 items
            OrderItem(order_id=order4.id, item_id=9, quantity=2, price_at_order=3.49),  # 2 pizza slices

            # Order 5 items (cancelled order)
            OrderItem(order_id=order5.id, item_id=10, quantity=1, price_at_order=4.49),  # 1 hot dog

            # Order 6 items
            OrderItem(order_id=order6.id, item_id=1, quantity=1, price_at_order=8.99),  # 1 burger
            OrderItem(order_id=order6.id, item_id=4, quantity=2, price_at_order=3.99),  # 2 fries
            OrderItem(order_id=order6.id, item_id=7, quantity=1, price_at_order=4.99),  # 1 milkshake

            # Order 7 items
            OrderItem(order_id=order7.id, item_id=6, quantity=1, price_at_order=7.49),  # 1 caesar salad
        ]
        db.add_all(order_items)
        db.commit()

        logger.info(f"Created 7 orders with {len(order_items)} order items")

        # Seed Reviews
        logger.info("Seeding reviews...")
        reviews = [
            # Approved reviews
            Review(rating=5, comment="Best burger in town! Will definitely order again.",
                   user_id=1, item_id=1, status=ReviewStatus.APPROVED),
            Review(rating=4, comment="Really good chicken sandwich, crispy and flavorful.",
                   user_id=2, item_id=2, status=ReviewStatus.APPROVED),
            Review(rating=5, comment="Love the veggie wrap! Fresh ingredients and great taste.",
                   user_id=3, item_id=3, status=ReviewStatus.APPROVED),
            Review(rating=4, comment="Fries were hot and crispy, perfect!",
                   user_id=4, item_id=4, status=ReviewStatus.APPROVED),

            # Pending reviews (waiting for admin approval)
            Review(rating=5, comment="Amazing milkshake! So thick and creamy.",
                   user_id=5, item_id=7, status=ReviewStatus.PENDING),
            Review(rating=3, comment="Pizza was okay, but a bit cold when it arrived.",
                   user_id=1, item_id=9, status=ReviewStatus.PENDING),
            Review(rating=4, comment="Great hot dog, love the toppings selection.",
                   user_id=2, item_id=10, status=ReviewStatus.PENDING),

            # Rejected reviews (inappropriate content)
            Review(rating=1, comment="This place is terrible! Never ordering again!",
                   user_id=3, item_id=1, status=ReviewStatus.REJECTED),
            Review(rating=2, comment="Food took forever and was cold.",
                   user_id=4, item_id=2, status=ReviewStatus.REJECTED),
        ]
        db.add_all(reviews)
        db.commit()
        logger.info(f"Created {len(reviews)} reviews")

        logger.info("✅ Database seeding completed successfully!")
        logger.info(f"   - {len(users)} users")
        logger.info(f"   - {len(items)} items")
        logger.info(f"   - 7 orders with {len(order_items)} order items")
        logger.info(f"   - {len(reviews)} reviews")

    except Exception as e:
        logger.error(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()