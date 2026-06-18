from __future__ import annotations

import uuid
from datetime import datetime, timezone

from config import settings
from database import Base
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM, INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User( Base ):
    __tablename__ = "users"

    id:                    Mapped[ UUID ]                         = mapped_column( UUID( as_uuid=True ), primary_key=True, default=uuid.uuid4 )
    email:                 Mapped[ str ]                          = mapped_column( String( 255 ), unique=True, index=True , nullable=False )
    password_hash:         Mapped[ str ]                          = mapped_column( String( 255 ), nullable=False )
    display_name:          Mapped[ str ]                          = mapped_column( String( 50 ), nullable=False )
    created_at:            Mapped[ datetime ]                     = mapped_column( DateTime( timezone=True ), server_default=func.now( ) )
    updated_at:            Mapped[ datetime ]                     = mapped_column( DateTime( timezone=True ), server_default=func.now( ), onupdate=func.now( ) )
    api_keys:              Mapped[ list[ "APIKey" ] ]             = relationship( back_populates="user" )
    refresh_tokens:        Mapped[ list[ "RefreshToken" ] ]       = relationship( back_populates="user" )
    password_reset_tokens: Mapped[ list[ "PasswordResetToken" ] ] = relationship( back_populates="user" )
    log_entries:           Mapped[ list[ "LogEntry" ] ]           = relationship( back_populates="user" )
    

class APIKey( Base ):
    __tablename__ = "api_keys"

    id:           Mapped[ UUID ]            = mapped_column( UUID( as_uuid=True ), primary_key=True, default=uuid.uuid4 )
    user_id:      Mapped[ UUID ]            = mapped_column( UUID( as_uuid=True ), ForeignKey( "users.id", ondelete="CASCADE" ), index=True, nullable=False )
    key_hash:     Mapped[ str ]             = mapped_column( String( 64 ), nullable=False )
    key_prefix:   Mapped[ str ]             = mapped_column( String( settings.api_key_prefix_length ) )
    label:        Mapped[ str ]             = mapped_column( String( 50 ), nullable=False, default=lambda: f"key_{ datetime.now( timezone.utc ):%Y-%m-%d %H:%M }" )
    is_active:    Mapped[ bool ]            = mapped_column( Boolean, nullable=False, server_default=text( "true" ) )
    last_used_at: Mapped[ datetime | None ] = mapped_column( DateTime( timezone=True ), nullable=True )
    created_at:   Mapped[ datetime ]        = mapped_column( DateTime( timezone=True ), nullable=False, server_default=func.now( ) )
    revoked_at:   Mapped[ datetime | None ] = mapped_column( DateTime( timezone=True ) )
    user:         Mapped[ User ]            = relationship( back_populates="api_keys" )

class RefreshToken( Base ):
    __tablename__ = "refresh_tokens"

    id:             Mapped[ UUID ]            = mapped_column( UUID( as_uuid=True ), primary_key=True, default=uuid.uuid4 )
    user_id:        Mapped[ UUID ]            = mapped_column( UUID( as_uuid=True ), ForeignKey( "users.id", ondelete="CASCADE" ), index=True, nullable=False )
    token_hash:     Mapped[ str ]             = mapped_column( String( 64 ), unique=True, index=True, nullable=False )
    expires_at:     Mapped[ datetime ]        = mapped_column( DateTime( timezone=True ), nullable=False )
    created_at:     Mapped[ datetime ]        = mapped_column( DateTime( timezone=True ), nullable=False, server_default=func.now( ) )
    revoked_at:     Mapped[ datetime | None ] = mapped_column( DateTime( timezone=True ), nullable=True )
    family_id:      Mapped[ UUID ]            = mapped_column( UUID( as_uuid=True ), index=True, nullable=False )
    replaced_by_id: Mapped[UUID | None]       = mapped_column( UUID( as_uuid=True ), ForeignKey( "refresh_tokens.id" ), nullable=True )
    ip_address:     Mapped[ str | None ]      = mapped_column( INET, nullable=True )
    user_agent:     Mapped[ str | None ]      = mapped_column( String( 255 ), nullable=True )
    user:           Mapped[ User ]            = relationship( back_populates="refresh_tokens" )

class LogEntry( Base ):
    __tablename__ = "log_entries"

    id:                Mapped[ int ]        = mapped_column( BigInteger, primary_key=True, autoincrement=True )
    api_key_id:        Mapped[ UUID ]       = mapped_column( UUID( as_uuid=True ), ForeignKey( "api_keys.id", ondelete="CASCADE" ), index=True, nullable=False )
    user_id:           Mapped[ UUID ]       = mapped_column( UUID( as_uuid=True ), ForeignKey( "users.id", ondelete="CASCADE" ), index=True, nullable=False )

    src_ip:            Mapped[ str ]        = mapped_column( INET, index=True )       
    dst_ip:            Mapped[ str ]        = mapped_column( INET, index=True )
    src_port:          Mapped[ int ]        = mapped_column( SmallInteger )
    dst_port:          Mapped[ int ]        = mapped_column( SmallInteger )
    protocol:          Mapped[ str ]        = mapped_column( ENUM( "TCP", "UDP", "ICMP", "OTHER", name="protocol_enum" ), index=True )
    packet_size_bytes: Mapped[ int ]        = mapped_column( )
    flags:             Mapped[ str | None ] = mapped_column( String( 20 ), nullable=True )
    country_code:      Mapped[ str | None ] = mapped_column( String( 2 ), nullable=True, index=True )
    anomaly_score:     Mapped[ float ]      = mapped_column( default=0.0, index=True )
    raw_payload:       Mapped[ dict ]       = mapped_column( JSONB )
    captured_at:       Mapped[ datetime ]   = mapped_column( DateTime( timezone=True ), nullable=False, index=True )
    inserted_at:       Mapped[ datetime ]   = mapped_column( DateTime( timezone=True ), server_default=func.now( ) )
    user:              Mapped[ User ]       = relationship( back_populates="log_entries" )
    
class PasswordResetToken( Base ):
    __tablename__ = "password_reset_tokens"

    id:         Mapped[ UUID ]            = mapped_column( UUID( as_uuid=True ), primary_key=True, default=uuid.uuid4 )
    user_id:    Mapped[ UUID ]            = mapped_column( UUID( as_uuid=True ), ForeignKey( "users.id", ondelete="CASCADE" ), index=True, nullable=False )
    token_hash: Mapped[ str ]             = mapped_column( String( 64 ), unique=True, index=True, nullable=False )
    created_at: Mapped[ datetime ]        = mapped_column( DateTime( timezone=True ), server_default=func.now( ) )
    expires_at: Mapped[ datetime ]        = mapped_column( DateTime( timezone=True ), nullable=False )
    used_at:    Mapped[ datetime | None ] = mapped_column( DateTime( timezone=True ), nullable=True )
    user:       Mapped[ User ]            = relationship( back_populates="password_reset_tokens" )