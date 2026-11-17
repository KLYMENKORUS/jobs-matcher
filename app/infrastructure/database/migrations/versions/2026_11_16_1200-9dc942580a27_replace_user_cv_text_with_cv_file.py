"""replace users.cv_text with users.cv_file

Revision ID: 9dc942580a27
Revises: a603000141cd
Create Date: 2026-11-16 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9dc942580a27"
down_revision: str | Sequence[str] | None = "a603000141cd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # not a rename: cv_text held the CV itself, cv_file holds a path to it,
    # so the stored texts are dropped and users have to upload a file
    op.add_column(
        "users", sa.Column("cv_file", sa.String(length=512), nullable=True)
    )
    op.drop_column("users", "cv_text")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("users", sa.Column("cv_text", sa.Text(), nullable=True))
    op.drop_column("users", "cv_file")
