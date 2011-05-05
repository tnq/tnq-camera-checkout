from __future__ import with_statement

import os
from nagare import presentation, component, util, var
from .models import *

class TaskSelector(object):
    pass

@presentation.render_for(TaskSelector)
def render(self, h, comp, *args):
    with h.div(class_='big-button'):
        h << h.a('Borrow Equipment').action(lambda: comp.answer("borrow"))
    with h.div(class_='big-button'):
        h << h.a('Return Equipment').action(lambda: comp.answer("return"))

    return h.root

class ScanBarcode(object):
    def __init__(self, message):
        self.message = message
    def handle_scan(self, comp, barcode):
        pass
@presentation.render_for(ScanBarcode)
def render(self, h, comp, *args):
    r = var.Var()
    return h.form(
                  self.message, ' ',
                  h.input.action(r),
                  h.input(type='submit', value='Send').action(lambda: self.handle_scan(comp, r()))
                 ) 

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
                h << h.td(h.a(u.first_name + " " + u.last_name).action(lambda: comp.answer(u)))
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
                manboard_user = comp.call(ScanUserBarcode("Scan manboard member's barcode"))
                if manboard_user.user_type != u'MANBOARD':
                    comp.call(util.Confirm("You must be a manboard member to authorize a checkout."))
                else:
                    staph_user = comp.call(SelectUser())
                    items = comp.call(SelectEquipment())
                    comp.call(util.Confirm("Manboard member "+manboard_user.full_name+" checking out equipment for "+staph_user.full_name+": "+items))
            comp.call(util.Confirm(task))

class Tnq_checkout(object):
    def __init__(self):
        self.body = component.Component(RootView())

@presentation.render_for(Tnq_checkout)
def render(self, h, *args):
    h.head.css_url('/static/nagare/application.css')
    h.head << h.head.title('Up and Running !')

    with h.div(class_='mybody'):
        with h.div(id='main'):
            h << self.body

    h << h.div(class_='footer')

    return h.root

# ---------------------------------------------------------------

app = Tnq_checkout