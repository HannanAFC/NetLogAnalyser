from __future__ import annotations

import uuid
from datetime import datetime, timezone

from config import settings
from database import Base
from geoip import GeoStatus
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM, INET, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User( Base ):
    __tablename__ = "users"

    id:                        Mapped[ uuid.UUID ]                        = mapped_column( PGUUID( as_uuid=True ), primary_key=True, default=uuid.uuid4 )
    email:                     Mapped[ str ]                              = mapped_column( String( 255 ), unique=True, index=True , nullable=False )
    password_hash:             Mapped[ str ]                              = mapped_column( String( 255 ), nullable=False )
    display_name:              Mapped[ str ]                              = mapped_column( String( 50 ), nullable=False )
    created_at:                Mapped[ datetime ]                         = mapped_column( DateTime( timezone=True ), server_default=func.now( ) )
    updated_at:                Mapped[ datetime ]                         = mapped_column( DateTime( timezone=True ), server_default=func.now( ), onupdate=func.now( ) )
    email_verified_at:         Mapped[ datetime | None ]                  = mapped_column( DateTime( timezone=True ), nullable=True )
    api_keys:                  Mapped[ list[ APIKey ] ]                   = relationship( back_populates="user", cascade="all, delete-orphan" )
    refresh_tokens:            Mapped[ list[ RefreshToken ] ]             = relationship( back_populates="user", cascade="all, delete-orphan" )
    password_reset_tokens:     Mapped[ list[ PasswordResetToken ] ]       = relationship( back_populates="user", cascade="all, delete-orphan" )
    log_entries:               Mapped[ list[ LogEntry ] ]                 = relationship( back_populates="user", cascade="all, delete-orphan" )
    email_verification_tokens: Mapped[ list[ EmailVerificationToken ] ]   = relationship( back_populates="user", cascade="all, delete-orphan" )

    def __repr__(self):
        return f"""
id: { self.id }
email: { self.email }
display_name: { self.display_name }
created_at: { self.created_at }
updated_at: { self.updated_at }
                """
    

class APIKey( Base ):
    __tablename__ = "api_keys"

    id:           Mapped[ uuid.UUID ]       = mapped_column( PGUUID( as_uuid=True ), primary_key=True, default=uuid.uuid4 )
    user_id:      Mapped[ uuid.UUID ]       = mapped_column( PGUUID( as_uuid=True ), ForeignKey( "users.id", ondelete="CASCADE" ), index=True, nullable=False )
    key_hash:     Mapped[ str ]             = mapped_column( String( 64 ), nullable=False )
    key_prefix:   Mapped[ str ]             = mapped_column( String( settings.api_key_prefix_length ) )
    label:        Mapped[ str ]             = mapped_column( String( 50 ), nullable=False, default=lambda: f"key_{ datetime.now( timezone.utc ):%Y-%m-%d %H:%M }" )
    last_used_at: Mapped[ datetime | None ] = mapped_column( DateTime( timezone=True ), nullable=True )
    created_at:   Mapped[ datetime ]        = mapped_column( DateTime( timezone=True ), nullable=False, server_default=func.now( ) )
    revoked_at:   Mapped[ datetime | None ] = mapped_column( DateTime( timezone=True ), index=True )
    user:         Mapped[ User ]            = relationship( back_populates="api_keys" )

    __table_args__ = (
        Index( "ix_api_keys_user_id_revoked_at", "user_id", "revoked_at" ),
        Index( "ix_api_keys_user_id_created_at", "user_id", "created_at" ),
    )

    def __repr__(self):
        return f"""
id: { self.id }
user_id: { self.user_id }
key_prefix: { self.key_prefix }
label: { self.label }
last_used_at: { self.last_used_at }
created_at: { self.created_at }
revoked_at: { self.revoked_at }
                """

class RefreshToken( Base ):
    __tablename__ = "refresh_tokens"

    id:             Mapped[ uuid.UUID ]        = mapped_column( PGUUID( as_uuid=True ), primary_key=True, default=uuid.uuid4 )
    user_id:        Mapped[ uuid.UUID ]        = mapped_column( PGUUID( as_uuid=True ), ForeignKey( "users.id", ondelete="CASCADE" ), index=True, nullable=False )
    token_hash:     Mapped[ str ]              = mapped_column( String( 64 ), unique=True, index=True, nullable=False )
    expires_at:     Mapped[ datetime ]         = mapped_column( DateTime( timezone=True ), nullable=False )
    created_at:     Mapped[ datetime ]         = mapped_column( DateTime( timezone=True ), nullable=False, server_default=func.now( ) )
    revoked_at:     Mapped[ datetime | None ]  = mapped_column( DateTime( timezone=True ), nullable=True )
    family_id:      Mapped[ uuid.UUID ]        = mapped_column( PGUUID( as_uuid=True ), index=True, nullable=False )
    replaced_by_id: Mapped[ uuid.UUID | None ] = mapped_column( PGUUID( as_uuid=True ), ForeignKey( "refresh_tokens.id" ), nullable=True )
    ip_address:     Mapped[ str | None ]       = mapped_column( INET, nullable=True )
    user_agent:     Mapped[ str | None ]       = mapped_column( String( 255 ), nullable=True )
    user:           Mapped[ User ]             = relationship( back_populates="refresh_tokens" )

    __table_args__ = (
        Index( "ix_refresh_tokens_user_id_revoked_at", "user_id", "revoked_at" ),
    )

    def __repr__(self):
        return f"""
id: { self.id }
user_id: { self.user_id }
expires_at: { self.expires_at }
created_at: { self.created_at }
revoked_at: { self.revoked_at }
family_id: { self.family_id }
replaced_by_id: { self.replaced_by_id }
ip_address: { self.ip_address }
user_agent: { self.user_agent }
                """

class LogEntry( Base ):
    __tablename__ = "log_entries"

    id:                Mapped[ int ]          = mapped_column( BigInteger, primary_key=True, autoincrement=True )
    api_key_id:        Mapped[ uuid.UUID ]    = mapped_column( PGUUID( as_uuid=True ), ForeignKey( "api_keys.id", ondelete="CASCADE" ), index=True, nullable=False )
    user_id:           Mapped[ uuid.UUID ]    = mapped_column( PGUUID( as_uuid=True ), ForeignKey( "users.id", ondelete="CASCADE" ), index=True, nullable=False )

    src_ip:            Mapped[ str ]          = mapped_column( INET, index=True )       
    dst_ip:            Mapped[ str ]          = mapped_column( INET, index=True )
    src_port:          Mapped[ int ]          = mapped_column( Integer )
    dst_port:          Mapped[ int ]          = mapped_column( Integer )
    protocol:          Mapped[ str ]          = mapped_column( ENUM( "TCP", "UDP", "ICMP", "OTHER", name="protocol_enum" ), index=True )
    packet_size_bytes: Mapped[ int ]          = mapped_column( )
    flags:             Mapped[ str | None ]   = mapped_column( String( 20 ), nullable=True )
    src_country_code:  Mapped[ str | None ]   = mapped_column( String( 2 ), nullable=True )
    dst_country_code:  Mapped[ str | None ]   = mapped_column( String( 2 ), nullable=True )
    src_geo_status:    Mapped[ GeoStatus ]    = mapped_column( ENUM( GeoStatus, name="geo_status" ), nullable=False, index=True )
    dst_geo_status:    Mapped[ GeoStatus ]    = mapped_column( ENUM( GeoStatus, name="geo_status" ), nullable=False, index=True )
    anomaly_score:     Mapped[ float ]        = mapped_column( default=0.0, index=True )
    raw_payload:       Mapped[ dict ]         = mapped_column( JSONB )
    captured_at:       Mapped[ datetime ]     = mapped_column( DateTime( timezone=True ), nullable=False, index=True )
    inserted_at:       Mapped[ datetime ]     = mapped_column( DateTime( timezone=True ), server_default=func.now( ) )
    anomaly_reasons:   Mapped[ list[ dict ] ] = mapped_column( JSONB, nullable=False, server_default=text( "'[]'::jsonb" )
)
    user:              Mapped[ User ]         = relationship( back_populates="log_entries" )

    __table_args__ = (
        Index( "ix_log_entries_user_id_captured_at", "user_id", "captured_at" ),
    )

    def __repr__(self):
        return f"""
id: { self.id }
api_key_id: { self.api_key_id }
user_id: { self.user_id }
src_ip: { self.src_ip }
dst_ip: { self.dst_ip }
src_port: { self.src_port }
dst_port: { self.dst_port }
protocol: { self.protocol }
packet_size_bytes: { self.packet_size_bytes }
flags: { self.flags }
src_country_code: { self.src_country_code }
dst_country_code: { self.dst_country_code }
src_geo_status: { self.src_geo_status }
dst_geo_status: { self.dst_geo_status }
anomaly_score: { self.anomaly_score }
raw_payload: { self.raw_payload }
captured_at: { self.captured_at }
inserted_at: { self.inserted_at }
                """
    
class PasswordResetToken( Base ):
    __tablename__ = "password_reset_tokens"

    id:         Mapped[ uuid.UUID ]       = mapped_column( PGUUID( as_uuid=True ), primary_key=True, default=uuid.uuid4 )
    user_id:    Mapped[ uuid.UUID ]       = mapped_column( PGUUID( as_uuid=True ), ForeignKey( "users.id", ondelete="CASCADE" ), index=True, nullable=False )
    token_hash: Mapped[ str ]             = mapped_column( String( 64 ), unique=True, index=True, nullable=False )
    created_at: Mapped[ datetime ]        = mapped_column( DateTime( timezone=True ), server_default=func.now( ) )
    expires_at: Mapped[ datetime ]        = mapped_column( DateTime( timezone=True ), nullable=False )
    used_at:    Mapped[ datetime | None ] = mapped_column( DateTime( timezone=True ), nullable=True )
    user:       Mapped[ User ]            = relationship( back_populates="password_reset_tokens" )

class EmailVerificationToken( Base ):
    __tablename__ = "email_verification_tokens"

    id:         Mapped[ uuid.UUID ]       = mapped_column( PGUUID( as_uuid=True ), primary_key=True, default=uuid.uuid4 )
    user_id:    Mapped[ uuid.UUID ]       = mapped_column( PGUUID( as_uuid=True ), ForeignKey( "users.id", ondelete="CASCADE" ), index=True, nullable=False )
    token_hash: Mapped[ str ]             = mapped_column( unique=True, nullable=False )
    expires_at: Mapped[ datetime ]        = mapped_column( DateTime( timezone=True ), nullable=False )
    used_at:    Mapped[ datetime | None ] = mapped_column( DateTime( timezone=True ), nullable=True )
    created_at: Mapped[ datetime ]        = mapped_column( DateTime( timezone=True ), server_default=func.now( ), nullable=False )
    user:       Mapped[ User ]            = relationship( back_populates="email_verification_tokens" )

    __table_args__ = (
        Index( "ix_email_verification_tokens_user_id_used_at", "user_id", "used_at" ),
    )