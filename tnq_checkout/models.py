from elixir import *
from elixir import options
import sqlalchemy
from sqlalchemy import MetaData
from sqlalchemy.sql.expression import func
from sqlextensions import Enum

old_create_engine = sqlalchemy.create_engine
def my_create_engine(*args, **kwargs):
    if 'pool_recycle' in kwargs:
        kwargs['pool_recycle'] = int(kwargs['pool_recycle'])
    return old_create_engine(*args, **kwargs)
sqlalchemy.create_engine = my_create_engine

options.MULTIINHERITANCECOL_NAMEFORMAT = "%(key)s"

__metadata__ = MetaData()

# Here, put the definition of your Elixir or SQLAlchemy models

# Django base user class
class AuthUser(Entity):
    """AuthUser: Django's identity class."""
    using_options(tablename="auth_user")

    username = Field(String(30),required=True)
    username.__doc__ = "MIT kerberos name"

    first_name = Field(String(30),required=True)
    last_name = Field(String(30),required=True)
    full_name = ColumnProperty(lambda c: c.first_name + " " + c.last_name)

    email = Field(String(75),required=True)
    email.__doc__ = "The user's email can be something other than @mit.edu."

    password = Field(String(128),required=True)

    is_staff = Field(Boolean,required=True)
    is_active = Field(Boolean,required=True)
    is_superuser = Field(Boolean,required=True)

    last_login = Field(DATETIME,required=True)
    date_joined = Field(DATETIME,required=True)

class User(AuthUser):
    """User: The person who will be checking out equipment.

    Users can be split into two types, manboard or staph. Staph can only be responsible for equipment checked out, but
    manboard users can actually go through the checkout procedure.
    """
    using_options(tablename="checkout_user", inheritance="multi", polymorphic=False)

    barcode_id = Field(String(9),required=False,unique=True)
    barcode_id.__doc__ = "MIT ID number"

    phone = Field(String(20))

    checkouts = OneToMany('Checkout', inverse='user')

class Equipment(Entity):
    """Equipment: What the User will be checking out.
    
    Equipment can be anything we slap a barcode on...cameras, tripods, batteries, memory, lighting, umbrellas, whatever...
    """
    using_options(tablename="checkout_equipment")
    barcode_id = Field(String(7),required=True,unique=True)
    barcode_id.__doc__ = "(required) 7 digit string starting with TNQ and ending with 4 numbers. Ex: TNQ1234"
    equip_type = Field(Enum([u'CAMERA', u'LENS', u'MEMORY', u'EXTERNAL_FLASH', u'STROBE', u'TRIPOD', u'MONOPOD', u'ACCESSORY',u'35MM_CAMERA',u'MEDIUM_FORMAT_CAMERA',u'LARGE_FORMAT_CAMERA',u'SNAX',None]),required=True)
    pet_name = Field(String(30))
    pet_name.__doc__ = "(optional) The name given to the equipment by TNQ Staph."
    brand = Field(String(30),required=True)
    model = Field(String(128))
    checkout_hours = Field(Integer)
    full_name = ColumnProperty(lambda c: func.concat_ws(" ", c.brand, c.model, func.concat("(", c.pet_name, ")")))
    description = Field(String(500))
    manual_link = Field(String(256))
    manual_link.__doc__ = "link to the pdf manual of the equipment"
    checkouts = OneToMany('Checkout')
    serial = Field(String(128))
    notes = Field(String(500))

class Checkout(Entity):
    using_options(tablename="checkout_checkout")
    user = ManyToOne('User')
    equipment = ManyToOne('Equipment')
    manboard_member = ManyToOne('User')
    manboard_member.__doc__ = "the manboard member who checked out the equipment for the staph"
    date_out = Field(DATETIME)
    date_due = Field(DATETIME)
    date_in = Field(DATETIME)

