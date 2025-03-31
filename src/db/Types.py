from enum import Enum


class OrderStatus(str, Enum):
    PROCESSING = "processing"
    PREPARING = "preparing"
    PACKING = "packing"
    HANDED_DELIVERY = "handed_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order_Size(str, Enum):
    LARGE = "large"
    MEDIUM = "medium"
    SMALL = "small"


class Delivery_Type(str, Enum):
    HOME_DELIVERY = "home_delivery"
    TAKEOUT = "takeout"
    DINE_IN = "dine_in"


class Payment_Method(str, Enum):
    UPI = "UPI"
    NEFT = "NEFT"
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    CASH = "Cash"


class Payment_Status(str, Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"


class Food_Type(str, Enum):
    PIZZA = "Pizza"
    APPETIZERS_AND_SIDES = "Appetizers & Sides"
    PASTA = "Pasta Dishes"
    SALADS = "Salads"
    BEVERAGE = "Beverages"
    DESSERTS = "Desserts"
    SANDWICH_AND_SUBS = "Sandwiches & Subs"
    CALZONES_AND_STROMBOLIS = "Calzones & Strombolis"
    OTHER = "Others"


class User_Roles(str, Enum):
    CUSTOMER = "customer"
    STAFF = "staff"
    MANAGER = "manager"
    ADMIN = "admin"


class Staff_Roles(str, Enum):
    KITCHEN = "kitchen staff / chef"
    DELIVERY = "delivery personnel"
    WAITER = "wait staff / server"
    MANAGER = "manager"
