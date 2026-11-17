"""interaction_status: add 'rejected', drop 'ignored'; analysis gets cv / prefilter states

Revision ID: 5e2b7c9d1f34
Revises: 9dc942580a27
Create Date: 2026-11-16 18:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5e2b7c9d1f34"
down_revision: str | Sequence[str] | None = "9dc942580a27"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_VALUES: tuple[str, ...] = (
    "new",
    "rejected",
    "pending",
    "sent",
    "applied",
    "skipped",
)
OLD_VALUES: tuple[str, ...] = (
    "new",
    "pending",
    "sent",
    "applied",
    "skipped",
    "ignored",
)


def _recreate_enum(values: tuple[str, ...]) -> None:
    # Postgres can not drop an enum value: build a new type and move the column
    labels: str = ", ".join(f"'{value}'" for value in values)
    op.execute("ALTER TYPE interaction_status RENAME TO interaction_status_old")
    op.execute(f"CREATE TYPE interaction_status AS ENUM ({labels})")
    op.execute(
        "ALTER TABLE user_vacancy_interactions ALTER COLUMN status "
        "TYPE interaction_status USING status::text::interaction_status"
    )
    op.execute("DROP TYPE interaction_status_old")


def upgrade() -> None:
    """Upgrade schema."""
    # 'ignored' meant the same as 'skipped'
    op.execute(
        "UPDATE user_vacancy_interactions SET status = 'skipped' WHERE status = 'ignored'"
    )
    _recreate_enum(NEW_VALUES)

    # analysis states: START=1, ANALYZE_VACANCIES 2 -> 4, COMPLETED 3 -> 5;
    # an unfinished run resumes at the same state
    op.execute(
        "UPDATE task_runs SET execution_status = execution_status + 2 "
        "WHERE task_type = 'analysis' AND execution_status >= 2"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "UPDATE task_runs SET execution_status = CASE "
        "WHEN execution_status = 5 THEN 3 WHEN execution_status >= 2 THEN 2 "
        "ELSE execution_status END "
        "WHERE task_type = 'analysis'"
    )
    op.execute(
        "UPDATE user_vacancy_interactions SET status = 'skipped' WHERE status = 'rejected'"
    )
    _recreate_enum(OLD_VALUES)
