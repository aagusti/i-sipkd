from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    String
    )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )
from zope.sqlalchemy import ZopeTransactionExtension
import transaction
import ziggurat_foundations.models
from ziggurat_foundations.models import BaseModel, UserMixin, GroupMixin
from ziggurat_foundations.models import GroupPermissionMixin, UserGroupMixin
from ziggurat_foundations.models import GroupResourcePermissionMixin, ResourceMixin
from ziggurat_foundations.models import UserPermissionMixin, UserResourcePermissionMixin
from ziggurat_foundations.models import ExternalIdentityMixin
from ziggurat_foundations import ziggurat_model_init
from pyramid.security import (
    Allow,
    Authenticated,
    Everyone,
    ALL_PERMISSIONS
    )
from pyramid.httpexceptions import (
    HTTPFound, HTTPNotFound
    )
    
from ..tools import as_timezone


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


##############
# Base model #
##############
class CommonModel(object):
    def to_dict(self): # Elixir like
        values = {}
        for column in self.__table__.columns:
            values[column.name] = getattr(self, column.name)
        return values
        
    def from_dict(self, values):
        for column in self.__table__.columns:
            if column.name in values:
                setattr(self, column.name, values[column.name])

    def as_timezone(self, fieldname):
        date_ = getattr(self, fieldname)
        return date_ and as_timezone(date_) or None


class DefaultModel(CommonModel):
    id = Column(Integer, primary_key=True)

    def save(self):
        if self.id:
            #Who knows another user edited, so use merge ()
            DBSession.merge(self)
        else:
            DBSession.add(self)    
        
    @classmethod
    def query(cls):
        return DBSession.query(cls)

    @classmethod
    def query_id(cls, id):
        return cls.query().filter_by(id=id)
        
    @classmethod
    def get_by_id(cls, id):
        return cls.query_id(id).first()                

    @classmethod
    def delete(cls, id):
        cls.query_id(id).delete()

class KodeModel(DefaultModel):
    kode = Column(String, unique=True)

    @classmethod
    def query_kode(cls, kode):
        return cls.query().filter_by(kode=kode)
        
    @classmethod
    def get_by_kode(cls, kode):
        return cls.query_kode(kode).first()                


class Group(GroupMixin, Base):
    pass

class GroupPermission(GroupPermissionMixin, Base):
    pass


class UserGroup(UserGroupMixin, Base):
    @classmethod
    def get_by_email(cls, email):
        user = User.get_by_email(email)
        return cls.get_by_user(user)
        
    @classmethod
    def _get_by_user(cls, user):
        return DBSession.query(cls).filter_by(user_id=user.id).all()
        
    @classmethod
    def get_by_user(cls, user):
        groups = []
        for g in cls._get_by_user(user):
            groups.append(g.group_id)
        return groups
                
    @classmethod
    def set_one(cls, session, user, group):
        member = DBSession.query(cls).filter_by(user_id=user.id, group_id=group.id)
        try:
            member = member.one()
        except NoResultFound:
            member = cls(user_id=user.id, group_id=group.id)
            DBSession.add(member)
            transaction.commit()
        
    @classmethod
    def set_all(cls, user, group_ids=[]):
        if type(user) in [StringType, UnicodeType]:
            user = User.get_by_email(user)
        olds = cls._get_by_user(user)
        news = []
        for group_id in group_ids:
            group = DBSession.query(Group).get(group_id)
            member = cls.set_one(user, group)
            news.append(group)
        for old in olds:
            if old not in news:
                old.delete()
                DBSession.commit()
                
    @classmethod
    def get_by_group(cls, group):
        users = []
        for g in DBSession.query(cls).filter_by(group=group):
            users.append(g.user)
        return users                


class GroupResourcePermission(GroupResourcePermissionMixin, Base):
    pass

class Resource(ResourceMixin, Base):
    pass

class UserPermission(UserPermissionMixin, Base):
    pass

class UserResourcePermission(UserResourcePermissionMixin, Base):
    pass


class User(UserMixin, BaseModel, CommonModel, Base):
    last_login_date = Column(DateTime(timezone=True), nullable=True)
    registered_date = Column(DateTime(timezone=True),
                             nullable=False,
                             default=datetime.utcnow)

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = self.set_password(password)

    password = property(_get_password, _set_password)

    def get_groups(self):
        return UserGroup.get_by_user(self)

    def last_login_date_tz(self):
        return as_timezone(self.last_login_date)
        
    def registered_date_tz(self):
        return as_timezone(self.registered_date)
        
    def nice_username(self):
        return self.user_name or self.email

    @classmethod
    def get_by_email(cls, email):
        return DBSession.query(cls).filter_by(email=email).first()

    @classmethod
    def get_by_name(cls, name):
        return DBSession.query(cls).filter_by(user_name=name).first()        
        
    @classmethod
    def get_by_identity(cls, identity):
        if identity.find('@') > -1:
            return cls.get_by_email(identity)
        return cls.get_by_name(identity)        
            

class ExternalIdentity(ExternalIdentityMixin, Base):
    pass
    

class RootFactory(object):
    def __init__(self, request):
        self.__name__ = ''
        self.__acl__ = [
            (Allow, Authenticated, 'delete'),
            (Allow, Authenticated, 'view'),
            (Allow, Authenticated, 'read'),
            (Allow, Authenticated, 'edit'),
            (Allow, Authenticated, 'add'),
            (Allow, Authenticated, 'delete'),
            
            (Allow, 'Admin', ALL_PERMISSIONS),
            (Allow, 'Staff', 'view'),
            (Allow, Everyone, 'view'),
            
            ]

class UserResourceFactory(object):
    def __init__(self, request):
        self.__acl__ = []
        rid = request.matchdict.get("resource_id") or 1

        if not rid:
            raise HTTPNotFound()
        self.resource = Resource.by_resource_id(rid)
        if not self.resource:
            raise HTTPNotFound()
        if self.resource and request.user:
            # append basic resource acl that gives all permissions to owner
            self.__acl__ = self.resource.__acl__
            # append permissions that current user may have for this context resource
            for perm_user, perm_name in self.resource.perms_for_user(request.user):
                self.__acl__.append((Allow, perm_user, perm_name,))

class GroupResourceFactory(object):
    def __init__(self, request):
        self.__acl__ = [(Allow,'Admin',ALL_PERMISSIONS),
                        (Allow, Everyone, 'view'),]
        rid = request.matchdict.get("resource_id") or 1
        if not rid:
            raise HTTPNotFound()
        self.resource = Resource.by_resource_id(rid)
        if not self.resource:
            raise HTTPNotFound()
        if self.resource and request.user:
            #groups = group_finder(request.user)
            # append basic resource acl that gives all permissions to owner
            self.__acl__ = self.resource.__acl__
            # append permissions that current user may have for this context resource
            for perm_group, perm_name in self.resource.perms_for_group(request.user):
                self.__acl__.append((Allow, 'g:%s' % perm_group, perm_name,))
                
def init_model():
    ziggurat_model_init(User, Group, UserGroup, GroupPermission, UserPermission,
                   UserResourcePermission, GroupResourcePermission, Resource,
                   ExternalIdentity, passwordmanager=None)
