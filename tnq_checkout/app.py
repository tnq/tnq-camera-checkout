from __future__ import with_statement

import os
import datetime
from nagare import presentation, component, util, var, log
from .models import *
from .barcode import *


class TaskSelector(object):
    """ TaskSelector provides the choice to either "borrow" or "return" equipment
    """
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
    with h.form(class_="confirm"):
        h << h.div(self.msg, class_="message")
        for i, button in enumerate(self.buttons):
            h << h.input(type='submit', value=button).action(lambda i=i: comp.answer(i))
    return h.root


class UserList(object):
    """ Displays a list of TNQ users
    """
    pass

@presentation.render_for(UserList)
def render(self, h, comp, *args):
    users = User.query.order_by(User.last_name, User.first_name)
    
    h.head.javascript_url('/static/tnq_checkout/scripts/scrollview.js')
    h.head.javascript_url('/static/tnq_checkout/scripts/vanillaos.js')
    
    with h.div(class_="scrollview-container",scrollviewbars="none",scrollviewmode="table",scrollviewenabledscrollx="no"):
        with h.div(class_="scrollview-content"):
            for u in users:
                with h.div(class_="scrollview-item"):
                    h << h.a(u.first_name + " " + u.last_name).action(lambda u=u: comp.answer(u))
    return h.root


class SelectStaph(object):
    def __init__(self, manboard_name):
        self.scan = component.Component(ScanUserBarcode(["<strong>"+manboard_name+"</strong> is checking out equipment for...","Select staph below or scan MIT ID"]))
        self.list = component.Component(UserList())

@presentation.render_for(SelectStaph)
def render(self, h, comp, *args):
    self.scan.on_answer(comp.answer)
    self.list.on_answer(comp.answer)
    with h.div(class_="vpane"):
        h << self.scan
    with h.div(class_="vpane"):
        h << self.list

    return h.root


class SelectEquipment(object):
    def __init__(self, manboard_name="", staph_name=""):
        self.scan = component.Component(ScanEquipmentBarcode(["<strong>"+manboard_name+"</strong> is checking out equipment for <strong>"+staph_name+"</strong>.","scan equipment"]))
        self.equipment = []
        self.scan.on_answer(self.add_equipment)

    def add_equipment(self, equipment):
        if equipment not in self.equipment:
            self.equipment.insert(0, equipment)

    def remove_equipment(self, equipment):
        self.equipment.remove(equipment)

@presentation.render_for(SelectEquipment)
def render(self, h, comp, *args):
    h << self.scan
    
    h.head.javascript_url('/static/tnq_checkout/scripts/scrollview.js')
    h.head.javascript_url('/static/tnq_checkout/scripts/vanillaos.js')
    
    with h.div(class_="scrollview-container equipment",scrollviewbars="none",scrollviewmode="table",scrollviewenabledscrollx="no"):
        with h.div(class_="scrollview-content"):
            for e in self.equipment:
                with h.div(class_="scrollview-item scrollview-disabledrag ui-helper-clearfix"):
                    h << h.img(src="/static/tnq_checkout/images/icons/"+e.equip_type+".svg", width="91", height="80",class_="icon")
                    with h.div:
                        h << e.brand
                        h << " "
                        h << e.model
                        h << " "
                        h << h.strong(e.pet_name)
                    h << h.a("X").action(lambda e=e: self.remove_equipment(e))
    with h.div(class_="finish-checkout"):
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
        manboard_user = comp.call(ScanUserBarcode(["Scan manboard member's barcode", "Typically, the barcode on the back of an MIT ID card."]), model="manboard")
        if not manboard_user.is_staff:
            comp.call(Confirm("You must be a manboard member to authorize a checkout."))
        else:
            staph_user = comp.call(SelectStaph(manboard_user.full_name))
            equipment_select = SelectEquipment(manboard_user.full_name, staph_user.full_name)
            checkout_ready = False
            while not checkout_ready:
                items = comp.call(equipment_select)
                checkout_ready = True
                for item in items:
                    existing_checkout = Checkout.get_by(equipment=item,date_in=None)
                    if existing_checkout:
                        choice = comp.call(Confirm("%s is currently checked out to %s. Do you want to check it in for them?" %
                                                   (item.brand+" "+item.model+(" ("+item.pet_name+")" if item.pet_name else ""),existing_checkout.user.full_name),
                                                   buttons=["Yes", "No"]))
                        if choice == 0:
                            existing_checkout.date_in = datetime.datetime.now()
                        else:
                            equipment_select.remove_equipment(item)
                            checkout_ready = False
            for item in items:
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
        #self.body.on_answer(lambda r:self.answer(r))

@presentation.render_for(TaskWrapper)
def render(self, h, comp, *args):
    if not self.body._channel:
        self.body._channel = comp._channel
    with h.div(id='header',class_=self.label+" ui-helper-clearfix"):
        h << h.a("cancel").action(lambda: comp.answer())
        h << h.div(self.label, class_="task")
    h << self.body

    return h.root

class Tnq_checkout(object):
    def __init__(self):
        self.body = component.Component(RootView())


@presentation.render_for(Tnq_checkout)
def render(self, h, *args):
    h.head.css_url('/static/tnq_checkout/styles/jquery-ui-core.css')
    h.head.css_url('/static/tnq_checkout/styles/base.css')
    h.head.javascript_url('https://ajax.googleapis.com/ajax/libs/jquery/1.6.0/jquery.min.js')
    h.head.javascript_url('/static/tnq_checkout/scripts/scrollview.js')
    h.head.javascript_url('/static/tnq_checkout/scripts/vanillaos.js')
    h.head << h.head.title('Technique Checkout')

    with h.div(id='content'):
        h << self.body

    return h.root

# ---------------------------------------------------------------

app = Tnq_checkout
