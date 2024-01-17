import os

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Function to parse custom arguments
def parse_custom_args(custom_args):
    args_dict = {}
    for arg in custom_args:
        if '=' not in arg:
            continue
        key, value = arg.split('=')
        args_dict[key] = value
    return args_dict

def retrieve_env(env):
    from sean_gpt.util.env import yaml_env
    yaml_env('sean_gpt_chart/values.yaml', prefix='sean_gpt_')
    yaml_env('config/values.yaml', prefix='sean_gpt_')
    if environment in ('prod', 'production'):
        yaml_env('config/production/secrets.yaml', prefix='sean_gpt_')
        yaml_env('config/production/values.yaml', prefix='sean_gpt_')
    elif environment in ('dev', 'development'):
        yaml_env('config/development/secrets.yaml', prefix='sean_gpt_')
        yaml_env('config/development/values.yaml', prefix='sean_gpt_')
    elif environment == 'local':
        yaml_env('config/local/test_secrets.yaml', prefix='sean_gpt_')
        yaml_env('config/local/values.yaml', prefix='sean_gpt_')
    else:
        raise ValueError('environment must be set to either "local", "development", or "production"')

# Accessing the custom arguments
custom_args = parse_custom_args(context.config.cmd_opts.x) if context.config.cmd_opts.x else {}

# values to indicate whether the script is generating or applying a migration
# alembic -x generate_or_migrate=generate revision --autogenerate -m "Initialize database"
# alembic -x generate_or_migrate=migrate upgrade head
# alembic -x generate_or_migrate=migrate -x migrate_outside_kubernetes upgrade head
# generate_or_migrate = generate or migrate
# environment = local, development (dev), or production (prod)
generate_or_migrate = custom_args.get('generate_or_migrate', None)
environment = custom_args.get('environment', 'local')
migrate_outside_kubernetes = 'migrate_outside_kubernetes' in context.config.cmd_opts.x

if generate_or_migrate == 'generate':
    # setup for autogeneration
    retrieve_env(environment)
    os.environ['sean_gpt_database_host'] = 'localhost'
    for env, val in os.environ.items():
        print(f'{env}={val}')
    from sean_gpt.model.ai import AI
    from sean_gpt.model.authenticated_user import AuthenticatedUser
    from sean_gpt.model.chat import Chat
    from sean_gpt.model.message import Message
    from sean_gpt.model.verification_token import VerificationToken
    from sean_gpt.model.file import File
    from sean_gpt.model.share_set import ShareSet
elif generate_or_migrate == 'migrate':
    # setup for migrations
    if migrate_outside_kubernetes:
        # Need to retrieve env variables if running outside of kubernetes
        retrieve_env(environment)
        os.environ['sean_gpt_database_host'] = 'localhost'
else:
    raise ValueError('generate_or_migrate must be set to either "generate" or "migrate"')

from logging.config import fileConfig

from sqlmodel import SQLModel

from sqlalchemy import engine_from_config
from sqlalchemy import pool

database_url = (
    f"{os.environ['sean_gpt_database_dialect']}{os.environ['sean_gpt_database_driver']}://"
    f"{os.environ['sean_gpt_api_db_user']}:{os.environ['sean_gpt_api_db_password']}@"
    f"{os.environ['sean_gpt_database_host']}:{os.environ['sean_gpt_database_port']}/"
    f"{os.environ['sean_gpt_database_name']}")
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

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
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_server_default=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
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
