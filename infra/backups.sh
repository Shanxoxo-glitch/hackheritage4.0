#!/bin/bash
echo 'Creating PostgreSQL backup...'
docker exec sih-postgres pg_dump -U sih_user sih_db > backups.sql
