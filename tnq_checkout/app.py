from __future__ import with_statement

import os
import datetime
from nagare import presentation, component, util, var
from .models import *

class TaskSelector(object):
    pass

@presentation.render_for(TaskSelector)
def render(self, h, comp, *args):
    with h.div(class_='task-selector ui-helper-clearfix'):
        with h.div(class_='borrow'):
            h << h.a('borrow').action(lambda: comp.answer("borrow"))
        with h.div(class_='return'):
            h << h.a('return').action(lambda: comp.answer("return"))
    return h.root

class Confirm(object):
    """Display a confirmation message, with buttons
    """

    def __init__(self, msg, buttons = ["ok"]):
        """Initialization

        In:
          - ``msg`` -- message to display
        """
        self.msg = msg
        self.buttons = buttons

@presentation.render_for(Confirm)
def render(self, h, comp, *args):
    """The view is a simple form with the text and multiple submit buttons

    In:
      - ``h`` -- the renderer
      - ``comp`` -- the component
      - ``model`` -- the name of the view

    Return:
      - a tree
    """
    with h.form:
        h << self.msg
        h << h.br
        for i, button in enumerate(self.buttons):
            h << h.input(type='submit', value=button).action(lambda i=i: comp.answer(i))
    return h.root

class ScanBarcode(object):
    def __init__(self, message):
        self.message = message
    def handle_scan(self, comp, barcode):
        pass

@presentation.render_for(ScanBarcode)
def render(self, h, comp, *args):
    r = var.Var()
    h.head.javascript_url('https://ajax.googleapis.com/ajax/libs/jquery/1.6.0/jquery.min.js')
    h << h.script('''$(function(){
                    $('#barcodeInput').focus();
                    });''', type='text/javascript')
    h << h.form(
                  self.message, ' ',
                  h.input(id='barcodeInput').action(r),
                  h.input(type='submit', value='Send').action(lambda: self.handle_scan(comp, r()))
                 ) 
    return h.root

class ScanUserBarcode(ScanBarcode):
    def handle_scan(self, comp, barcode):
        user = User.get_by(barcode_id=barcode)
        if user:
            comp.answer(user)

class ScanEquipmentBarcode(ScanBarcode):
    def handle_scan(self, comp, barcode):
        equip = Equipment.get_by(barcode_id=barcode)
        if equip:
            comp.answer(equip)

class UserList(object):
    pass

@presentation.render_for(UserList)
def render(self, h, comp, *args):
    users = User.query.order_by(User.last_name, User.first_name)
    with h.table:
        for u in users:
            with h.tr:
                h << h.td(h.a(u.first_name + " " + u.last_name).action(lambda u=u: comp.answer(u)))
    return h.root

class SelectUser(object):
    def __init__(self):
        self.scan = component.Component(ScanUserBarcode("Select user or scan user's barcode"))
        self.list = component.Component(UserList())

@presentation.render_for(SelectUser)
def render(self, h, comp, *args):
    self.scan.on_answer(comp.answer)
    self.list.on_answer(comp.answer)
    with h.div(class_="vpane"):
        h << self.scan
    with h.div(class_="vpane"):
        h << self.list

    return h.root

class SelectEquipment(object):
    def __init__(self):
        self.scan = component.Component(ScanEquipmentBarcode("Scan the barcode for each piece of equipment to add it to your checkout"))
        self.equipment = []
        self.scan.on_answer(self.add_equipment)

    def add_equipment(self, equipment):
        if equipment not in self.equipment:
            self.equipment.append(equipment)

    def remove_equipment(self, equipment):
        self.equipment.remove(equipment)

@presentation.render_for(SelectEquipment)
def render(self, h, comp, *args):
    h << self.scan
    h << h.h1("Current equipment list")
    with h.table:
        for e in self.equipment:
            with h.tr:
                with h.td:
                    h << "%s (%s %s)" % (e.pet_name, e.brand, e.model)
                with h.td:
                    h << h.a("Remove").action(lambda: self.remove_equipment(e))
    h << h.a("Finish checkout").action(lambda: comp.answer(self.equipment))

    return h.root

class RootView(component.Task):
    def go(self, comp):
        while True:
            task = comp.call(TaskSelector())
            if task == "borrow":
                comp.call(TaskWrapper("borrow", component.Component(BorrowTask())))
            elif task == "return":
                comp.call(TaskWrapper("return", component.Component(ReturnTask())))

class BorrowTask(component.Task):
    def go(self, comp):
        manboard_user = comp.call(ScanUserBarcode("Scan manboard member's barcode"))
        if manboard_user.user_type != u'MANBOARD':
            comp.call(util.Confirm("You must be a manboard member to authorize a checkout."))
        else:
            staph_user = comp.call(SelectUser())
            items = comp.call(SelectEquipment())
            for item in items:
                existing_checkout = Checkout.get_by(equipment=item,date_in=None)
                if existing_checkout:
                    choice = comp.call(Confirm("%s is currently checked out to %s. Do you want to check it in for them?" %
                                               (item.brand+" "+item.model+(" ("+item.pet_name+")" if item.pet_name else ""),existing_checkout.user.full_name),
                                               buttons=["Yes", "No"]))
                    if choice == 0:
                        existing_checkout.date_in = datetime.datetime.now()
                    else:
                        continue
                checkout = Checkout()
                checkout.user = staph_user
                checkout.equipment = item
                checkout.manboard_member = manboard_user
                checkout.date_out = datetime.datetime.now()

class ReturnTask(component.Task):
    def go(self, comp):
        returned_items = comp.call(SelectEquipment())
        for returned_item in returned_items:
            checkout = Checkout.get_by(equipment=returned_item,date_in=None)
            if checkout:
                checkout.date_in = datetime.datetime.now()

class TaskWrapper(object):
    def __init__(self, label, body):
        self.label = label
        self.body = body

@presentation.render_for(TaskWrapper)
def render(self, h, comp, *args):
    with h.div(id='header'):
        h << self.label
        h << h.a("cancel").action(lambda: comp.answer())
    h << self.body

    return h.root

class Tnq_checkout(object):
    def __init__(self):
        self.body = component.Component(RootView())

@presentation.render_for(Tnq_checkout)
def render(self, h, *args):
    h.head.css_url('/static/tnq_checkout/styles/jquery-ui-core.css')
    h.head.css_url('/static/tnq_checkout/styles/base.css')
    h.head << h.head.title('Technique Checkout')

    with h.div(id='content'):
        h << self.body

    return h.root

# ---------------------------------------------------------------

app = Tnq_checkout
