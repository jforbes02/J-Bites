from sqladmin import Admin, ModelView
from Database.dbConnect import engine
from Database.dbModels import User, Item, Order, Review


#How admin sees users
class UserAdmin(ModelView, model=User):
    #TODO: See and delete User reviews
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
    column_list = [Order.id, Order.user, Order.status]
    column_searchable_list = [Order.user, Order.status]
    column_sortable_list = [Order.id, Order.user, Order.status]
    can_edit = True
    can_delete = True
    name = "Order"
    name_plural = "Orders"
    icon = "fa-user fa-receipt"

class ReviewAdmin(ModelView, model=Review):
    column_list = [Review.id, Review.rating, Review.user_id, Review.item_id]
    column_searchable_list = [Review.user_id, Review.rating]
    column_sortable_list = [Review.id, Review.user_id, Review.rating]
    can_edit = True
    can_delete = True
    name = "Review"
    name_plural = "Reviews"
    icon = "fa-user fa-receipt"

def setup_admin(app):
    admin = Admin(app, engine, title='J-Bites Admin')

    admin.add_view(UserAdmin)
    admin.add_view(ItemAdmin)
    admin.add_view(OrderAdmin)
    admin.add_view(ReviewAdmin)
    return admin