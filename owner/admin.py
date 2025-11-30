import secrets

from sqladmin import Admin, ModelView, action
from Database.dbConnect import engine
from Database.dbModels import User, Item, Order, Review, OrderItem, OrderStatus, Admin as AdminModel
import stripe
from Database.dbConnect import SessionLocal
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from middleware.security import verify_password, create_access_token, decode_access_token
import os
from dotenv import load_dotenv

from owner.notifications import notify_order_cancelled

load_dotenv()
import datetime


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        """Handle admin login"""
        form = await request.form()
        email = form.get("username")  # sqladmin uses "username" field
        password = form.get("password")

        db = SessionLocal()
        try:
            # Check if admin exists
            admin = db.query(AdminModel).filter(AdminModel.email == email).first()

            if not admin:
                return False

            # Verify password
            if not verify_password(password, admin.password):
                return False

            # Create token and store in session
            request.session["admin_email"] = admin.email
            request.session["is_admin"] = True

            return True

        finally:
            db.close()

    async def logout(self, request: Request) -> bool:
        """Handle admin logout"""
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """Check if user is authenticated"""
        admin_email = request.session.get("admin_email")
        is_admin = request.session.get("is_admin", False)

        if not admin_email or not is_admin:
            return False

        # Verify admin still exists
        db = SessionLocal()
        try:
            admin = db.query(AdminModel).filter(AdminModel.email == admin_email).first()
            return admin is not None
        finally:
            db.close()

#How admin sees users
class UserAdmin(ModelView, model=User):
    column_list = [User.user_id, User.name, User.email, User.orders]
    column_searchable_list = [User.name, User.email]
    column_sortable_list = [User.user_id, User.name]
    column_details_exclude_list = [User.password] #hides passwords
    can_edit = True
    can_delete = True
    can_create = True
    name = "User"
    name_plural = "Users"
    icon = "fa-user"

class ItemAdmin(ModelView, model=Item):
    column_list = [Item.id, Item.name, Item.description, Item.price]
    column_searchable_list = [Item.name, Item.description, Item.price]
    column_sortable_list = [Item.id, Item.name, Item.description, Item.price]
    can_create = True
    can_edit = True
    can_delete = True
    can_update = True
    name = "Item"
    name_plural = "Items"
    icon = "fa-user fa-fries"

class OrderAdmin(ModelView, model=Order):
    column_list = [Order.id, Order.user, Order.status, Order.phone_num, Order.order_items, Order.payment_status]
    column_searchable_list = [Order.phone_num]
    column_sortable_list = [Order.id, Order.status]
    can_edit = True
    can_delete = True
    name = "Order"
    name_plural = "Orders"
    icon = "fa-receipt"

    @action(
        name="approve_refund",
        label="✅ Approve & Refund",
        add_in_detail=True,
        add_in_list=True
    )
    async def approve_refund(self, request):
        """Admin approves cancellation and processes refund with one click"""

        pks = request.query_params.get("pks", "").split(",")

        db = SessionLocal()
        messages = []

        try:
            for pk in pks:
                if not pk:
                    continue

                order = db.query(Order).filter(Order.id == int(pk)).first()

                if not order:
                    messages.append(f"Order #{pk} not found")
                    continue

                refund_amount = None

                # Process Stripe refund if paid
                if order.payment_status == "paid" and order.stripe_session_id:
                    try:
                        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
                        stripe_session = stripe.checkout.Session.retrieve(order.stripe_session_id)
                        refund = stripe.Refund.create(
                            payment_intent=stripe_session.payment_intent
                        )
                        refund_amount = refund.amount / 100
                        order.payment_status = "refunded"
                        messages.append(f"Order #{pk}: Refunded ${refund_amount:.2f}")
                    except stripe.error.StripeError as e:
                        messages.append(f"Order #{pk}: Refund failed - {str(e)}")
                        continue
                else:
                    messages.append(f"Order #{pk}: No payment to refund")

                # Update order status
                order.status = OrderStatus.CANCELLED
                if not order.cancelled_at:
                    order.cancelled_at = datetime.utcnow()

                db.commit()

                # Send notification
                notify_order_cancelled(order.phone_num, order.id, refund_amount)

            from starlette.responses import RedirectResponse
            # Redirect back to order list
            return RedirectResponse(url="/admin/order", status_code=302)

        except Exception as e:
            messages.append(f"Error: {str(e)}")
            db.rollback()
            from starlette.responses import RedirectResponse
            return RedirectResponse(url="/admin/order", status_code=302)
        finally:
            db.close()

    @action(
        name="deny_cancellation",
        label="❌ Deny Cancellation",
        add_in_detail=True,
        add_in_list=True
    )
    async def deny_cancellation(self, request):
        """Admin denies cancellation request"""
        from Database.dbConnect import SessionLocal
        from starlette.responses import RedirectResponse

        pks = request.query_params.get("pks", "").split(",")

        db = SessionLocal()
        try:
            for pk in pks:
                if not pk:
                    continue

                order = db.query(Order).filter(Order.id == int(pk)).first()

                if order and order.status == OrderStatus.CANCEL_REQUEST:
                    order.status = OrderStatus.PENDING
                    order.cancelled_at = None
                    db.commit()

            return RedirectResponse(url="/admin", status_code=302)
        finally:
            db.close()
class ReviewAdmin(ModelView, model=Review):
    column_list = [Review.id, Review.status, Review.rating, Review.user_id, Review.item_id]
    column_searchable_list = [Review.user_id, Review.rating]
    column_sortable_list = [Review.id, Review.user_id, Review.rating]
    can_edit = True
    can_delete = True
    name = "Review"
    name_plural = "Reviews"
    icon = "fa-user fa-receipt"

class OrderItemAdmin(ModelView, model=OrderItem):
    column_list = [OrderItem.id, OrderItem.order_id, OrderItem.item, OrderItem.quantity, OrderItem.price_at_order]
    column_searchable_list = [OrderItem.order_id]
    column_sortable_list = [OrderItem.id, OrderItem.order_id, OrderItem.quantity]
    can_edit = True
    can_delete = True
    name = "Order Item"
    name_plural = "Order Items"
    icon = "fa-shopping-cart"

def setup_admin(app):
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        secret_key = secrets.token_urlsafe(32)
    authentication_backend = AdminAuth(secret_key=secret_key)
    admin = Admin(app, engine, title='J-Bites Admin', authentication_backend=authentication_backend)

    admin.add_view(UserAdmin)
    admin.add_view(ItemAdmin)
    admin.add_view(OrderAdmin)
    admin.add_view(ReviewAdmin)
    admin.add_view(OrderItemAdmin)
    return admin