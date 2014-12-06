from email.utils import parseaddr
from datetime import (datetime, date)
from time import (strptime, strftime)
from sqlalchemy import not_
from pyramid.view import (
    view_config,
    )
from pyramid.httpexceptions import (
    HTTPFound,
    )
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
    )
    
from ..tools import (
    email_validator,
    BULANS
    )
    
from ..models import (
    DBSession
    )
    
    
from ..models.isipkd import (
    SptpdModel,
    UnitModel
    )

SESS_ADD_FAILED = 'gagal tambah data'
SESS_EDIT_FAILED = 'gagal edit data'

#######    
# Add #
#######

def form_validator(form, value):
    def err_no_rangka():
        raise colander.Invalid(form,
            'No Rangka Harus diisi' 
            )
    def err_nik():
        raise colander.Invalid(form,
            'NIK Harus diisi' 
            )
            
    def err_no_handphone():
        raise colander.Invalid(form,
            'No handphone harus diisi' 
            )
                                
    def err_no_handphone():
        raise colander.Invalid(form,
            'Kode validasi harus diisi' 
            )

def get_periode(year=True):
    adate = datetime.now()
    amonth = adate.month - 1
    amonth = amonth>0 and amonth or 12
    if year:
        ayear = amonth<12 and adate.year or adate.year-1
        return ayear
    else:
        print '***', amonth
        return amonth

def get_units():
    return DBSession.query(UnitModel).order_by(UnitModel.kode).all()
    
class PeriodeSchema(colander.Schema):
    
    tahun = colander.SchemaNode(
                    colander.Integer(),
                    default = get_periode()
                    )
                    
    bulan = colander.SchemaNode(
                    colander.Integer(),
                    default = get_periode(False),
                    widget=widget.SelectWidget(values=BULANS),
                    )
            
class AddSchema(colander.Schema):
    appstruct = {
        'readonly':'Read Only',
        'readwrite':'Read and Write',
        }
    @colander.deferred
    def deferred_missing(node, kw):
        return appstruct['readonly']
        
    no_tagihan = colander.SchemaNode(
                    colander.String(),
                    widget=widget.TextInputWidget(),
                    missing=deferred_missing,
                    )
     
    skpd       = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.SelectWidget(values=get_units()),
                    title = "SKPD"
                  )
    periode = PeriodeSchema()              
    omset = colander.SchemaNode(
                    colander.Decimal(),
                    widget=widget.MoneyInputWidget(
                           size=20, options={'allowZero':False})
                    )
    tarif = colander.SchemaNode(
                    colander.Decimal(),
                    widget=widget.MoneyInputWidget(
                           size=20, options={'allowZero':False})
                    )

    pokok_pajak = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.MoneyInputWidget(
                           size=20, options={'allowZero':False})
                    )

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    #schema = schema.bind(daftar_status=STATUS)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, user, row=None):
    """if not row:
        row = User()
    row.from_dict(values)
    if values['password']:
        row.password = values['password']
    DBSession.add(row)
    DBSession.flush()
    return row
    """
    row = {}
    row['email'] = 'aagusti@1'
    return row
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Tunggu beberpa saat.')
        
def route_list(request):
    return HTTPFound(location=request.route_url('pbbkb'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    

########                    
# List #
########    
@view_config(route_name='pbbkb', renderer='templates/pbbkb/list.pt',
             permission='edit')
def view_list(request):
    print request.user.id
    rows = DBSession.query(SptpdModel).filter(SptpdModel.create_uid==request.user.id).order_by('tahun','bulan')
    return dict(rows=rows)
    
    
########                    
# Add #
########    
@view_config(route_name='pbbkb-add', renderer='templates/pbbkb/add.pt',
             permission='edit')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_ADD_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('pbbkb-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form.render())
