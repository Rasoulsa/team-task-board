from app.api.rbac import role_allows
from app.models.enums import OrganizationRole


def test_owner_allows_everything() -> None:
    assert role_allows(OrganizationRole.OWNER, OrganizationRole.ADMIN)
    assert role_allows(OrganizationRole.OWNER, OrganizationRole.MEMBER)
    assert role_allows(OrganizationRole.OWNER, OrganizationRole.VIEWER)


def test_admin_allows_member_and_viewer() -> None:
    assert role_allows(OrganizationRole.ADMIN, OrganizationRole.MEMBER)
    assert role_allows(OrganizationRole.ADMIN, OrganizationRole.VIEWER)


def test_member_does_not_allow_admin() -> None:
    assert not role_allows(OrganizationRole.MEMBER, OrganizationRole.ADMIN)


def test_viewer_is_read_only() -> None:
    assert role_allows(OrganizationRole.VIEWER, OrganizationRole.VIEWER)
    assert not role_allows(OrganizationRole.VIEWER, OrganizationRole.MEMBER)
