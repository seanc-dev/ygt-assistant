import os
from pathlib import Path


def test_migration_file_present():
    mig_dir = Path('supabase/migrations')
    files = list(mig_dir.glob('*_add_ygt_assistant_tables.sql'))
    assert files, 'Expected migration file for YGT Assistant tables'


def test_migration_contains_expected_tables():
    mig_dir = Path('supabase/migrations')
    files = sorted(mig_dir.glob('*_add_ygt_assistant_tables.sql'))
    assert files, 'Missing migration file'
    content = files[-1].read_text()
    for table in ['approvals', 'drafts', 'automations', 'core_memory']:
        assert f"create table if not exists {table}" in content
    assert 'create extension if not exists vector' in content
