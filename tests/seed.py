from Database.dbConnect import SessionLocal, engine, Base
from Database.dbModels import User, Item, Order, Review, OrderStatus, ReviewStatus, OrderItem
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_database():
    """Seed the database with initial test data"""

    db = SessionLocal()

    try:
        logger.info("Starting database seeding...")

        # Reset database
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
            Item(name="Pan De Yuca", price=2.99,
                 description="Baked yuca bread filled with melted cheese, with a crispy exterior and soft interior"),
            Item(name="Empanada (Chicken/Potato)", price=3.99,
                 description="Fried patty made with our handmade crust. Filled with a mix of signature chicken and mashed potato"),
            Item(name="Empanada (Fusion Beef)", price=3.99,
                 description="Fried patty made with our handmade crust. Filled with an Asian-Latin Fusion shredded beef."),
            Item(name="Empanada (Cheese)", price=3.99,
                 description="Fried patty made with our handmade crust. Filled with melted queso blanco."),
            Item(name="Tres Leche (Original)", price=5.99,
                 description="Our signature mini tray of three milk sponge cake. Contains strawberries"),
            Item(name="Tres Leche (Oreo)", price=5.99,
                 description="Our signature mini tray of three milk sponge cake. Contains Oreo cookies"),
            Item(name="Tres Leche (Biscoff)", price=5.99,
                 description="Our signature mini tray of three milk sponge cake. Contains Biscoff cookies"),
            Item(name="Tres Leche (Maria)", price=5.99,
                 description="Our signature mini tray of three milk sponge cake. Contains Maria cookies"),
            Item(name="SEASONAL Tres Leche (Gingerbread)", price=5.99,
                 description="Our signature mini tray of three milk sponge cake. Contains Gingerbread"),
        ]
        db.add_all(items)
        db.commit()
        logger.info(f"Created {len(items)} items")

        # Seed Orders with OrderItems
        logger.info("Seeding orders with items...")

        orders = [
            Order(status=OrderStatus.DONE, user_id=1, phone_num="555-0101"),
            Order(status=OrderStatus.DONE, user_id=2, phone_num="555-0102"),
            Order(status=OrderStatus.PENDING, user_id=3, phone_num="555-0103"),
            Order(status=OrderStatus.DONE, user_id=4, phone_num="555-0104"),
            Order(status=OrderStatus.CANCELLED, user_id=1, phone_num="555-0101"),
            Order(status=OrderStatus.DONE, user_id=5, phone_num="555-0105"),
            Order(status=OrderStatus.PENDING, user_id=2, phone_num="555-0102"),
        ]

        for order in orders:
            db.add(order)
        db.flush()  # Assign IDs

        # Map orders to items
        order_items = [
            # Order 1
            OrderItem(order_id=orders[0].id, item_id=2, quantity=2, price_at_order=3.99),
            OrderItem(order_id=orders[0].id, item_id=4, quantity=1, price_at_order=3.99),

            # Order 2
            OrderItem(order_id=orders[1].id, item_id=3, quantity=1, price_at_order=3.99),
            OrderItem(order_id=orders[1].id, item_id=6, quantity=1, price_at_order=5.99),

            # Order 3
            OrderItem(order_id=orders[2].id, item_id=1, quantity=2, price_at_order=2.99),
            OrderItem(order_id=orders[2].id, item_id=5, quantity=1, price_at_order=5.99),

            # Order 4
            OrderItem(order_id=orders[3].id, item_id=9, quantity=2, price_at_order=5.99),

            # Order 5 (cancelled)
            OrderItem(order_id=orders[4].id, item_id=7, quantity=1, price_at_order=5.99),

            # Order 6
            OrderItem(order_id=orders[5].id, item_id=1, quantity=1, price_at_order=2.99),
            OrderItem(order_id=orders[5].id, item_id=4, quantity=2, price_at_order=3.99),
            OrderItem(order_id=orders[5].id, item_id=8, quantity=1, price_at_order=5.99),

            # Order 7
            OrderItem(order_id=orders[6].id, item_id=6, quantity=1, price_at_order=5.99),
        ]
        db.add_all(order_items)
        db.commit()
        logger.info(f"Created {len(orders)} orders with {len(order_items)} items")

        # Seed Reviews
        logger.info("Seeding reviews...")
        reviews = [
            # Approved reviews
            Review(rating=5, comment="Best Pan De Yuca in town!", user_id=1, item_id=1, status=ReviewStatus.APPROVED),
            Review(rating=4, comment="Chicken/Potato Empanada was great!", user_id=2, item_id=2, status=ReviewStatus.APPROVED),
            Review(rating=5, comment="Fusion Beef Empanada is amazing!", user_id=3, item_id=3, status=ReviewStatus.APPROVED),
            Review(rating=4, comment="Cheese Empanada was perfect.", user_id=4, item_id=4, status=ReviewStatus.APPROVED),

            # Pending reviews
            Review(rating=5, comment="Tres Leche Oreo is decadent!", user_id=5, item_id=6, status=ReviewStatus.PENDING),
            Review(rating=3, comment="Original Tres Leche okay, could be colder.", user_id=1, item_id=5, status=ReviewStatus.PENDING),
            Review(rating=4, comment="Biscoff Tres Leche is sweet but good.", user_id=2, item_id=7, status=ReviewStatus.PENDING),

            # Rejected reviews
            Review(rating=1, comment="Pan De Yuca was stale.", user_id=3, item_id=1, status=ReviewStatus.REJECTED),
            Review(rating=2, comment="Empanadas took too long.", user_id=4, item_id=2, status=ReviewStatus.REJECTED),
        ]
        db.add_all(reviews)
        db.commit()
        logger.info(f"Created {len(reviews)} reviews")

        logger.info("✅ Database seeding completed successfully!")

    except Exception as e:
        logger.error(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
