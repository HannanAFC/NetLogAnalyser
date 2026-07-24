from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

VALID_PASSWORD = "Str0ng!Pass"
VALID_EMAIL = "alice@example.com"
VALID_DISPLAY_NAME = "Alice"
VALID_KEY_LABEL = "my-test-key"


def _build_register_payload(
    email: str = VALID_EMAIL,
    password: str = VALID_PASSWORD,
    confirm_password: str = VALID_PASSWORD,
    display_name: str = VALID_DISPLAY_NAME
) -> dict:
    return {
        "email": email,
        "password": password,
        "confirm_password": confirm_password,
        "display_name": display_name
    }


async def _register_user(
    client: AsyncClient,
    email: str = VALID_EMAIL,
    password: str = VALID_PASSWORD,
    display_name: str = VALID_DISPLAY_NAME
) -> Response:
    """Register a user and return the parsed JSON response."""
    payload = _build_register_payload(
        email=email, password=password, display_name=display_name
    )
    response = await client.post( "/auth/register", json=payload )
    return response


async def _login_user(
    client: AsyncClient,
    email: str = VALID_EMAIL,
    password: str = VALID_PASSWORD
) -> Response:
    """Login and return the parsed JSON response (access_token + user)."""
    response = await client.post(
        "/auth/login", json={ "email": email, "password": password }
    )
    return response


async def _verify_user_email(
    db_session: AsyncSession, email: str = VALID_EMAIL
) -> None:
    """Mark a user's email as verified directly in the database."""
    from datetime import datetime, timezone

    from models.models import EmailVerificationToken, User
    from sqlalchemy import select, update

    result = await db_session.execute(
        select( User ).where( User.email == email.lower( ) )
    )
    user = result.scalar_one_or_none( )
    assert user is not None, f"No user found with email { email }"

    await db_session.execute(
        update( EmailVerificationToken )
        .where(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used_at.is_( None ),
        )
        .values( used_at=datetime.now( timezone.utc ) )
    )

    user.email_verified_at = datetime.now( timezone.utc )
    await db_session.commit( )


async def _register_and_get_token(
    client: AsyncClient,
    db_session: AsyncSession,
    email: str = VALID_EMAIL,
    password: str = VALID_PASSWORD,
    display_name: str = VALID_DISPLAY_NAME
) -> tuple[str, Response]:
    """Register, verify email, login, and return (access_token, login_response)."""
    await _register_user( client, email=email, password=password, display_name=display_name )
    await _verify_user_email( db_session, email=email )
    login_resp = await _login_user( client, email=email, password=password )
    assert login_resp.status_code == 200
    return login_resp.json( )[ "access_token" ], login_resp


async def _create_api_key(
    client: AsyncClient,
    access_token: str,
    label: str = VALID_KEY_LABEL
) -> Response:
    """Create an API key and return the response."""
    return await client.post(
        "/api-keys",
        json={ "label": label },
        headers={ "Authorization": f"Bearer { access_token }" }
    )


# ═══════════════════════════════════════════════════════════════════
# Create API Key  POST /api-keys
# ═══════════════════════════════════════════════════════════════════

class TestCreateAPIKey:
    """Happy-path and validation tests for POST /api-keys."""

    @pytest.mark.anyio
    async def test_create_returns_201_with_key_data(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """A valid request must return 201 with the key object and raw key."""
        access_token, _ = await _register_and_get_token( client, db_session )

        response = await _create_api_key( client, access_token )

        assert response.status_code == 201
        data = response.json( )
        assert "id" in data
        assert data[ "label" ] == VALID_KEY_LABEL
        assert "key_prefix" in data
        assert "api_key" in data
        assert "created_at" in data
        # raw key must start with "key_"
        assert data[ "api_key" ].startswith( "key_" )
        # prefix must match the raw key
        assert data[ "api_key" ].startswith( data[ "key_prefix" ] )

    @pytest.mark.anyio
    async def test_create_without_auth_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Creating a key without authentication must return 401."""
        response = await client.post( "/api-keys", json={ "label": VALID_KEY_LABEL } )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_create_with_empty_label_returns_422(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """An empty label must be rejected with 422."""
        access_token, _ = await _register_and_get_token( client, db_session )

        response = await _create_api_key( client, access_token, label="" )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_create_with_missing_label_returns_422(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Omitting the label field must return 422."""
        access_token, _ = await _register_and_get_token( client, db_session )

        response = await client.post(
            "/api-keys",
            json={},
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_create_with_whitespace_label_fails(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """A label that is only whitespace is rejected (min_length=1 not satisfied)."""
        access_token, _ = await _register_and_get_token( client, db_session )

        response = await _create_api_key( client, access_token, label=" " )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_create_with_whitespace_removes_on_ends(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """A label that contains whitespace on the edges has it stripped"""
        access_token, _ = await _register_and_get_token( client, db_session )

        response = await _create_api_key( client, access_token, label=" Hello " )
        data = response.json( )

        assert data[ "label" ] == "Hello"

    @pytest.mark.anyio
    async def test_create_key_is_unique(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Two created keys must have different raw values and IDs."""
        access_token, _ = await _register_and_get_token( client, db_session )

        resp1 = await _create_api_key( client, access_token, label="key-1" )
        resp2 = await _create_api_key( client, access_token, label="key-2" )

        data1 = resp1.json( )
        data2 = resp2.json( )

        assert data1[ "id" ] != data2[ "id" ]
        assert data1[ "api_key" ] != data2[ "api_key" ]

    @pytest.mark.anyio
    async def test_create_key_raw_key_not_in_list_response(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """The raw API key must only appear in the create response, never in list."""
        access_token, _ = await _register_and_get_token( client, db_session )

        create_resp = await _create_api_key( client, access_token )
        assert "api_key" in create_resp.json( )

        list_resp = await client.get(
            "/api-keys",
            headers={ "Authorization": f"Bearer { access_token }" }
        )
        for key in list_resp.json( ):
            assert "api_key" not in key, "Raw key leaked in list response"


# ═══════════════════════════════════════════════════════════════════
# List API Keys  GET /api-keys
# ═══════════════════════════════════════════════════════════════════

class TestListAPIKeys:
    """Tests for GET /api-keys."""

    @pytest.mark.anyio
    async def test_list_returns_empty_when_no_keys(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """A new user with no API keys must get an empty list."""
        access_token, _ = await _register_and_get_token( client, db_session )

        response = await client.get(
            "/api-keys",
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert response.status_code == 200
        assert response.json( ) == [ ]

    @pytest.mark.anyio
    async def test_list_returns_all_created_keys(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """After creating multiple keys, all must appear in the list."""
        access_token, _ = await _register_and_get_token( client, db_session )

        labels = [ "key-a", "key-b", "key-c" ]
        created_ids: set[ str ] = set( )
        for label in labels:
            resp = await _create_api_key( client, access_token, label=label )
            assert resp.status_code == 201
            created_ids.add( resp.json( )[ "id" ] )

        response = await client.get(
            "/api-keys",
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert response.status_code == 200
        keys = response.json( )
        assert len( keys ) == 3
        returned_ids = { k[ "id" ] for k in keys }
        assert returned_ids == created_ids
        returned_labels = { k[ "label" ] for k in keys }
        assert returned_labels == set( labels )

    @pytest.mark.anyio
    async def test_list_includes_expected_fields(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Each key in the list must have id, label, key_prefix, created_at,
        last_used_at, revoked_at, and must not include key_hash or api_key."""
        access_token, _ = await _register_and_get_token( client, db_session )
        await _create_api_key( client, access_token, label="test-label" )

        response = await client.get(
            "/api-keys",
            headers={ "Authorization": f"Bearer { access_token }" } 
        )

        key = response.json( )[ 0 ]
        assert "id" in key
        assert "label" in key
        assert key["label"] == "test-label"
        assert "key_prefix" in key
        assert "created_at" in key
        assert "last_used_at" in key  # may be None
        assert "revoked_at" in key  # may be None
        assert "key_hash" not in key
        assert "api_key" not in key
        assert "user_id" not in key

    @pytest.mark.anyio
    async def test_list_is_user_scoped(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """User A must not see User B's API keys."""
        # User A
        token_a, _ = await _register_and_get_token(
            client, db_session, email="usera@example.com"
        )
        await _create_api_key( client, token_a, label="a-key" )

        # User B
        token_b, _ = await _register_and_get_token(
            client, db_session, email="userb@example.com"
        )
        await _create_api_key( client, token_b, label="b-key-1" )
        await _create_api_key( client, token_b, label="b-key-2" )

        # User A only sees their own key
        resp_a = await client.get(
            "/api-keys",
            headers={ "Authorization": f"Bearer { token_a }" }
        )
        assert len( resp_a.json( ) ) == 1
        assert resp_a.json( )[ 0 ][ "label" ] == "a-key"

        # User B sees both of theirs
        resp_b = await client.get(
            "/api-keys",
            headers={ "Authorization": f"Bearer { token_b }" }
        )
        assert len( resp_b.json( ) ) == 2

    @pytest.mark.anyio
    async def test_list_without_auth_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Listing keys without authentication must return 401."""
        response = await client.get( "/api-keys" )
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════
# Revoke (Delete) API Key  DELETE /api-keys/{key_id}
# ═══════════════════════════════════════════════════════════════════

class TestRevokeAPIKey:
    """Tests for DELETE /api-keys/{key_id}."""

    @pytest.mark.anyio
    async def test_revoke_returns_204(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Revoking a valid key must return 204 No Content."""
        access_token, _ = await _register_and_get_token( client, db_session )
        create_resp = await _create_api_key( client, access_token )
        key_id = create_resp.json( )[ "id" ]

        response = await client.delete(
            f"/api-keys/{ key_id }",
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert response.status_code == 204

    @pytest.mark.anyio
    async def test_revoke_then_list_shows_revoked(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """After revoking a key, it must still appear in the list with
        revoked_at set."""
        access_token, _ = await _register_and_get_token( client, db_session )
        create_resp = await _create_api_key( client, access_token )
        key_id = create_resp.json( )[ "id" ]

        # revoke it
        await client.delete(
            f"/api-keys/{ key_id }",
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        # list should still include it, with revoked_at populated
        list_resp = await client.get(
            "/api-keys",
            headers={ "Authorization": f"Bearer { access_token }" }
        )
        keys = list_resp.json( )
        assert len( keys ) == 1
        assert keys[ 0 ][ "id" ] == key_id
        assert keys[ 0 ][ "revoked_at" ] is not None

    @pytest.mark.anyio
    async def test_revoke_nonexistent_key_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Revoking a UUID that doesn't exist must return 404."""
        access_token, _ = await _register_and_get_token( client, db_session )

        fake_id = str( uuid.uuid4( ) )
        response = await client.delete(
            f"/api-keys/{ fake_id }",
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert response.status_code == 404
        assert "not found" in response.json( )[ "detail" ].lower( )

    @pytest.mark.anyio
    async def test_revoke_already_revoked_key_returns_409(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Revoking a key that is already revoked must return 409."""
        access_token, _ = await _register_and_get_token( client, db_session )
        create_resp = await _create_api_key( client, access_token )
        key_id = create_resp.json( )[ "id" ]

        # first revoke
        resp1 = await client.delete(
            f"/api-keys/{ key_id }",
            headers={ "Authorization": f"Bearer { access_token }" }
        )
        assert resp1.status_code == 204

        # second revoke
        resp2 = await client.delete(
            f"/api-keys/{ key_id }",
            headers={ "Authorization": f"Bearer { access_token }" }
        )
        assert resp2.status_code == 409
        assert "already been revoked" in resp2.json( )[ "detail" ].lower( )

    @pytest.mark.anyio
    async def test_revoke_another_users_key_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """User A must not be able to revoke User B's key (returns 404
        to avoid leaking information about other users' keys)."""
        # User A creates a key
        token_a, _ = await _register_and_get_token(
            client, db_session, email="usera@example.com"
        )
        create_resp = await _create_api_key( client, token_a )
        key_a_id = create_resp.json( )[ "id" ]

        # User B tries to revoke User A's key
        token_b, _ = await _register_and_get_token(
            client, db_session, email="userb@example.com"
        )
        response = await client.delete(
            f"/api-keys/{ key_a_id }",
            headers={ "Authorization": f"Bearer { token_b }" }
        )

        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_revoke_without_auth_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Revoking without authentication must return 401."""
        response = await client.delete( f"/api-keys/{ uuid.uuid4( ) }" )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_revoke_invalid_uuid_returns_422(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """A non-UUID string in the path must return 422."""
        access_token, _ = await _register_and_get_token( client, db_session )

        response = await client.delete(
            "/api-keys/not-a-uuid",
            headers={ "Authorization": f"Bearer { access_token }" }
        )

        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════════
# API Key Limit  POST /api-keys (max keys enforcement)
# ═══════════════════════════════════════════════════════════════════

class TestAPIKeyLimit:
    """Tests for the maximum API keys per user limit."""

    @pytest.mark.anyio
    async def test_create_up_to_limit_succeeds(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Creating keys up to the max limit must succeed."""
        from config import settings

        access_token, _ = await _register_and_get_token( client, db_session )

        for i in range( settings.api_key_max_per_user ):
            resp = await _create_api_key( client, access_token, label=f"key-{ i }" )
            assert resp.status_code == 201, f"Key { i } creation failed"

    @pytest.mark.anyio
    async def test_create_beyond_limit_returns_403(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Creating one more than the max limit must return 403."""
        from config import settings

        access_token, _ = await _register_and_get_token( client, db_session )

        # fill up to the limit
        for i in range( settings.api_key_max_per_user ):
            resp = await _create_api_key( client, access_token, label=f"key-{ i }" )
            assert resp.status_code == 201

        # one more must fail
        response = await _create_api_key( client, access_token, label="over-limit" )
        assert response.status_code == 403
        assert "maximum" in response.json( )[ "detail" ].lower( )

    @pytest.mark.anyio
    async def test_revoke_then_create_respects_limit(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """After revoking a key, a new one can be created within the limit."""
        from config import settings

        access_token, _ = await _register_and_get_token( client, db_session )

        # fill up to the limit
        created_ids: list[ str ] = [ ]
        for i in range( settings.api_key_max_per_user ):
            resp = await _create_api_key( client, access_token, label=f"key-{ i }" )
            assert resp.status_code == 201
            created_ids.append( resp.json( )[ "id" ] )

        # revoke one key
        revoke_resp = await client.delete(
            f"/api-keys/{ created_ids[ 0 ] }",
            headers={ "Authorization": f"Bearer { access_token }" }
        )
        assert revoke_resp.status_code == 204

        # now creating a new key should succeed
        new_resp = await _create_api_key( client, access_token, label="new-after-revoke" )
        assert new_resp.status_code == 201


# ═══════════════════════════════════════════════════════════════════
# Auth dependency on API key endpoints
# ═══════════════════════════════════════════════════════════════════

class TestAPIKeyAuth:
    """Verify all API key endpoints properly enforce authentication."""

    @pytest.mark.anyio
    async def test_create_with_expired_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """An obviously invalid JWT must be rejected."""
        response = await client.post(
            "/api-keys",
            json={ "label": "test" },
            headers={ "Authorization": "Bearer this.is.not.valid" }
        )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_create_with_tampered_token_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """A JWT whose signature has been tampered with must be rejected."""
        access_token, _ = await _register_and_get_token( client, db_session )

        response = await client.post(
            "/api-keys",
            json={ "label": "test" },
            headers={ "Authorization": f"Bearer { access_token }tampered" }
        )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_create_with_wrong_scheme_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Using 'Basic' auth instead of 'Bearer' must be rejected."""
        access_token, _ = await _register_and_get_token( client, db_session )

        response = await client.post(
            "/api-keys",
            json={ "label": "test" },
            headers={ "Authorization": f"Basic { access_token }" }
        )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_list_with_empty_bearer_returns_401(
        self, client: AsyncClient
    ) -> None:
        """An empty string after 'Bearer ' must be rejected."""
        response = await client.get(
            "/api-keys",
            headers={ "Authorization": "Bearer " }
        )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_list_with_nonexistent_user_returns_401(
        self, client: AsyncClient
    ) -> None:
        """A JWT for a user that doesn't exist must be rejected."""
        from auth.security import create_access_token

        fake_token = create_access_token( user_id=str( uuid.uuid4( ) ) )

        response = await client.get(
            "/api-keys",
            headers={ "Authorization": f"Bearer { fake_token }" }
        )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_revoke_with_missing_auth_header_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Deleting without an Authorization header must return 401."""
        access_token, _ = await _register_and_get_token( client, db_session )
        create_resp = await _create_api_key( client, access_token )
        key_id = create_resp.json( )[ "id" ]

        # clear cookies just in case
        client.cookies.clear()
        response = await client.delete( f"/api-keys/{ key_id }" )
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════
# No secrets leaked
# ═══════════════════════════════════════════════════════════════════

class TestAPIKeyNoSecrets:
    """Ensure API key hashes and raw keys never leak inappropriately."""

    @pytest.mark.anyio
    async def test_create_response_has_no_key_hash(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """The create response must not include the key_hash."""
        access_token, _ = await _register_and_get_token( client, db_session )

        response = await _create_api_key( client, access_token )
        body = response.text

        assert response.status_code == 201
        assert "key_hash" not in body

    @pytest.mark.anyio
    async def test_list_response_has_no_key_hash_or_raw_key(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """The list response must not include key_hash or api_key."""
        access_token, _ = await _register_and_get_token( client, db_session )
        await _create_api_key( client, access_token )

        response = await client.get(
            "/api-keys",
            headers={ "Authorization": f"Bearer { access_token }" }
        )
        body = response.text

        assert "key_hash" not in body
        assert "api_key" not in body
        assert "token_hash" not in body

    @pytest.mark.anyio
    async def test_error_responses_have_no_secrets(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Even error responses must not leak internal state."""
        access_token, _ = await _register_and_get_token( client, db_session )

        # 404 from revoke
        resp = await client.delete(
            f"/api-keys/{ uuid.uuid4( ) }",
            headers={ "Authorization": f"Bearer { access_token }" }
        )
        body = resp.text
        assert "key_hash" not in body
        assert "token_hash" not in body
