from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Define the Roles model
class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String)

    user_memberships = relationship("UserMembership", back_populates="role")
    need_methods = relationship("NeedMethod", back_populates="role")

# Define the Users model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String)

    user_memberships = relationship("UserMembership", back_populates="user")

# Define the Memberships model
class Membership(Base):
    __tablename__ = 'memberships'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('memberships.id'))
    name = Column(String)

    parent = relationship("Membership", remote_side=[id], back_populates="children")
    children = relationship("Membership", back_populates="parent")
    user_memberships = relationship("UserMembership", back_populates="membership")
    membership_data_object_types = relationship("MembershipDataObjectType", back_populates="membership")
    membership_needs = relationship("MembershipNeed", back_populates="membership")
    source_memberships = relationship("SourceMembership", back_populates="membership")
    membership_data_object_type_allowed_attributes = relationship("MembershipDataObjectTypeAllowedAttribute", back_populates="membership")

# Define the UserMemberships model
class UserMembership(Base):
    __tablename__ = 'user_memberships'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    membership_id = Column(Integer, ForeignKey('memberships.id'))
    role_id = Column(Integer, ForeignKey('roles.id'))

    user = relationship("User", back_populates="user_memberships")
    membership = relationship("Membership", back_populates="user_memberships")
    role = relationship("Role", back_populates="user_memberships")

# Define the DataObjectTypes model
class DataObjectType(Base):
    __tablename__ = 'data_object_types'
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('sources.id'))
    name = Column(String)

    source = relationship("Source", back_populates="data_object_types")
    membership_data_object_types = relationship("MembershipDataObjectType", back_populates="data_object_type")
    data_object_type_attributes = relationship("DataObjectTypeAttribute", back_populates="data_object_type")
    needs = relationship("Need", back_populates="data_object_type")

# Define the DataObjectTypeAttributes model
class DataObjectTypeAttribute(Base):
    __tablename__ = 'data_object_type_attributes'
    id = Column(Integer, primary_key=True)
    data_object_type_id = Column(Integer, ForeignKey('data_object_types.id'))
    name = Column(String)

    data_object_type = relationship("DataObjectType", back_populates="data_object_type_attributes")
    membership_data_object_type_allowed_attributes = relationship("MembershipDataObjectTypeAllowedAttribute", back_populates="data_object_type_attribute")

# Define the MembershipDataObjectTypes model
class MembershipDataObjectType(Base):
    __tablename__ = 'membership_data_object_types'
    id = Column(Integer, primary_key=True)
    membership_id = Column(Integer, ForeignKey('memberships.id'))
    data_object_type_id = Column(Integer, ForeignKey('data_object_types.id'))

    membership = relationship("Membership", back_populates="membership_data_object_types")
    data_object_type = relationship("DataObjectType", back_populates="membership_data_object_types")
    membership_data_object_type_allowed_attributes = relationship("MembershipDataObjectTypeAllowedAttribute", back_populates="membership_data_object_type")

# Define the MembershipDataObjectTypeAllowedAttributes model
class MembershipDataObjectTypeAllowedAttribute(Base):
    __tablename__ = 'membership_data_object_type_allowed_attributes'
    id = Column(Integer, primary_key=True)
    membership_data_object_type_id = Column(Integer, ForeignKey('membership_data_object_types.id'))
    data_object_type_attribute_id = Column(Integer, ForeignKey('data_object_type_attributes.id'))

    membership_data_object_type = relationship("MembershipDataObjectType", back_populates="membership_data_object_type_allowed_attributes")
    data_object_type_attribute = relationship("DataObjectTypeAttribute", back_populates="membership_data_object_type_allowed_attributes")

# Define the MembershipNeeds model
class MembershipNeed(Base):
    __tablename__ = 'membership_needs'
    id = Column(Integer, primary_key=True)
    membership_id = Column(Integer, ForeignKey('memberships.id'))
    need_id = Column(Integer, ForeignKey('needs.id'))

    membership = relationship("Membership", back_populates="membership_needs")
    need = relationship("Need", back_populates="membership_needs")

# Define the Sources model
class Source(Base):
    __tablename__ = 'sources'
    id = Column(Integer, primary_key=True)
    name = Column(String)

    data_object_types = relationship("DataObjectType", back_populates="source")
    source_memberships = relationship("SourceMembership", back_populates="source")

# Define the SourceMemberships model
class SourceMembership(Base):
    __tablename__ = 'source_memberships'
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('sources.id'))
    membership_id = Column(Integer, ForeignKey('memberships.id'))
    source_member_ship_object_name = Column(String)

    source = relationship("Source", back_populates="source_memberships")
    membership = relationship("Membership", back_populates="source_memberships")

# Define the Needs model
class Need(Base):
    __tablename__ = 'needs'
    id = Column(Integer, primary_key=True)
    data_object_type_id = Column(Integer, ForeignKey('data_object_types.id'))

    data_object_type = relationship("DataObjectType", back_populates="needs")
    membership_needs = relationship("MembershipNeed", back_populates="need")
    need_methods = relationship("NeedMethod", back_populates="need")

# Define the NeedMethods model
class NeedMethod(Base):
    __tablename__ = 'need_methods'
    id = Column(Integer, primary_key=True)
    need_id = Column(Integer, ForeignKey('needs.id'))
    method_id = Column(Integer, ForeignKey('methods.id'))
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)

    need = relationship("Need", back_populates="need_methods")
    method = relationship("Method", back_populates="need_methods")
    role = relationship("Role", back_populates="need_methods")

# Define the Methods model
class Method(Base):
    __tablename__ = 'methods'
    id = Column(Integer, primary_key=True)
    identifier = Column(String)

    need_methods = relationship("NeedMethod", back_populates="method")

# Set up the engine and session
engine = create_engine('sqlite:///:memory:')  # Use an actual database URI in production
Base.metadata.create_all(engine)
