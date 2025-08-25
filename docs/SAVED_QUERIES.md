# Saved Queries

Use these Maximo saved queries to monitor work-order exceptions.

## Work orders started without a permit

```
status='INPRG' AND (permit_id IS NULL OR permit_verified=0)
```

## Missing closure evidence

```
status='COMP' AND (closure_evidence IS NULL OR closure_evidence='')
```

## Review cadence

Review the results of each query weekly and track exception counts. After cutover, counts should trend toward zero.
