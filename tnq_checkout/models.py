from elixir import *
from sqlalchemy import MetaData
from sqlextensions import Enum

__metadata__ = MetaData()

# Here, put the definition of your Elixir or SQLAlchemy models

class User(Entity):
    """User: The person who will be checking out equipment.
    
    Users can be split into two types, manboard or staph. Staph can only be responsible for equipment checked out, but
    manboard users can actually go through the checkout procedure.
    """
    barcode_id = Field(String(9),required=True,unique=True)
    barcode_id.__doc__ = "(required) MIT ID number"
    user_type = Field(Enum([u'STAPH', u'MANBOARD',None]),required=True,default=u'STAPH')
    first_name = Field(String(30),required=True)
    last_name = Field(String(30),required=True)
    full_name = ColumnProperty(lambda c: c.first_name + " " + c.last_name)
    krb_name = Field(String(8))
    krb_name.__doc__ = "(optional) MIT kerberos name, if available."
    phone = Field(String(20))
    email = Field(String(254),required=True)
    email.__doc__ = "The user's email can be something other than @mit.edu."
    checkouts = OneToMany('Checkout', inverse='user')

class Equipment(Entity):
    """Equipment: What the User will be checking out.
    
    Equipment can be anything we slap a barcode on...cameras, tripods, batteries, memory, lighting, umbrellas, whatever...
    """
    barcode_id = Field(String(7),required=True,unique=True)
    barcode_id.__doc__ = "(required) 7 digit string starting with TNQ and ending with 4 numbers. Ex: TNQ1234"
    equip_type = Field(Enum([u'CAMERA', u'LENS', u'MEMORY', u'EXTERNAL_FLASH', u'STROBE', u'TRIPOD', u'MONOPOD', u'ACCESSORY',u'35MM_CAMERA',u'MEDIUM_FORMAT_CAMERA',u'LARGE_FORMAT_CAMERA',None]),required=True)
    pet_name = Field(String(30))
    pet_name.__doc__ = "(optional) The name given to the equipment by TNQ Staph."
    brand = Field(String(30),required=True)
    model = Field(String(128))
    description = Field(String(500))
    manual_link = Field(String(256))
    manual_link.__doc__ = "link to the pdf manual of the equipment"
    checkouts = OneToMany('Checkout')
    serial = Field(String(128))
    notes = Field(String(500))

class Checkout(Entity):
    user = ManyToOne('User')
    equipment = ManyToOne('Equipment')
    manboard_member = ManyToOne('User')
    manboard_member.__doc__ = "the manboard member who checked out the equipment for the staph"
    date_out = Field(DateTime)
    date_in = Field(DateTime)

