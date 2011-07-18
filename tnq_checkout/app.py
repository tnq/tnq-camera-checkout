from __future__ import with_statement

import os
import datetime
from nagare import presentation, component, util, var, log
from .models import *
from .barcode import *

from smtplib import SMTP

def sendCheckoutConfirmEmail(staph_user,manboard_user,equipment):
    from_name = 'H.R.H. Grogo'
    from_email = 'hrhgrogo@mit.edu'
    subject = '[Technique Checkouts] Confirmation of Checkout'
    headers = """From: %s <%s>\nTo: %s <%s>\nCc: %s <%s>\nSubject: %s\n\n""" % (from_name,from_email,
                                       staph_user.full_name,staph_user.email,
                                       manboard_user.full_name,manboard_user.email,
                                       subject)
    message = """Hello %s,

You've checked out the following equipment from Technique:

============================================================

%s

============================================================

Laters,
--H.R.H. Grogo

P.S. %s was the manboard member who checked it out for you.""" % (
        staph_user.first_name,
        "\n".join(e.full_name for e in equipment),
        manboard_user.full_name)
    connection = SMTP()
    connection.connect("outgoing.mit.edu")
    connection.sendmail(from_email, ", ".join((staph_user.email,manboard_user.email)), headers+message)
    connection.close()


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
            h << h.input(type='submit', value=button, class_="button-%s"%(i)).action(lambda i=i: comp.answer(i))
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
        self.scan = component.Component(ScanUserBarcode(["<strong>%s</strong> is checking out equipment for..."%(manboard_name),"Select staph below or scan MIT ID"]))
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
    def __init__(self, manboard=None, staph=None):
        self.manboard = manboard
        self.staph = staph
        if manboard:
            if manboard == staph:
                prompt = "<strong>%s</strong> is checking out equipment."%(manboard.full_name)
            else:
                prompt = "<strong>%s</strong> is checking out equipment for <strong>%s</strong>."%(manboard.full_name,staph.full_name)
            self.scan = component.Component(ScanEquipmentBarcode([prompt,"scan equipment"]))
            self.final_action = "Finish Checkout"
            self.selected_task = "borrow"
        else:
            self.scan = component.Component(ScanEquipmentBarcode([" ","scan equipment to return"]))
            self.final_action = "Return Equipment"
            self.selected_task = "return"
        self.equipment = []
        self.scan.on_answer(self.add_equipment)

    def add_equipment(self, equipment):
        if equipment not in self.equipment:
            self.equipment.insert(0, equipment)

    def remove_equipment(self, equipment):
        self.equipment.remove(equipment)

    def confirm(self, equipment_list):
        self.final_action = "Okay"
        self.selected_task = "confirm"
        self.equipment = equipment_list

@presentation.render_for(SelectEquipment)
def render(self, h, comp, *args):
    if self.selected_task == "confirm":
        with h.div(class_="message message-1 confirm"):
            h << "%s has checked out:" % (self.staph.first_name)
    else:
        h << self.scan
    
    h.head.javascript_url('/static/tnq_checkout/scripts/scrollview.js')
    h.head.javascript_url('/static/tnq_checkout/scripts/vanillaos.js')
    
    with h.div(class_="scrollview-container equipment %s"%(self.selected_task),scrollviewbars="none",scrollviewmode="table",scrollviewenabledscrollx="no"):
        with h.div(class_="scrollview-content"):
            for e in self.equipment:
                with h.div(class_="scrollview-item scrollview-disabledrag ui-helper-clearfix"):
                    
                    h << h.img(src="/static/tnq_checkout/images/icons/%s.svg"%(e.equip_type),class_="icon")
                    with h.div(class_="name"):
                        h << e.brand
                        if e.model:
                            h << " "
                            h << e.model
                        if e.pet_name:
                            h << h.strong("(%s)" % (e.pet_name))
                    if self.selected_task == "confirm":
                        with h.div(class_="due"):
                            h << h.strong("Due: ")
                            h << "6 days"
                    else:
                        h << h.a("X",class_="ex").action(lambda e=e: self.remove_equipment(e))
    with h.div(class_="finish-checkout"):
        h << h.a(self.final_action ).action(lambda: comp.answer(self.equipment))

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
            equipment_select = SelectEquipment(manboard_user, staph_user)
            checkout_ready = False
            while not checkout_ready:
                items = comp.call(equipment_select)
                checkout_ready = True
                for item in items:
                    existing_checkout = Checkout.get_by(equipment=item,date_in=None)
                    if existing_checkout:
                        choice = 0;
                        if staph_user != existing_checkout.user:
                            choice = comp.call(Confirm("%s is currently checked out to %s. Do you want to check it in for them?" %
                                                   (item.full_name,existing_checkout.user.full_name),
                                                   buttons=["Yes", "No"]))
                        if choice == 0:
                            existing_checkout.date_in = datetime.datetime.now()
                        else:
                            equipment_select.remove_equipment(item)
                            checkout_ready = False
            sendCheckoutConfirmEmail(staph_user,manboard_user,items)
            for item in items:
                checkout = Checkout()
                checkout.user = staph_user
                checkout.equipment = item
                checkout.manboard_member = manboard_user
                checkout.date_out = datetime.datetime.now()
            equipment_select.confirm(items)
            comp.call(equipment_select)


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
