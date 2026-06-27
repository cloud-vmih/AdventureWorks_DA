from sqlalchemy import create_engine
from src.common.config import get_db_config

def get_engine(db_type):
    """
    Get sqlalchemy engine for 'oltp' or 'dwh' databases.
    """
    db_cfg = get_db_config()[db_type]
    url = f"postgresql://{db_cfg['user']}:{db_cfg['password']}@{db_cfg['host']}:{db_cfg['port']}/{db_cfg['database']}"
    return create_engine(url)

def get_oltp_engine():
    return get_engine('oltp')

def get_dwh_engine():
    return get_engine('dwh')
