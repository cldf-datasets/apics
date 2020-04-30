SCHEMA="public"
DB="apics"

psql -Atc "select tablename from pg_tables where schemaname='$SCHEMA'" $DB |\
  while read TBL; do
    psql -c "COPY $SCHEMA.$TBL TO STDOUT WITH (format CSV, header true)" $DB > $TBL.csv
  done

