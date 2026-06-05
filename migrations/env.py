from logging.config import fileConfig
from database.connection import Base, DATABASE_URL
from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

from models.person import Person
from models.case import Cases
from models.sighting import Sighting
from models.activity_log import ActivityLog
from models.alerts import Alerts
from models.agencies import Agencies
from models.cameras import Cameras
from models.data_matches import Data_Matches
from models.data_sources import Data_Source
from models.evidence import Evidence
from models.leads import Leads
from models.user import User
from models.timeline_events import Timeline_Event
from models.investigators import Investigators
from models.IntegrationSource import IntegrationSource
from models.match import Match
from models.external_record import ExternalRecord
from models.evidence_chain import EvidenceChain
from models.legal_access_request import LegalAccessRequest
from models.case_access_grant import CaseAccessGrant
from models.case_team_member import CaseTeamMember




# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
